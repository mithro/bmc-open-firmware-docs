# AST2050 SCU, clocking, reset & watchdog

This is a register-by-register reference for the Aspeed **AST2050 / AST1100 (A3, "G3")**
System Control Unit (SCU), its clock/PLL tree, the hardware strap register, the
SoC reset domains, and the watchdog timer. Every claim is cross-referenced
between the vendor A3 datasheet and the in-repo Raptor Engineering AST2050 port
(register headers + DDR/PLL init assembly), and where useful against the
register-close AST2400 (G4) mainline Linux clock driver.

Unless stated otherwise, all offsets in this document are relative to the SCU
base `0x1E6E2000`, all reset ("Init") values are the datasheet power-on values,
and all field bit ranges are inclusive `[msb:lsb]`. The AST2050 is **not**
supported by mainline Linux; the G4 driver is only used here to corroborate
formulas and strap semantics, and the strap *bit positions differ* between G3
and G4 (documented below).

```{admonition} Conventions
:class: note

- **Access** column: `RO` read-only, `RW` read/write, `WO` write-only,
  `W1C` write-1-to-clear, `R/WSC` read + write-set/self-clearing.
- Offsets not listed in a block's register map are **reserved** on the G3 and
  must not be assumed to exist just because a later Aspeed generation defines
  them.
- The SCU input reference is **always a 24 MHz crystal** on the AST2050
  (there is no 25/48 MHz crystal option as on the AST2400). [DS §8.1 p.84](#sources)
  [pin R22 CLKIN, DS p.47](#sources) [RAPTOR-PORTING-GUIDE.md:40,232](#sources)
```

## System Control Unit (SCU)

