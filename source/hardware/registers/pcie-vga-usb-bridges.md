# AST2050 PCI-slave endpoint, VGA/USB & AHB bridges

Register-by-register reference for the Aspeed **AST2050 (G3)** host-facing blocks:
the **PCI-slave (VGA/PCIe) endpoint**, the **VGA display + Video (capture)
Engine**, the **USB 2.0 virtual hub**, and the three **AHB access/steer
mechanisms** (AHB remap, the **P2A** PCIe-to-AHB bridge, and the **iLPC-to-AHB**
bridge) that provide out-of-band bring-up on a dead-firmware board. The UARTs,
VIC and timers are on {doc}`uart-vic-timers`.

Citations use these short forms: [DS §N p.P](#sources) = the *AST2050/AST1100 A3
Datasheet V1.05* (25 May 2010), chapter N / printed page P; repository filenames
(e.g. [g3-vic patch](#sources), [TIMER-RCA](#sources), [P2A-BOOT](#sources), [CULVERT-G3](#sources),
[`hwreg.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h), [`ast2050.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/ast2050.h)) = hardware-verified reverse-engineering in the
program repo; named URLs = external cross-references (see **Sources**). Every
load-bearing value is backed by at least two of these.

## PCI-slave endpoint, VGA & Video Engine

The AST2050 presents itself to the host over a 32-bit / 33 MHz **PCI slave**
function (the "PCIe/VGA endpoint" of a board like the C410X is this PCIS block).
The endpoint fronts three internal engines — the **VGA display controller**, the
**2D graphics engine**, and the **P2A bridge** — sharing the top of SDRAM as a
frame buffer. [DS §33.1 p.363](#sources), [DS §34.1 p.369](#sources)

### PCI-slave configuration space (PCIS)

13 PCI config registers; `Init` values reflect the power-on defaults.
[DS §33 p.363-368](#sources)

```{list-table} PCI Slave Controller config registers
:header-rows: 1
:widths: 10 26 16 48

* - Offset
  - Register
  - Init
  - Function
* - `0x00`
  - **PCIS00** Device/Vendor ID
  - `0x2000_1A03`
  - Device `0x2000`, Vendor `0x1A03` (ASPEED). Overridable via `SCU30`
* - `0x04`
  - **PCIS04** Command/Status
  - `0x0210_0000`
  - Command/status:
    - bit1 mem-space-enable
    - bit0 IO-space-enable
    - bit10 INT-disable
    - status: caps-list=1, DEVSEL=medium
* - `0x08`
  - **PCIS08** Class/Revision
  - `0x0X00_0010`
  - Class `0x030000` (VGA) when VGA enabled, else `0x040000` (video); overridable via `SCU38`, `SCU70[15]`
* - `0x0C`
  - **PCIS0C** Misc (BIST/header/latency/cacheline)
  - `0x0000_0000`
  - BIST/bus-master unsupported; header type 0
* - `0x10`
  - **PCIS10** BAR0 (linear frame buffer)
  - `0x0000_0000`
  - Re-locatable **8/16/32/64 MB** frame-buffer aperture; size set by trapping (`SCU70[3:2]`)
* - `0x14`
  - **PCIS14** BAR1 (MMIO)
  - `0x0000_0000`
  - **128 KB** MMIO: first 64 KB = VGA I/O, **second 64 KB = P2A bridge window** (`MMIOBASE`)
* - `0x18`
  - **PCIS18** BAR2 (relocatable I/O)
  - `0x0000_0001`
  - 128 KB I/O space for VGA legacy + extended I/O cycles
* - `0x2C`
  - **PCIS2C** Subsystem ID
  - `0x2000_1A03`
  - Per-byte write-once; Subsystem `0x2000`, Sub-vendor `0x1A03`
* - `0x30`
  - **PCIS30** Expansion ROM BAR
  - `0x0000_0000`
  - 64 KB VGA-BIOS aperture (disabled by trapping when BIOS merged with system BIOS)
* - `0x34`
  - **PCIS34** Capability pointer
  - `0x0000_0040`
  - Points to `0x40` (PCI Power-Management capability)
* - `0x3C`
  - **PCIS3C** Interrupt
  - `0x0000_0100`
  - Interrupt pin INTA# (`0x01`); interrupt line RW (no HW effect)
* - `0x40`
  - **PCIS40** PM Capability
  - `0xFFC3_0001`
  - PME from D0/D1/D2/D3hot/D3cold; PM spec rev 1.2
* - `0x44`
  - **PCIS44** PM Control/Status
  - `0x0000_0000`
  - - `[1:0]` power state D0–D3 (also gates HSYNC/VSYNC/DAC)
    - bit8 PME-enable
    - bit15 PME-status
```

```{admonition} PCIS14 second 64 KB = the P2A window
:class: important

BAR1 carves 128 KB of host MMIO into **two 64 KB halves**: the first is the VGA
MMIO aperture; the **second 64 KB is the P2A (P-Bus-to-AHB) bridge window** —
`MMIOBASE + 0x10000 … MMIOBASE + 0x1FFFF`. That second half is exactly what
`culvert p2a vga` drives to reach the BMC's AHB from the host. [DS §33 p.366](#sources),
[DS §36.2 p.400](#sources), [CULVERT-G3](#sources)
```

`PCIS04[1]` (memory-space-enable) and `PCIS04[0]` (IO-space-enable) gate whether
the endpoint answers host cycles at all. `PCIS44[1:0]` maps PCI power states to
display behaviour: D0=Active (HSYNC/VSYNC/DAC on), D1=Standby, D2=Suspend,
D3=Off. [DS §33 p.364, p.368](#sources)

### VGA display controller

IBM-VGA-compatible CRTC with a 200 MHz triple-DAC, up to 1920×1200@60, VESA DDC,
and a 64×64 hardware overlay cursor (§37). The standard VGA register file is at
its legacy I/O addresses (also memory-mapped for advanced OSes). [DS §34 p.369](#sources)

```{list-table} VGA display controller — standard registers (legacy I/O)
:header-rows: 1
:widths: 16 18 66

* - I/O
  - Register
  - Function
* - `0x3C3`
  - **VGAER** Enable
  - bit0 VGA enable (`1`=VGA, class `0x030000`; `0`=video device, class `0x040000`)
* - `0x3C2`(W)/`0x3CC`(R)
  - **VGAMR** Misc Output
  - sync polarity (bits 7/6), page bit (5), clock-select `[3:2]` (`00`=25.175, `01`=28.322 MHz, `1x`=D-PLL), video-mem enable (1), I/O 3Bx/3Dx (0)
* - `0x3BA/3DA`(W)/`0x3CA`(R)
  - **VGAFCR** Feature Control
  - feature control bits `[3]`, `[1:0]`
* - `0x3C2`(R)
  - **VGAIR0** Input Status 0
  - - bit7 vertical-retrace interrupt flag
    - bit4 DAC comparator readback
* - `0x3BA/3DA`(R)
  - **VGAIR1** Input Status 1
  - diagnostic `[5:4]`, vertical-retrace (3), display-enable inversion (0)
* - `0x3CD` / `0x3CB`
  - **VGAFBR0/1** Frame-buffer Segment
  - 8-bit segment read/write address (banked window)
* - `0x3C4`/`0x3C5`
  - **VGASRI + VGASR0–4** Sequencer
  - index + reset / clocking-mode / map-mask / char-map / memory-mode (Chain-4, odd/even, 64K/256K)
* - `0x3D4`/`0x3D5`
  - CRTC (index/data)
  - CRT Controller registers (§34.5) — timings, cursor, start address
* - `0x3CE`/`0x3CF`, `0x3C0`
  - GDC / ATC
  - Graphics + Attribute controllers (§34.6/34.7)
* - `0x3C6–0x3C9`
  - RAMDAC
  - palette / pixel-mask (§34.8)
```

The **extended CRT registers** (§34.9, p.382+) carry the Aspeed-specific
frame-buffer base, scan pitch, and mode controls — programmed by the display
driver on top of DRAM already initialised by the ARM. [DS §34.1 p.369](#sources)

### Framebuffer / VGA memory carve-out (SCU70[3:2])

VGA shares the **top** of SDRAM. Its size is a hardware trap:

```{list-table} SCU70[3:2] VGA memory size
:header-rows: 1
:widths: 22 78

* - `SCU70[3:2]`
  - VGA memory (carved from the top of SDRAM)
* - `00`
  - 8 MB
* - `01`
  - 16 MB
* - `10`
  - 32 MB
* - `11`
  - 64 MB
```

[DS §18 p.218](#sources). The absolute ARM addresses follow the *DRAM size × VGA size*
map in [DS §9 p.98](#sources). For the KGPE-D16 (64 MB DRAM, `SCU70[3:2]=00` → 8 MB VGA)
this is **`0x43800000–0x43FFFFFF`**, and the host's x86 display actively writes it
through the VGA PCI function.

```{admonition} Reserve the VGA carve-out in the DT
:class: warning

If Linux is allowed to allocate from the 8 MB VGA region, the host's live VGA
traffic corrupts kernel pages (observed: init SIGILL). Every Aspeed board DT
reserves it `no-map`; the G3 fix:
`reserved-memory { vga_memory: framebuffer@43800000 { no-map; reg = <0x43800000 0x800000>; }; }`.
[TIMER-RCA](#sources)
```

VGA-related SCU controls: `SCU0C[5]` gates the VGA display clock (DCLK);
`SCU2C[6]` disables the VGA CRT display; `SCU2C[5]` forces VGA-register access
outside trapping; `SCU2C[3]` disables the video DAC; `SCU18` holds the VGA
cursor / scratch-register change interrupts; `SCU40/44` are the ARM↔host VGA
handshake scratch (e.g. `SCU40[31:24]=0x5A` "boot to Linux properly").
[DS §18 p.209, p.213-214, p.211, p.215-216](#sources)

### Video (compression) Engine

Separate from the VGA display path: a JPEG/VQ capture-and-compress engine for KVM
(`Base = 0x1E700000`, §20). It reads the VGA output (or external DVO) via M-Bus,
up to 1920×1200×32bpp@60. Register highlights: [DS §20 p.232-235](#sources)

```{list-table} Video Engine — key registers (offsets from 0x1E700000)
:header-rows: 1
:widths: 12 22 66

* - Offset
  - Register
  - Function
* - `0x000`
  - **VR000** Protection Key
  - Unlock with `0x1A03_8AA8`; reads `1` unlocked / `0` locked; reset by POR/WDT/SCU-SW-reset
* - `0x004`
  - **VR004** Sequence Control
  - - bit4 enable/trigger compression
    - bit5 auto multi-frame
    - bit3 capture multi-frame
    - bit7 mode-change watchdog
    - `[11:10]` YUV444/YUV420
    - bit18 compress-idle
    - bit16 capture-idle status
```

The Video Engine clock (ECLK) is gated by `SCU0C[0]`; its reset is `SCU04[6]`.
[DS §18 p.210, p.207](#sources)

---

## USB 2.0 Virtual Hub Controller

A USB2.0 (480 Mb/s, FS/LS-capable) **virtual hub**: one hub device port + seven
downstream device controllers, 21 programmable endpoints, an integrated DMA
engine (bypasses AHB via M-Bus), 32-stage descriptor mode. [DS §15.1-15.2 p.154](#sources)

```{admonition} Base address 0x1E6A0000
:class: note

`Base of USB Hub = 0x1E6A0000`; physical = base + offset. [DS §15.3 p.155](#sources)
```

### USB register-space layout

```{list-table} USB2.0 register regions (offsets from 0x1E6A0000)
:header-rows: 1
:widths: 22 12 66

* - Offset range
  - Size
  - Region
* - `0x000–0x03F`
  - 64 B
  - Root / Global device registers (HUB00…)
* - `0x040–0x07F`
  - 64 B
  - *Reserved*
* - `0x080–0x087`
  - 8 B
  - Root device SETUP data buffer
* - `0x088–0x0BF`
  - 8 B ea.
  - Device 1–7 SETUP data buffers
* - `0x0C0–0x0FF`
  - 64 B
  - *Reserved*
* - `0x100–0x16F`
  - 16 B ea.
  - Device 1–7 registers
* - `0x170–0x1FF`
  - 144 B
  - *Reserved*
* - `0x200–0x34F`
  - 16 B ea.
  - Programmable Endpoint 0–20 registers
```

[DS §15.3.1 p.155](#sources)

### HUB00 — Root Function Control & Status (offset 0x00)

```{list-table} HUB00 (0x1E6A0000)
:header-rows: 1
:widths: 12 40 48

* - Bit
  - Name
  - Meaning
* - 31
  - USB PHY clock enable status (R)
  - `1`=PHY clock enabled (via `SCU0C[14]`)
* - 30:18
  - —
  - Reserved (0)
* - 17
  - Isochronous-IN null-data response
  - `0`=no response, `1`=0-byte DATA0
* - 16
  - Complete SPLIT-IN after SOF
  - must be `1` during Set_Address status phase
* - 15 / 14
  - Loopback test result / finished (R)
  - test-mode diagnostics
* - 13 / 12
  - USB PHY BIST result (R) / control
  - built-in self-test
* - 11
  - **Disable USB PHY reset**
  - `1`=de-assert PHY reset (step 3 of USB bring-up)
* - 10:8
  - USB Test Mode select
  - `000`=disable; Test-J/K/SE0_NAK/Packet/Loopback (debug)
* - 7 / 6
  - Force bus-state timer / force High-Speed (debug)
  - test only
* - 5
  - Remote-wakeup pulse width
  - `0`=8 ms, `1`=12 ms
* - 4 / 3
  - Enable manual / automatic Remote Wakeup
  - Suspend-state resume
* - 2
  - Enable clock-stop in Suspend
  - must be `1` to use remote wakeup
* - 1
  - Upstream port speed select
  - `0`=HS+FS, `1`=FS only
* - 0
  - Enable upstream port connection
  - `1`=connect
```

[DS §15.3.2 p.156-157](#sources)

```{admonition} USB2.0 bring-up order
:class: note

1. Enable the USB2.0 clock: `SCU0C[14]=1`, then **wait 10 ms** for clock stability.
2. De-assert the USB2.0 global reset: `SCU04[14]=0`.
3. De-assert the PHY reset: `HUB00[11]=1`.
4. Start using the controller.

[DS §18 p.209](#sources) (SCU0C[14] note), [DS §15.3.2 p.156](#sources). (USB1.1 clock is gated
separately at `SCU0C[7]`.)
```

---

## AHB remap, P2A & iLPC-to-AHB bridges

Three mechanisms give access to (or steer) the internal AHB space. All three are
the AST2050's version of the interfaces flagged industry-wide as
**CVE-2019-6260 ("Pantsdown")** for the AST2400/2500 — arbitrary host→BMC AHB
read/write. On the AST2050 they are the *intended* out-of-band bring-up path for a
dead-firmware board. [CVE-2019-6260 / Pantsdown][pantsdown]

### AHB Bus Controller — unlock key + boot-area remap

`Base of AHBC = 0x1E600000`; 4 registers. [DS §12.3 p.114](#sources), [`hwreg.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h)

```{list-table} AHB Bus Controller registers
:header-rows: 1
:widths: 12 26 62

* - Offset
  - Register
  - Function
* - `0x00`
  - **AHBC00** Protection Key
  - Write **`0xAEED1A03`** → regs `0x80–0x8C` become programmable; write anything else locks them. Read `1`=unlocked, `0`=locked
* - `0x80`
  - **AHBC80** Priority Control
  - Two-level round-robin master priority:
    - bit1=P-Bus-to-AHB bridge
    - bit2=CPU-instr
    - bit3=CPU-data
    - bit4=PCI host
    - bit5=LPC master
* - `0x88`
  - **AHBC88** Interrupt Control
  - - bit24 int-status (W0-to-clear)
    - bit16 int-enable
    - `[21:20]` decode response (00=OK, 01=ERROR)
* - `0x8C`
  - **AHBC8C** Address Remapping
  - - **bit0 Boot-area remap**: `0`=`0x0000_0000–0x0FFF_FFFF` → Static Memory (flash), `1`=→ SDRAM
    - bit4 PCI-remap-0 (`0x6000_0000–0x7FFF_FFFF`→PCI host)
    - bit5 PCI-remap-1 (`0x8000_0000–0xFFFF_FFFF`→PCI host)
```

The DRAM-at-`0x0` boot trick unlocks `AHBC00 = 0xAEED1A03` then sets
`AHBC8C[0] = 1`. [P2A-BOOT](#sources), [`hwreg.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h)

```{admonition} The boot-area remap resets on HRST_N
:class: warning

`AHBC8C[0]` is in the AHB-Controller reset domain (`HRST_N`), so **any
ARM-restarting reset clears the remap** — the naive "set remap + watchdog-reset"
boot re-fetches `0x0` = (dead) flash. The working P2A-only boot instead freezes
the ARM across the reset with `SCU70[1:0]=11` ("Disable ARM CPU operation", which
survives `HRST_N` because the SCU is `PWRSTNin`-only), re-sets the remap, then
re-enables the ARM with `SCU70[1:0]=10`. DDR2 and the SCU survive the reset.
[P2A-BOOT](#sources), [DS §18 p.219](#sources)
```

### P2A — P-Bus (PCIe) to AHB bridge

A **one-way** bridge: host PCI cycles into the second 64 KB of PCIS14 (`MMIOBASE`)
are converted to AHB accesses. `Base = MMIOBASE` (from PCI config). Two registers.
[DS §36 p.400](#sources)

```{list-table} P2A bridge registers
:header-rows: 1
:widths: 12 30 58

* - Offset
  - Register
  - Function
* - `0xF000`
  - **P2A00** Protection Key
  - bit0: `1`=enable P2A bridge, `0`=disable (ignores all P-Bus commands). "Keep locked when not needed"
* - `0xF004`
  - **P2A04** Re-mapping Base Address
  - bits `[31:16]` = AHB address high half; the low `[15:0]` come from the P-Bus command. **`AHB addr = (P2A04[31:16]) + (pbus_addr[15:0])`**. The 64 KB window is `MMIOBASE+0x10000 … MMIOBASE+0x1FFFF`; byte/word/dword access
```

The two documented uses are **(1)** host-side flash update and **(2)** HW/SW
debugging. [DS §36.1 p.400](#sources). `SCU2C[8]` **Disable PCI-slave-to-AHB bus bridge**
is the coarse master gate (`0`=enabled, `1`=disabled). [DS §18 p.214](#sources)

```{admonition} P2A behaviour verified on the KGPE-D16
:class: note

Over `culvert p2a vga`, P2A reads/writes DRAM (`0x40000000`), the SCU
(`SCU7C=0x00000202`), and the Timer freely, and can drive UART2 to a live console
— but it is **blind to the `0x1E6C0000` VIC block** (reads 0, writes dropped) and
does **not** serve the external SMC flash window (`0x14000000` reads 0 on a
dead-firmware board). [TIMER-RCA](#sources), [CULVERT-G3](#sources)
```

### iLPC-to-AHB bridge (LPC → AHB)

The LPC Slave Controller (`Base = 0x1E789000`, §30) contains a second host→AHB
back door reached over the **LPC bus** rather than PCIe. It is steered by four
Host-Interface-Control registers. [DS §30 p.319-321](#sources)

```{list-table} iLPC-to-AHB bridge registers (offsets from 0x1E789000)
:header-rows: 1
:widths: 12 22 66

* - Offset
  - Register
  - Function
* - `0x80`
  - **HICR5**
  - - bit8 **ENL2H** = Enable LPC-to-AHB bridge
    - `[31:24]` **HWMBASE** = LPC-to-AHB address-decode base `[31:24]`
    - bit10 ENFWH
    - bit9 ENINT_PME
* - `0x84`
  - **HICR6**
  - - `[27:24]` **HWNCARE** = address-decode range (don't-care) control `[27:24]`
    - `[2:0]` PME / snoop interrupt status (W1C)
* - `0x88`
  - **HICR7**
  - `[31:16]` **ADRBASE** = remapping address base `[31:16]` of the LPC-to-AHB bridge
* - `0x8C`
  - **HICR8**
  - `[31:16]` **ADRMASK** = remapping address mask `[31:16]` of the LPC-to-AHB bridge
```

```{admonition} Reading the iLPC posture
:class: note

`HICR5[8] ENL2H` tells you whether the LPC-to-AHB bridge is *live*. On the
KGPE-D16, `0x1E789080` (HICR5) reads **`0x98000000`** → HWMBASE = `0x98`, **ENL2H
= 0 → the iLPC bridge is Disabled** (only P2A is usable in-band). [culvert](https://github.com/mithro/culvert)'s
`aspeed,ast2050-ilpc-ahb-bridge` ops read exactly this bit. [CULVERT-G3](#sources)
```

Related: `LHCR0[12]` (LPC Host Control 0, `0x1E7890AC`... offset `0xA0`) —
**Disable vector-interrupt-output-connected-to-host-serial-IRQ** — is the rev-A2
feature that lets the host consume the VIC's `nIRQ` over the KCS #2 serial IRQ
when the ARM is disabled (see also `HICR5[19:16]`/`HICR5[13:12]`). [DS §30 p.322](#sources),
[DS §7 p.7](#sources)

### SCU posture: clock gates, straps, reset flags

The bits that decide whether these bridges/blocks are alive and how the SoC boots.
`Base of SCU = 0x1E6E2000`; unlock with `SCU00 = 0x1688A8A8` (RMW to preserve the
strap). [DS §18 p.205](#sources), [P2A-BOOT](#sources)

```{list-table} Key SCU control/status bits
:header-rows: 1
:widths: 18 20 62

* - Register
  - Field
  - Meaning
* - `SCU00`
  - Protection Key
  - Write `0x1688A8A8` to unlock SCU regs; reads `0x1` unlocked / `0x0` locked
* - `SCU04`
  - System Reset Control (init `0x000FFE5C`)
  - Per-block async resets:
    - bit19 PCI-host
    - bit14 USB2.0
    - bit12/11 MAC2/MAC1
    - bit8 **PCI-slave+VGA**
    - bit6 Video
    - bit5 LPC
    - bit4 HACE
    - bit2 I2C
    - bit1 AHB-bridges
    - bit0 SDRAM
* - `SCU0C`
  - Clock Stop (init `0x000C3E8B`)
  - Clock-stop gates (`1`=stopped):
    - bit15 UARTCLK
    - bit14 USB2.0
    - bit8 LPC LCLK
    - bit7 USB1.1 UCLK
    - bit5 VGA DCLK
    - bit4 PCI-slave BCLK
    - bit2 SDRAM MCLK
    - bit1 2D GCLK
    - bit0 Video ECLK
* - `SCU2C`
  - Misc Control
  - - bit8 disable P2A bridge
    - bit6 disable VGA CRT
    - bit3 disable video DAC
    - bit15/14 UART1↔2 link/mux
    - bit12 UART ÷13 reference
* - `SCU30/34/38`
  - PCI config override
  - Device/Vendor, Subsystem, Class/Revision (init `0x20001A03`/`0x20001A03`/`0x03000000`)
* - `SCU3C`
  - System-reset status/control (init `0x1`)
  - Reset status/control (the flags are a post-reset witness):
    - bit3 enable external SOC reset (GPIOB7/EXTRST#)
    - bit2 external-reset flag
    - **bit1 watchdog-reset flag**
    - bit0 power-on-reset flag
* - `SCU70`
  - Hardware Trapping (init `0`)
  - - **`[1:0]` ARM boot select** (`10`=boot SPI flash, `11`=disable ARM)
    - **bit16 boot-full-speed**
    - `[13:12]` CPU:AHB ratio
    - `[11:9]` H-PLL default (100/133/166/200 MHz)
    - `[8:6]` MAC mode
    - bit5 VGA-BIOS ROM
    - **`[3:2]` VGA memory size**
    - bit20 disable ARM-to-M-bus
* - `SCU7C`
  - Silicon Revision (R)
  - `0x00000202` = AST2050/AST1100-A2/A3
```

[DS §18 p.205-220](#sources). `SCU3C[1]` (watchdog-reset flag) is the clean post-reset
"did the WDT fire?" witness used by the P2A boot sequence. [P2A-BOOT](#sources)

---

## Coverage notes & uncertainties

- **Fully register-mapped from the datasheet + hardware:** UART1/2 (16550,
  every register + baud/clock), VIC (all 13/14 offsets incl. reserved VIC30 and
  the VIC34 gap; the 32-source Table 36; SENSE/EVENT/DUAL derived and
  bit-summed), Timers (TMC00–TMC30), PCI-slave config (PCIS00–PCIS44), AHBC
  (00/80/88/8C), P2A (P2A00/P2A04), iLPC-to-AHB (HICR5–HICR8), and the governing
  SCU bits.
- **High-level (as scoped):** the VGA display controller is given as its standard
  legacy-I/O register file plus the extended-CRT pointer (§34.9, ~p.382+, not
  transcribed in full); the Video Engine is summarised at VR000/VR004 (the full
  §20 register file is large and KVM-specific); USB is the region map + HUB00
  (per-endpoint registers, §15.3.3–15.3.4, not transcribed).
- **Cross-checked ≥2 sources per load-bearing claim:** datasheet ⇄
  hardware-verified project docs / Raptor headers for every base address and the
  VIC/timer/P2A behaviour; datasheet ⇄ ARM PL190, Faraday FTTMR010 driver, and
  the CVE-2019-6260 advisory for the VIC layout, timer semantics, and the AHB
  back-door model respectively.
- **Uncertainty — RTC INT polarity:** Table 36 lists RTC INT#22–26 as "edge
  trigger and both edge"; the driver programs them DUAL (VIC28) with SENSE=0.
  Not independently exercised on hardware (the timer/eth path was), so the
  both-edge RTC handling is datasheet-derived, not HW-proven. [g3-vic patch](#sources)
- **Uncertainty — VIC34:** the datasheet defines VIC30 (reserved) and VIC38 but
  nothing at `0x34`; treated here as undefined/reserved. No register is documented
  there.
- **P2A window ↔ MMIOBASE:** `MMIOBASE` is the runtime-relocated value the host
  BIOS assigns to PCIS14; the datasheet gives the *offset* (`+0x10000`) and the
  remap arithmetic, not an absolute address (correctly host-dependent).

## See also

**Related pages**

- {doc}`/hardware/registers/uart-vic-timers` — the sibling CPU-facing peripherals (UARTs, VIC, timers) split off from this page
- {doc}`/hardware/registers/display-usb` — the full USB 2.0 / Video Engine / VGA register maps summarised here
- {doc}`/hardware/registers/engines-blocks` — the 2D engine and the outbound A2P bridge (counterpart to the inbound P2A)
- {doc}`/hardware/soc-ast2050` — the P2A/iLPC AHB debug bridges at SoC level

**External references**

- [Linux PCI subsystem](https://docs.kernel.org/PCI/index.html) — the PCI model behind this PCI-slave/VGA endpoint
- [Linux DRM/KMS](https://docs.kernel.org/gpu/drm-kms.html) — the display/DRM framework for the VGA controller
- [Linux USB gadget API](https://docs.kernel.org/driver-api/usb/gadget.html) — the gadget/vhub model this USB block exposes
- [QEMU Aspeed SoC documentation](https://www.qemu.org/docs/master/system/arm/aspeed.html) — how QEMU models the Aspeed endpoint and AHB bridges

## Sources

- **[AST2050/AST1100 A3 Datasheet, V1.05](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/datasheets/aspeed/AST2050_AST1100_A3_Datasheet_V1.05.pdf)** (25 May 2010), in-repo PDF. Chapters
  used here: §12 AHB Bus Controller (p.113-115), §15 USB2.0 Virtual Hub
  (p.154-157), §18 SCU (p.204-220), §20 Video Engine (p.232-235), §30 LPC
  Controller / iLPC-to-AHB (p.311-326), §33 PCI Slave Controller (p.363-368), §34
  VGA Display Controller (p.369-372), §36 P-Bus to AHB Bridge (p.400).
- **[`P2A-DRAM-BOOT-SEQUENCE.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/P2A-DRAM-BOOT-SEQUENCE.md)** — AHB unlock/remap, the reset tree,
  `SCU70[1:0]` freeze-across-reset.
- **[`CULVERT-G3-HARDWARE-RESULTS.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/CULVERT-G3-HARDWARE-RESULTS.md)** — verified culvert P2A/iLPC posture
  (`HICR5[8] ENL2H`, the PCIS14 P2A window), SoC identity `SCU7C=0x202`.
- **[`TIMER-CLOCKEVENT-ROOT-CAUSE.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/TIMER-CLOCKEVENT-ROOT-CAUSE.md)** — the VGA carve-out reservation and the
  P2A-blind-to-VIC finding.
- **[`hwreg.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h), [`ast2050.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/ast2050.h)** — Raptor Engineering reverse-engineered register
  bases (AHBC key/remap).
- [CVE-2019-6260 "Pantsdown" write-up][pantsdown] and the [NVD entry][nvd] — the
  iLPC2AHB / PCIe-P2A / X-DMA AHB back-door model these G3 bridges belong to.

[pantsdown]: https://www.flamingspork.com/blog/2019/01/23/cve-2019-6260-gaining-control-of-bmc-from-the-host-processor/
[nvd]: https://nvd.nist.gov/vuln/detail/cve-2019-6260
