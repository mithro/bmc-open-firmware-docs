# Digi NS9360 SoC

The **Digi (NetSilicon) NS9360** is a single-chip 0.13 µm CMOS network-attached
processor from the NET+ARM family, built around an **ARM926EJ-S** (ARMv5TEJ)
core. It powers the HPE Intelligent Modular PDU (AF531A), whose stock firmware
is Digi **NET+OS** (a ThreadX-based RTOS), not Linux [ANALYSIS.md](#sources). This page is
a register-by-register reference for every on-chip block a Linux, U-Boot, or
Zephyr port must drive.

The authority for this document is the **NS9360 Hardware Reference**, Digi part
number 90000675 rev J (cited `[HWRef p.N](#sources)`, where the printed page number equals
the PDF page number), supported by the **NS9360 Datasheet** 91001326 rev D
(`[Datasheet](#sources)`). Every register base address and offset below is independently
cross-checked against the archived open-source Linux `arch/arm/mach-ns9xxx`
(cited `[mach-ns9xxx](#sources)`) and the U-Boot NS9750 support (`[u-boot ns9750](#sources)`); those
two code bases agree on every base and offset, and that agreement is noted where
it matters. See the Sources section at the end of this page.

```{admonition} Scope and conventions
:class: note

- **Reset marking.** Bit ranges the datasheet marks reserved / "not used" are
  labelled *reserved* in every bitfield table. Where the datasheet says a
  reserved or "not used" field must be written with a specific value, that value
  is given.
- **Access codes.** `R/W` read-write, `R` read-only, `W` write-only,
  `RW1TC` / `R/C` read, write-1-to-clear (or clear-on-read).
- **Single-access rule.** For every block in this SoC the configuration
  registers "must be accessed as 32-bit words and as single accesses only.
  Bursting is not allowed" [HWRef p.462, p.281, p.341, p.463](#sources).
- **Public-safe.** No credentials, MAC addresses, private IP addresses, or host
  names appear here; the firmware's factory-default network identity is
  deliberately omitted.
```

## System overview


### What is on the chip

```{list-table} NS9360 on-chip blocks (feature summary)
:header-rows: 1
:widths: 26 74

* - Block
  - Summary
* - CPU
  - ARM926EJ-S (ARMv5TEJ), 5-stage pipeline, Harvard, 8 KB I-cache + 4 KB
    D-cache, MMU with TLB, DSP extensions, Jazelle Java, EmbeddedICE-RT/JTAG.
    Grades 103 / 155 / 177 MHz [HWRef p.24-25](#sources)
* - Memory controller
  - AMBA AHB MultiPort Memory Controller (PL172/PL175-style): 4 dynamic
    (SDRAM/LP-SDRAM) + 4 static (ROM/Flash/SRAM) chip selects, 8/16/32-bit,
    1-32 wait states, 2 external DMA channels [HWRef p.25, p.196](#sources)
* - Ethernet
  - 10/100 Mbps MAC with MII **or** RMII to an external PHY; 2 KB RX FIFO,
    256-byte TX FIFO, four RX descriptor rings + one TX ring, separate RX/TX
    DMA, 39 statistics counters [HWRef p.26, p.319](#sources)
* - Serial (×4)
  - Four independent channels A-D, each UART **or** SPI-master **or**
    SPI-slave; 32-byte TX + 32-byte RX FIFO; DMA-capable [HWRef p.27, p.564](#sources)
* - I2C
  - One master/slave port, 100 kHz (standard) / 400 kHz (fast), 7- and 10-bit
    addressing, multi-master arbitration [HWRef p.27, p.508](#sources)
* - GPIO
  - 73 pins (gpio0-gpio72), each 4-way muxed (3 peripheral functions + GPIO),
    per-pin direction/inversion; 4 external interrupt pins [HWRef p.29, p.462](#sources)
* - Timers
  - 8 general-purpose 16/32-bit timer/counters (concatenatable, PWM), plus a
    software watchdog and a bus monitor [HWRef p.28, p.144](#sources)
* - Interrupt controller
  - Vectored interrupt controller (VIC): 32 priority levels, IRQ/FIQ, 32
    sources [HWRef p.147](#sources)
* - RTC
  - On-chip real-time clock/calendar (10 ms resolution) with alarm and rollover
    interrupts [HWRef p.489](#sources)
* - USB
  - USB 2.0 full/low speed: independent OHCI Host + Device, internal PHY (+
    external PHY option) [HWRef p.26](#sources)
* - LCD
  - TFT/STN LCD controller (AHB DMA master) up to 1024×768, up to 64K colours
    [HWRef p.524](#sources)
* - IEEE 1284
  - Parallel peripheral port (compatibility/nibble/byte/ECP) [HWRef p.626](#sources)
* - Clocking
  - On-chip PLL from an external crystal; software-programmable multiplier;
    separate PLL for USB [HWRef p.29](#sources)
```

The board using this SoC pairs 32 MB SDRAM (ISSI IS42S32800D, 32-bit), 16 MB NOR
flash (2× Macronix MX29LV640EB on CS0/CS1), an ICS1893 Ethernet PHY, and a
29.4912 MHz system crystal [ANALYSIS.md][REFERENCE-MATERIAL.md].

### System (AHB) address map

The AHB decoder assigns the 256 MB windows below at reset; the low chip-select
windows are re-mappable by software after boot [HWRef p.142-144, Table 47](#sources).

```{list-table} System address map
:header-rows: 1
:widths: 34 12 54

* - Address range
  - Size
  - Region
* - 0x0000_0000 - 0x0FFF_FFFF
  - 256 MB
  - System memory dynamic (SDRAM) chip select 0 (default)
* - 0x1000_0000 - 0x3FFF_FFFF
  - 768 MB
  - System memory dynamic chip selects 1-3 (default)
* - 0x4000_0000 - 0x4FFF_FFFF
  - 256 MB
  - System memory static chip select 0 (NOR flash bank 1 on this board)
* - 0x5000_0000 - 0x5FFF_FFFF
  - 256 MB
  - System memory static chip select 1 (NOR flash bank 2 on this board)
* - 0x6000_0000 - 0x7FFF_FFFF
  - 512 MB
  - System memory static chip selects 2-3
* - 0x8000_0000 - 0x8FFF_FFFF
  - 256 MB
  - Reserved
* - 0x9000_0000 - 0x9FFF_FFFF
  - 256 MB
  - BBus peripherals (see below)
* - 0xA000_0000 - 0xA03F_FFFF
  - 4 MB
  - Reserved
* - 0xA040_0000 - 0xA04F_FFFF
  - 1 MB
  - BBus-to-AHB bridge control/status registers
* - 0xA060_0000 - 0xA06F_FFFF
  - 1 MB
  - Ethernet Communication Module
* - 0xA070_0000 - 0xA07F_FFFF
  - 1 MB
  - Memory controller
* - 0xA080_0000 - 0xA08F_FFFF
  - 1 MB
  - LCD controller (LCD palette RAM at 0xA080_0200)
* - 0xA090_0000 - 0xA09F_FFFF
  - 1 MB
  - System Control Module (SCM)
* - 0xFFFF_0000 - 0xFFFF_003F
  - 64 B
  - 16-word on-chip RAM (interrupt-vector relocation), word access only
```

The BBus peripheral space (base 0x9000_0000) sub-decodes as follows
[HWRef p.415-416, Table 305](#sources); confirmed by [mach-ns9xxx hardware.h](#sources) and
[u-boot ns9750_ser.h](#sources).

```{list-table} BBus peripheral base addresses
:header-rows: 1
:widths: 22 78

* - Base address
  - Peripheral
* - 0x9000_0000
  - BBus DMA controller 1 (16 channels)
* - 0x9020_0000
  - Serial channel B
* - 0x9020_0040
  - Serial channel A
* - 0x9030_0000
  - Serial channel C
* - 0x9030_0040
  - Serial channel D
* - 0x9040_0000
  - IEEE 1284 controller
* - 0x9050_0000
  - I2C controller
* - 0x9060_0000
  - BBus utility (GPIO, master reset, endian, USB config)
* - 0x9070_0000
  - Real time clock
* - 0x9080_0000
  - USB host (OHCI + front end)
* - 0x9090_0000
  - USB device
* - 0x9091_0000
  - BBus DMA controller 2 (USB device, 16 channels)
```

### Clock tree

A crystal (or external oscillator) feeds an on-chip PLL. The PLL VCO output is
divided down by fixed ratios to the CPU, AHB (system + memory bus), and BBus
(peripheral bus) clocks [HWRef p.36, p.153, Figure 39]:

$$
\begin{aligned}
f_\text{vco} &= f_\text{osc} \times (ND+1) / FS & &FS \in \{1,2,4,8\},\ ND+1 = \text{PLL multiplier}\\
f_\text{cpu} &= f_\text{vco} / 2 & &\text{ARM926EJ-S core clock}\\
f_\text{ahb} &= f_\text{vco} / 4 & &(= f_\text{cpu} / 2)\\
f_\text{bbus} &= f_\text{vco} / 8 & &(= f_\text{ahb} / 2)\\
f_\text{lcd} &= f_\text{vco} / \{4,8,16,32\} & &\text{programmable (or external)}
\end{aligned}
$$

So the fixed ratio is **cpu : ahb : bbus = 4 : 2 : 1**. With the board's
29.4912 MHz crystal at the 177 MHz grade (ND+1 = 24, FS = ÷2), f_vco =
353.8944 MHz, giving CPU 176.9472 MHz, AHB 88.4736 MHz, BBus 44.2368 MHz
[HWRef p.36 Table 3][REFERENCE-MATERIAL.md]. Speed grades: 177 MHz (0-70 °C),
155 MHz (-40..+85 °C), 103 MHz [HWRef p.29](#sources).

Linux computes the same tree: $\text{systemclock} = \text{CRYSTAL} \times (ND+1) \gg FS$ (the raw VCO
output) and $\text{cpuclock} = \text{systemclock} / 2$, with $\text{CRYSTAL} = 29491200$
[mach-ns9xxx processor-ns9360.c](#sources). U-Boot's `ns9750dev.h` states the full tree
explicitly as CPU = system/2, AHB = system/4, BBus = system/8 [u-boot ns9750dev.h](#sources).

```{admonition} "System clock" naming caveat
:class: warning

Digi's reference code labels the **raw PLL/VCO output** as the "system clock"
(`CONFIG_SYS_CLK_FREQ` in U-Boot; `ns9360_systemclock()` in Linux), which is
~354 MHz at the 177 MHz grade — this is *not* the ~88 MHz AHB bus clock. The
ARM core runs at f_vco/2 ≈ 176.9 MHz. One repo port draft set
`CONFIG_SYS_CLK_FREQ = 176.9 MHz` (= f_vco/2) and derived the buses from there,
which shifts the BBus figure to ~22 MHz and changes UART divisor math; prefer
the datasheet tree above (BBus = f_vco/8 ≈ 44.2 MHz) when computing baud rates
[HWRef p.36][PLAN-INCREMENTAL-PORT.md].
```

USB is clocked by a **separate PLL** from an external 48 MHz crystal/oscillator
[HWRef p.38](#sources).

### Boot and reset

The chip supports two glueless boot methods, selected by the `reset_done`
strap sampled at power-up [HWRef p.32-35]:

- **`reset_done` = 1 (default): boot from flash/ROM** on the system memory bus
  (8-, 16-, or 32-bit static memory). The board boots from NOR flash on CS0
  [ANALYSIS.md](#sources).
- **`reset_done` = 0: boot from SDRAM via a serial SPI-EEPROM.** An on-chip boot
  engine drives Serial channel B in SPI-master mode, reads a 128-130 byte
  configuration header (memory-controller + SDRAM mode settings) from EEPROM
  address 0, programs the memory controller, copies the image into SDRAM at
  address 0, then releases the CPU [HWRef p.32-34, p.425-427](#sources).

At power-on reset, **static CS1 is mirrored onto CS0 and CS4**; clearing the
address-mirror bit (`M`) in the memory-controller Control register makes the
chip selects independent [HWRef p.198](#sources). Reset sources differ in scope: only the
hard `reset_n` pin re-samples the PLL/endian/GPIO bootstrap straps; `sreset_n`,
the watchdog reset, and a PLL software-change reset do not [HWRef p.33 Table 1](#sources).
The `Reset and Sleep Control` register records the last reset cause (see the SCM
"Reset and Sleep Control register" section below). Hardware reset needs ~4 ms for PLL
lock; a software reset lasts 128 CPU clocks [HWRef p.35](#sources).

### Bootstrap / strapping pins

Sampled on the hard `reset_n` pin; "1" = internal pull-up, "0" = external
pull-down [HWRef p.153-156, Table 49][ANALYSIS.md].

```{list-table} Power-up strapping pins
:header-rows: 1
:widths: 34 66

* - Pin(s)
  - Configures
* - reset_done
  - Boot mode: 0 = SDRAM via SPI-EEPROM; 1 = flash/ROM (default)
* - gpio[44]
  - Endian mode: 0 = big endian, 1 = little endian
* - gpio[24], gpio[20]
  - CS1 data width: 00 = 16-bit, 01 = 8-bit, 11 = 32-bit
* - gpio[49]
  - Chip-select polarity: 0 = active high, 1 = active low
* - rtck_out
  - CS1 byte-lane-enable / write-enable select for byte-wide devices
* - gpio[17], gpio[12], gpio[10], gpio[8], gpio[4]
  - PLL ND[4:0] — 5-bit code mapping to the PLL multiplier (ND+1), 1-32, via
    HWRef Table 50
* - gpio[2], gpio[0]
  - PLL FS[1:0] frequency select: divide by 1 / 2 / 4 / 8
* - gpio[19]
  - Reserved — must NOT be pulled to 0 until reset_done = 1, or the chip is
    unusable
```

The 5-bit ND strap does not map linearly; e.g. code `10010` = multiplier 24
(the 176.9472 MHz grade) [HWRef p.155-156, Table 50](#sources). The board boots big-endian
(gpio[44] = 0) and a software stub then switches the CPU and buses to
little-endian to reuse the little-endian Digi/Linux/U-Boot code base
[REFERENCE-MATERIAL.md][PLAN-INCREMENTAL-PORT.md].

## CPU — ARM926EJ-S


The core is a standard **ARM926EJ-S** (ARMv5TEJ): 32-bit ARM + 16-bit Thumb +
Jazelle (Java) instruction sets, a Harvard cached micro-architecture with
separate instruction and data AHB interfaces, an integer core with single-cycle
MAC / DSP extensions, an 8 KB instruction cache and 4 KB data cache, an MMU with
TLB, and EmbeddedICE-RT debug over JTAG [HWRef p.24, p.67-70](#sources). The CP15 system
control coprocessor (accessed via `MRC`/`MCR` in privileged mode) governs the
cache, MMU, and three address spaces — VA (core), MVA (cache/MMU, via the FCSE
PID), and PA (AMBA/physical) [HWRef p.71-72](#sources). CP15 and MMU page-table behaviour
are the generic ARM926EJ-S definitions and are not repeated here; the SoC-specific
programming lives in the blocks below. One SoC hook: CP15 control-register bit 7
(CPU endianness) is one of the four bits the boot stub clears when switching
big→little endian [PLAN-INCREMENTAL-PORT.md](#sources).

## System Control Module (SCM)


**Base address: 0xA0900000** [HWRef p.143][mach-ns9xxx regs-sys-ns9360.h][u-boot ns9750_sys.h].

The SCM contains the AHB bus arbiter, system address decoding (the chip-select
base/mask registers), the programmable timers, the software watchdog, the
vectored interrupt controller, the PLL/clock configuration, reset/sleep control,
and the RTC clock divider [HWRef p.136](#sources).

### SCM register map

```{list-table} SCM registers (offset from 0xA0900000)
:header-rows: 1
:widths: 18 26 56

* - Offset
  - Register
  - Description
* - 0x000
  - AHB Arbiter Gen Config
  - CPU external-memory access mode
* - 0x004-0x010
  - BRC0-BRC3
  - Bus Request Config (16 arbiter channels, 4 per register)
* - 0x044-0x060
  - Timer 0-7 Reload Count
  - Reload value per GP timer (step 4)
* - 0x084-0x0A0
  - Timer 0-7 Read
  - Current counter value per GP timer (step 4)
* - 0x0C4-0x140
  - Interrupt Vector Address 0-31
  - ISR address per priority level (step 4)
* - 0x144-0x160
  - Int Config 0-31
  - Interrupt configuration, 4 fields of 8 bits per register
* - 0x164
  - ISRADDR
  - Highest-priority active ISR address / priority mask
* - 0x168
  - Interrupt Status Active
  - Active + enabled interrupt levels
* - 0x16C
  - Interrupt Status Raw
  - All interrupt levels (enabled and disabled)
* - 0x170
  - Timer Interrupt Status
  - Per-timer interrupt request bits (16)
* - 0x174
  - Software Watchdog Config
  - Watchdog enable / clock / interrupt-vs-reset
* - 0x178
  - Software Watchdog Timer
  - Watchdog counter (write to service)
* - 0x17C
  - Clock Configuration
  - Per-peripheral clock gating
* - 0x180
  - Reset and Sleep Control
  - Module resets, sleep entry, wake sources, last-reset cause
* - 0x184
  - Misc System Config and Status
  - Revision/ID, endian bit (ENDM), strap status
* - 0x188
  - PLL Configuration
  - PLL multiplier (ND), divider (FS), software-change trigger
* - 0x18C
  - Active Interrupt Level Status
  - Level of the currently active interrupt
* - 0x190-0x1AC
  - Timer 0-7 Control
  - Per GP timer control (step 4)
* - 0x1D0-0x1EC
  - CS0-3 Dynamic Base/Mask
  - Dynamic (SDRAM) chip-select address decode (base+mask pairs)
* - 0x1F0-0x20C
  - CS0-3 Static Base/Mask
  - Static (flash/SRAM) chip-select address decode (base+mask pairs)
* - 0x210
  - Gen ID
  - GPIO inputs latched at reset (board ID)
* - 0x214-0x220
  - External Interrupt 0-3 Control
  - Edge/level/polarity for the 4 external interrupt pins
* - 0x224
  - RTC Clock Control
  - RTC clock divider (generates 100 Hz)
```

Register offsets are confirmed bit-for-bit by [u-boot ns9750_sys.h](#sources) (`PLL`=0x188,
`CLOCK`=0x17C, `RESET`=0x180, `MISC`=0x184, `ISRADDR`=0x164, `TIMER_*`,
`CS_*_BASE/MASK`) and [mach-ns9xxx regs-sys-ns9360.h](#sources) / `regs-sys-common.h`
(`SYS_PLL`=0xa0900188, `SYS_ISA`=0xa0900168, `SYS_TC`=0xa0900190, etc.).

### AHB bus arbiter (BRC0-BRC3)

The main arbiter holds a 16-entry Bus Request Config (BRC) set, four 8-bit
channels per 32-bit register (BRC0 = channels 0-3 … BRC3 = channels 12-15). At
power-up only the CPU is assigned, on a 100 %-bandwidth channel [HWRef p.136-140](#sources).

```{list-table} BRC per-channel byte fields [HWRef p.163](#sources)
:header-rows: 1
:widths: 12 14 12 62

* - Bits
  - Field
  - Access
  - Meaning
* - 7
  - CEB
  - R/W
  - Channel enable (reset 1): 0 = disable, 1 = enable
* - 6
  - reserved
  - —
  - reserved
* - 5:4
  - BRF
  - R/W
  - Bandwidth reduction: 00 = 100 %, 01 = 75 %, 10 = 50 %, 11 = 25 %
* - 3:0
  - HMSTR
  - R/W
  - AHB master (hmaster) assigned to this channel
```

`AHB Arbiter Gen Config` (0x000) bit 0 `EXMA`: 0 = CPU direct external-memory
access via slave port 1; 1 = arbitrate through slave port 0 [HWRef p.162](#sources).
Hmaster encodings: ARM I/D = 0000, Ethernet Rx = 0001, Ethernet Tx = 0010,
BBus = 0101, LCD = 0110 [HWRef p.144, Table 48](#sources).

### Programmable timers

There are **8 general-purpose 16/32-bit timer/counters** (Timer 0-7), each with a
16-bit counter and 16-bit prescaler, individually enabled, concatenatable to form
32-bit (or longer) counters, and usable in internal-timer, gated, or
event-counter modes; two timers can be paired for PWM output [HWRef p.144-147](#sources).
Each has a Reload Count register (0x044+), a read-back register (0x084+), and a
control register (0x190+). Linux uses timer 0 as clocksource and timer 1 as
clockevent, both clocked at the CPU rate [mach-ns9xxx time-ns9360.c](#sources).

```{admonition} Timer count discrepancy
:class: note

The datasheet states "8" general-purpose timers in one place (p.28) and
"sixteen" in another (p.31); the register map exposes Timer 0-7 control/reload/read
registers, while the `Timer Interrupt Status` register reports 16 timer interrupt
bits [HWRef p.28, p.31, p.172](#sources). Treat the programmable set as Timer 0-7.
```

```{list-table} Timer 0-7 Control register (0x190 + n*4) [HWRef p.165-167](#sources)
:header-rows: 1
:widths: 12 14 12 62

* - Bits
  - Field
  - Access
  - Meaning
* - 31:16
  - reserved
  - —
  - reserved
* - 15
  - TEN
  - R/W
  - Timer enable
* - 14:11
  - reserved
  - —
  - reserved
* - 10
  - TDBG
  - R/W
  - Debug-halt behaviour: 0 = run while CPU halted, 1 = stop
* - 9
  - INTC
  - R/W
  - Interrupt clear (write 1 then 0)
* - 8:6
  - TLCS
  - R/W
  - Clock select: 000 = CPU, 001-110 = CPU/{2,4,8,16,32,64}, 111 = external event
* - 5:4
  - TM
  - R/W
  - Mode: 00 = internal/event, 01 = ext low-gated, 10 = ext high-gated, 11 = concatenate lower timer
* - 3
  - INTS
  - R/W
  - Interrupt select: 1 = generate IRQ
* - 2
  - UDS
  - R/W
  - Up/down: 0 = up (TC 0xFFFFFFFF), 1 = down (TC 0x0)
* - 1
  - TSZ
  - R/W
  - Timer size: 0 = 16-bit, 1 = 32-bit
* - 0
  - REN
  - R/W
  - Reload enable: 0 = halt at terminal count, 1 = reload and continue
```

Bit positions match [u-boot ns9750_sys.h](#sources) (TEN=15, INTC=9, TLCS=8:6, TM=5:4,
INTS=3, UDS=2, TSZ=1, REN=0) and [mach-ns9xxx regs-sys-ns9360.h](#sources). The
`Timer Interrupt Status` register (0x170) bits 15:0 = per-timer requests (1 =
active) [HWRef p.172](#sources).

### Software watchdog

```{list-table} Software Watchdog Config (0x174) [HWRef p.173-174](#sources)
:header-rows: 1
:widths: 12 14 12 62

* - Bits
  - Field
  - Access
  - Meaning
* - 31:9
  - reserved
  - —
  - reserved
* - 8
  - SDBG
  - R/W
  - Debug-halt: 0 = run, 1 = stop while CPU halted
* - 7
  - SWWE
  - R/W
  - Watchdog enable — once set, cannot be cleared
* - 6
  - reserved
  - —
  - reserved
* - 5
  - SWWI
  - R/W
  - Interrupt clear (write 1 then 0)
* - 4
  - SWWIC
  - R/W
  - Response: 0 = generate interrupt, 1 = generate reset
* - 3
  - reserved
  - —
  - reserved
* - 2:0
  - SWTCS
  - R/W
  - Clock select: 000-101 = CPU/{2,4,8,16,32,64}, 110/111 reserved
```

Write the `Software Watchdog Timer` register (0x178) to service the watchdog; a
read returns the current value without changing it [HWRef p.174](#sources).

### Interrupt controller (VIC)

The vectored interrupt controller has **32 priority levels** (line 0 = highest,
line 31 = lowest) and two classes, IRQ and FIQ; the single FIQ source must be
assigned to level 0 [HWRef p.147-149](#sources). Each level has an `Int Config` field
(assign a source, set polarity, IRQ/FIQ, enable) and an `Interrupt Vector
Address` register (the ISR entry point). The highest-priority active level drives
`ISRADDR`; reading `ISRADDR` masks that and all lower priorities (nested
handling), and writing any value to `ISRADDR` clears the mask [HWRef p.151, p.170](#sources).

```{list-table} Int Config field, one 8-bit field per source-level (0x144+) [HWRef p.169-170](#sources)
:header-rows: 1
:widths: 12 14 12 62

* - Bits
  - Field
  - Access
  - Meaning
* - 7
  - IE
  - R/W
  - Interrupt enable
* - 6
  - INV
  - R
  - Invert source level
* - 5
  - IT
  - R/W
  - Type: 0 = IRQ, 1 = FIQ (FIQ must be highest priority)
* - 4:0
  - ISD
  - R/W
  - Interrupt source ID assigned to this priority level (0-31)
```

`Interrupt Vector Address 0-31` (0x0C4+) each hold a 32-bit ISR address.
`Interrupt Status Active` (0x168) reports active + enabled levels; `Interrupt
Status Raw` (0x16C) reports all levels; `Active Interrupt Level Status` (0x18C,
bits 5:0) reports the current level [HWRef p.168, p.171, p.182](#sources).

The 32 interrupt source IDs are hardwired [HWRef p.150-151]:

```{list-table} NS9360 interrupt source IDs
:header-rows: 1
:widths: 8 42 8 42

* - ID
  - Source
  - ID
  - Source
* - 0
  - Watchdog Timer
  - 16
  - Timer 0
* - 1
  - AHB Bus Error
  - 17
  - Timer 1
* - 2
  - BBus Bridge aggregate
  - 18
  - Timer 2
* - 3
  - Reserved
  - 19
  - Timer 3
* - 4
  - Ethernet Receive
  - 20
  - Timer 4
* - 5
  - Ethernet Transmit
  - 21
  - Timer 5
* - 6
  - Ethernet PHY
  - 22
  - Timer 6
* - 7
  - LCD Module
  - 23
  - Timer 7
* - 8
  - Serial Port B Receive
  - 24
  - RTC
* - 9
  - Serial Port B Transmit
  - 25
  - USB Host
* - 10
  - Serial Port A Receive
  - 26
  - USB Device
* - 11
  - Serial Port A Transmit
  - 27
  - IEEE 1284
* - 12
  - Serial Port C Receive
  - 28
  - External Interrupt 0
* - 13
  - Serial Port C Transmit
  - 29
  - External Interrupt 1
* - 14
  - I2C
  - 30
  - External Interrupt 2
* - 15
  - BBus DMA
  - 31
  - External Interrupt 3
```

### PLL Configuration register

**Offset 0x188.** Multiplier and divider fields, plus a software-change trigger
that resets the chip to lock new settings [HWRef p.181-182](#sources). FS = bits 24:23 and
ND = bits 20:16 match [mach-ns9xxx regs-sys-ns9360.h](#sources) (`SYS_PLL_FS`,
`SYS_PLL_ND`, `SYS_PLL_SWC`) and [u-boot ns9750_sys.h](#sources) (`PLL_PLLFS_MA`=0x01800000,
`PLL_PLLND_MA`=0x001F0000, `PLL_PLLSW`=0x00008000).

```{list-table} PLL Configuration (0x188) [HWRef p.181-182](#sources)
:header-rows: 1
:widths: 12 14 12 62

* - Bits
  - Field
  - Access
  - Meaning
* - 31:25
  - reserved
  - —
  - reserved
* - 24:23
  - PLLFS
  - R
  - PLL FS status (strap or last SW value)
* - 22:21
  - reserved
  - —
  - reserved
* - 20:16
  - PLLND
  - R
  - PLL ND status (strap or last SW value)
* - 15
  - PLLSW
  - W
  - Write 1 to apply D9:0; chip resets to lock the new PLL settings
* - 14:10
  - reserved
  - —
  - reserved
* - 9
  - PLLBW
  - R/W
  - PLL bypass (software) — keep 0
* - 8:7
  - FSEL
  - R/W
  - PLL frequency select FS: 00 = ÷1, 01 = ÷2, 10 = ÷4, 11 = ÷8
* - 6:5
  - reserved
  - —
  - reserved
* - 4:0
  - NDSW
  - R/W
  - PLL multiplier ND ($f_\text{vco} = f_\text{osc} \times (ND+1) / FS$)
```

### Clock Configuration register

**Offset 0x17C — per-peripheral clock gating.** Most peripheral clocks reset
*enabled* (1 = enabled); the exception is the memory-clock MC0 field, whose sense
is inverted (0 = enabled) [HWRef p.175-177](#sources). There is no GPIO clock-enable here —
GPIO/BBus utility is not clock-gated in this register.

```{list-table} Clock Configuration (0x17C) [HWRef p.175-177](#sources)
:header-rows: 1
:widths: 12 14 12 62

* - Bits
  - Field
  - Access
  - Meaning
* - 31:19
  - reserved
  - —
  - reserved
* - 18
  - MC0
  - R/W
  - Memory clock 0 (reset 0): 0 = enabled, 1 = disabled (inverted sense)
* - 17
  - BBDMA
  - R/W
  - BBus DMA clock (reset 1 enabled)
* - 16
  - 1284
  - R/W
  - IEEE 1284 clock
* - 15
  - USBD
  - R/W
  - USB device clock
* - 14
  - USBH
  - R/W
  - USB host clock
* - 13
  - SERCD
  - R/W
  - Serial C/D clock
* - 12
  - SERAB
  - R/W
  - Serial A/B clock
* - 11
  - RTC
  - R/W
  - Real-time clock
* - 10
  - I2C
  - R/W
  - I2C clock
* - 9:7
  - LPCS
  - R/W
  - LCD panel clock select: 000 = AHB, 001-011 = AHB/{2,4,8}, 1xx = external
* - 6
  - BBC
  - R/W
  - BBus clock (reset 1)
* - 5
  - LCC
  - R/W
  - LCD controller clock (reset 1)
* - 4
  - MCC
  - R/W
  - Memory controller clock (reset 1)
* - 3:1
  - reserved
  - —
  - reserved
* - 0
  - MACC
  - R/W
  - Ethernet MAC clock (reset 1)
```

Bit assignments match [u-boot ns9750_sys.h](#sources) (`CLOCK_BBC`=0x40, `CLOCK_LCC`=0x20,
`CLOCK_MCC`=0x10, `CLOCK_MACC`=0x01, `CLOCK_LPCS_MA`=0x380).

### Reset and Sleep Control register

**Offset 0x180.** Individual module resets, CPU sleep entry, wake-up source
enables, and (read-only) last-reset cause [HWRef p.177-179](#sources).

```{list-table} Reset and Sleep Control (0x180) [HWRef p.177-179](#sources)
:header-rows: 1
:widths: 12 14 12 62

* - Bits
  - Field
  - Access
  - Meaning
* - 31:27
  - reserved
  - —
  - reserved
* - 26:24
  - RSTAT
  - R
  - Last reset cause: 001 = reset_n, 010 = sreset_n, 011 = PLL change, 100 = watchdog, 101 = AHB monitor
* - 23:22
  - reserved
  - —
  - reserved
* - 21
  - BBW
  - R/W
  - Wake on BBus aggregate interrupt
* - 20
  - I2CW
  - R/W
  - Wake on I2C interrupt
* - 19
  - CSE
  - R/W
  - CPU sleep enable (stop CPU clock; stop other clocks first)
* - 18
  - SMWE
  - R/W
  - Wake on serial character match
* - 17
  - EWE
  - R/W
  - Wake on Ethernet packet
* - 16
  - EI0WE
  - R/W
  - Wake on external interrupt 0
* - 15:7
  - reserved
  - —
  - reserved
* - 6
  - BBT
  - R/W
  - BBus top: 0 = reset, 1 = enabled (reset 1)
* - 5
  - LCDC
  - R/W
  - LCD controller: 0 = reset, 1 = enabled (reset 1)
* - 4
  - MEMC
  - R/W
  - Memory controller: 0 = reset, 1 = enabled (reset 1)
* - 3:2
  - reserved
  - —
  - reserved
* - 1
  - reserved
  - R/W
  - write 0
* - 0
  - MACM
  - R/W
  - Ethernet MAC: 0 = reset, 1 = enabled (reset 1)
```

Field bits match [u-boot ns9750_sys.h](#sources) (`RESET_CSE`=0x00080000, `RESET_BBT`=0x40,
`RESET_MEMC`=0x10, `RESET_MACM`=0x01).

### Miscellaneous System Config and Status register

**Offset 0x184.** Revision/ID, strap status, and the CPU-visible **endian bit
ENDM** [HWRef p.179-181](#sources).

```{list-table} Misc System Config and Status (0x184) [HWRef p.179-181](#sources)
:header-rows: 1
:widths: 12 14 12 62

* - Bits
  - Field
  - Access
  - Meaning
* - 31:24
  - REV
  - R
  - Hardware revision
* - 23:16
  - ID
  - R
  - Chip identification (reset 0x1)
* - 15:12
  - reserved
  - —
  - reserved
* - 11
  - BMM
  - R
  - Boot memory mode (0 = SDRAM via SPI-EEPROM, 1 = flash/ROM); from reset_done strap
* - 10
  - CS1DB
  - R
  - CS1 byte-lane/write-enable strap status
* - 9:8
  - CS1DW
  - R
  - CS1 data width strap: 00 = 8-bit, 01 = 16-bit, 10 = 32-bit
* - 7:6
  - reserved
  - —
  - reserved
* - 5
  - CS1P
  - R
  - CS1 polarity strap status
* - 4
  - reserved
  - —
  - reserved
* - 3
  - ENDM
  - R/W
  - Endian mode: 0 = little, 1 = big (reset from gpio[44] strap)
* - 2:1
  - reserved
  - —
  - reserved
* - 0
  - IRAM0
  - R/W
  - Internal register access: 0 = privileged only, 1 = privileged or user (reset 1)
```

```{admonition} Endian polarity: strap vs register bit
:class: note

The bootstrap table reads gpio[44] as **0 = big / 1 = little** (p.154), while the
`ENDM` register bit reads **0 = little / 1 = big** (p.184) — the register field is
the inverse encoding of the pin. Both are as printed; the board straps gpio[44] = 0
(big-endian boot) and software later selects little-endian
[HWRef p.154, p.181][REFERENCE-MATERIAL.md]. Endianness lives in four places that
the BE→LE stub clears together: memory-controller Config bit 0, this ENDM bit,
BBus Endian Config, and CP15 R1 bit 7 [PLAN-INCREMENTAL-PORT.md](#sources).
```

### System memory chip-select base/mask registers

Four dynamic (0x1D0-0x1EC) and four static (0x1F0-0x20C) chip selects, each a
base+mask pair. In both, base bits 31:12 set the region base; mask bits 31:12 set
the size and bit 0 is the enable (minimum region 4 KB) [HWRef p.183-191](#sources).

```{list-table} Chip-select base/mask register pairs [HWRef p.183-191](#sources)
:header-rows: 1
:widths: 16 14 14 14 42

* - CS
  - Base offset
  - Mask offset
  - Default enable
  - Default range
* - Dyn 0
  - 0x1D0
  - 0x1D4
  - 1
  - 0x0000_0000-0x0FFF_FFFF
* - Dyn 1
  - 0x1D8
  - 0x1DC
  - 1
  - 0x1000_0000-0x1FFF_FFFF
* - Dyn 2
  - 0x1E0
  - 0x1E4
  - 1
  - 0x2000_0000-0x2FFF_FFFF
* - Dyn 3
  - 0x1E8
  - 0x1EC
  - 1
  - 0x3000_0000-0x3FFF_FFFF
* - Stat 0
  - 0x1F0
  - 0x1F4
  - 1
  - 0x4000_0000-0x4FFF_FFFF
* - Stat 1
  - 0x1F8
  - 0x1FC
  - 1
  - 0x5000_0000-0x5FFF_FFFF
* - Stat 2
  - 0x200
  - 0x204
  - 1
  - 0x6000_0000-0x6FFF_FFFF
* - Stat 3
  - 0x208
  - 0x20C
  - 1
  - 0x7000_0000-0x7FFF_FFFF
```

These match [mach-ns9xxx regs-sys-ns9360.h](#sources) (`SYS_SMCSDMB/DMM`=0x1d0/0x1d4,
`SYS_SMCSSMB/SMM`=0x1f0/0x1f4) and [u-boot ns9750_sys.h](#sources)
(`CS_DYN_BASE/MASK`, `CS_STATIC_BASE/MASK`). U-Boot's `dram_init` reads
`CS_DYN_MASK(0)` to size SDRAM [PLAN-INCREMENTAL-PORT.md](#sources).

### External interrupt control and RTC clock

`External Interrupt 0-3 Control` (0x214-0x220): bit 3 `STS` (raw signal), bit 2
`CLR` (write 1 then 0), bit 1 `PLTY` (polarity/edge), bit 0 `LVEDG` (0 = level,
1 = edge) [HWRef p.192-193](#sources); fields match [mach-ns9xxx](#sources) `SYS_EIC_*` and
[u-boot ns9750_sys.h](#sources) `EXT_INT_CTRL_*`.

`RTC Clock Control` (0x224): 32-bit divider that generates the 100 Hz RTC clock;
program to (PLL output frequency)/200 [HWRef p.193-194](#sources).

## Sources

Primary datasheets (in-repo, the authority for the register map):

- **NS9360 Hardware Reference**, Digi 90000675 rev J — `[HWRef p.N](#sources)`
  (`hpe-ipdu-firmware/datasheets/NS9360_HW_Reference_90000675_J.pdf`);
  online: <https://ftp1.digi.com/support/documentation/90000675_J.pdf>.
- **NS9360 Datasheet**, Digi 91001326 rev D — `[Datasheet](#sources)`
  (`hpe-ipdu-firmware/datasheets/NS9360_datasheet_91001326_D.pdf`);
  online: <https://ftp1.digi.com/support/documentation/91001326_D.pdf>.

In-repo analysis and port planning (board specifics, firmware evidence):

- `[ANALYSIS.md](#sources)` — `hpe-ipdu-firmware/ANALYSIS.md` (board inventory, NS9360 I/O
  map, firmware register usage).
- `[REFERENCE-MATERIAL.md](#sources)` — `hpe-ipdu-firmware/uboot-port/REFERENCE-MATERIAL.md`.
- `[PLAN-INCREMENTAL-PORT.md](#sources)` — `hpe-ipdu-firmware/uboot-port/PLAN-INCREMENTAL-PORT.md`
  (register quick reference and clock/baud derivation).

Independent open-source cross-reference (register names, bases, bitfields):

- `[mach-ns9xxx](#sources)` — Linux kernel `arch/arm/mach-ns9xxx` at tag v2.6.39:
  `include/mach/regs-sys-ns9360.h`, `regs-sys-common.h`, `regs-bbu.h`,
  `regs-mem.h`, `hardware.h`, `processor-ns9360.c`, `time-ns9360.c`,
  `gpio-ns9360.c`. Raw source, e.g.
  <https://raw.githubusercontent.com/torvalds/linux/v2.6.39/arch/arm/mach-ns9xxx/include/mach/regs-sys-ns9360.h>.
- `[u-boot ns9750](#sources)` — U-Boot at tag v2012.10: `include/ns9750_sys.h`,
  `ns9750_mem.h`, `ns9750_bbus.h`, `ns9750_ser.h`, `include/configs/ns9750dev.h`,
  `drivers/serial/ns9750_serial.c`. Raw source, e.g.
  <https://raw.githubusercontent.com/u-boot/u-boot/v2012.10/include/ns9750_sys.h>.
- `[u-boot ns9750_eth.h](#sources)` — the Ethernet register header is not in mainline
  U-Boot; the Digi-derived version is preserved in a mirror at
  <https://raw.githubusercontent.com/true-systems/om5p-ac-v2-unlocker/master/u-boot_mr1750/include/ns9750_eth.h>.

```{toctree}
:hidden:

soc-ns9360-memory-serial
soc-ns9360-io
soc-ns9360-secondary
```
