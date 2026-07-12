# AST2050 DDR2 / SDRAM controller & init

This page is a register-by-register reference for the ASPEED **AST2050 (G3)**
SDRAM / DDR2 memory controller, plus the complete cold-boot DDR2 bring-up
procedure. It is written for people re-implementing the boot code (U-Boot,
OpenBMC, a QEMU model) and cross-checks every value against the ASPEED
AST2050/AST1100 A3 datasheet, the hardware-verified Raptor Engineering U-Boot
`platform.S`, and the JEDEC JESD79-2 DDR2 standard.

The controller is register-compatible with the AST2400/AST2100 SDRAM controller;
the AST2050 (SoC generation 0, part of the AST2000/AST2050/AST2100 "G3" family)
is **not** in mainline Linux, and mainline reuses the AST2400 (G4) SDRAM code.
Where a value is board-specific to the ASUS KGPE-D16 (the reverse-engineering
oracle), it is marked as such. See [§9](#9-ast2050-specific-vs-shared-with-ast2400).

- **Controller base address:** `0x1E6E0000` (registers are named `MCRnn` by
  their offset, e.g. `MCR04` = `0x1E6E0004`) [DS §17.3 p.184] [hwreg.h:37-71].
- **Register unlock key (MCR00):** write `0xFC600309` to `0x1E6E0000` to unlock
  `MCR04`..`MCR7C`; write anything else (e.g. `0x00000000`) to re-lock.
  Reads back `0x00000001` when unlocked, `0x00000000` when locked
  [DS §17.3 p.184 MCR00] [platform.S:287-289].
- **A companion SCU unlock** (`0x1E6E2000` = `0x1688A8A8`) is required because
  init also programs the M-PLL and scratch registers [DS §18 p.205] [platform.S:132-134].

---

## 1. Overview

```{list-table} AST2050 SDRAM controller — headline parameters
:header-rows: 1
:widths: 30 30 40

* - Parameter
  - Value
  - Source
* - CPU / memory master
  - ARM926EJ-S (ARMv5TEJ), ~200 MHz
  - [DDR2-INIT-REVERSE-ENGINEERING.md §2.1]
* - External DRAM type
  - DDR2 SDRAM, 1.8 V SSTL_18
  - [DS §17.3 p.196-197 MCR60] (decoded below)
* - External DDR2 data bus
  - **16-bit** (DQ15:0), single rank
  - [DS §17.3 p.185 MCR04 bit9:8] [DS §17.5 p.202]
* - Internal data bus
  - 64-bit (all internal IPs 8-byte aligned)
  - [DS §17.5 p.202]
* - Memory clock (MCLK)
  - ~200 MHz from M-PLL → DDR2-400 (400 MT/s)
  - [DS §18.2 p.212 SCU20] [platform.S:338-340]
* - Total DRAM (KGPE-D16, HW-verified)
  - 64 MiB (`MCR04[3:2]=01`)
  - [DS §17.3 p.185 MCR04 bit3:2] [platform.S:373-375]
* - Max addressable space
  - 256 MB (28-bit internal address)
  - [DS §17.4.1 p.201]
* - Refresh clock reference
  - 12 MHz source; refresh freq = 12 MHz / MCR0C[15:8]
  - [DS §17.3 p.186 MCR0C]
* - ECC
  - Supported by family; **disabled** on this board
  - [DS §17.3 p.185 MCR04 bit3:2 note]
```

> **Datasheet correction to prior RE notes.** The reverse-engineering write-up
> described a "32-bit DDR2 bus". The A3 datasheet is explicit: `MCR04[9:8]` only
> defines `01 = 16-bit data bus (DQ15..DQ0)`, "others: Reserved", and §17.5 says
> the *internal* bus is always 64 bits [DS §17.3 p.185] [DS §17.5 p.202]. The
> external DDR2 interface on AST2050/AST1100 is 16 bits wide; `MCR60[25]` and
> `MCR60[24]` enable both byte lanes DQ[15:8] and DQ[7:0] [DS §17.3 p.196].

### 1.1 Fixed-priority DRAM requestors (REQ0–REQ22)

The arbiter serves up to 23 request sources at fixed priority (REQ0 highest).
Several MCR registers (`MCR08`, `MCR38`, `MCR3C`, `MCR40`–`MCR48`) are indexed by
this REQ number, so the table is needed to read them [DS §17.2 p.184].

```{list-table} Fixed-priority DRAM request sources
:header-rows: 1
:widths: 12 14 74

* - Priority
  - Request
  - Source
* - 1
  - REQ0
  - VGA hardware cursor read
* - 2
  - REQ1
  - VGA text-mode CG font read
* - 3
  - REQ2
  - VGA text-mode ASCII code read
* - 4
  - REQ3
  - VGA CRT controller read
* - 5
  - REQ4
  - Video high-priority write
* - 6
  - REQ5
  - USB2.0 DMA read/write
* - 7
  - REQ6
  - CPU data read/write
* - 8
  - REQ7
  - CPU instruction read
* - 9
  - REQ8
  - PCI bus write
* - 10
  - REQ9
  - PCI bus read
* - 11
  - REQ10
  - AHB bus read/write
* - 12
  - REQ11
  - MAC1 DMA read/write
* - 13
  - REQ12
  - MAC2 DMA read/write
* - 14–15
  - REQ13–14
  - Reserved
* - 16
  - REQ15
  - Encryption engine read/write
* - 17
  - REQ16
  - 2D command queue read
* - 18
  - REQ17
  - Video flag read/write
* - 19
  - REQ18
  - Video low-priority write
* - 20
  - REQ19
  - MDMA read/write
* - 21
  - REQ20
  - 2D engine data read/write
* - 22
  - REQ21
  - I2C DMA buffer-mode read/write
* - 23
  - REQ22
  - Memory Integrity Check engine read
```

---

## 2. Complete MCR register map

Every offset from the SDRAM controller base `0x1E6E0000`. "Init" is the
datasheet power-on reset value; "X" means undefined at reset. Offsets not listed
in the A3 datasheet register table are flagged in the Notes column
[DS §17.3 p.184-201].

```{list-table} SDRAM controller register map (base 0x1E6E0000)
:header-rows: 1
:widths: 10 16 14 10 50

* - Offset
  - Register
  - Init
  - Access
  - Description / Notes
* - `0x00`
  - MCR00
  - `0`
  - RW
  - Protection Key (unlock = `0xFC600309`; read `1`=unlocked, `0`=locked)
* - `0x04`
  - MCR04
  - `0`
  - RW
  - Configuration (bank mode, capacity, bus width, column bits, burst, VGA aperture); bit6 is read-only status
* - `0x08`
  - MCR08
  - `0`
  - RW
  - Graphics (VGA) memory request protection — per-REQ re-map into graphics aperture
* - `0x0C`
  - MCR0C
  - `0`
  - RW
  - Refresh Timing (period, cycles/period, force-precharge, low-priority refresh enable)
* - `0x10`
  - MCR10
  - `0`
  - RW
  - Normal-Speed AC Timing #1 (tRP, tRRD, tRCD, tAPD, tRTP, tWTP, tRTW, tWTR)
* - `0x14`
  - MCR14
  - `0`
  - RW
  - Low-Speed AC Timing #1 (same field layout as MCR10)
* - `0x18`
  - MCR18
  - `0`
  - RW
  - Normal-Speed AC Timing #2 (tXSNR, write latency, tRAS, tMRD, tRFC)
* - `0x1C`
  - MCR1C
  - `0`
  - RW
  - Low-Speed AC Timing #2 (same field layout as MCR18)
* - `0x20`
  - MCR20
  - `0`
  - RW
  - Normal-Speed Delay Control (DQS window size/mode, read-latch edge, CK phase, manual delays)
* - `0x24`
  - MCR24
  - `0`
  - RW
  - Low-Speed Delay Control (same field layout as MCR20)
* - `0x28`
  - MCR28
  - `0`
  - RW
  - Mode Setting Control ([2:1]=MRS/EMRS1/EMRS2/EMRS3 select, [0]=fire)
* - `0x2C`
  - MCR2C
  - `X`
  - RW
  - MRS/EMRS2 Mode Setting ([12:0]=MRS value, [28:16]=EMRS2 value)
* - `0x30`
  - MCR30
  - `X`
  - RW
  - EMRS1/EMRS3 Mode Setting ([12:0]=EMRS1 value, [28:16]=EMRS3 value)
* - `0x34`
  - MCR34
  - `0`
  - RW
  - Power Control (CKE, ODT enable/auto, self-refresh, auto power-down); bits [31:24] are read-only debug status
* - `0x38`
  - MCR38
  - `0`
  - RW
  - Page Miss Latency Mask ([31:3]=per-REQ mask, [2:0]=threshold)
* - `0x3C`
  - MCR3C
  - `0`
  - RW
  - Priority Group Setting (per-REQ equal/greater priority pairs)
* - `0x40`
  - MCR40
  - `0`
  - RW
  - Maximum Grant Length #1 (REQ0–REQ7, 4 bits each)
* - `0x44`
  - MCR44
  - `0`
  - RW
  - Maximum Grant Length #2 (REQ8–REQ15)
* - `0x48`
  - MCR48
  - `0`
  - RW
  - Maximum Grant Length #3 (REQ16–REQ22)
* - `0x4C`
  - —
  - —
  - —
  - **Not documented in A3 datasheet.** Written `0` by init [platform.S:427-429]
* - `0x50`
  - MCR50
  - —
  - —
  - **Not in A3 datasheet register table.** Named "ECC Control/Status" in Raptor `hwreg.h`; written `0`
* - `0x54`
  - MCR54
  - —
  - —
  - Not in A3 datasheet. Named "ECC Segment Enable" in `hwreg.h`; written `0`
* - `0x58`
  - MCR58
  - —
  - —
  - Not in A3 datasheet. Named "ECC Scrub Request Mask" in `hwreg.h`; written `0`
* - `0x5C`
  - MCR5C
  - —
  - —
  - Not in A3 datasheet. Named "ECC First Error Address" in `hwreg.h`; written `0`
* - `0x60`
  - MCR60
  - `0`
  - RW
  - IO Buffer Mode (byte-lane enables, SSTL/LVTTL select, per-group drive strength & ODT resistance)
* - `0x64`
  - MCR64
  - `0`
  - RW
  - DLL Control #1 (DLL1/DLL3 reset/power-down/ref-clock, output-phase SADJ)
* - `0x68`
  - MCR68
  - `0`
  - RW
  - DLL Control #2 (DLL1 input-phase SADJ for DQS0/DQS1)
* - `0x6C`
  - MCR6C
  - `0`
  - RW
  - DLL Control #3 (DLL1/DLL3 master-adjust MADJ)
* - `0x70`
  - MCR70
  - `0`
  - RW
  - Testing Control/Status (built-in memory BIST); [31:16],[7:6] read-only
* - `0x74`
  - MCR74
  - `0`
  - RW
  - Testing Start Address & Length (8 MB max window)
* - `0x78`
  - MCR78
  - `0`
  - R
  - Testing Fail DQ Bit (bit n = DQn failed)
* - `0x7C`
  - MCR7C
  - `0`
  - RW
  - Test Initial Value (seed for BIST pattern generator)
* - `0x100`
  - MCR100
  - `0x000000A8`
  - R
  - AST2000 backward-compatible SCU password (mirror)
* - `0x120`
  - MCR120
  - `0`
  - RW
  - AST2000 backward-compatible SCU M-PLL parameter mirror ([15:14]=post-div, [13:5]=numerator, [4:0]=denumerator)
* - `0x170`
  - MCR170
  - `0`
  - R
  - AST2000 backward-compatible SCU hardware-strapping value mirror (reads all `0`)
```

### 2.1 SCU registers touched by DDR2 init

DDR2 bring-up also programs a handful of System Control Unit registers (base
`0x1E6E2000`) [DS §18.2 p.205-220] [hwreg.h:77-94].

```{list-table} SCU registers used during DDR2 init
:header-rows: 1
:widths: 14 16 20 50

* - Address
  - Register
  - Reset
  - Purpose
* - `0x1E6E2000`
  - SCU00 Protection Key
  - `0`
  - Unlock key `0x1688A8A8`; reads `1` when unlocked
* - `0x1E6E2020`
  - SCU20 M-PLL Parameter
  - `0x00004291`
  - Memory clock PLL (num/den/output-div/post-div); default 133 MHz
* - `0x1E6E2040`
  - SCU40 SOC Scratch
  - `0`
  - Inter-stage flags: [6]=DRAM init done, [7]=init in progress, [31:24]=`0x5A` Linux-boot key
* - `0x1E6E2070`
  - SCU70 HW Strapping
  - strap
  - [3:2] = VGA aperture size strap → copied into `MCR04[5:4]`
* - `0x1E6E207C`
  - SCU7C Silicon Revision ID
  - `0x00000202`
  - AST2050-A3 = `0x00000202` ([7:0]=2 → A2/A3, [9:8]=2 bonding)
```

---

## 3. MCR04 — Configuration register (geometry)

`MCR04` encodes the DRAM geometry and **must exactly match the populated SDRAM
device**, or the controller malfunctions [DS §17.3 p.185].

```{list-table} MCR04 Configuration Register — bitfields
:header-rows: 1
:widths: 10 8 82

* - Bits
  - Access
  - Field / encoding
* - `[31:12]`
  - —
  - Reserved (0)
* - `[11]`
  - RW
  - Bank mode: `0` = 4-bank addressing, `1` = 8-bank addressing (must match device)
* - `[10]`
  - RW
  - Enable SDRAM auto pre-charge command (`1` = enable)
* - `[9:8]`
  - RW
  - SDRAM data bus width: `01` = 16-bit (DQ15:0); others reserved
* - `[7]`
  - RW
  - DRAM burst length: `0` = BL2 (1 clock/transaction), `1` = BL4 (2 clocks)
* - `[6]`
  - R
  - SDRAM bus-width status: `0`=32-bit, `1`=16-bit (decoded from [9:8]; AST2000 back-compat)
* - `[5:4]`
  - RW
  - Graphics (VGA) aperture: `00`=8 MB, `01`=16 MB, `10`=32 MB, `11`=64 MB (set from SCU70[3:2])
* - `[3:2]`
  - RW
  - Total data-memory capacity: `00`=≤32 MB, `01`=64 MB, `10`=128 MB, `11`=256 MB (excludes ECC)
* - `[1:0]`
  - RW
  - Column-address bits: `00`=9, `01`=10, `10`=11, `11`=reserved (JEDEC column count)
```

### 3.1 The two build-time values decoded

`platform.S` selects one of two constants by compile flag, then ORs in the VGA
aperture bits read from `SCU70[3:2]` [platform.S:363-377]:

```{list-table} MCR04 constants — datasheet-accurate decode
:header-rows: 1
:widths: 20 16 16 16 16 16

* - Value
  - bank [11]
  - capacity [3:2]
  - data bus [9:8]
  - column [1:0]
  - burst [7]
* - `0x00000585` ("512M" flag)
  - `0` → **4-bank**
  - `01` → **64 MiB**
  - `01` → 16-bit
  - `01` → 10 bits
  - `1` → BL4
* - `0x00000D89` ("1G" flag)
  - `1` → **8-bank**
  - `10` → 128 MiB
  - `01` → 16-bit
  - `01` → 10 bits
  - `1` → BL4
```

Both values additionally have `[10]=1` (auto-precharge enabled) and `[5:4]=00`
before the SCU70 OR. On the ASUS KGPE-D16 the DRAM is **hardware-verified at
64 MiB**, so the operative constant is `0x00000585`: a **4-bank, 64 MiB**,
16-bit-bus, 10-column DDR2 device with BL4 [DS §17.3 p.185] [platform.S:373-375].
The `0x00000D89` alternative programs a 128 MiB, 8-bank geometry.

> **Naming caveat / open item.** `platform.S` gates these with
> `#ifdef CONFIG_1G_DDRII` / `#ifdef CONFIG_512M_DDRII` [platform.S:370-375],
> but the ASUS board config header defines `CONFIG_DDRII1G_200` and sets
> `PHYS_SDRAM_1_SIZE = 0x04000000` (64 MiB) [ast2050.h:49,107]. The two macro
> spellings do not match, so which constant a given tree compiles depends on how
> `CONFIG_*_DDRII` gets defined in the board Makefile — not captured here. The
> 64 MiB decode of `0x585` is what matches the measured hardware.

### 3.2 VGA aperture strap and address translation

`SCU70[3:2]` (two board strap resistors) is masked, shifted left by 2, and ORed
into `MCR04[5:4]` so the VGA aperture size in `MCR04` always tracks the strap
[platform.S:363-377] [DS §17.3 p.185 MCR04]. The graphics segment sits at the top
of DRAM [DS §17.4.2 p.202]:

- `MCR04[5:4]=0`, 8 MB → base `0xF80_0000`
- `MCR04[5:4]=1`, 16 MB → base `0xF00_0000`
- `MCR04[5:4]=2`, 32 MB → base `0xE00_0000`
- `MCR04[5:4]=3`, 64 MB → base `0xC00_0000`

Internal 28-bit addresses split into Row / Bank / Column per `MCR04[1:0]` (CA)
and the bank/bus-width mode; e.g. for a 4/8-bank device with 16-bit bus and
CA=10, `A[27:13]`=row, `A[12:11]`=bank, `A[10:0]`=column [DS §17.4.1 p.201-202,
Figure 66].

---

## 4. AC timing, refresh, arbitration and protection registers

### 4.1 MCR08 — Graphics memory protection

`MCR08[n]=1` re-maps requestor REQn into the graphics aperture (top of memory,
`MCR04[5:4]`); `0` leaves it unchanged. It stops the host CPU from clobbering VGA
memory [DS §17.3 p.185-186].

The init value `0x0011030F` sets bits `{0,1,2,3, 8,9, 16, 20}` [platform.S:379-381],
i.e. it protects **REQ0–REQ3** (the four VGA read streams), **REQ8/REQ9** (PCI
write/read), **REQ16** (2D command-queue read) and **REQ20** (2D engine data) —
exactly the graphics/PCI/2D masters, cross-referenced against the REQ table in
[§1.1](#11-fixed-priority-dram-requestors-req0req22).

### 4.2 MCR0C — Refresh timing

```{list-table} MCR0C Refresh Timing Register — bitfields
:header-rows: 1
:widths: 12 10 78

* - Bits
  - Access
  - Field
* - `[31:16]`
  - —
  - Reserved (0)
* - `[15:8]`
  - RW
  - High-priority refresh-cycle period. Refresh frequency = 12 MHz / period
* - `[7:6]`
  - —
  - Reserved (0)
* - `[5]`
  - RW
  - Enable low-priority refresh cycle (opportunistic, uses spare bandwidth)
* - `[4]`
  - RW
  - Force all banks pre-charged before refresh (insurance; normally 0)
* - `[3:0]`
  - RW
  - Refresh cycles per refresh period: `0000`=disabled, `0001`=1, … `1xxx`=8
```

Two values are used [platform.S:510-512,538-540]:

- **Initial `0x00005A08`** — period `0x5A`=90 → 12 MHz/90 = **133 kHz ≈ 7.5 µs**
  refresh interval (within the DDR2 7.8 µs limit), and `[3:0]=8` → **8 refresh
  cycles per period** (a burst of refreshes during init, satisfying the JEDEC
  "≥2 AUTO REFRESH" requirement), low-priority refresh off.
- **Final `0x00005A21`** — same 7.5 µs period, `[3:0]=1` (one refresh/period for
  steady state), `[5]=1` (low-priority refresh enabled).

> Corrects the earlier RE note that read `[15:0]` as a single ~23048-count
> period; the datasheet splits it into a 12 MHz-referenced period `[15:8]` and a
> cycles-per-period field `[3:0]` [DS §17.3 p.186].

### 4.3 MCR10/MCR14 — AC timing #1

Same layout for normal-speed (`MCR10`) and low-speed (`MCR14`). The encoding is
an offset code: read each field's base from the table and add the field value
[DS §17.3 p.187-188].

```{list-table} MCR10/MCR14 AC Timing #1 — fields and Raptor value 0x22201725
:header-rows: 1
:widths: 12 34 18 18 18

* - Bits
  - Parameter
  - Encoding base
  - Field (hex)
  - Decoded
* - `[31:28]`
  - t-RP (row precharge)
  - `0000`=2T
  - `2`
  - 4T
* - `[27:24]`
  - t-RRD (active→active)
  - `0000`=1T
  - `2`
  - 3T
* - `[23:20]`
  - t-RCD (active→read/write)
  - `0000`=2T
  - `2`
  - 4T
* - `[19:16]`
  - t-APD (ACT/PRE→R/W, diff bank)
  - `0000`=1T
  - `0`
  - 1T
* - `[15:12]`
  - t-RTP (read→precharge)
  - `0000`=1T
  - `1`
  - 2T
* - `[11:8]`
  - t-WTP (write→precharge)
  - `0000`=1T
  - `7`
  - 8T
* - `[7:4]`
  - t-RTW (read→write)
  - `0000`=2T
  - `2`
  - 4T
* - `[3:0]`
  - t-WTR (write→read)
  - `0000`=2T
  - `5`
  - 7T
```

### 4.4 MCR18/MCR1C — AC timing #2

```{list-table} MCR18/MCR1C AC Timing #2 — fields and Raptor value 0x1E29011A
:header-rows: 1
:widths: 12 40 16 16 16

* - Bits
  - Parameter
  - Encoding base
  - Field
  - Decoded
* - `[31:30]`
  - Reserved (0)
  - —
  - `0`
  - —
* - `[29:24]`
  - t-XSNR (exit self-refresh → non-read)
  - `000010`=3T
  - `0x1E`
  - 31T
* - `[23:21]`
  - Write latency (DDR2: WL = CL − 1)
  - `000`=1T
  - `001`
  - 2T
* - `[20:16]`
  - t-RAS (active → min precharge)
  - `00000`=1T
  - `0x09`
  - 10T
* - `[15:12]`
  - Reserved (0)
  - —
  - `0`
  - —
* - `[11:8]`
  - tMRD (mode-set interval)
  - `0000`=1T
  - `1`
  - 2T
* - `[7:6]`
  - Reserved (0)
  - —
  - `0`
  - —
* - `[5:0]`
  - t-RFC (refresh → active)
  - `000000`=2T
  - `0x1A`
  - 28T
```

**Timing sanity at DDR2-400 (5 ns/T):** tRP=20 ns, tRCD=20 ns, tRAS=50 ns,
tRFC=140 ns (covers a 1 Gbit DDR2 device's 127.5 ns), and **write latency = 2T =
CL(3) − 1** — internally consistent with the `MCR2C` CAS-latency-3 setting in
[§6](#6-ddr2-mode-register-mrsemrs-programming). These numbers all sit inside
the JEDEC DDR2-400 envelope [DS §17.3 p.187-189].

### 4.5 MCR20/MCR24 — Delay control

```{list-table} MCR20/MCR24 Delay Control — fields and Raptor value 0x00C82222
:header-rows: 1
:widths: 12 10 60 18

* - Bits
  - Access
  - Field
  - Decoded
* - `[31:24]`
  - —
  - Reserved (0)
  - 0
* - `[23]`
  - RW
  - DQS window size: `0`=small (1T/2T), `1`=big (2T/3T)
  - big
* - `[22:21]`
  - RW
  - DQS window mode: `00`=normal, `01`=extend 0.5T, `10`=delay 0.5T, `11`=invalid
  - delay 0.5T
* - `[20:18]`
  - RW
  - Window-enable delay read-cmd→DQS: `000`=1T … `111`=8T
  - 3T
* - `[17]`
  - RW
  - Read-data latch clock/edge selection
  - 0 (DQS+ / MCLK+)
* - `[16]`
  - RW
  - CK/CKN output phase: `0`=normal, `1`=inverted
  - normal
* - `[15:12]`
  - RW
  - CK/CKN output delay (only when DLL disabled): ~0.3 ns + N·0.25 ns
  - N=2 (n/a, DLL on)
* - `[11:8]`
  - RW
  - DQS read-window delay: ~0.3 ns + N·0.25 ns
  - N=2 (~0.8 ns)
* - `[7:4]`
  - RW
  - DQS feedback delay (only when DLL disabled)
  - N=2 (n/a, DLL on)
* - `[3:0]`
  - RW
  - DQS output delay (only when DLL disabled)
  - N=2 (n/a, DLL on)
```

Raptor programs `MCR20`, `MCR24` (and `MCR10=MCR14`, `MCR18=MCR1C`) to identical
values, so the low-speed clock path is never actually used on this board
[platform.S:383-405] — see [§9](#9-ast2050-specific-vs-shared-with-ast2400).

### 4.6 MCR38 / MCR3C / MCR40–MCR48 — arbitration

- **MCR38 Page Miss Latency Mask `0xFFFFFF82`** [platform.S:407-409]:
  `[2:0]`=2 (page-miss threshold); `[31:3]` per-REQ mask where bit(n+3) masks
  REQn once its page-miss counter exceeds the threshold. Bits for REQ0–REQ3
  (the VGA/CRT streams) are **0 = never masked**, all others = masked — matching
  the datasheet's "keep CRT refresh high-priority" guidance [DS §17.3 p.195].
- **MCR3C Priority Group `0x00000000`** [platform.S:411-413]: every
  `REQ(n)>REQ(n+1)` bit = 0 → strict fixed priority per [§1.1](#11-fixed-priority-dram-requestors-req0req22)
  [DS §17.3 p.195].
- **MCR40/MCR44/MCR48 Max Grant Length = `0`** [platform.S:415-425]: 4 bits per
  REQ (REQ0–REQ22). Field code → length: `0/1`=2, `2/3`=4, … `14/15`=16 grants.
  All zero = 2-grant cap everywhere / no special bandwidth reservation
  [DS §17.3 p.195-196]. (`0x4C` is written 0 but is undocumented; see the map.)

### 4.7 MCR60 — IO buffer mode

`MCR60 = 0x032AA02A` [platform.S:447-449] configures the DDR2 pad electricals
[DS §17.3 p.196-197]:

```{list-table} MCR60 IO Buffer Mode — decode of 0x032AA02A
:header-rows: 1
:widths: 12 58 30

* - Bits
  - Field
  - Value
* - `[25]`
  - Enable IO pins DQ[15:8], DM1, DQS1/DQS1n
  - 1 = enabled
* - `[24]`
  - Enable IO pins DQ[7:0], DM0, DQS0/DQS0n
  - 1 = enabled
* - `[23]`
  - DDR IO LVCMOS select
  - 0 = SSTL2 / SSTL18
* - `[22]`
  - DDR IO DS select
  - 0 = SSTL18 (1.8 V DDR2)
* - `[21:20]`
  - Drive strength — pin ODT (S1,S0)
  - `10`
* - `[19:18]`
  - Drive strength — CS/RAS/CAS/WE/CKE/MA/BA
  - `10`
* - `[17:16]`
  - Drive strength — CK/CKN
  - `10`
* - `[15:14]`
  - Drive strength — DQS/DQSn
  - `10`
* - `[13:12]`
  - Drive strength — DQ/DM
  - `10`
* - `[11:10]`
  - ODT resistance — pin ODT (A6,A2)
  - `00` = disabled
* - `[9:8]`
  - ODT — CS/RAS/CAS/WE/CKE/MA/BA
  - `00` = disabled
* - `[7:6]`
  - ODT — CK/CKN
  - `00` = disabled
* - `[5:4]`
  - ODT — DQS/DQSn
  - `10` = 150 Ω
* - `[3:2]`
  - ODT — DM
  - `10` = 150 Ω
* - `[1:0]`
  - ODT — DQ
  - `10` = 150 Ω
```

So both byte lanes are enabled (16-bit interface, consistent with `MCR04[9:8]`),
the pads run 1.8 V SSTL_18 (DDR2), and **150 Ω on-die termination** is applied to
the data group (DQ/DM/DQS) while control and clock pins have ODT off. The
controller-side ODT here pairs with the DRAM-side 150 Ω ODT programmed via EMRS1
in [§6](#6-ddr2-mode-register-mrsemrs-programming).

---

## 5. DLL training

The controller has two DLLs: **DLL1** aligns the input DQS strobes (read data
capture, DQS0/DQS1), and **DLL3** aligns the CK/CKn and DQS output phase. Getting
their reset/power sequencing and phase (SADJ) settings right is what makes reads
sample in the data valid window [DS §17.3 p.197-199].

### 5.1 MCR64 — DLL Control #1

```{list-table} MCR64 DLL Control #1 — bitfields
:header-rows: 1
:widths: 12 10 78

* - Bits
  - Access
  - Field
* - `[31:25]`
  - —
  - Reserved (0)
* - `[24]`
  - RW
  - DLL3 reference clock: `0`=MCLK, `1`=MCLK/2 (for CK/CKn)
* - `[23]`
  - RW
  - Reserved
* - `[22]`
  - RW
  - DLL1 reference clock: `0`=MCLK, `1`=MCLK/2 (for DQS1/DQS0)
* - `[21]`
  - RW
  - DLL3 reset control (CK/CKn & DQS output phase): `0`=Reset, `1`=Normal
* - `[20]`
  - RW
  - Reserved, must be 0
* - `[19]`
  - RW
  - DLL1 reset control (DQS1/DQS0 input phase): `0`=Reset, `1`=Normal
* - `[18]`
  - RW
  - DLL3 power-down (CK/CKn & DQS output): `0`=power-down, `1`=Normal
* - `[17]`
  - RW
  - Reserved, must be 0
* - `[16]`
  - RW
  - DLL1 power-down (DQS1/DQS0 input): `0`=power-down, `1`=Normal
* - `[15:8]`
  - RW
  - DLL3 output-phase SADJ for CK/CKn output
* - `[7:0]`
  - RW
  - DLL3 output-phase SADJ for DQS output
```

Two writes happen, and the difference between them is the crux of DLL training:

```{list-table} The two MCR64 writes
:header-rows: 1
:widths: 22 20 20 20 18

* - Write
  - DLL1 [16]/[19]
  - DLL3 [18]/[21]
  - SADJ [15:8]/[7:0]
  - Meaning
* - **Early `0x00050000`** [platform.S:358-360]
  - pwr=1 / reset=0
  - pwr=1 / reset=0
  - 0 / 0
  - DLLs powered up but **held in reset**
* - **Final `0x002D3000`** [platform.S:451-453]
  - pwr=1 / **normal=1**
  - pwr=1 / **normal=1**
  - `0x30` / `0x00`
  - DLLs **released from reset**, CK/CKn output phase SADJ = 0x30 (=48)
```

Decoding `0x002D3000`: `[7:0]=0x00` (DQS-output SADJ), `[15:8]=0x30` (CK/CKn
output SADJ = 48), and the control bits `[21]=1, [19]=1, [18]=1, [16]=1` — i.e.
both DLL1 and DLL3 powered **and released into normal operation**, ref clock =
MCLK. The early `0x00050000` set only the two power bits (`[18]`,`[16]`) and left
both reset bits at 0, so the DLLs were parked in reset during controller setup
and CKE assertion, then released once clocks and mode registers are stable.

> **Why the final DLL block matters.** Omitting the final `MCR64 = 0x002D3000`
> write leaves the DLLs in reset (or at the wrong output phase), so DQS/CK are
> not phase-aligned to the data window. On real hardware this produced marginal
> captures measured at **~0.29 % data errors** [DDR2-INIT-REVERSE-ENGINEERING.md].
> The datasheet fields make the mechanism concrete: bits `[21]`/`[19]` move the
> DLLs from *Reset* to *Normal operation* and `[15:8]` sets the CK/CKn output
> phase [DS §17.3 p.197-198]. (This supersedes the earlier RE guess that read
> `0x2D` as a "delay-tap count" — `0x2D` actually lands across the reset/
> power-down control bits `[21:16]`, and the operative output-phase value is the
> `0x30` in `[15:8]`.)

### 5.2 MCR68 — DLL Control #2

`MCR68 = 0x02020202` [platform.S:455-457]. Only `[15:0]` are defined: `[7:0]` =
DLL1 input-phase SADJ for DQS0, `[15:8]` = DLL1 input-phase SADJ for DQS1 — both
`0x02`. `[31:16]` are reserved; the upper `0x0202` written to them is harmless
[DS §17.3 p.198].

### 5.3 MCR6C — DLL Control #3 (master adjust)

`MCR6C = 0x00909090` [platform.S:354-356]. `[7:0]` = DLL1 master-adjust **MADJ**
= `0x90` (144), `[23:16]` = DLL3 MADJ = `0x90` (144); `[15:8]` and `[31:24]` are
reserved [DS §17.3 p.198]. Per the datasheet DLL note, the minimum MADJ is 40 and
the operating-frequency relation is `MIN_FREQ = 67·120/MADJ`,
`MAX_FREQ = 347·120/MADJ`, with output delay `(SADJ+24)/MADJ · Tref + 0.1 ns`
[DS §17.3 p.199]. MADJ=144 sets the DLL's operating band around the ~200 MHz MCLK.
This is written **before** the main register block so the DLL master loop is
running when `MCR64`'s phase settings take effect.

---

## 6. DDR2 mode-register (MRS/EMRS) programming

### 6.1 The controller's indirect mode-set mechanism

The DDR2 device's own mode registers are programmed indirectly:

- **MCR2C** holds the **MRS** value in `[12:0]` and the **EMRS2** value in
  `[28:16]` [DS §17.3 p.190].
- **MCR30** holds the **EMRS1** value in `[12:0]` and the **EMRS3** value in
  `[28:16]` [DS §17.3 p.191].
- **MCR28** fires one command: `[2:1]` selects which mode register, `[0]` is the
  fire bit (hardware clears it and locks the AHB bus until the command's timing
  completes) [DS §17.3 p.190].

```{list-table} MCR28[2:1] mode-register selection (matches JEDEC BA[1:0])
:header-rows: 1
:widths: 18 22 30 30

* - MCR28 write
  - [2:1] select
  - Mode register
  - Uses value from
* - `0x01`
  - `00`
  - MRS
  - `MCR2C[12:0]`
* - `0x03`
  - `01`
  - EMRS1
  - `MCR30[12:0]`
* - `0x05`
  - `10`
  - EMRS2
  - `MCR2C[28:16]`
* - `0x07`
  - `11`
  - EMRS3
  - `MCR30[28:16]`
```

> **Datasheet correction.** Each `MCR28` fire issues exactly **one** mode
> register (selected by `[2:1]`), not the "two-at-once" combinations the earlier
> RE walkthrough guessed. The selection encoding is identical to JEDEC's bank
> address for mode commands — `BA=00` MRS, `01` EMRS1, `10` EMRS2, `11` EMRS3
> [JESD79-2B] — which independently confirms the mapping.

### 6.2 MRS value (MCR2C[12:0]) — DDR2 decode

```{list-table} MRS field decode (DDR2), MCR2C[12:0]
:header-rows: 1
:widths: 12 44 22 22

* - Bits
  - Field
  - `0x732` (init)
  - `0x632` (final)
* - `[12]`
  - Active power-down exit: `0`=fast (tXARD), `1`=slow (tXARDS)
  - 0 = fast
  - 0 = fast
* - `[11:9]`
  - Write recovery: `001`=2T…`011`=4T…`101`=6T
  - `011` = 4T
  - `011` = 4T
* - `[8]`
  - DLL Reset
  - **1 = reset**
  - **0 = no reset**
* - `[7]`
  - Test mode
  - 0
  - 0
* - `[6:4]`
  - CAS latency: `010`=2T, `011`=3T, `100`=4T, `101`=5T, `110`=6T
  - `011` = **CL3**
  - `011` = CL3
* - `[3]`
  - Burst type: `0`=sequential, `1`=interleave (unsupported)
  - 0 = seq
  - 0 = seq
* - `[2:0]`
  - Burst length: `010`=BL4, `011`=BL8
  - `010` = **BL4**
  - `010` = BL4
```

`0x732` is issued first (with DLL reset); after refresh is enabled the same
settings are re-issued as `0x632` with the DLL-reset bit cleared for normal
operation [platform.S:486-488,514-516] [DS §17.3 p.191].

### 6.3 EMRS1 value (MCR30[12:0]) — DDR2 decode

```{list-table} EMRS1 field decode (DDR2), MCR30[12:0]
:header-rows: 1
:widths: 12 46 42

* - Bits
  - Field
  - Values used
* - `[12]`
  - Reserved (0)
  - 0
* - `[11]`
  - Enable RDQS (unsupported)
  - 0
* - `[10]`
  - DQS# control: `0`=enable, `1`=disable
  - 0 = enabled
* - `[9:7]`
  - OCD program: `000`=exit/maintain, `111`=OCD calibration default
  - `000` (normal) → `111` (default) → `000` (exit)
* - `[6],[2]`
  - ODT resistance (A6,A2): `00`=off, `01`=75 Ω, `10`=150 Ω
  - `10` = **150 Ω**
* - `[5:3]`
  - Additive latency: `000`=0 (others unsupported)
  - `000` = AL0
* - `[1]`
  - Output driver impedance: `0`=100 %, `1`=60 %
  - 0 = 100 %
* - `[0]`
  - DLL disable: `0`=enable DLL, `1`=disable
  - 0 = DLL enabled
```

- `0x040` — DLL enabled, 150 Ω ODT, AL=0, OCD in normal/exit state
  [platform.S:490-492,530-532].
- `0x3C0` — same but `[9:7]=111` = **OCD calibration default**
  [platform.S:522-524].

EMRS2 and EMRS3 are both programmed as **0** (via the `[28:16]` halves of `MCR2C`
/ `MCR30`, which are left zero): default DDR2-400 operation, no high-temperature
self-refresh or partial-array self-refresh [platform.S:486-492] [DS §17.3 p.190-191].

---

## 7. Complete cold-init procedure

The full ordered sequence, mapped line-for-line to `platform.S`
(`lowlevel_init`, run from SPI flash before any stack/DRAM exists). Cross-checked
against JEDEC JESD79-2 DDR2 power-up [JESD79-2B].

1. **Save return address** in `r4` (no stack yet) [platform.S:116].
2. **Start Timer4** as an init-duration counter (`0x1E782044` = `0xFFFFFFFF`,
   `TIMER_CONTROL[13:12]=0b11`) [platform.S:118-128].
3. **Unlock SCU** — write `0x1688A8A8` to `SCU00` [platform.S:132-134].
4. **Mark "init in progress"** — `SCU40 |= 0x80` (bit 7) [platform.S:136-139].
5. **Warm-boot guard** — read `SCU40`, isolate **bit 6**; if set (DRAM already
   initialised), branch straight to `reg_lock` and skip the whole sequence
   [platform.S:142-147]. This prevents a watchdog/soft reset from re-running the
   destructive DLL-reset + PRECHARGE-ALL and wiping still-valid DRAM.
6. **Coarse M-PLL** — `SCU20 = 0x00004C81` to start the memory PLL near 200 MHz
   (superseded in step 12) [platform.S:149-159]. A silicon-revision read of
   `SCU7C` precedes it; the `beq set_MPLL` target is the next instruction, so the
   branch is effectively unconditional [platform.S:150-154].
7. **UART2 debug console** — configure `0x1E784000` (8N1) and print
   `"\r\nDRAM Init-DDR\r\n"` [platform.S:162-226]. Baud is 38400 on this board
   (`CONFIG_DRAM_UART_38400`) [ast2050.h:187].
8. **~100 µs settle** delay loop [platform.S:229-234].
9. **Re-unlock + verify SCU** — write `0x1688A8A8`, read back `0x01`; on failure
   print `"SCU LOCKED"` and abort [platform.S:240-248].
10. **Scratch = `0x5A000080`** — Linux-boot key `0x5A` in `[31:24]` + init-in-
    progress bit 7 [platform.S:283-285] [DS §18.2 p.215 SCU40].
11. **Unlock + verify SDRAM controller** — `MCR00 = 0xFC600309`, read back
    `0x01`; on failure print `"SDRAM LOCKED"` and abort [platform.S:287-295].
12. **Final M-PLL** — `SCU20 = 0x000041F0` (numerator 15, denumerator 0, output
    divider 1, post-divider ÷2 → 24 MHz·17/1÷2 ≈ **204 MHz ≈ DDR2-400**), then a
    **~400 µs PLL-lock** delay [platform.S:334-348] [DS §18.2 p.212 SCU20].
13. **Re-unlock SDRAM** (`MCR00 = 0xFC600309`) in case the PLL change bounced the
    lock [platform.S:350-352].
14. **DLL pre-config** — `MCR6C = 0x00909090` (MADJ) and `MCR64 = 0x00050000`
    (DLLs powered, held in reset) [platform.S:354-360]. See [§5](#5-dll-training).
15. **MCR04 geometry** — OR `SCU70[3:2]` (VGA strap) into the geometry constant
    and write `MCR04` (`0x585` = 64 MiB/4-bank on this board)
    [platform.S:363-377]. See [§3](#3-mcr04--configuration-register-geometry).
16. **Graphics protection** — `MCR08 = 0x0011030F` [platform.S:379-381].
17. **AC timing + delay** — `MCR10=MCR14=0x22201725`, `MCR18=MCR1C=0x1E29011A`,
    `MCR20=MCR24=0x00C82222` [platform.S:383-405]. See [§4](#4-ac-timing-refresh-arbitration-and-protection-registers).
18. **Arbitration** — `MCR38=0xFFFFFF82`, `MCR3C=0`, `MCR40=MCR44=MCR48=0`, and
    the undocumented `0x4C=0` [platform.S:407-429].
19. **ECC / reserved block** — `MCR50=MCR54=MCR58=MCR5C=0` (named ECC in
    `hwreg.h`; disabled) [platform.S:431-445].
20. **IO buffers** — `MCR60 = 0x032AA02A` (16-bit SSTL18, 150 Ω data ODT)
    [platform.S:447-449]. See [§4.7](#47-mcr60--io-buffer-mode).
21. **DLL final** — `MCR64 = 0x002D3000` (release DLL1+DLL3 from reset, set
    CK/CKn output phase) and `MCR68 = 0x02020202` (DQS input SADJ)
    [platform.S:451-457]. This is the block whose omission caused ~0.29 % errors.
22. **BIST off** — `MCR70=MCR74=MCR78=MCR7C=0` [platform.S:459-473].
23. **Assert CKE** — `MCR34 = 0x00000001` (bit 0 = SDRAM CKE Enable), then a
    **~400 µs** delay — the JEDEC "CKE high, then wait ≥400 ns after a ≥200 µs
    stable-clock/NOP period" requirement [platform.S:475-484] [DS §17.3 p.194]
    [JESD79-2B]. The controller auto-issues PRECHARGE ALL and the AUTO REFRESH
    cycles as part of the mode-set state machine.
24. **Load MRS/EMRS1 seeds** — `MCR2C = 0x00000732` (MRS=0x732, EMRS2=0),
    `MCR30 = 0x00000040` (EMRS1=0x040, EMRS3=0) [platform.S:486-492].
25. **Fire EMRS2** — `MCR28 = 0x05` (JEDEC step: program EMRS2 = 0)
    [platform.S:494-496].
26. **Fire EMRS3** — `MCR28 = 0x07` (EMRS3 = 0) [platform.S:498-500].
27. **Fire EMRS1** — `MCR28 = 0x03` (EMRS1 = 0x040: **enable DLL**, 150 Ω ODT)
    [platform.S:502-504].
28. **Fire MRS with DLL reset** — `MCR28 = 0x01` (MRS = 0x732: BL4, CL3, WR4,
    **DLL reset**); controller also runs PRECHARGE ALL + AUTO REFRESH here
    [platform.S:506-508].
29. **Enable refresh (init rate)** — `MCR0C = 0x00005A08` (8 refresh cycles/
    period) [platform.S:510-512].
30. **Fire MRS without DLL reset** — `MCR2C = 0x00000632`, `MCR28 = 0x01`
    (MRS = 0x632, DLL-reset cleared → normal operation) [platform.S:514-520].
31. **OCD calibration default** — `MCR30 = 0x000003C0`, `MCR28 = 0x03`
    (EMRS1 = 0x3C0, `[9:7]=111`) [platform.S:522-528].
32. **OCD calibration exit** — `MCR30 = 0x00000040`, `MCR28 = 0x03`
    (EMRS1 = 0x040, `[9:7]=000`, back to 150 Ω ODT) [platform.S:530-536].
33. **Steady-state refresh** — `MCR0C = 0x00005A21` (1 refresh/period, low-
    priority refresh enabled) [platform.S:538-540].
34. **Power control** — `MCR34 = 0x00007C03`: CKE enabled, auto power-down on,
    SDRAM ODT + internal ODT auto-ON/OFF for reads and writes, CKE-delay 1T
    [platform.S:542-544] [DS §17.3 p.193-194].
35. **Back-compat M-PLL mirror** — `MCR120 = 0x00004C41` [platform.S:546-548].
36. **Mark init complete** — `SCU40 |= 0x40` (bit 6) so future warm boots take
    the step-5 skip path [platform.S:559-564].
37. **Print `"...Done\r\n"`** [platform.S:567-585].
38. **Re-lock** — `SCU00 = 0`, `MCR00 = 0` [platform.S:588-596].
39. **Return** — restore `lr` from `r4` [platform.S:600-603].

**Total cold-boot UART2 output:** `\r\nDRAM Init-DDR\r\n...Done\r\n`.

### 7.1 Mapping to the JEDEC JESD79-2 power-up sequence

```{list-table} Aspeed sequence vs JEDEC DDR2 power-up
:header-rows: 1
:widths: 50 50

* - JEDEC JESD79-2 step
  - Aspeed controller action
* - ≥200 µs stable clock + NOP, then CKE high
  - `MCR34=0x01` + ~400 µs delay (steps 23)
* - PRECHARGE ALL
  - Auto-issued by mode-set state machine
* - EMRS2, EMRS3
  - `MCR28=0x05`, `MCR28=0x07` (steps 25–26)
* - EMRS1 (enable DLL)
  - `MCR28=0x03`, EMRS1=0x040 (step 27)
* - MRS (DLL reset, A8=1)
  - `MCR28=0x01`, MRS=0x732 (step 28)
* - PRECHARGE ALL + ≥2× AUTO REFRESH
  - Controller + `MCR0C=0x5A08` (8 cycles) (steps 28–29)
* - MRS (no DLL reset — set operating params)
  - `MCR28=0x01`, MRS=0x632 (step 30)
* - EMRS1 OCD default (A9:A7=111)
  - `MCR28=0x03`, EMRS1=0x3C0 (step 31)
* - EMRS1 OCD exit (A9:A7=000)
  - `MCR28=0x03`, EMRS1=0x040 (step 32)
```

JEDEC allows the four mode registers to be programmed in any order but requires
DLL-enable (EMRS1) before the DLL-reset MRS, and the two-step OCD default→exit at
the end — both of which the Aspeed order honours [JESD79-2B].

---

## 8. Self-refresh and clock-switch sequences (datasheet)

Not used in the cold-boot path but part of the controller contract, and useful
for a faithful model [DS §17.6-17.7 p.203]:

- **Enter self-refresh:** stop all IP traffic (swap ARM code to static flash),
  then `MCR34[2]=1` (optionally `[4:3]` for extra saving).
- **Exit self-refresh:** `MCR34[2]=0`; reset DRAM DLL via `MCR2C[8]=1` then
  `MCR28=1`; then clear `MCR2C[8]=0` and `MCR28=1` again.
- **Clock switch normal→low:** load low-speed AC params into `MCR14/1C/24`, set
  `MCR2C` low-speed mode, set `MCR34[22:21]=0x3`, `[19:17]`=slow ratio, then
  `MCR34[20]=1`.
- **Clock switch low→normal:** `MCR2C` normal mode, `MCR34[22:21]=0x2`,
  `MCR34[20]=1`.

---

## 9. AST2050-specific vs shared with AST2400

- **Shared SoC-level values** (identical in the Raptor AST2050 code and the
  independent AMI AST2100/AST2300 code, so they are controller requirements, not
  board tuning) [DDR2-INIT-REVERSE-ENGINEERING.md §7.1]: `MCR00` unlock key
  `0xFC600309`; DLL block `MCR6C=0x00909090`, `MCR64` pre/final
  (`0x00050000`/`0x002D3000`), `MCR68=0x02020202`; `MCR08=0x0011030F`;
  `MCR38=0xFFFFFF82`; `MCR60=0x032AA02A`; the `MCR28` fire order (5,7,3,1) and the
  `MCR34` init/final (`0x01`/`0x7C03`) and `MCR0C` init/final (`0x5A08`/`0x5A21`).
- **Board / speed-grade tuning** that differs between implementations: `MCR04`
  geometry constant (capacity/bank/column); the AC timing values
  (`MCR10/18/20`); the MRS latency (**Raptor CL3/WR4 `0x732`** vs AMI CL4/WR5
  `0x942`); whether low-speed registers differ from normal-speed (Raptor makes
  them identical — no low-speed mode on this board — while AMI programs separate
  low-speed timing); and VGA grant limits (`MCR40`) [DDR2-INIT-REVERSE-ENGINEERING.md §7.2-7.3].
- **AST2050 vs mainline AST2400:** the AST2050 (G3) is register-compatible enough
  that mainline Linux and modern U-Boot reuse the **AST2400 (G4)** SDRAM
  controller model; there is no upstream G3 SDRAM binding. The device tree used
  for this hardware is derived from `aspeed-g4.dtsi` for the same reason
  [CLAUDE.md]. The chief AST2050 realities to preserve in a model: **16-bit
  external DDR2 bus**, **64 MiB** on the KGPE-D16, ~200 MHz MCLK, and the M-PLL
  formula in [DS §18.2 p.212].

---

## Sources

Primary (in-repo, read-only reverse-engineering + datasheet):

- ASPEED AST2050/AST1100 A3 Datasheet V1.05 — Chapter 17 "SDRAM Memory
  Controller" (pp. 183–203, register base `0x1E6E0000`) and Chapter 18 "System
  Control Unit" (SCU20 p.212, SCU40 p.215, SCU7C p.220). In repo at
  `datasheets/aspeed/AST2050_AST1100_A3_Datasheet_V1.05.pdf`. Cited inline as
  `[DS §x p.N]` (N = datasheet printed page).
- `asus-kgpe-d16-firmware/platform.S` — Raptor Engineering AST2050 U-Boot
  `lowlevel_init` (hardware-verified DDR2 init). Cited as `[platform.S:LINE]`.
- `asus-kgpe-d16-firmware/hwreg.h` — register address definitions.
- `asus-kgpe-d16-firmware/ast2050.h` — board configuration (`CONFIG_DRAM_UART_38400`,
  `PHYS_SDRAM_1_SIZE = 64 MiB`).
- `asus-kgpe-d16-firmware/DDR2-INIT-REVERSE-ENGINEERING.md` — the detailed
  line-by-line RE analysis (the ~0.29 % DLL-error result; Raptor-vs-AMI compare).

Secondary (web, corroboration for JEDEC DDR2 procedure):

- JEDEC JESD79-2B DDR2 SDRAM standard — mode-register set, EMRS/OCD, and the
  power-up order (BA[1:0] = 00/01/10/11 → MRS/EMRS1/EMRS2/EMRS3):
  <https://cs.baylor.edu/~maurer/CSI5338/JESD79-2B.pdf>
- JEDEC DDR2 standard landing page:
  <https://www.jedec.org/standards-documents/docs/jesd-79-2e>
- DDR2 power-up timing (≥200 µs stable clock/NOP before CKE high; PRECHARGE ALL;
  ≥2 AUTO REFRESH), e.g. Samsung DDR2 device-operation guide and the Microchip
  "DDR2-SDRAM Initialization" reference:
  <https://onlinedocs.microchip.com/oxy/GUID-4D282FC5-82FC-4934-8BAD-D4A5D8422E6C-en-US-7/GUID-D24491A8-4CCA-4A45-88A4-E324434824DD.html>
- Raptor Engineering AST2050 U-Boot upstream (origin of `platform.S`):
  <https://github.com/raptor-engineering/ast2050-uboot>
- QEMU Aspeed SoC memory-map / SDMC model reference:
  <https://www.qemu.org/docs/master/system/arm/aspeed.html>
