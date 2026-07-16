# NS9360 secondary blocks (full register maps): LCD, IEEE 1284, USB host & device

This page brings the four NS9360 "secondary" controllers — the LCD controller,
the IEEE 1284 peripheral parallel port, the USB 2.0 OHCI host, and the USB 2.0
device — up to the same per-bit depth as the rest of the NS9360 register
reference. Each is documented directly from the *NS9360 Hardware Reference*
(Digi 90000675 rev J): chapter 12 (LCD), chapter 15 (IEEE 1284), chapter 16
(USB host) and chapter 17 (USB device). The block base addresses are the ones
listed in the NS9360 memory map and confirmed by the vendor U-Boot headers
[HWRef p.415-416](#sources), [digi-uboot](https://github.com/mithro/ai-shenanigans-for-bmcs/tree/main/hpe-ipdu-firmware/uboot-port/reference/digi-cc9p9360-uboot).

**None of these four blocks is used on the HPE iPDU board** (Digi NS9360, NET+OS
firmware). They are documented in full anyway because this reference aims to
cover every NS9360 register at full depth, and because the blocks still consume
address space, reset bits and clock-enable bits that a port must account for.

**Open-source cross-reference.** The mainline Linux `arch/arm/mach-ns9xxx`
support contains **no** register definitions for any of these four blocks:
`regs-bbu.h` defines only the GPIO config/control/status registers and
`regs-sys-ns9360.h` only the system-control (PLL, timer, arbiter, chip-select,
external-interrupt) registers — neither names LCD, IEEE 1284, USB host or USB
device [mach-ns9xxx regs-bbu.h](https://github.com/torvalds/linux/blob/v2.6.39/arch/arm/mach-ns9xxx/include/mach/regs-bbu.h), [mach-ns9xxx regs-sys-ns9360.h](https://github.com/torvalds/linux/blob/v2.6.39/arch/arm/mach-ns9xxx/include/mach/regs-sys-ns9360.h). The only
open-source register-level cross-reference is the vendor FS-Forth / Digi U-Boot
tree (in-repo), which carries an OHCI header and a USB base-address header for
this exact SoC [digi-uboot ns9750_usb_ohci.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/reference/digi-cc9p9360-uboot/u-boot-1.1.4-digi/U-Boot/include/ns9750_usb_ohci.h), [digi-uboot ns9360_usb.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/reference/digi-cc9p9360-uboot/u-boot-1.1.4-digi/U-Boot/include/ns9360_usb.h), plus the
BBus master-reset and USB-config bits that gate these blocks
[digi-uboot ns9750_bbus.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/reference/digi-cc9p9360-uboot/u-boot-1.1.4-digi/U-Boot/include/ns9750_bbus.h). Mainline's only "touch" of these blocks is indirect:
the BBus Master Reset register (0x9060_0000, documented under
{doc}`soc-ns9360-io`) holds their reset bits, and the system-control module's
clock registers (documented under {doc}`soc-ns9360`) hold their clock-select /
clock-enable fields.

---

## LCD Controller

**Base address: 0xA080_0000** — chapter 12 [HWRef p.543](#sources). An AHB-master colour
LCD controller for TFT (up to 18-bit / 64K colour) and STN (mono or colour,
single or dual panel) panels up to 1024×768, with a 256-entry palette RAM at
0xA080_0200–0xA080_03FC. All configuration registers are 32-bit, single-access
(no bursting) [HWRef p.543](#sources).

**Unused on the iPDU.** The block is still listed because the endian-switch /
early-boot code executes from the LCD palette RAM as scratch memory (the palette
is ordinary RAM until the controller is enabled) [HWRef p.543](#sources), [PLAN-INCREMENTAL-PORT.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/PLAN-INCREMENTAL-PORT.md).
Its clock-enable (`LCDC`) and panel-clock-select fields live in the
system-control module [HWRef p.144, Table 48](#sources).

```{list-table} LCD controller register map (offset from 0xA080_0000)
:header-rows: 1
:widths: 18 26 56

* - Offset
  - Register
  - Description
* - 0x000
  - LCDTiming0
  - Horizontal axis panel control (HBP, HFP, HSW, PPL)
* - 0x004
  - LCDTiming1
  - Vertical axis panel control (VBP, VFP, VSW, LPP)
* - 0x008
  - LCDTiming2
  - Clock and signal polarity control
* - 0x00C
  - LCDTiming3
  - Line-end control (LEE, LED)
* - 0x010
  - LCDUPBASE
  - Upper-panel DMA frame base address
* - 0x014
  - LCDLPBASE
  - Lower-panel DMA frame base address
* - 0x018
  - LCDINTRENABLE
  - Interrupt enable mask
* - 0x01C
  - LCDControl
  - Panel pixel parameters / enable
* - 0x020
  - LCDStatus
  - Raw interrupt status (read/clear)
* - 0x024
  - LCDInterrupt
  - Final masked interrupt status
* - 0x028
  - LCDUPCURR
  - Upper-panel current DMA address (read-only)
* - 0x02C
  - LCDLPCURR
  - Lower-panel current DMA address (read-only)
* - 0x030–0x1FC
  - reserved
  - Reserved
* - 0x200–0x3FC
  - LCDPalette
  - 256 × 16-bit colour palette (128 words, 2 entries/word)
```

### LCDTiming0 (0x000) — horizontal timing [HWRef p.543-545, Table 386](#sources)

```{list-table} LCDTiming0 bitfields
:header-rows: 1
:widths: 12 14 10 12 52

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31:24
  - HBP
  - R/W
  - 0x00
  - Horizontal back porch, CLCP periods (program value − 1); 1–256 pixel clocks
* - D23:16
  - HFP
  - R/W
  - 0x00
  - Horizontal front porch, CLCP periods (program value − 1); 1–256 pixel clocks
* - D15:08
  - HSW
  - R/W
  - 0x00
  - Horizontal sync pulse width in CLCP periods (program value − 1)
* - D07:02
  - PPL
  - R/W
  - 0x00
  - Pixels-per-line $= 16 \times (\text{PPL}+1)$; 16–1024 pixels
* - D01:00
  - reserved
  - N/A
  - N/A
  - Reserved
```

### LCDTiming1 (0x004) — vertical timing [HWRef p.546-547, Table 388](#sources)

```{list-table} LCDTiming1 bitfields
:header-rows: 1
:widths: 12 14 10 12 52

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31:24
  - VBP
  - R/W
  - 0x00
  - Vertical back porch: inactive lines at start of frame (0–255)
* - D23:16
  - VFP
  - R/W
  - 0x00
  - Vertical front porch: inactive lines at end of frame (0–255)
* - D15:10
  - VSW
  - R/W
  - 0x00
  - Vertical sync pulse width in lines (program value − 1)
* - D09:00
  - LPP
  - R/W
  - 0x000
  - Lines-per-panel (program lines − 1); 1–1024 lines
```

### LCDTiming2 (0x008) — clock / signal polarity [HWRef p.547-550, Table 389](#sources)

```{list-table} LCDTiming2 bitfields
:header-rows: 1
:widths: 12 12 10 10 56

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31:27
  - reserved
  - N/A
  - N/A
  - Reserved
* - D26
  - BCD
  - R/W
  - 0x0
  - Bypass pixel-clock divider (set for most TFT panels)
* - D25:16
  - CPL
  - R/W
  - 0x000
  - Clocks-per-line (actual CLCP clocks per line − 1)
* - D15
  - reserved
  - N/A
  - N/A
  - Reserved
* - D14
  - IOE
  - R/W
  - 0x0
  - Invert output enable: 0 = CLAC active high, 1 = active low (TFT)
* - D13
  - IPC
  - R/W
  - 0x0
  - Invert panel clock: 0 = data changes on CLCP rising, 1 = falling edge
* - D12
  - IHS
  - R/W
  - 0x0
  - Invert horizontal sync (CLLP): 0 = active high, 1 = active low
* - D11
  - IVS
  - R/W
  - 0x0
  - Invert vertical sync (CLFP): 0 = active high, 1 = active low
* - D10:06
  - ACB
  - R/W
  - 0x00
  - AC bias pin frequency: line clocks between CLAC toggles − 1 (STN only)
* - D05
  - reserved
  - N/A
  - N/A
  - Reserved
* - D04:00
  - PCD
  - R/W
  - 0x00
  - Panel clock divisor: $\text{CLCP} = \text{CLCDCLK}/(\text{PCD}+2)$
```

### LCDTiming3 (0x00C) — line-end control [HWRef p.551, Table 390](#sources)

```{list-table} LCDTiming3 bitfields
:header-rows: 1
:widths: 12 14 10 12 52

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31:17
  - reserved
  - N/A
  - N/A
  - Reserved
* - D16
  - LEE
  - R/W
  - 0x0
  - LCD line-end enable: 0 = CLLE held low, 1 = CLLE active
* - D15:07
  - reserved
  - N/A
  - N/A
  - Reserved
* - D06:00
  - LED
  - R/W
  - 0x00
  - Line-end signal delay from last CLCP rising edge (CLCDCLK periods − 1)
```

### LCDUPBASE (0x010) / LCDLPBASE (0x014) — DMA frame base [HWRef p.552-553, Tables 391-392](#sources)

Both hold a word-aligned frame-buffer base address in D31:02 (R/W, reset
0x00000000); D01:00 are reserved / read as 0. LCDUPBASE serves TFT, single-panel
STN and the upper panel of dual-panel STN; LCDLPBASE serves the lower panel of
dual-panel STN. They are copied to LCDUPCURR/LCDLPCURR at each vertical sync,
setting `LNBU` in LCDStatus [HWRef p.552-553](#sources).

### LCDINTRENABLE (0x018) — interrupt enable [HWRef p.553, Table 393](#sources)

```{list-table} LCDINTRENABLE bitfields
:header-rows: 1
:widths: 12 18 10 10 50

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31:05
  - reserved
  - N/A
  - N/A
  - Reserved
* - D04
  - MBERRINTRENB
  - R/W
  - 0x0
  - AHB master bus-error interrupt enable
* - D03
  - VCOMPINTRENB
  - R/W
  - 0x0
  - Vertical-compare interrupt enable
* - D02
  - LNBUINTRENB
  - R/W
  - 0x0
  - Next-base-update interrupt enable
* - D01:00
  - reserved
  - N/A
  - 0x0
  - Always write 0
```

### LCDControl (0x01C) — mode / enable [HWRef p.554-556, Table 394](#sources)

```{list-table} LCDControl bitfields
:header-rows: 1
:widths: 12 12 10 10 56

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31:17
  - reserved
  - N/A
  - N/A
  - Reserved
* - D16
  - WATERMARK
  - R/W
  - 0x0
  - DMA FIFO request level: 0 = ≥4 empty, 1 = ≥8 empty (recommended)
* - D15:14
  - reserved
  - N/A
  - N/A
  - Reserved
* - D13:12
  - LcdVComp
  - R/W
  - 0x0
  - VCOMP interrupt trigger: 00 = vsync, 01 = back porch, 10 = active video, 11 = front porch
* - D11
  - LcdPwr
  - R/W
  - 0x0
  - LCD power enable (gate power + enable CLD[17:0])
* - D10
  - BEPO
  - R/W
  - 0x0
  - Big-endian pixel ordering within a byte (1/2/4 bpp only)
* - D09
  - BEBO
  - R/W
  - 0x0
  - Big-endian byte order
* - D08
  - BGR
  - R/W
  - 0x0
  - 0 = RGB, 1 = BGR (red/blue swapped)
* - D07
  - LcdDual
  - R/W
  - 0x0
  - 0 = single panel, 1 = dual-panel STN
* - D06
  - LcdMono8
  - R/W
  - 0x0
  - Mono STN interface width: 0 = 4-bit, 1 = 8-bit
* - D05
  - LcdTFT
  - R/W
  - 0x0
  - 0 = STN (use grayscaler), 1 = TFT
* - D04
  - LcdBW
  - R/W
  - 0x0
  - STN: 0 = colour, 1 = monochrome (no meaning in TFT)
* - D03:01
  - LcdBpp
  - R/W
  - 0x0
  - Bits/pixel: 000=1, 001=2, 010=4, 011=8, 100=16; 101–111 reserved
* - D00
  - LcdEn
  - R/W
  - 0x0
  - LCD controller enable (enables CLLP/CLCP/CLFP/CLAC/CLLE)
```

### LCDStatus (0x020) — raw interrupt status [HWRef p.557, Table 395](#sources)

Read returns the three raw interrupt sources; write-1-to-clear (R/C).

```{list-table} LCDStatus bitfields
:header-rows: 1
:widths: 12 14 10 10 54

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31:05
  - reserved
  - N/A
  - N/A
  - Reserved
* - D04
  - MBERROR
  - R/C
  - 0x0
  - AHB master bus-error status (write 1 to clear + release master)
* - D03
  - VCOMP
  - R/C
  - 0x0
  - Vertical compare reached (region set by LcdVComp)
* - D02
  - LNBU
  - R/C
  - 0x0
  - Next base address loaded into current (safe to reprogram base)
* - D01:00
  - reserved
  - N/A
  - 0x0
  - Reserved
```

### LCDInterrupt (0x024) — masked interrupt status [HWRef p.557-558, Table 396](#sources)

Bit-by-bit logical AND of LCDStatus and LCDINTRENABLE (all read-only): D04
`MBERRORINTR`, D03 `VCOMPINTR`, D02 `LNBUINTR`; all others reserved
[HWRef p.558](#sources).

### LCDUPCURR (0x028) / LCDLPCURR (0x02C) — current DMA address [HWRef p.558-559, Tables 397-398](#sources)

Each is a full 32-bit read-only field (D31:00, reset undefined) giving an
approximate/coarse value of the upper/lower panel DMA address; usable only for
coarse timing [HWRef p.558-559](#sources).

### LCDPalette (0x200–0x3FC) — colour palette [HWRef p.559-560, Table 399](#sources)

128 words, two 16-bit palette entries per word (order depends on BEBO). Each
entry: `Int` (D31/D15, intensity LSB for 6:6:6 TFT), `B[4:0]`, `G[4:0]`,
`R[4:0]`. STN colour uses only the four MSBs of each component; mono uses only
R[4:0] [HWRef p.559-560](#sources). This RAM is used as boot scratch before the controller
is enabled [HWRef p.543](#sources).

**Interrupts.** The block drives one system interrupt from three maskable
sources: `MBERRORINTR` (master bus error, cleared via MBERROR), `VCOMPINTR`
(vertical compare, cleared via VCOMP) and `LNBUINTR` / next-base-update (cleared
via LNBU) [HWRef p.561-562](#sources).

---

## IEEE 1284 Parallel Port

**Base address: 0x9040_0000** — chapter 15 [HWRef p.635](#sources). An IEEE-1284
*peripheral*-side parallel port supporting compatibility (SPP), nibble, byte and
ECP modes (no EPP), driven either by direct CPU FIFO access or by BBus DMA. All
configuration registers are 32-bit single-access; the "CSR" sub-block at
0x0100–0x0178 is functionally 8-bit but is read/written as 32-bit words
[HWRef p.635-637](#sources).

**Unused on the iPDU.** Its reset bit (`1284`, bit 6 of the BBus Master Reset)
and its endian bit (`ENDIAN_CFG` bit 6) gate the block
[digi-uboot ns9750_bbus.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/reference/digi-cc9p9360-uboot/u-boot-1.1.4-digi/U-Boot/include/ns9750_bbus.h).

```{list-table} IEEE 1284 register map (offset from 0x9040_0000) [HWRef p.635-637, Table 425](#sources)
:header-rows: 1
:widths: 16 30 54

* - Offset
  - Register
  - Description
* - 0x0000
  - GenConfig
  - General configuration (thresholds, DMA/CPU modes)
* - 0x0004
  - InterruptStatusandControl
  - FIFO/peripheral interrupt status + masks
* - 0x0008
  - FIFO Status
  - Forward/reverse FIFO level/ready flags
* - 0x000C
  - FwdCmdFifoReadReg
  - Forward command FIFO read (CPU mode)
* - 0x0010
  - FwDatFifoReadReg
  - Forward data FIFO read (CPU mode)
* - 0x0014–0x0018
  - reserved
  - Reserved
* - 0x001C
  - RvFifoWriteReg
  - Reverse FIFO write (CPU mode)
* - 0x0020
  - RvFifoWriteReg — Last
  - Reverse FIFO write, last entry (CPU mode)
* - 0x0024
  - FwdCmdDmaControl
  - Forward command DMA: max-buffer + byte-gap timer
* - 0x0028
  - FwDatDmaControl
  - Forward data DMA: max-buffer + byte-gap timer
* - 0x0100
  - pd
  - Printer Data Pins (8-bit data bus read)
* - 0x0104
  - psr
  - Port Status register, host side
* - 0x0108
  - pcr
  - Port Control register
* - 0x010C
  - pin
  - Port Status register, peripheral side
* - 0x0110
  - reserved
  - Reserved
* - 0x0114
  - fea
  - Feature Control Register A
* - 0x0118
  - reserved
  - Reserved
* - 0x011C
  - fei
  - Interrupt Enable register
* - 0x0120
  - fem
  - Master Enable register
* - 0x0124
  - exr
  - Extensibility byte requested by host
* - 0x0128
  - ecr
  - Extended Control register
* - 0x012C
  - sti
  - Interrupt Status register
* - 0x0130
  - reserved
  - Reserved
* - 0x0134
  - msk
  - Pin Interrupt Mask register
* - 0x0138
  - pit
  - Pin Interrupt Control register
* - 0x013C–0x0164
  - reserved
  - Reserved
* - 0x0168
  - grn
  - Granularity Count register
* - 0x016C–0x0170
  - reserved
  - Reserved
* - 0x0174
  - eca
  - Forward Address register (ECP channel)
* - 0x0178
  - pha
  - Core Phase register
```

### GenConfig (0x0000) — general configuration [HWRef p.637-638, Table 426](#sources)

```{list-table} GenConfig bitfields
:header-rows: 1
:widths: 12 12 10 10 56

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31:15
  - reserved
  - N/A
  - N/A
  - Reserved
* - D14
  - AFSH
  - R/W
  - 0x0
  - HostAck handling: 0 = split by HostAck into data/command FIFO, 1 = all to data FIFO
* - D13
  - CPS
  - R/W
  - 0x0
  - Connector PLH: 1 = signal host that the 1284 slave is ready (set after init)
* - D12
  - reserved
  - N/A
  - N/A
  - Reserved
* - D11:10
  - FCRT
  - R/W
  - 0x3
  - Forward command ready threshold (encoding as FDRT)
* - D09:08
  - FDRT
  - R/W
  - 0x3
  - Forward data ready threshold: 00=4, 01=8, 10=≥16, 11=≥28 bytes
* - D07:06
  - reserved
  - N/A
  - N/A
  - Reserved
* - D05:04
  - RRT
  - R/W
  - 0x3
  - Reverse ready threshold: 00=1–4, 01=13–16, 10=21–24, 11=25–28 bytes
* - D03
  - FCM
  - R/W
  - 0x0
  - Forward command mode: 0 = CPU, 1 = DMA
* - D02
  - reserved
  - N/A
  - N/A
  - Reserved
* - D01
  - FDM
  - R/W
  - 0x0
  - Forward data mode: 0 = CPU, 1 = DMA
* - D00
  - RM
  - R/W
  - 0x0
  - Reverse mode: 0 = CPU, 1 = DMA
```

### InterruptStatusandControl (0x0004) — interrupt masks + status [HWRef p.639-641, Table 427](#sources)

Mask bits (D26:D17) are R/W; status bits (D10:D01) are R/C (write 1 to clear,
after clearing the underlying condition).

```{list-table} InterruptStatusandControl bitfields
:header-rows: 1
:widths: 12 12 10 10 56

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31:27
  - reserved
  - R
  - 0x0
  - Reserved
* - D26
  - RFRIM
  - R/W
  - 0x0
  - Reverse FIFO ready interrupt mask (1 = enable)
* - D25:24
  - reserved
  - N/A
  - N/A
  - Reserved
* - D23
  - FDBGM
  - R/W
  - 0x0
  - Forward data FIFO byte-gap interrupt mask
* - D22
  - FCBGM
  - R/W
  - 0x0
  - Forward command FIFO byte-gap interrupt mask
* - D21
  - FDMBM
  - R/W
  - 0x0
  - Forward data FIFO max-buffer interrupt mask
* - D20
  - FCMBM
  - R/W
  - 0x0
  - Forward command FIFO max-buffer interrupt mask
* - D19
  - FDRIM
  - R/W
  - 0x0
  - Forward data FIFO ready interrupt mask
* - D18
  - FCRIM
  - R/W
  - 0x0
  - Forward command FIFO ready interrupt mask
* - D17
  - I1M
  - R/W
  - 0x0
  - Peripheral controller interrupt 1 mask
* - D16:11
  - reserved
  - N/A
  - N/A
  - Reserved
* - D10
  - RFRI
  - R/C
  - 0x1
  - Reverse FIFO ready interrupt
* - D09:08
  - reserved
  - N/A
  - —
  - Reserved
* - D07
  - FDFBG
  - R/C
  - 0x0
  - Forward data FIFO byte-gap (timer expired, buffer closed)
* - D06
  - FCFBG
  - R/C
  - 0x0
  - Forward command FIFO byte-gap
* - D05
  - FDFMB
  - R/C
  - 0x0
  - Forward data FIFO max-buffer reached
* - D04
  - FCFMB
  - R/C
  - 0x0
  - Forward command FIFO max-buffer reached
* - D03
  - FDFRI
  - R/C
  - 0x0
  - Forward data FIFO ready (data from host)
* - D02
  - FCFRI
  - R/C
  - 0x0
  - Forward command FIFO ready (data from host)
* - D01
  - PC1I
  - R/C
  - 0x0
  - Peripheral controller interrupt 1 (read sti for source)
* - D00
  - reserved
  - N/A
  - 0x1
  - Reserved
```

### FIFO Status (0x0008) — FIFO levels [HWRef p.642-643, Table 428](#sources)

All read-only; ignore in DMA mode.

```{list-table} FIFO Status bitfields
:header-rows: 1
:widths: 12 12 10 10 56

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31:16
  - reserved
  - N/A
  - N/A
  - Reserved
* - D15:14
  - FCFDR
  - R
  - 0x0
  - Forward command FIFO depth remain: 00=4, 01=1, 10=2, 11=3 valid bytes
* - D13
  - FCFE
  - R
  - 0x1
  - Forward command FIFO empty
* - D12
  - FCFA
  - R
  - 0x1
  - Forward command FIFO almost empty (one 1–4 byte entry left)
* - D11
  - FCFR
  - R
  - 0x0
  - Forward command FIFO ready (per FwCmdReadyThreshold)
* - D10:08
  - reserved
  - N/A
  - N/A
  - Reserved
* - D07:06
  - FDFDR
  - R
  - 0x0
  - Forward data FIFO depth remain (encoding as FCFDR)
* - D05
  - FDFE
  - R
  - 0x1
  - Forward data FIFO empty
* - D04
  - FDFAE
  - R
  - 0x0
  - Forward data FIFO almost empty
* - D03
  - FDFR
  - R
  - 0x0
  - Forward data FIFO ready (per FwDatReadyThreshold)
* - D02
  - RFF
  - R
  - 0x0
  - Reverse FIFO full
* - D01
  - RFAF
  - R
  - 0x0
  - Reverse FIFO almost full
* - D00
  - RFR
  - R
  - 0x0
  - Reverse FIFO ready (per RvReadyThreshold)
```

### FIFO data registers (0x000C / 0x0010 / 0x001C / 0x0020) [HWRef p.644-646, Tables 429-431](#sources)

`FwdCmdFifoReadReg` (0x000C, R) and `FwDatFifoReadReg` (0x0010, R) each read up
to four bytes (D31:00) from the forward command / forward data FIFO in CPU mode;
software reads FIFO Status first to learn how many bytes are valid.
`RvFifoWriteReg` (0x001C, W) and `RvFifoWriteReg — Last` (0x0020, W) write one to
four bytes into the reverse FIFO; a final short (1–3 byte) entry is committed via
the "— Last" register [HWRef p.644-646](#sources).

### Forward Command / Data DMA Control (0x0024 / 0x0028) [HWRef p.647-648, Tables 432-433](#sources)

Identical layout for both registers: D31:16 = `Fw{Cmd,Dat}MaxBufSize` (R/W, reset
0x0000) maximum DMA buffer size in bytes; D15:00 = `Fw{Cmd,Dat}ByteGapTimer`
(R/W, reset 0x0000) 16-bit byte-gap timeout in BBus clock cycles (reaching the
buffer size raises the max-buffer interrupt; the byte-gap timer flushes a partial
dword and closes the buffer) [HWRef p.647-648](#sources).

### CSR block — port pin / status registers (0x0100–0x0178)

```{list-table} pd — Printer Data Pins (0x0100) [HWRef p.649, Table 434](#sources)
:header-rows: 1
:widths: 12 12 10 10 56

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31:08
  - reserved
  - N/A
  - N/A
  - Reserved
* - D07:00
  - pd
  - R
  - —
  - Direct read of the 8-bit parallel data bus
```

`psr` (host, 0x0104) and `pin` (peripheral, 0x010C) both expose the 1284 handshake
lines directly; bit meanings depend on the active mode (compatibility / nibble /
byte / ECP) [HWRef p.650-651, Tables 435, 437](#sources).

```{list-table} psr — Port Status, host (0x0104); pin — Port Status, peripheral (0x010C) [HWRef p.650-651](#sources)
:header-rows: 1
:widths: 12 18 12 10 48

* - Bits
  - Field (psr / pin)
  - Access
  - Reset
  - Meaning
* - D31:04
  - reserved
  - N/A
  - N/A
  - Reserved
* - D03
  - N_AUTOFD / N_FLT
  - R
  - —
  - Host control / peripheral status pin (mode-dependent)
* - D02
  - N_INIT / SEL
  - R
  - —
  - Host control / peripheral status pin (mode-dependent)
* - D01
  - N_SLCTIN / PERR
  - R
  - —
  - Host control / peripheral status pin (mode-dependent)
* - D00
  - N_STROBE / N_ACK
  - R
  - —
  - Host control / peripheral status pin (mode-dependent)
```

Note the `pin` register additionally exposes BUSY (D07), N_ACK (D06), PERR (D05),
SEL (D04), N_FLT (D03) as a five-bit peripheral-status field [HWRef p.651, Table 437](#sources).

```{list-table} pcr — Port Control (0x0108) [HWRef p.651, Table 436](#sources)
:header-rows: 1
:widths: 12 12 10 10 56

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31:08
  - reserved
  - N/A
  - N/A
  - Reserved
* - D07
  - BUSY
  - R/W
  - 0x0
  - Direct control of 1284 pin (valid only if no mode enabled in fem)
* - D06
  - N_ACK
  - R/W
  - 0x0
  - Direct control of 1284 pin (mode-dependent meaning)
* - D05
  - PERR
  - R/W
  - 0x0
  - Direct control of 1284 pin
* - D04
  - SEL
  - R/W
  - 0x0
  - Direct control of 1284 pin
* - D03
  - N_FLT
  - R/W
  - 0x0
  - Direct control of 1284 pin (set D07:03 = 1 before enabling printer)
* - D02:00
  - reserved
  - N/A
  - N/A
  - Reserved
```

```{list-table} fea — Feature Control A (0x0114) [HWRef p.652, Table 438](#sources)
:header-rows: 1
:widths: 12 12 10 10 56

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31:01
  - reserved
  - N/A
  - N/A
  - Reserved
* - D00
  - PPtEn
  - R/W
  - 0x0
  - Printer port enable: 0 = outputs high-Z, 1 = normal operation
```

```{list-table} fei — Interrupt Enable (0x011C) [HWRef p.653-654, Table 439](#sources)
:header-rows: 1
:widths: 12 16 10 10 52

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31:06
  - reserved
  - N/A
  - N/A
  - Reserved
* - D05
  - PinSelectInterrupt
  - R/W
  - 0x0
  - Pin-select interrupt enable
* - D04
  - ECPChannelAddress
  - R/W
  - 0x0
  - ECP channel-address update-detect interrupt enable
* - D03:02
  - reserved
  - N/A
  - N/A
  - Reserved
* - D01
  - NegotiationStart
  - R/W
  - 0x0
  - Negotiation-start interrupt enable (rising edge of nSTROBE)
* - D00
  - TransferStart
  - R/W
  - 0x0
  - Transfer-start interrupt enable (falling nSTROBE, compatibility mode)
```

```{list-table} fem — Master Enable (0x0120) [HWRef p.655, Table 440](#sources)
:header-rows: 1
:widths: 12 14 10 10 54

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31:07
  - reserved
  - N/A
  - N/A
  - Reserved
* - D06
  - ECP
  - R/W
  - 0x0
  - ECP mode enable
* - D05
  - SPP–PS2
  - R/W
  - 0x0
  - SPP–PS2 mode enable
* - D04
  - AutoTransfer
  - R/W
  - 0x0
  - Auto-transfer mode enable
* - D03
  - reserved
  - N/A
  - N/A
  - Reserved
* - D02
  - AutoNegotiate
  - R/W
  - 0x0
  - Auto-negotiate mode enable
* - D01:00
  - reserved
  - N/A
  - N/A
  - Reserved
```

```{list-table} exr — Extensibility byte (0x0124) and ecr — Extended Control (0x0128) [HWRef p.655-656, Tables 441-442](#sources)
:header-rows: 1
:widths: 12 16 10 10 52

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - exr D07:00
  - exr
  - R/W
  - 0x08
  - Extensibility byte received from host (0x08 = host terminated mode)
* - ecr D06
  - Enable reverse
  - R/W
  - 0x0
  - Enable reverse data transfers (other ecr bits reserved)
```

```{list-table} sti — Interrupt Status (0x012C, cleared on read) [HWRef p.657, Table 443](#sources)
:header-rows: 1
:widths: 12 16 10 10 52

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31:06
  - reserved
  - N/A
  - N/A
  - Reserved
* - D05
  - PSINT
  - R
  - 0x0
  - Pin-select interrupt
* - D04
  - ECP channel address
  - R
  - 0x0
  - Channel-address update-detect interrupt
* - D03:02
  - reserved
  - N/A
  - N/A
  - Reserved
* - D01
  - NSDI
  - R
  - 0x0
  - Negotiation-start detect interrupt
* - D00
  - TSDI
  - R
  - 0x0
  - Transfer-start detect interrupt
```

`msk` (Pin Interrupt Mask, 0x0134) and `pit` (Pin Interrupt Control, 0x0138)
carry eight R/W bits each (D07:00) selecting edge/level detection on the four
handshake pins (`n_autofd`, `n_init`, `n_selectin`, `n_strobe`) — D07:04 are the
edge-detect enables/edges (in `pit`, must be 1 = rising edge) and D03:00 the
level-detect enables/polarity (0 = low, 1 = high) [HWRef p.658-659, Tables 444-445](#sources).

```{list-table} grn — Granularity Count (0x0168), eca — Forward Address (0x0174), pha — Core Phase (0x0178) [HWRef p.660-662, Tables 446-448](#sources)
:header-rows: 1
:widths: 12 12 10 10 56

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - grn D07:00
  - grn
  - R/W
  - 0x00
  - BBus clock periods between peripheral signal changes (Tp ≥ 500 ns)
* - eca D07:00
  - eca
  - R
  - 0x00
  - ECP forward address (channel address command)
* - pha D07:00
  - pha
  - R
  - 0x00
  - Core phase code (e.g. 0x00 = SPP idle, 0x14 = negotiate, 0x30 = ECP fwd idle)
```

---

## USB Host (OHCI)

**Base address: 0x9080_0000** — chapter 16 [HWRef p.663, p.667](#sources). A USB 2.0
full-/low-speed host built from a standard OpenHCI (OHCI 1.0) controller plus a
NS9360-specific "USB Host Front End" (UHFE) wrapper that bridges OHCI to the
BBus. The address space splits in two [HWRef p.667, Table 449]:

```{list-table} USB host address map (base 0x9080_0000) [HWRef p.667, Table 449](#sources)
:header-rows: 1
:widths: 34 66

* - Address range
  - Register space
* - 0x9080_0000–0x9080_0FFF
  - UHFE control/status (NS9360-specific wrapper)
* - 0x9080_1000–0x9080_1FFF
  - Standard USB OHCI host controller registers
```

**Unused in the stock firmware.** Sideband signals are USB_PWR = gpio[17] and
USB_OVR = gpio[16]; the host reset bit is `USBHST` (bit 11 of the BBus Master
Reset) [HWRef p.663-664](#sources). The OHCI base 0x9080_1000 and HcRhPortStatus at +0x54
are confirmed by the vendor U-Boot header [digi-uboot ns9360_usb.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/reference/digi-cc9p9360-uboot/u-boot-1.1.4-digi/U-Boot/include/ns9360_usb.h).

### UHFE wrapper registers (0x0000, 0x000C, 0x0010) [HWRef p.667-670, Tables 451-453](#sources)

```{list-table} UHFE registers (offset from 0x9080_0000)
:header-rows: 1
:widths: 14 18 12 10 46

* - Offset / Bits
  - Field
  - Access
  - Reset
  - Meaning
* - 0x0000 D11
  - HSTRST
  - R
  - 1
  - Host block reset status: 0 = operational, 1 = in reset (other bits read 0)
* - 0x000C D01
  - OHCI_IRQ
  - R/W
  - 0
  - UHFE interrupt enable for the OHCI interrupt (1 = enable)
* - 0x0010 D01
  - OHCI_IRQ
  - RW1TC
  - 0
  - UHFE interrupt status: OHCI controller raised an interrupt (write 1 to clear)
```

### OHCI operational registers (0x1000–0x1054)

These are the standard **OpenHCI 1.0** operational registers. The NS9360 HW
Reference reproduces the OHCI specification and enumerates each register with
full bitfields (Tables 455–476); the vendor U-Boot OHCI driver confirms the same
control/command bit masks [digi-uboot ns9750_usb_ohci.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/reference/digi-cc9p9360-uboot/u-boot-1.1.4-digi/U-Boot/include/ns9750_usb_ohci.h). The full standard set,
as listed by the datasheet [HWRef p.671-672, Table 454](#sources), is:

```{list-table} OHCI register map (offset from 0x9080_1000) [HWRef p.671-672, Table 454](#sources)
:header-rows: 1
:widths: 16 28 56

* - Offset
  - Register
  - Description
* - 0x000
  - HcRevision
  - OHCI revision (0x10)
* - 0x004
  - HcControl
  - Operating mode / list enables
* - 0x008
  - HcCommandStatus
  - Commands + status (write-to-set)
* - 0x00C
  - HcInterruptStatus
  - Hardware interrupt event status
* - 0x010
  - HcInterruptEnable
  - Interrupt enable (write-1-to-set)
* - 0x014
  - HcInterruptDisable
  - Interrupt disable (write-1-to-clear enable)
* - 0x018
  - HcHCCA
  - Host Controller Communication Area base
* - 0x01C
  - HcPeriodCurrentED
  - Current periodic endpoint descriptor
* - 0x020
  - HcControlHeadED
  - Head of control list
* - 0x024
  - HcControlCurrentED
  - Current control endpoint descriptor
* - 0x028
  - HcBulkHeadED
  - Head of bulk list
* - 0x02C
  - HcBulkCurrentED
  - Current bulk endpoint descriptor
* - 0x030
  - HcDoneHead
  - Head of done queue
* - 0x034
  - HcFmInterval
  - Frame interval + FS max packet
* - 0x038
  - HcFmRemaining
  - Bit time remaining in frame
* - 0x03C
  - HcFmNumber
  - Frame number counter
* - 0x040
  - HcPeriodicStart
  - Earliest periodic-list start time
* - 0x044
  - HcLSThreshold
  - Low-speed packet threshold
* - 0x048
  - HcRhDescriptorA
  - Root hub descriptor A
* - 0x04C
  - HcRhDescriptorB
  - Root hub descriptor B
* - 0x050
  - HcRhStatus
  - Root hub status / hub status change
* - 0x054
  - HcRhPortStatus[1]
  - Root hub port 1 status / change
```

The pointer registers `HcHCCA`, `HcPeriodCurrentED`, `HcControlHeadED`,
`HcControlCurrentED`, `HcBulkHeadED`, `HcBulkCurrentED` and `HcDoneHead` each
hold a physical address in their upper bits (D31:08 for HcHCCA — 256-byte
aligned; D31:04 for the ED/done pointers — 16-byte aligned) with the low bits
"must be 0" [HWRef p.686-692, Tables 461-467](#sources). The control/status registers have
these bitfields:

```{list-table} HcControl (0x1004) [HWRef p.674-677, Table 456](#sources)
:header-rows: 1
:widths: 12 10 10 10 58

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31:11
  - reserved
  - N/A
  - N/A
  - Reserved
* - D10
  - RWE
  - R/W
  - 0b
  - RemoteWakeupEnable
* - D09
  - RWC
  - R/W
  - 0b
  - RemoteWakeupConnected (firmware sets during POST)
* - D08
  - IR
  - R/W
  - 0b
  - InterruptRouting: 0 = normal host IRQ, 1 = SMI
* - D07:06
  - HCFS
  - R/W
  - 00b
  - Functional state: 00=RESET, 01=RESUME, 10=OPERATIONAL, 11=SUSPEND
* - D05
  - BLE
  - R/W
  - 0b
  - BulkListEnable
* - D04
  - CLE
  - R/W
  - 0b
  - ControlListEnable
* - D03
  - IE
  - R/W
  - 0b
  - IsochronousEnable
* - D02
  - PLE
  - R/W
  - 0b
  - PeriodicListEnable
* - D01:00
  - CBSR
  - R/W
  - 00b
  - ControlBulkServiceRatio: 0=1:1, 1=2:1, 2=3:1, 3=4:1
```

```{list-table} HcCommandStatus (0x1008, write-to-set) [HWRef p.678-680, Table 457](#sources)
:header-rows: 1
:widths: 12 10 10 10 58

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31:18
  - reserved
  - N/A
  - N/A
  - Reserved
* - D17:16
  - SOC
  - R
  - 00b
  - SchedulingOverrunCount (wraps at 11b)
* - D15:04
  - reserved
  - N/A
  - N/A
  - Reserved
* - D03
  - OCR
  - R/W
  - 0b
  - OwnershipChangeRequest
* - D02
  - BLF
  - R/W
  - 0b
  - BulkListFilled
* - D01
  - CLF
  - R/W
  - 0b
  - ControlListFilled
* - D00
  - HCR
  - R/W
  - 0b
  - HostControllerReset (software reset)
```

`HcInterruptStatus` (0x100C, write-1-to-clear), `HcInterruptEnable` (0x1010,
write-1-to-set) and `HcInterruptDisable` (0x1014, write-1-to-clear the enable)
share one event-bit layout [HWRef p.680-685, Tables 458-460]:

```{list-table} OHCI interrupt event bits (HcInterruptStatus / Enable / Disable)
:header-rows: 1
:widths: 12 10 10 12 56

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31
  - MIE
  - R/W
  - 0b
  - MasterInterruptEnable (Enable/Disable regs only; not in Status)
* - D30
  - OC
  - R/W
  - 0b
  - OwnershipChange
* - D29:07
  - reserved
  - N/A
  - N/A
  - Reserved
* - D06
  - RHSC
  - R/W
  - 0b
  - RootHubStatusChange
* - D05
  - FNO
  - R/W
  - 0b
  - FrameNumberOverflow
* - D04
  - UE
  - R/W
  - 0b
  - UnrecoverableError
* - D03
  - RD
  - R/W
  - 0b
  - ResumeDetected
* - D02
  - SF
  - R/W
  - 0b
  - StartOfFrame
* - D01
  - WDH
  - R/W
  - 0b
  - WritebackDoneHead
* - D00
  - SO
  - R/W
  - 0b
  - SchedulingOverrun
```

```{list-table} HcFmInterval (0x1034) [HWRef p.693-694, Table 468](#sources)
:header-rows: 1
:widths: 12 12 10 10 56

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31
  - FIT
  - R/W
  - 0b
  - FrameIntervalToggle
* - D30:16
  - FSMPS
  - R/W
  - 0
  - FSLargestDataPacket
* - D15:14
  - reserved
  - N/A
  - N/A
  - Reserved
* - D13:00
  - FI
  - R/W
  - 0x2EDF
  - FrameInterval in bit times (nominal 11,999)
```

`HcFmRemaining` (0x1038): D31 `FRT` (FrameRemainingToggle), D13:00 `FR`
(down-counter of bit time remaining) [HWRef p.694, Table 469](#sources). `HcFmNumber`
(0x103C): D15:00 `FN` frame-number counter [HWRef p.695, Table 470](#sources).
`HcPeriodicStart` (0x1040): D13:00 `PS` (R/W) earliest periodic-list start
[HWRef p.696, Table 471](#sources). `HcLSThreshold` (0x1044): D11:00 `LST` (R/W, reset
0x0628) low-speed threshold [HWRef p.697, Table 472](#sources).

```{list-table} HcRhDescriptorA (0x1048) [HWRef p.699-700, Table 473](#sources)
:header-rows: 1
:widths: 12 10 10 10 58

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31:24
  - POTPGT
  - R/W
  - IS
  - PowerOnToPowerGoodTime (×2 ms)
* - D23:13
  - reserved
  - N/A
  - N/A
  - Reserved
* - D12
  - NOCP
  - R/W
  - IS
  - NoOverCurrentProtection
* - D11
  - OCPM
  - R/W
  - IS
  - OverCurrentProtectionMode (per-port vs global)
* - D10
  - DT
  - R
  - 0b
  - DeviceType (root hub is never compound; reads 0)
* - D09
  - PSM
  - R/W
  - IS
  - PowerSwitchingMode (global vs per-port)
* - D08
  - NPS
  - R/W
  - IS
  - NoPowerSwitching
* - D07:00
  - NDP
  - R
  - IS
  - NumberDownstreamPorts (1–15)
```

`HcRhDescriptorB` (0x104C): D31:16 `PPCM` PortPowerControlMask (bit *n* = port
*n*, bit 0 reserved), D15:00 `DR` DeviceRemovable (bit *n* = port *n*, bit 0
reserved) [HWRef p.701, Table 474](#sources). ("IS" = implementation-specific reset value.)

```{list-table} HcRhStatus (0x1050) [HWRef p.702-704, Table 475](#sources)
:header-rows: 1
:widths: 12 10 10 10 58

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31
  - CRWE
  - W
  - N/A
  - ClearRemoteWakeupEnable (write 1)
* - D30:18
  - reserved
  - N/A
  - N/A
  - Always write 0
* - D17
  - CCIC
  - R/W
  - 0b
  - OverCurrentIndicatorChange (write 1 to clear)
* - D16
  - LPSC
  - R/W
  - 0b
  - LocalPowerStatusChange (read 0) / SetGlobalPower (write)
* - D15
  - DRWE
  - R/W
  - 0b
  - DeviceRemoteWakeupEnable (read) / SetRemoteWakeupEnable (write)
* - D14:02
  - reserved
  - N/A
  - N/A
  - Always write 0
* - D01
  - OCI
  - R
  - 0b
  - OverCurrentIndicator (global reporting)
* - D00
  - LPS
  - R/W
  - 0b
  - LocalPowerStatus (read 0) / ClearGlobalPower (write)
```

```{list-table} HcRhPortStatus[1] (0x1054) [HWRef p.705-710, Table 476](#sources)
:header-rows: 1
:widths: 12 10 10 10 58

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31:21
  - reserved
  - N/A
  - N/A
  - Always write 0
* - D20
  - PRSC
  - R/W
  - 0b
  - PortResetStatusChange (write 1 to clear)
* - D19
  - OCIC
  - R/W
  - 0b
  - PortOverCurrentIndicatorChange
* - D18
  - PSSC
  - R/W
  - 0b
  - PortSuspendStatusChange
* - D17
  - PESC
  - R/W
  - 0b
  - PortEnableStatusChange
* - D16
  - CSC
  - R/W
  - 0b
  - ConnectStatusChange
* - D15:10
  - reserved
  - N/A
  - N/A
  - Always write 0
* - D09
  - LSDA
  - R/W
  - Xb
  - LowSpeedDeviceAttached (read) / ClearPortPower (write)
* - D08
  - PPS
  - R/W
  - 0b
  - PortPowerStatus (read) / SetPortPower (write)
* - D07:05
  - reserved
  - N/A
  - N/A
  - Always write 0
* - D04
  - PRS
  - R/W
  - 0b
  - PortResetStatus (read) / SetPortReset (write)
* - D03
  - POCI
  - R/W
  - 0b
  - PortOverCurrentIndicator (read) / ClearSuspendStatus (write)
* - D02
  - PSS
  - R/W
  - 0b
  - PortSuspendStatus (read) / SetPortSuspend (write)
* - D01
  - PES
  - R/W
  - 0b
  - PortEnableStatus (read) / SetPortEnable (write)
* - D00
  - CCS
  - R/W
  - 0b
  - CurrentConnectStatus (read) / ClearPortEnable (write)
```

---

## USB Device

**Base address: 0x9090_0000** — chapter 17 [HWRef p.723](#sources). A USB 2.0 device
controller with 11 physical endpoints (bidirectional control endpoint 0 plus up
to 10 unidirectional), a 12-FIFO front end (UDFE) and a 13-channel BBus DMA
controller (one channel per endpoint FIFO). All configuration registers are
32-bit single-access [HWRef p.723-724](#sources).

**Unused in the stock firmware.** Its reset bit is `USBDEV` (bit 12 of the BBus
Master Reset) and its host/device role is selected by the BBus USB configuration
register (0x9060_0070) [HWRef p.723](#sources), [digi-uboot ns9750_bbus.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/reference/digi-cc9p9360-uboot/u-boot-1.1.4-digi/U-Boot/include/ns9750_bbus.h). (Note: the older
2-port NS9750 variant used a single combined `USB` reset bit; the NS9360 splits
host and device — see the BBus Master Reset table under {doc}`soc-ns9360-io`.)

```{list-table} USB device address map (base 0x9090_0000) [HWRef p.723, Table 479](#sources)
:header-rows: 1
:widths: 34 66

* - Address range
  - Register space
* - 0x9090_0000–0x9090_0FFF
  - UDFE control/status (global)
* - 0x9090_2000–0x9090_2FFF
  - USB device controller block (endpoint descriptors)
* - 0x9090_3000–0x9090_3FFF
  - UDFE endpoint-FIFO control (interrupt/packet/status registers)
* - 0x9091_0000–0x9091_FFFF
  - USB device DMA (BBus DMA controller 2; see the DMA chapter)
```

### UDFE global registers (0x0000–0x0014) [HWRef p.724-731, Tables 480-485](#sources)

```{list-table} UDFE Control/Status Register 0 (0x0000) [HWRef p.725, Table 481](#sources)
:header-rows: 1
:widths: 12 12 10 10 56

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31:11
  - reserved
  - R
  - 0
  - Always read 0
* - D10:09
  - DRST
  - R
  - 11
  - Device block reset status: 00 = operational, 11 = in reset
* - D08:06
  - reserved
  - R
  - 0
  - Read-only
* - D05
  - SUSP
  - R
  - 0
  - Suspend: 1 = device is suspended
* - D04:03
  - reserved
  - R
  - 0
  - Read-only
* - D02
  - WKUP
  - R/W
  - 0
  - Remote-wakeup enable
* - D01:00
  - reserved
  - R
  - 1
  - Read-only
```

```{list-table} UDFE Control/Status Register 1 (0x0004) [HWRef p.726-727, Table 482](#sources)
:header-rows: 1
:widths: 12 12 10 10 56

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31
  - RSME
  - R/W
  - 0
  - Resume: set to start, clear to end a resume sequence
* - D30
  - reserved
  - R
  - 0
  - Read 0
* - D29
  - SPWR
  - R/W
  - 0
  - Self-powered (write 1 — NS9360 is always self-powered)
* - D28
  - reserved
  - R/W
  - 0
  - Always write 1
* - D27
  - SYNC
  - R/W
  - 0
  - SYNC_FRAME support (isochronous)
* - D26:23
  - reserved
  - R
  - 0
  - Read-only
* - D22:12
  - FRAME
  - R
  - 0x000
  - Current frame number (diagnostic)
* - D11:08
  - ALT
  - R
  - 0x0
  - Current alternate value (diagnostic)
* - D07:04
  - INTF
  - R
  - 0x0
  - Current interface value (diagnostic)
* - D03:00
  - CFG
  - R
  - 0x0
  - Current configuration value (diagnostic)
```

```{list-table} UDFE Interrupt Enable (0x000C) [HWRef p.727-728, Table 483](#sources)
:header-rows: 1
:widths: 12 14 10 10 54

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31
  - GBL_EN
  - R/W
  - 0
  - Global interrupt enable (write 1 for normal operation)
* - D30:28
  - reserved
  - R
  - 0
  - Read 0
* - D27
  - GBL_DMA
  - R/W
  - 0
  - Global DMA interrupt enable
* - D26
  - reserved
  - R/W
  - 0
  - Always write 0
* - D25:14
  - DMA12…DMA1
  - R/W
  - 0
  - Per-channel DMA interrupt enable (channel 12 down to 1)
* - D13
  - reserved
  - R/W
  - 0
  - Always write 0
* - D12
  - FIFO
  - R/W
  - 0
  - Enable any-FIFO interrupt (gated by per-FIFO enables)
* - D11
  - URST
  - R/W
  - 0
  - USB bus-reset interrupt enable
* - D10
  - SOF
  - R/W
  - 0
  - Start-of-frame packet interrupt enable
* - D09
  - SSPND
  - R/W
  - 0
  - Suspend interrupt enable
* - D08
  - SETINTF
  - R/W
  - 0
  - SET_INTERFACE packet interrupt enable
* - D07
  - SETCFG
  - R/W
  - 0
  - SET_CONFIGURATION packet interrupt enable
* - D06:00
  - reserved
  - N/A
  - 0
  - Reserved
```

```{list-table} UDFE Interrupt Status (0x0010, write-1-to-clear) [HWRef p.729-730, Table 484](#sources)
:header-rows: 1
:widths: 12 14 10 10 54

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31:28
  - reserved
  - R
  - 0
  - Read 0
* - D27
  - GBL_DMA
  - R
  - 0
  - Logical OR of the DMA channel interrupt bits
* - D26
  - reserved
  - R
  - 0
  - N/A
* - D25:14
  - DMA12…DMA1
  - R
  - 0
  - Per-channel DMA interrupt (service in the DMA block)
* - D13
  - reserved
  - R
  - 0
  - Read 0
* - D12
  - FIFO
  - R
  - 0
  - Logical OR of enabled FIFO interrupt-status bits
* - D11
  - URST
  - RW1TC
  - 0
  - USB reset detected on the bus
* - D10
  - SOF
  - RW1TC
  - 0
  - Start-of-frame packet received
* - D09
  - SSPND
  - RW1TC
  - 0
  - Device entered SUSPEND
* - D08
  - SETINTF
  - RW1TC
  - 0
  - SET_INTERFACE packet received
* - D07
  - SETCFG
  - RW1TC
  - 0
  - SET_CONFIGURATION packet received
* - D06
  - reserved
  - N/A
  - N/A
  - Reserved
* - D05:00
  - reserved
  - R
  - 0
  - Read 0
```

```{list-table} UDFE Device Controller Programming Control/Status (0x0014) [HWRef p.731, Table 485](#sources)
:header-rows: 1
:widths: 12 12 10 10 56

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31:03
  - reserved
  - R
  - 0
  - Read 0x00000000
* - D02
  - SETCSR
  - R
  - 0
  - CSR programming start (1 = safe to program the controller CSRs)
* - D01
  - DONECSR
  - R/W
  - 0
  - CSR programming done (write 1 when finished)
* - D00
  - CSRPRG
  - R/W
  - 0
  - CSR dynamic-programming enable (set at power-up, then leave)
```

### USB device controller block (0x2000–0x2030) [HWRef p.732-734, Tables 486-487](#sources)

`Device Descriptor / Setup Command register` (0x2000) is a legacy register that
must be written to 0x0000_0100 [HWRef p.733](#sources). The 12 **Physical Endpoint
Descriptor** registers (0x2004, 0x2008, … 0x2030 — one per endpoint descriptor
#0–#11) all share this layout:

```{list-table} Physical Endpoint Descriptor #0–#11 (0x2004–0x2030) [HWRef p.734, Table 487](#sources)
:header-rows: 1
:widths: 12 12 10 10 56

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31:29
  - reserved
  - R/W
  - 0x0
  - Always write 0
* - D28:19
  - MAXSIZE
  - R/W
  - 0x000
  - Maximum packet size (match the FIFO Packet Control MAX field)
* - D18:15
  - ALT
  - R/W
  - 0x0
  - Alternate setting this endpoint belongs to (0–4)
* - D14:11
  - IF
  - R/W
  - 0x0
  - Interface number (0–4)
* - D10:07
  - CONFIG
  - R/W
  - 0x0
  - Configuration number (0–5; 0 invalid if dynamic programming enabled)
* - D06:05
  - TYPE
  - R/W
  - 0x0
  - Endpoint type: 00 = control, 01 = isochronous, 10 = bulk, 11 = interrupt
* - D04
  - DIR
  - R/W
  - 0x0
  - Direction: 0 = OUT, 1 = IN
* - D03:00
  - EP
  - R/W
  - 0x0
  - Endpoint number (0–10)
```

### UDFE endpoint-FIFO control block (0x3000–0x3158) [HWRef p.735-752, Tables 488-500](#sources)

The 12 endpoint FIFOs have a fixed FIFO ↔ DMA-channel ↔ endpoint mapping: FIFO/
channel 1 = EP0 (CTRL-Out), FIFO 2 = EP0 (CTRL-In), FIFO 3 = EP1, … FIFO 12 =
EP10 [HWRef p.736-737, Table 489](#sources). Register map:

```{list-table} UDFE endpoint-FIFO control register map (offset from 0x9090_0000) [HWRef p.735-736, Table 488](#sources)
:header-rows: 1
:widths: 20 34 46

* - Offset
  - Register
  - Description
* - 0x3000 / 3010 / 3020 / 3030
  - FIFO Interrupt Status 0–3
  - Per-endpoint ACK/NAK/ERROR status (write-1-to-clear)
* - 0x3004 / 3014 / 3024 / 3034
  - FIFO Interrupt Enable 0–3
  - Per-endpoint ACK/NAK/ERROR interrupt enable
* - 0x3080–0x30AC
  - FIFO Packet Control #1–#12
  - Per-FIFO max packet size + IN packet count
* - 0x3100–0x3158
  - FIFO Status and Control #1–#12
  - Per-FIFO stall/type/direction/clear + status
```

Each **FIFO Interrupt Status** register packs three status bits per endpoint —
`ACKn` / `NAKn` / `ERRORn`, where *n* is the FIFO number — into byte-aligned
fields; the meanings (per direction) are defined once in Table 490
[HWRef p.738, Table 490](#sources). The bit positions are [HWRef p.738-745, Tables 491-494]:

```{list-table} FIFO Interrupt Status bit layout (Enable registers mirror these positions)
:header-rows: 1
:widths: 20 14 14 14 38

* - Register (offset)
  - D31:29 / D23:21
  - D15:13
  - D07:05
  - Endpoints covered
* - FIFO Int Status 0 (0x3000)
  - —
  - ACK2/NAK2/ERROR2
  - ACK1/NAK1/ERROR1
  - EP0-In (FIFO 2), EP0-Out (FIFO 1)
* - FIFO Int Status 1 (0x3010)
  - ACK6…/ACK5…
  - ACK4/NAK4/ERROR4
  - ACK3/NAK3/ERROR3
  - EP4, EP3, EP2, EP1 (FIFO 6/5/4/3)
* - FIFO Int Status 2 (0x3020)
  - ACK10…/ACK9…
  - ACK8/NAK8/ERROR8
  - ACK7/NAK7/ERROR7
  - EP8, EP7, EP6, EP5 (FIFO 10/9/8/7)
* - FIFO Int Status 3 (0x3030)
  - —
  - ACK12/NAK12/ERROR12
  - ACK11/NAK11/ERROR11
  - EP10 (FIFO 12), EP9 (FIFO 11)
```

Within each 3-bit group the high bit is `ACKn`, the middle `NAKn`, the low
`ERRORn` (all RW1TC); for IN endpoints ACK = host ACK received, NAK = NAK sent
(no data ready), ERROR = no ACK / STALL sent; for OUT endpoints ACK = ACK sent,
NAK = NAK sent (FIFO full), ERROR = receive error / STALL sent [HWRef p.738,
Table 490]. The FIFO Interrupt Enable registers (0x3004/3014/3024/3034) carry an
enable bit at each of these positions [HWRef p.742-748, Tables 495-498](#sources).

```{list-table} FIFO Packet Control #1–#12 (0x3080–0x30AC) [HWRef p.749, Table 499](#sources)
:header-rows: 1
:widths: 12 12 10 10 56

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31:30
  - reserved
  - R
  - 0x0
  - Read 0
* - D29:20
  - MAX
  - R/W
  - 0x040
  - Maximum packet size (match the endpoint descriptor; N/A for FIFO 2)
* - D19:16
  - reserved
  - R
  - 0x0
  - Read 0
* - D15:00
  - COUNT
  - R
  - 0x0000
  - Error-free IN packets sent with the current DMA descriptor (N/A for FIFO 1)
```

```{list-table} FIFO Status and Control #1–#12 (0x3100–0x3158) [HWRef p.750-752, Table 500](#sources)
:header-rows: 1
:widths: 12 14 10 10 54

* - Bits
  - Field
  - Access
  - Reset
  - Meaning
* - D31:24
  - reserved
  - R
  - 0x00
  - Read 0
* - D23
  - STALL_SENT
  - RW1TC
  - 0
  - Device sent a STALL because SEND_STALL was set
* - D22
  - SEND_STALL
  - R/W
  - 0
  - Send STALL to all IN/OUT packets until cleared
* - D21:20
  - TYPE
  - R/W
  - 0x0
  - Endpoint type: 00 = control, 01 = iso, 10 = bulk, 11 = interrupt
* - D19
  - CLR
  - R/W
  - 1
  - Write 1 to reset/flush the FIFO and disable the endpoint
* - D18
  - DIR
  - R/W
  - 0
  - FIFO direction: 0 = OUT, 1 = IN
* - D17:14
  - reserved
  - R
  - 0x0
  - Read 0
* - D13
  - M31
  - R
  - 0
  - Successful-transfer status (1 = ACK path completed)
* - D12
  - M30
  - R
  - 0
  - Setup-command status (1 = current transaction is a setup)
* - D11
  - OVERFLOW
  - R
  - 0
  - FIFO overflowed during a USB-OUT packet
* - D10
  - TIMEOUT
  - R
  - 0
  - DMA receive buffer closed due to timeout
* - D09:04
  - reserved
  - R
  - 0x00
  - Read 0
* - D03:00
  - TIMEOUT_CNT
  - R/W
  - 0x0
  - Timeout count (SOFs) to close a receive buffer on an exact-multiple OUT packet
```

The endpoint FIFO *data* is moved by the USB device BBus DMA controller at
0x9091_0000–0x9091_FFFF (BBus DMA controller 2); its per-channel buffer-descriptor
/ control / status registers are documented in the BBus DMA chapter and under
{doc}`soc-ns9360-io` [HWRef p.723, Table 479](#sources).

---

## See also

**Related pages**

- {doc}`/hardware/soc-ns9360` — the NS9360 SoC overview and SCM register map
- {doc}`/hardware/soc-ns9360-io` — the BBus Master Reset / clock-enable bits that gate these blocks
- {doc}`/hardware/soc-ns9360-memory-serial` — memory controller, Ethernet and serial
- {doc}`/systems/hpe-ipdu` — the board where these blocks sit unused

**External references**

- [Linux `arch/arm/mach-ns9xxx` (v2.6.39)](https://github.com/torvalds/linux/tree/v2.6.39/arch/arm/mach-ns9xxx) — the historical mainline tree (which carries **no** LCD/1284/USB register defs)
- [U-Boot documentation](https://docs.u-boot.org/en/latest/) — the open-firmware path chosen for this SoC
- [Zephyr architecture-porting guide](https://docs.zephyrproject.org/latest/hardware/porting/arch.html) — the ARMv5 / ARM926EJ-S port this core needs

## Sources

Primary datasheet (in-repo, the authority for the register map):

- **NS9360 Hardware Reference**, Digi 90000675 rev J — cited inline as **HWRef p.N**, where `N`
  is the printed document page (identical to the PDF page). In-repo at
  [`hpe-ipdu-firmware/datasheets/NS9360_HW_Reference_90000675_J.pdf`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/datasheets/NS9360_HW_Reference_90000675_J.pdf); online at
  [ftp1.digi.com/90000675_J.pdf][hwref-url]. Chapters used: ch 12 LCD
  (p.543–562), ch 15 IEEE 1284 (p.635–662), ch 16 USB host (p.663–710), ch 17
  USB device (p.723–752).

In-repo analysis / port planning (board specifics):

- [`PLAN-INCREMENTAL-PORT.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/PLAN-INCREMENTAL-PORT.md) — [`hpe-ipdu-firmware/uboot-port/PLAN-INCREMENTAL-PORT.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/PLAN-INCREMENTAL-PORT.md)
  (LCD palette RAM used as endian-switch scratch; register quick reference).

Open-source cross-reference (register names, bases, bitfields):

- [mach-ns9xxx regs-bbu.h](https://github.com/torvalds/linux/blob/v2.6.39/arch/arm/mach-ns9xxx/include/mach/regs-bbu.h), [mach-ns9xxx regs-sys-ns9360.h](https://github.com/torvalds/linux/blob/v2.6.39/arch/arm/mach-ns9xxx/include/mach/regs-sys-ns9360.h) — mainline Linux
  [`arch/arm/mach-ns9xxx`](https://github.com/torvalds/linux/tree/v2.6.39/arch/arm/mach-ns9xxx) (tag v2.6.39). Verified to contain **no** LCD / IEEE 1284
  / USB register definitions; only GPIO ([`regs-bbu.h`](https://github.com/torvalds/linux/blob/v2.6.39/arch/arm/mach-ns9xxx/include/mach/regs-bbu.h)) and system-control
  ([`regs-sys-ns9360.h`](https://github.com/torvalds/linux/blob/v2.6.39/arch/arm/mach-ns9xxx/include/mach/regs-sys-ns9360.h)) registers. Raw source, e.g.
  [regs-bbu.h][machbbu-url].
- [digi-uboot ns9360_usb.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/reference/digi-cc9p9360-uboot/u-boot-1.1.4-digi/U-Boot/include/ns9360_usb.h) — FS-Forth / Digi U-Boot for the CC9P9360
  (in-repo at
  [`hpe-ipdu-firmware/uboot-port/reference/digi-cc9p9360-uboot/u-boot-1.1.4-digi/U-Boot/include/ns9360_usb.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/reference/digi-cc9p9360-uboot/u-boot-1.1.4-digi/U-Boot/include/ns9360_usb.h)):
  confirms OHCI base `0x9080_1000` and `HcRhPortStatus` at `+0x54`.
- [digi-uboot ns9750_usb_ohci.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/reference/digi-cc9p9360-uboot/u-boot-1.1.4-digi/U-Boot/include/ns9750_usb_ohci.h) — same tree,
  [`include/ns9750_usb_ohci.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/reference/digi-cc9p9360-uboot/u-boot-1.1.4-digi/U-Boot/include/ns9750_usb_ohci.h): standard OHCI `HcControl` / `HcCommandStatus`
  bit masks (`OHCI_CTRL_CBSR/PLE/IE/CLE/BLE/HCFS/IR/RWC/RWE`, `OHCI_HCR/CLF/BLF/OCR`),
  matching the datasheet bitfields above.
- [digi-uboot ns9750_bbus.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/reference/digi-cc9p9360-uboot/u-boot-1.1.4-digi/U-Boot/include/ns9750_bbus.h) — same tree, [`include/ns9750_bbus.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/reference/digi-cc9p9360-uboot/u-boot-1.1.4-digi/U-Boot/include/ns9750_bbus.h): BBus Master
  Reset bits (`…RESET_1284`=0x40, `…RESET_USB`) and USB configuration bits
  (`USB_CFG_CFG_HOST/DEVICE/DIS`) that gate these blocks; note the 2-port NS9750
  uses one combined USB reset bit whereas the NS9360 splits host/device.
- [digi-uboot](https://github.com/mithro/ai-shenanigans-for-bmcs/tree/main/hpe-ipdu-firmware/uboot-port/reference/digi-cc9p9360-uboot) — the FS-Forth / Digi CC9P9360 U-Boot tree as a whole (in-repo,
  path above), used to confirm the block base addresses.

[hwref-url]: https://ftp1.digi.com/support/documentation/90000675_J.pdf
[machbbu-url]: https://raw.githubusercontent.com/torvalds/linux/v2.6.39/arch/arm/mach-ns9xxx/include/mach/regs-bbu.h