The SCU implements the chip-level control registers at base `0x1E6E2000`
(4 KiB region `1E6E:2000–1E6E:2FFF`). It owns the PLLs, clock select/stop, module
resets, hardware-strap readback, silicon-revision ID, pin muxing, and the
ARM↔host scratch registers. Because writing these registers can badly disturb
SoC operation, the whole block is write-protected by the SCU00 protection key:
software must write `0x1688A8A8` to unlock, program, then write any other value
to re-lock. [DS §18.1 p.204](#sources) [DS §9 p.97](#sources) [hwreg.h:77](#sources)

```{list-table} SCU register map (base 0x1E6E2000)
:header-rows: 1

* - Offset
  - Register
  - Reset
  - Access
  - Description
* - 0x00
  - SCU00 Protection Key
  - 0x00000000
  - RW
  - Write `0x1688A8A8` to unlock; any other value locks. Reads back `1` when unlocked, `0` when locked. [DS p.204](#sources) [hwreg.h:79](#sources)
* - 0x04
  - SCU04 System Reset Control
  - 0x000FFE5C
  - RW
  - Per-module asynchronous reset bits (SDRAM, AHB bridges, I2C, HAC, LPC, video, MAC1/2, PWM, PECI, USB2.0, MDMA, MIC, PCI host). Default holds most modules in reset. [DS p.205](#sources) [hwreg.h:80](#sources)
* - 0x08
  - SCU08 Clock Selection
  - 0xE3F00070
  - RW
  - LHCLK/PCLK/BHCLK dividers, RTC clock source, video-port-A delay, CPU throttle, ECLK & MCLK source selects. [DS p.207](#sources)
* - 0x0C
  - SCU0C Clock Stop Control
  - 0x000C3E8B
  - RW
  - Per-clock gate (stop) bits: ECLK, GCLK, MCLK, V1CLK, BCLK, DCLK, REFCLK, UCLK, LCLK, YCLK, USB2.0, UARTCLK, BHCLK. [DS p.209](#sources)
* - 0x10
  - SCU10 Frequency Counter Control
  - 0x00000000
  - RW/RO
  - Ring-oscillator / PLL frequency-measurement control and pass/finish status. [DS p.210](#sources)
* - 0x14
  - SCU14 Frequency Counter Measurement
  - 0x00000000
  - RO
  - 14-bit measured counter value; $\text{freq} = \dfrac{24\,\text{MHz}}{512} \times (\text{value}+1)$. [DS p.211](#sources)
* - 0x18
  - SCU18 Interrupt Control & Status
  - 0x00000000
  - RW/W1C
  - Enable + status for VGA-cursor-change and VGA-scratch-change interrupts (status bits are W1C). [DS p.211](#sources)
* - 0x1C
  - SCU1C 32.768 KHz Error Correction
  - 0x0000001B
  - RW
  - Fine-tunes the RTC 32.768 KHz source: $\text{RTCclk} = \dfrac{12\,\text{MHz} \times 128}{46848 + \text{corr}}$. [DS p.211](#sources) [hwreg.h:86](#sources)
* - 0x20
  - SCU20 M-PLL Parameter
  - 0x00004291
  - RW
  - Memory-clock PLL. Numerator/denominator/output-divider/post-divider, bypass, power-down. Default ≈133 MHz. [DS p.211](#sources) [hwreg.h:87](#sources)
* - 0x24
  - SCU24 H-PLL Parameter
  - 0x00004291
  - RW
  - CPU/AHB PLL. Same field layout as M-PLL, plus strap-vs-register select (bit 18). Default from straps (100/133/166/200 MHz). [DS p.212](#sources) [hwreg.h:88](#sources)
* - 0x28
  - SCU28 Frequency Counter Comparison Range
  - 0x00000000
  - RW
  - Upper limit [29:16] and lower limit [13:0] for the SCU10 pass/fail compare. [DS p.213](#sources) [hwreg.h:89](#sources)
* - 0x2C
  - SCU2C Misc. Control
  - 0x00000000
  - RW
  - UART1/2 link & mux, UART div13 reference-clock enable (bit 12), YCLK invert, D1-PLL disable, video DAC, SMC output buffers, PCI-slave bridge disable. [DS p.213](#sources)
* - 0x30
  - SCU30 PCI Config Setting #1
  - 0x20001A03
  - RW
  - PCI Device ID [31:16] / Vendor ID [15:0] presented to the host. [DS p.214](#sources)
* - 0x34
  - SCU34 PCI Config Setting #2
  - 0x20001A03
  - RW
  - PCI Sub-System ID [31:16] / Sub-Vendor ID [15:0]. [DS p.214](#sources)
* - 0x38
  - SCU38 PCI Config Setting #3
  - 0x03000000
  - RW
  - PCI Class Code [31:8] / Revision ID [7:0]. [DS p.214](#sources)
* - 0x3C
  - SCU3C System Reset Control (reset flags)
  - 0x00000001
  - RW
  - EXTRST# (GPIOB7) enable, and the power-on / watchdog / external reset source flags. [DS p.214](#sources)
* - 0x40
  - SCU40 SOC Scratch #1 (VGA handshake, bits 31:0)
  - 0x00000000
  - RW
  - ARM→host scratch. Bits used by firmware: Linux-boot key [31:24]=0x5A, DRAM-init-select [7], DRAM-init-ready [6], MAC PHY mode [15:12]. [DS p.215](#sources) [hwreg.h:91](#sources)
* - 0x44
  - SCU44 SOC Scratch #2 (scratch bits 63:32)
  - 0x00000000
  - RW
  - ARM→host scratch, upper 32 bits; firmware stores "last service IRQ number". [DS p.216](#sources) [hwreg.h:92](#sources)
* - 0x48
  - (reserved on G3)
  - —
  - —
  - Not defined in the A3 datasheet. On the AST2400 this offset is the MAC clock-delay register (`AST_SCU_MAC_CLK`); treat as reserved on the AST2050. [DS §18.1 p.204](#sources) [RAPTOR_ENGINEERING_AST2050_ANALYSIS.md:320](#sources)
* - 0x4C
  - (reserved on G3)
  - —
  - —
  - Not defined in the A3 datasheet — reserved/unused on the G3.
* - 0x50–0x6C
  - SCU50…SCU6C VGA Scratch #1…#8
  - 0x00000000
  - RO
  - Host→ARM scratch, 256 bits total (8×32). Read-only to the ARM; written by the host CPU. [DS p.216](#sources)
* - 0x70
  - SCU70 Hardware Trapping (strap)
  - strap-defined (Init listed 0)
  - RW/RO
  - Latched hardware straps: boot source, H-PLL freq, CPU:AHB ratio, boot speed, MAC mode, VGA memory size, PLL bypass, LPC reset pin, test mode. [DS p.217](#sources)
* - 0x74
  - SCU74 Multi-function Pin Control #1
  - 0x40048000
  - RW
  - Pin-mux enables: I2C#5–7, PWM1–4, PECI, MAC MDIO/PHYLINK, VGA/DDC, UART2 full pins, HCLK output, NOR-flash pins, PCI REQ/GNT. [DS p.219](#sources)
* - 0x78
  - SCU78 Multi-function Pin Control #2
  - 0x00000000
  - RW
  - Watchdog-reset event output enable (bit 3), video-port-A modes, PCI INTA# disable. [DS p.219](#sources)
* - 0x7C
  - SCU7C Silicon Revision ID
  - 0x00000202
  - RO
  - Chip-bonding option [9:8] + silicon revision ID [7:0]. AST2050/AST1100-A2 and -A3 both read `0x00000202`. [DS p.220](#sources) [hwreg.h:94](#sources)
```

```{admonition} Offsets 0x48 and 0x4C
:class: warning

These two words are the only gaps in the SCU00–SCU7C range and are **not
documented** in the AST2050/AST1100 A3 datasheet. Do not port the AST2400 MAC
clock-delay handling (SCU48) blindly; verify on hardware before using it on the
G3. [DS §18.1 p.204](#sources)
```

### SCU00 — Protection Key (offset 0x00)

The password gate for the whole SCU. The password is `0x1688A8A8`; writing it
unlocks, writing anything else re-locks. Reads are *not* gated — reading any SCU
register works regardless of lock state — but this register itself reads back a
status value, not the key. The initial state is **locked**. [DS p.204](#sources)

```{list-table} SCU00 fields
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 31:0
  - Protection Key
  - RW
  - Write `0x1688A8A8` = unlock. Write any other value = lock. Read-back: `0x00000001` when unlocked, `0x00000000` when locked. [DS p.204](#sources)
```

The Raptor DDR init exercises exactly this: it writes `0x1688a8a8`, then reads
back and compares against `0x01` to confirm the unlock succeeded before touching
any clock/DRAM register, and finally writes `0x00000000` to re-lock.
[platform.S:240-247](#sources) [platform.S:334-336](#sources) [platform.S:590-592](#sources)

### SCU08 — Clock Selection (offset 0x08)

Selects dividers and sources for the derived bus clocks. All dividers here run
off H-PLL. [DS p.207](#sources)

```{list-table} SCU08 fields
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 31:29
  - LPC master LHCLK divider
  - RW
  - `000`=H-PLL/2 … `111`=H-PLL/16 (steps of 2). [DS p.207](#sources)
* - 28
  - LHCLK generate/output enable
  - RW
  - 0=LHCLK from external LCLK pin; 1=generated internally. [DS p.207](#sources)
* - 27:26
  - Reserved
  - RW
  - Don't use. [DS p.207](#sources)
* - 25:23
  - APB PCLK divider
  - RW
  - `000`=H-PLL/2 … `111`=H-PLL/16. PCLK frequency has LPC-related limits (see clock tree). [DS p.207](#sources)
* - 22:20
  - PCI host BHCLK divider
  - RW
  - `000`=H-PLL/2 … `111`=H-PLL/16. [DS p.207](#sources)
* - 19
  - BHCLK generate/output enable
  - RW
  - 0=from external BCLK pin; 1=generated internally. [DS p.207](#sources)
* - 18:17
  - Reserved
  - RW
  - Don't use. [DS p.207](#sources)
* - 16
  - RTC clock source (test only)
  - RW
  - 0=32.768 KHz source; 1=24 MHz source. [DS p.208](#sources)
* - 15:11
  - Reserved
  - RW
  - Keep 0. [DS p.208](#sources)
* - 10:8
  - Video port-A output clock delay [3:1]
  - RW
  - Combined with SCU2C[9] as bit[0]; 0–3.5 ns delay, optional clock inversion. [DS p.208](#sources)
* - 7
  - ARM CPU clock throttle enable
  - RW
  - 1=slow CPU for standby power saving (anti-glitch). [DS p.208](#sources)
* - 6:4
  - ARM CPU throttle ratio
  - RW
  - `000`=÷2 … `111`=÷16. [DS p.208](#sources)
* - 3:2
  - ECLK source select
  - RW
  - 00=M-PLL, 01=H-PLL, 10=inverted M-PLL, 11=inverted H-PLL. Stop ECLK + reset Video Engine before changing. [DS p.208](#sources)
* - 1:0
  - MCLK source select
  - RW
  - 00=M-PLL, 01=H-PLL, 10=inv M-PLL, 11=inv H-PLL. Change only at boot before DRAM init; disable MCLK (SCU0C[2]) first. [DS p.208](#sources)
```

### SCU0C — Clock Stop Control (offset 0x0C)

Per-clock gating. On most bits `1` = stop (gate off); several default to stopped
to save power until a driver enables the block. [DS p.209](#sources)

```{list-table} SCU0C fields (selected)
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 19
  - Stop BHCLK (PCI host)
  - RW
  - 1=stop (default). [DS p.209](#sources)
* - 15
  - Stop UARTCLK (UART1/2)
  - RW
  - 0=run (default), 1=stop. [DS p.209](#sources)
* - 14
  - Enable USB2.0 clock
  - RW
  - 0=stop + power-down PHY (default); 1=run (then wait 10 ms before clearing SCU04[14]). [DS p.209](#sources)
* - 13
  - Stop YCLK (HAC)
  - RW
  - 1=stop (default). [DS p.209](#sources)
* - 8
  - Stop LCLK (LPC)
  - RW
  - 0=run (default). [DS p.209](#sources)
* - 7
  - Stop UCLK (USB1.1)
  - RW
  - 1=stop (default). [DS p.209](#sources)
* - 6
  - REFCLK stop (24 MHz)
  - RW
  - 0=run (default). [DS p.209](#sources)
* - 5
  - Stop DCLK (VGA)
  - RW
  - 0=run (default). [DS p.209](#sources)
* - 4
  - Stop BCLK (PCI slave)
  - RW
  - 0=run (default). [DS p.209](#sources)
* - 3
  - Stop V1CLK (video capture #1)
  - RW
  - 1=stop (default). [DS p.210](#sources)
* - 2
  - Stop MCLK (SDRAM)
  - RW
  - 0=run (default). Disable before changing SCU08[1:0]. [DS p.210](#sources)
* - 1
  - Stop GCLK (2D engine)
  - RW
  - 1=stop (default). [DS p.210](#sources)
* - 0
  - Stop ECLK (video engine)
  - RW
  - 1=stop (default). [DS p.210](#sources)
```

Bits `18` and `12:9` are marked "reserved, must keep at 1"; bits `31:20`, `17:16`
are reserved 0. [DS p.209](#sources)

### SCU10 / SCU14 — Frequency counter (offsets 0x10, 0x14)

A ring-oscillator / PLL frequency measurement facility used for self-test and to
calibrate clocks against the 24 MHz reference. [DS p.210-211](#sources) [hwreg.h:83-84](#sources)

```{list-table} SCU10 fields
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 7
  - Compare result
  - RO
  - 0=fail, 1=pass (SCU14 within SCU28 limits). [DS p.210](#sources)
* - 6
  - Measurement finished
  - RO
  - 0=not finished, 1=finished; cleared by SCU10[1]=0. [DS p.210](#sources)
* - 5:2
  - Measurement clock source
  - RW
  - 0011=D2-PLL, 0100=M-PLL, 0101=H-PLL, 0010=PCI, 0110=LPC, ring oscillators, video port clocks. [DS p.210](#sources)
* - 1
  - Oscillator counter enable
  - RW
  - 0=reset counter, 1=enable. [DS p.210](#sources)
* - 0
  - Enable ring oscillator
  - RW
  - 1=enable (wait 1 ms to settle). [DS p.210](#sources)
```

Measurement algorithm: reference `CLK24M` counts 0→512 while `OSCCLK` is counted,
giving $\text{OSCCLK} = \dfrac{24\,\text{MHz}}{512} \times (\text{SCU14}+1)$. SCU14[13:0] holds the count; SCU28
holds the pass/fail comparison window (upper limit [29:16], lower limit [13:0]).
[DS p.210-211, §SCU28 p.213](#sources)

### SCU2C — Misc. Control (offset 0x2C)

Miscellaneous control, notably the **UART div13 reference-clock enable** the DDR
init reads to pick a baud divisor. [DS p.213](#sources)

```{list-table} SCU2C fields (selected)
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 15
  - UART1↔UART2 internal link
  - RW
  - 1=cross-connect the two UART signal sets internally. [DS p.213](#sources)
* - 14
  - UART1 pin MUX enable
  - RW
  - 1=UART1 and UART2 share the UART1 pins/connector. [DS p.213](#sources)
* - 13
  - VUART timeout control
  - RW
  - See VUART20/VUART24. [DS p.213](#sources)
* - 12
  - UART div13 reference-clock enable
  - RW
  - 0: $\text{baud} = \dfrac{24\,\text{MHz}}{16 \cdot \text{div}}$; 1: $\text{baud} = \dfrac{24\,\text{MHz}/13}{16 \cdot \text{div}}$. [DS p.213](#sources)
* - 11
  - Invert YCLK
  - RW
  - 0=YCLK from MCLK, 1=from inverted MCLK. [DS p.213](#sources)
* - 9
  - Video port-A delay bit[0]
  - RW
  - LSB of the SCU08[10:8] delay field. [DS p.213](#sources)
* - 8
  - Disable PCI-slave→AHB bridge
  - RW
  - 0=enable bridge, 1=disable. [DS p.213](#sources)
* - 2
  - Disable D1-PLL
  - RW
  - 0=enable, 1=disable. [DS p.213](#sources)
* - 0
  - Disable SMC output buffers
  - RW
  - 0=enable, 1=disable. [DS p.213](#sources)
```

```{admonition} Source discrepancy: SCU2C vs SCU28 in the Raptor headers
:class: warning

`hwreg.h` defines `SCU_FREQ_CNTR_CTRL_RANGE_REG` as base `+0x28`, but
`platform.S` uses that symbol with an inline comment of `0x1e6e202c` and then
tests **bit 12** of the read value to select the UART baud divisor — i.e. it is
functionally reading **SCU2C[12]** (the div13 enable), not SCU28. The label and
the actual intent disagree by one register slot. Treat the datasheet as
authoritative: SCU28 is the frequency-counter comparison range, SCU2C is Misc.
Control (which is where the div13 bit lives). [hwreg.h:89](#sources) [platform.S:166-176](#sources) [DS p.213](#sources)
```

### SCU7C — Silicon Revision ID (offset 0x7C)

Read-only identity register. This is the register the DDR init reads to confirm
it is running on an AST2050/AST1100 before programming the M-PLL. [DS p.220](#sources)

```{list-table} SCU7C fields
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 31:10
  - Reserved
  - RO
  - 0. [DS p.220](#sources)
* - 9:8
  - Chip bonding option
  - RO
  - Product-differentiation bonding status. [DS p.220](#sources)
* - 7:0
  - Silicon revision ID
  - RO
  - 0=A0, 1=A1, 2=A2/A3, … [DS p.220](#sources)
```

```{list-table} SCU7C revision-ID readback values
:header-rows: 1

* - Part / rev
  - SCU7C value
* - AST1100-A0 / AST2050-A0
  - 0x00000200
* - AST1100-A1 / AST2050-A1
  - 0x00000201
* - AST1100-A2 / AST2050-A2
  - 0x00000202
* - AST1100-A3 / AST2050-A3
  - 0x00000202
* - AST2100-A2 / -A3
  - 0x00000302
```

[DS p.220](#sources)

The A3 silicon in the lab reads **`0x00000202`**, which matches the datasheet
(A2 and A3 share the value) and has been independently confirmed on hardware via
both the P2A and JTAG AHB backdoors (SCU7C = 0x202). The DDR init shifts SCU7C
right by 8 and compares the low byte against `0x02` to detect AST2050/AST1100.
[DS p.220](#sources) [platform.S:150-154](#sources)

## Clock tree (PLLs and derived clocks)

The clock tree is rooted at the external **24 MHz crystal** on the CLKIN pin
(R22). Three on-chip PLLs derive the main domains — **H-PLL** (CPU/AHB/APB/UART),
**M-PLL** (memory) and the video PLLs (**V-PLL1/dclk_pll**, plus D2/D1-PLL) —
while the low-rate housekeeping clocks (1 MHz, 12 MHz, 32 KHz, PECI, PWM, tach)
are simple integer divisions of the 24 MHz reference. USB2.0 has its own PHY PLL.
[DS §8.1 p.84, §8.5 p.88](#sources) [RAPTOR-PORTING-GUIDE.md:222-227](#sources)

```{figure} /_static/diagrams/ast2050-clock-tree.svg
:alt: AST2050 clock tree: the 24 MHz CLKIN crystal feeding the H-PLL (CPU/AHB), M-PLL (DDR), V-PLL (video) and the fixed 24 MHz path, through the integer dividers to the CPU/AHB/APB/MAC/UART/RTC clock domains.
:width: 90%

The AST2050 clock tree — 24 MHz CLKIN → PLLs → dividers → clock domains (the M-PLL and H-PLL are SCU20 / SCU24 above).
```

[DS Figure 22 §8.5 p.88](#sources) [DS §8.1 p.84](#sources)

```{list-table} Clock domains and typical/max rates
:header-rows: 1

* - Clock
  - Source
  - Rate (max)
  - Consumers
* - CPUCLK
  - H-PLL
  - 200 MHz
  - ARM926EJ-S core. [DS p.84](#sources)
* - HCLK
  - H-PLL
  - 100 MHz
  - AHB bus / most AHB masters+slaves. [DS p.84](#sources)
* - PCLK
  - H-PLL ÷ (SCU08[25:23])
  - 100 MHz
  - APB peripherals (timer, WDT, UART, I2C, LPC, GPIO, PWM, PECI). [DS p.84](#sources)
* - MCLK
  - M-PLL (or H-PLL)
  - 200 MHz
  - SDRAM controller. [DS p.84](#sources)
* - ECLK
  - M-PLL or H-PLL (SCU08[3:2])
  - 200 MHz
  - Video engine. [DS p.84](#sources)
* - YCLK / GCLK
  - MCLK
  - 200 MHz
  - HAC crypto / 2D engine. [DS p.84](#sources)
* - DCLK
  - V-PLL1
  - 165 MHz
  - CRT display. [DS p.84](#sources)
* - V1CLK
  - V1-PLL or DVI input
  - 165 MHz
  - Video capture #1. [DS p.84](#sources)
* - BCLK
  - external PCI clock
  - 33 MHz
  - PCI slave / bridge. [DS p.84](#sources)
* - LCLK
  - external LPC clock
  - 33 MHz
  - LPC controller. [DS p.84](#sources)
* - USB2CLK
  - USB2.0 PHY
  - 30 MHz
  - USB2.0 controller. [DS p.84](#sources)
* - UARTCLK
  - 24 MHz (opt. ÷13 via SCU2C[12])
  - 24 MHz
  - UART1/UART2 baud generation. [DS p.84, p.213](#sources)
* - CLK12M / CLK1M / CLK32K
  - 24 MHz ÷ integer
  - 12 / 1 / 0.032 MHz
  - RTC, timers, watchdog 1 MHz option. [DS p.84](#sources)
* - PECICLK / PWMCLK / TACHCLK
  - 24 MHz ÷ integer
  - 2 / 24 / 6 MHz
  - PECI, PWM/fan. [DS p.84](#sources)
```

### H-PLL and M-PLL formula (SCU24 / SCU20)

H-PLL and M-PLL share an identical field layout and output equation. The vendor
formula printed in the datasheet is:

$$
F_\text{out} = 24\,\text{MHz} \times (2 - \text{OD}) \times \frac{\text{Numerator} + 2}{\text{Denumerator} + 1}
$$

where **OD** is the output-divider bit, **Numerator** = bits[10:5],
**Denumerator** = bits[3:0]. The **post-divider** field (bits[14:12]) then
divides $F_\text{out}$ further (÷1/2/4/8/16). Worked example: the SCU24 reset value
`0x00004291` decodes to N=20, OD=1, D=1, post=÷2 → $24 \cdot (2-1) \cdot (22/2) / 2 = 132\,\text{MHz}$,
matching the datasheet's stated 133 MHz H-PLL default. [DS §SCU24 p.212,
§SCU20 p.211-212]

This is the same equation the mainline AST2400 clock driver implements
($F = 24\,\text{MHz} \times (2-\text{OD}) \times \frac{N+2}{D+1}$, with N=`(val>>5)&0x3f`, OD=`(val>>4)&1`,
D=`val&0xf`), which corroborates the field decode across G3 and G4.
[codebrowser clk-aspeed.c](#sources) [DS p.212](#sources)

```{list-table} SCU20 (M-PLL) / SCU24 (H-PLL) fields
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 18 (SCU24 only)
  - H-PLL parameter selection
  - RW
  - 0=take H-PLL parameters from trapping resistors; 1=from SCU24[17:0]. [DS p.212](#sources)
* - 17
  - Enable PLL bypass mode
  - RW
  - 1=output clock is the raw 24 MHz reference (shared with USB reference). [DS p.211-212](#sources)
* - 16
  - Turn off PLL
  - RW
  - 1=power down PLL, output forced to 0. M-PLL defaults OFF if SCU70[16] straps low-speed boot. [DS p.211-212](#sources)
* - 14:12
  - Post divider
  - RW
  - `0xx`=÷1, `100`=÷2, `101`=÷4, `110`=÷8, `111`=÷16. [DS p.211-212](#sources)
* - 10:5
  - Numerator (N)
  - RW
  - Feedback multiplier term (N+2). [DS p.211-212](#sources)
* - 4
  - Output divider (OD)
  - RW
  - Contributes `(2-OD)` to the formula. [DS p.211-212](#sources)
* - 3:0
  - Denumerator (D)
  - RW
  - Reference divider term (D+1). [DS p.211-212](#sources)
```

The Raptor DDR init programs the M-PLL twice: first `SCU20 = 0x00004c81`
(commented "200 MHz") right after silicon-ID detection, then `SCU20 = 0x000041f0`
(commented "numerator=0b001111, output divider=1, post divider=÷2") during the
DRAM bring-up, and finally writes the AST2000-backward-compatible shadow
`MCR120 = 0x00004c41`. The H-PLL is *not* reprogrammed by this code — it is left
at its strap-selected value. [platform.S:158-159](#sources) [platform.S:338-340](#sources)
[platform.S:546-548](#sources)

### CPU:AHB and APB derivation

`CPUCLK`, `HCLK` and `PCLK` all come from H-PLL. The CPU:AHB ratio is
strap-selected (SCU70[13:12] on the G3), and `PCLK = H-PLL ÷ SCU08[25:23]`.
Boot-up speed is gated by SCU70[16]: when strapped to low-speed boot, the CPU
runs at 1/16 (via the throttle logic) and MCLK is sourced from the raw 24 MHz
until firmware sets SCU70[16]=1. [DS Figure 23 §8.5 p.88-89](#sources) [DS §SCU70 p.217-218](#sources)

```{admonition} 384 MHz vs 200 MHz — a template artifact
:class: note

The illustrative `ast2050.dtsi` in the repo analysis lists
`clk_hpll clock-frequency = <384000000>` and `clk_apb = HPLL/6`. 384 MHz is the
**AST2400** default H-PLL rate; on the AST2050 the strap options are
100/133/166/200 MHz and CPUCLK maxes at 200 MHz. The 384 MHz figure is a copied
G4 placeholder, not the real G3 value — use the strap-selected rate (typically
200 MHz) when building a real G3 device tree. [RAPTOR_ENGINEERING_AST2050_ANALYSIS.md:1421-1433](#sources)
[DS §SCU24 p.212](#sources) [RAPTOR-PORTING-GUIDE.md:38](#sources)
```

## Hardware straps (SCU70)

`SCU70` is the latched hardware-trapping register: at power-on the SoC samples
strap pins (shared with the NOR-flash address/data bus while `SRST#` is low) and
presents the result here. It selects the boot source, H-PLL frequency, CPU:AHB
ratio, boot speed, MAC interface mode, VGA memory size, and several test/PCI
options. Firmware can also override some straps by writing this RW register.
[DS §SCU70 p.217-218](#sources) [pins ROMA*, DS p.42-43](#sources)

```{admonition} G3 vs G4 strap bit positions differ
:class: warning

The AST2050 places the **H-PLL frequency strap at [11:9]** and the **CPU:AHB
ratio at [13:12]**. The AST2400 uses **[9:8]** and **[11:10]** respectively. A
G4 clock driver will mis-decode a G3 strap word. This is the single most
important porting hazard in this block. [DS §SCU70 p.217-218](#sources)
[RAPTOR-PORTING-GUIDE.md:41-42,229-232](#sources) [codebrowser clk-aspeed.c](#sources)
```

```{list-table} SCU70 hardware-trapping fields
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 31:24
  - Software-defined trapping
  - RW
  - General-purpose strap scratch. [DS p.217](#sources)
* - 23
  - LPC dedicated reset pin
  - RW
  - 0=LPC reset shared with PCI reset pin; 1=LPC reset on pin B10. [DS p.217](#sources)
* - 22
  - Test mode
  - RW
  - 0=normal, 1=test mode (also forces bypass clock). [DS p.217](#sources)
* - 21
  - Reverse PCI AD[31:0] order
  - RW
  - PCB-routing option; swaps AD/CBE pin order. [DS p.217](#sources)
* - 20
  - Disable ARM→M-bus bridge
  - RW
  - 1=ARM reaches memory only via AHB. [DS p.217](#sources)
* - 19
  - Bypass all PLL
  - RW
  - 1=bypass every PLL (test only). [DS p.217](#sources)
* - 18
  - Reserved
  - RW
  - Keep 0. [DS p.217](#sources)
* - 17
  - PCI VGA config prefetch bit
  - RW
  - Value returned for the PCI config prefetch bit. [DS p.217](#sources)
* - 16
  - SOC boot-up full-speed
  - RW
  - 0=boot at 1/16 speed (throttled, M-PLL off, MCLK=24 MHz); 1=full speed. Firmware must set to 1 to leave low-speed mode. [DS p.217-218](#sources)
* - 15
  - PCI class-code select
  - RW
  - 0=video-device class code; 1=VGA-device class code. [DS p.218](#sources)
* - 14
  - Bypass VGA DAC
  - RW
  - Test-only DAC bypass. [DS p.218](#sources)
* - 13:12
  - **CPU:AHB clock ratio**
  - RW
  - 00=1:1, 01=2:1, 10=4:1, 11=3:1. (G4 uses [11:10].) [DS p.218](#sources)
* - 11:9
  - **H-PLL default frequency**
  - RW
  - `010`=200 MHz, `011`=166 MHz, `100`=133 MHz, `101`=100 MHz, `111`=24 MHz (H-PLL bypass); `00x`/`110`=reserved. (G4 uses [9:8].) [DS p.218](#sources)
* - 8:6
  - MAC interface mode
  - RW
  - `011`=MII (MAC#1) only, `100`=RMII (MAC#1) only, `110`=RMII MAC#1+MAC#2, `111`=disable MAC; others reserved. [DS p.218](#sources)
* - 5
  - Enable VGA BIOS ROM
  - RW
  - 0=no VGA BIOS ROM (on-board); 1=enable (add-on card). Also sets GPIOB4–B7 defaults. [DS p.218](#sources)
* - 4
  - Reserved
  - RW
  - Keep 0. [DS p.218](#sources)
* - 3:2
  - VGA memory size
  - RW
  - 00=8 MB, 01=16 MB, 10=32 MB, 11=64 MB, shared from SDRAM. [DS p.218](#sources)
* - 1:0
  - ARM CPU boot code select
  - RW
  - `10`=boot from SPI flash, `11`=disable ARM CPU, `0x`=reserved. [DS p.218](#sources)
```

The DDR init reads SCU70[3:2] (VGA memory-size strap) and folds it into the
SDRAM configuration register `MCR04`, confirming the strap encoding is live on
this silicon. [platform.S:363-377](#sources)

## Reset control and reset domains

Two SCU registers drive resets: **SCU04** issues per-module software resets, and
**SCU3C** enables the external `EXTRST#` pin and latches the *source* of the last
reset (power-on / watchdog / external). The reset topology (datasheet §8.6) is:
a power reset `PWRSTNin` (from the `SRST#` pin) resets literally everything
including the SCU itself; the **AHB/CPU domain reset `HRST_N`** is the logical OR
of `PWRSTNin`, the **watchdog reset** `wdt_rst`, and the **external reset**
`EXTRSTNin` (gated by `SCU3C[3]`); and each module additionally has its own
`*_RST_N` = `PWRSTNin | SCU04[bit]`. [DS §8.6 p.94-96](#sources) [DS §SCU04 p.205-207](#sources)
[DS §SCU3C p.214](#sources)

```{admonition} Verified reset-domain facts (datasheet Figures 38–39)
:class: important

- **`PWRSTNin`** (the `SRST#` power-on reset) asynchronously resets *all* SCU
  registers; **no other reset input can affect the SCU**. Hold `SRST#` low ≥10 ms
  after power is stable. [DS §8.6 p.94](#sources) [pin R20 SRST#, DS p.47](#sources)
- **`HRST_N` = PWRSTNin | wdt_rst | (EXTRSTNin & SCU3C[3])**. So a watchdog
  timeout and an external `EXTRST#` assertion both pull the whole AHB/CPU domain
  into reset, but neither clears the SCU/RTC/power-domain state. [DS Figure 39 p.94](#sources)
- **`EXTRST#` (GPIOB7)** resets all SoC modules *except* the DRAM controller;
  it is enabled by `SCU3C[3]` and is active-low. [DS §SCU3C p.214](#sources) [pin C9, DS p.46](#sources)
- **`WDTRST` (GPIOB6, pin D9)** is the external watchdog-reset *output*, enabled
  by `SCU78[3]` + `WDT0C[3]`; it does not exist on A0 silicon. [DS p.46](#sources) [DS §SCU78 p.219](#sources) [DS §WDT0C p.288](#sources)
- The **RTC and GPIO** live in the `PWRSTNin` power domain (not `HRST_N`), so
  they survive watchdog/EXTRST resets. [DS §8.2 p.85](#sources)
```

### SCU04 — System Reset Control (offset 0x04)

Writing `1` to a bit asserts that module's asynchronous reset; writing `0`
releases it. The reset value `0x000FFE5C` holds most peripherals in reset at
power-on, so firmware releases them as it brings each block up. Several bits are
"reserved, must keep at 1". [DS §SCU04 p.205-207](#sources)

```{list-table} SCU04 fields
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 31:22
  - Reserved
  - —
  - 0. [DS p.205](#sources)
* - 21
  - PCI host reset output enable
  - RW
  - Controls BRST# pin direction; 0=input (default). [DS p.205](#sources)
* - 20
  - Force PCI host reset high
  - RW
  - 1=hold BRST# high while resetting host controller. [DS p.205](#sources)
* - 19
  - Reset PCI host bus controller
  - RW
  - 1=reset (default). [DS p.205](#sources)
* - 18
  - Reset MIC controller
  - RW
  - 1=reset (default). [DS p.205](#sources)
* - 17
  - Reserved (keep 1)
  - RW
  - Must stay 1. [DS p.205](#sources)
* - 16
  - Reset MDMA controller
  - RW
  - 1=reset (default). [DS p.205](#sources)
* - 15
  - Reserved (keep 1)
  - RW
  - Must stay 1. [DS p.205](#sources)
* - 14
  - Reset USB2.0 controller
  - RW
  - 1=reset (default). Clear only after enabling USB2.0 clock + 10 ms wait. [DS p.205](#sources)
* - 13
  - Reserved (keep 1)
  - RW
  - Must stay 1. [DS p.205](#sources)
* - 12
  - Reset MAC#2 controller
  - RW
  - 1=reset (default). [DS p.206](#sources)
* - 11
  - Reset MAC#1 controller
  - RW
  - 1=reset (default). [DS p.206](#sources)
* - 10
  - Reset PECI controller
  - RW
  - 1=reset (default). [DS p.206](#sources)
* - 9
  - Reset PWM controller
  - RW
  - 1=reset (default). [DS p.206](#sources)
* - 8
  - Reset PCI slave + VGA
  - RW
  - 1=reset; 0=no operation (default). [DS p.206](#sources)
* - 7
  - Reserved (keep 0)
  - RW
  - Must stay 0. [DS p.206](#sources)
* - 6
  - Reset video engine
  - RW
  - 1=reset (default). [DS p.206](#sources)
* - 5
  - Reset LPC controller
  - RW
  - 1=reset LPC + embedded BMC controller; 0=default. [DS p.206](#sources)
* - 4
  - Reset HAC engine
  - RW
  - 1=reset (default). [DS p.206](#sources)
* - 3
  - Reserved (keep 1)
  - RW
  - Must stay 1. [DS p.206](#sources)
* - 2
  - Reset I2C/SMBus
  - RW
  - 1=reset all 7 controllers (default). [DS p.206](#sources)
* - 1
  - Reset AHB bridges
  - RW
  - 1=reset AHB↔M-bus, AHB↔APB, AHB↔P-bus bridges; write 0 to resume. [DS p.206](#sources)
* - 0
  - Reset SDRAM controller
  - RW
  - 1=reset (may lose DRAM contents); 0=default. [DS p.207](#sources)
```

### SCU3C — External reset enable + reset-source flags (offset 0x3C)

Enables the `EXTRST#` pin and records which reset last fired. The three flag bits
are cleared by `SRST#` and set by their respective reset sources; software clears
them after reading. Reset value `0x00000001` (power-on-reset flag set).
[DS §SCU3C p.214](#sources)

```{list-table} SCU3C fields
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 31:4
  - Reserved
  - —
  - 0. [DS p.214](#sources)
* - 3
  - Enable external SOC reset (GPIOB7/EXTRST#)
  - RW
  - 1=GPIOB7 acts as active-low EXTRST# (resets SoC except DRAM). Cleared by SRST#; software may set after boot. Keep pin high when enabling. [DS p.214](#sources)
* - 2
  - External reset flag
  - R/WSC
  - Cleared by SRST#; **set when EXTRST# fired**. Software clears after reading. [DS p.214](#sources)
* - 1
  - Watchdog reset flag
  - R/WSC
  - Cleared by SRST#; **set when the internal watchdog reset fired**. Software clears after reading. [DS p.214](#sources)
* - 0
  - Power-on reset flag
  - R/WSC
  - **Set by SRST#** (power-on). Software clears after reading. [DS p.214](#sources)
```

## Watchdog timer (WDT)

The watchdog is a standalone 32-bit down-counter on the APB bus at
**`0x1E785000`** (region `1E78:5000–1E78:5FFF`). On timeout it can emit three
things: a **system reset** (into the `HRST_N` domain), a **CPU interrupt**, and an
**external `WDTRST` pulse** (A1+ silicon only). The counter reloads from `WDT04`
and is kicked by writing the magic `0x4755` to `WDT08`. It is clocked by either
PCLK or the 1 MHz reference (selected by `WDT0C[4]`). [DS §27 p.287-289](#sources)
[hwreg.h:164-169](#sources) [DS §8.2 p.85](#sources)

```{list-table} WDT register map (base 0x1E785000)
:header-rows: 1

* - Offset
  - Register
  - Reset
  - Access
  - Description
* - 0x00
  - WDT00 Counter Status
  - 0x03EF1480
  - RO
  - Current counter value; resets to `0x03EF1480` on `HRST_N`; loaded from WDT04 on restart. Counts down while WDT0C[0]=1. [DS p.287](#sources) [hwreg.h:166](#sources)
* - 0x04
  - WDT04 Counter Reload Value
  - 0x03EF1480
  - RW
  - Value loaded into WDT00 on reset/restart; sets the timeout period. [DS p.288](#sources) [hwreg.h:167](#sources)
* - 0x08
  - WDT08 Counter Restart
  - 0x00000000
  - WO
  - Write `0x4755` (bits[15:0]) to reload WDT00 and (re)start counting — the "kick". [DS p.288](#sources) [hwreg.h:168](#sources)
* - 0x0C
  - WDT0C Control
  - 0x00000000
  - RW
  - Enable, reset-on-timeout, interrupt-on-timeout, external-signal-on-timeout, clock select. [DS p.288](#sources) [hwreg.h:169](#sources)
* - 0x10
  - WDT10 Timeout Status
  - 0x00000000
  - RO
  - Bit0=1 latches that a timeout has ever occurred. [DS p.288](#sources)
* - 0x14
  - WDT14 Clear Timeout Status
  - 0x00000000
  - W1C
  - Write 1 to bit0 to clear WDT10. [DS p.288](#sources)
* - 0x18
  - WDT18 Reset Width
  - 0x000000FF
  - RW
  - Asserting width of wdt_intr / wdt_ext in PCLK cycles (default 256). With 1 MHz clock, max ~1.25 µs. [DS p.288-289](#sources)
```

```{list-table} WDT0C control fields
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 31:5
  - Reserved
  - —
  - 0. [DS p.288](#sources)
* - 4
  - Clock select
  - RW
  - 0=PCLK, 1=1 MHz source. [DS p.288](#sources)
* - 3
  - External signal enable (wdt_ext)
  - RW
  - 1=drive external `WDTRST` output pin D9 high on timeout. [DS p.288](#sources)
* - 2
  - Interrupt enable (wdt_intr)
  - RW
  - 1=raise CPU interrupt on timeout. [DS p.288](#sources)
* - 1
  - Reset system on timeout
  - RW
  - 1=assert system reset on timeout (feeds `HRST_N`). [DS p.288](#sources)
* - 0
  - WDT enable
  - RW
  - 1=counter runs. [DS p.288](#sources)
```

**Programming sequence** (datasheet §27.4): (1) disable the WDT, (2) write the
reload period to `WDT04`, (3) write `0x4755` to `WDT08`, (4) set the clock select
`WDT0C[4]`, (5) enable via `WDT0C[0]`. The default reload `0x03EF1480` is a 1 s
timeout on a 66 MHz reference. The watchdog reset feeds directly into `HRST_N`,
so it resets the CPU/AHB domain but not the SCU/RTC/power domain (see reset
domains above). [DS §27.4 p.289](#sources) [DS Figure 39 §8.6 p.94](#sources)

## AST2000-backward-compatible SCU shadow registers

For AST2000 software compatibility, a few SCU-equivalent registers are shadowed
inside the **memory controller** block (base `0x1E6E0000`). The Raptor DDR init
writes the MPLL shadow at the end of bring-up. These are *not* in the SCU block
but belong to this subsystem's programming model. [DS §17 p.200-201](#sources)
[hwreg.h:70-71](#sources)

```{list-table} MMC-resident SCU-compatible shadow registers (base 0x1E6E0000)
:header-rows: 1

* - Offset
  - Register
  - Reset
  - Access
  - Description
* - 0x100
  - MCR100 AST2000-compat SCU password
  - 0x000000A8
  - RO
  - Fixed `0x000000A8`. [DS p.201](#sources) [hwreg.h:70](#sources)
* - 0x120
  - MCR120 AST2000-compat SCU M-PLL parameter
  - 0x00000000
  - RW
  - Post-divider [15:14], numerator [13:5], denumerator [4:0]. DDR init writes `0x00004c41`. [DS p.201](#sources) [platform.S:546-548](#sources)
* - 0x170
  - MCR170 AST2000-compat SCU hardware-strap value
  - 0x00000000
  - RO
  - Reads all 0. [DS p.201](#sources)
```

## SoC power-on / init sequence (SCU/clock/reset touchpoints)

The Raptor `lowlevel_init` (`platform.S`) is the reference low-level bring-up. The
SCU/clock/reset-relevant steps, in order, are:

1. **Unlock SCU** — write `0x1688A8A8` to `SCU00`. [platform.S:132-134,240-242](#sources)
2. **Claim DRAM init** — set `SCU40[7]` (SOC-firmware-initialises-DRAM). [platform.S:136-139](#sources)
3. **Skip if already done** — read `SCU40[6]`; if the DRAM-init-ready flag is
   already set, jump straight to the lock/return path. [platform.S:141-147](#sources)
4. **Detect silicon** — read `SCU7C`, shift right 8, compare low byte against
   `0x02` to confirm AST2050/AST1100 before touching the PLL. [platform.S:150-154](#sources)
5. **Program M-PLL (first pass)** — `SCU20 = 0x00004c81` (commented "200 MHz").
   [platform.S:156-159](#sources)
6. **Pick UART baud** — read the misc/div13 control (SCU2C[12]) to choose the
   baud divisor, then bring up UART2 for debug output. [platform.S:162-225](#sources)
7. **Verify unlock** — re-write `SCU00 = 0x1688A8A8` and read back, requiring
   `0x01`; abort with "SCU LOCKED" if not. [platform.S:240-247](#sources)
8. **Set boot key** — `SCU40 = 0x5A000080` (Linux-boot key `0x5A` in [31:24] +
   DRAM-init-by-firmware bit[7]). [platform.S:283-285](#sources)
9. **Unlock SDRAM** — write `0xFC600309` to the SDRAM protection key (`MCR00`),
   verify. [platform.S:287-295](#sources)
10. **Program M-PLL (second pass)** — `SCU20 = 0x000041f0` (numerator 0b001111,
    OD=1, post-÷2), then the full DDR2 timing/DLL init. [platform.S:338-340,354-544](#sources)
11. **Read VGA-size strap** — `SCU70[3:2]` folded into `MCR04` SDRAM config.
    [platform.S:363-377](#sources)
12. **Write MPLL shadow** — `MCR120 = 0x00004c41` (AST2000-compat). [platform.S:546-548](#sources)
13. **Signal done** — set `SCU40[6]` (DRAM-init-ready). [platform.S:559-564](#sources)
14. **Re-lock** — write `0` to `SCU00` and to the SDRAM key, then return.
    [platform.S:588-603](#sources)

Note the H-PLL (`SCU24`) is never reprogrammed here: the ARM core runs at its
strap-selected H-PLL rate (SCU70[11:9]); only the memory PLL is set up by this
sequence. The `0x033103F1` value loaded into `r2` at [platform.S:149](#sources) before the
silicon check is dead/unused (the subsequent `set_MPLL` writes literal
`0x00004c81` instead). [platform.S:149-159](#sources)

## Sources

- **AST2050/AST1100 A3 Datasheet V1.05** (in-repo:
  `datasheets/aspeed/AST2050_AST1100_A3_Datasheet_V1.05.pdf`), sections cited as
  `[DS …](#sources)`:
  - §8.1 Clock Information (p.84); §8.2 Clock & Reset Tree Mapping (p.85);
    §8.3 Reset Tree Control Table (p.86); §8.4 Symbol Description (p.87);
    §8.5 Clock Tree Architecture, Figures 22–37 (p.88-93);
    §8.6 Reset Tree Architecture, Figures 38–56 (p.94-96).
  - §9 ARM Address Space Mapping (p.97).
  - §17 SDRAM controller MCR100/MCR120/MCR170 shadow regs (p.200-201).
  - §18 System Control Unit (SCU) register descriptions SCU00–SCU7C (p.204-220).
  - §27 Watchdog Timer WDT00–WDT18 + operation (p.287-289).
  - Pin descriptions: SRST# (R20), EXTRST# (C9/GPIOB7), WDTRST (D9/GPIOB6),
    CLKIN (R22) (p.42-47).
- **In-repo Raptor Engineering AST2050 port** (`asus-kgpe-d16-firmware/`):
  - `hwreg.h` — SCU/WDT/MMC register offset definitions.
  - `ast2050.h` — board config (24 MHz UART clock, DDR sizing).
  - `platform.S` — `lowlevel_init` DDR/PLL/SCU bring-up assembly (line refs
    cited inline).
  - `RAPTOR_ENGINEERING_AST2050_ANALYSIS.md` — SCU/clock/WDT driver analysis,
    example dtsi.
  - `RAPTOR-PORTING-GUIDE.md` — G3-vs-G4 strap bit differences, clock tree,
    reset/WDT porting notes.
- **Web cross-references:**
  - Mainline Linux `drivers/clk/clk-aspeed.c` (AST2400/G4) — H-PLL formula
    $F = 24\,\text{MHz} \times (2-\text{OD}) \times \frac{N+2}{D+1}$, strap decode:
    <https://codebrowser.dev/linux/linux/drivers/clk/clk-aspeed.c.html>
  - Aspeed SCU device-tree binding (context):
    <https://www.kernel.org/doc/Documentation/devicetree/bindings/mfd/aspeed-scu.txt>
