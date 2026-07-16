# AST2050 UARTs, interrupts (VIC) & timers

Register-by-register reference for the Aspeed **AST2050 (G3)** CPU-facing
peripherals a from-scratch OpenBMC / u-bmc / Zephyr port must drive directly: the
console **UARTs**, the **Vector Interrupt Controller (VIC)**, and the **timers**.
The PCI/VGA/USB endpoint and the AHB debug bridges are on
{doc}`pcie-vga-usb-bridges`.

Citations use these short forms: [DS §N p.P](#sources) = the *AST2050/AST1100 A3
Datasheet V1.05* (25 May 2010), chapter N / printed page P; repository filenames
(e.g. [g3-vic patch](#sources), [TIMER-RCA](#sources), [P2A-BOOT](#sources), [CULVERT-G3](#sources),
[`hwreg.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h), [`ast2050.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/ast2050.h)) = hardware-verified reverse-engineering in the
program repo; named URLs = external cross-references (see **Sources**). Every
load-bearing value is backed by at least two of these.

```{admonition} G3 vs G4+ — the register maps are NOT the same
:class: important

The AST2050 is *not* mainline-Linux-supported (the earliest Aspeed in mainline is
the AST2400 / "G4"). Several G3 blocks sit at **different offsets** from their
G4+ equivalents, and drivers that assume the G4 layout silently write to
nonexistent registers. The one that bit this project hardest: the **VIC** is a
compact 32-source map at `0x1E6C0000` (§16), whereas the AST2400+ "new" VIC lives
at `0x1E6C0080` with an interleaved layout that mainline [`irq-aspeed-vic.c`](https://github.com/torvalds/linux/blob/master/drivers/irqchip/irq-aspeed-vic.c)
drives — its writes miss the G3 entirely, so no interrupt is ever enabled and the
timer clockevent is dead. [TIMER-RCA](#sources), [g3-vic patch](#sources)
```

## Address map & clock/reset context

ARM address-space decode (relevant slices of the full table). All peripheral
register blocks are byte/half/word accessible unless noted. [DS §9 p.97](#sources)

```{list-table} ARM address space — peripheral blocks used here
:header-rows: 1
:widths: 26 12 62

* - Address range
  - Size
  - IP module
* - `0x00000000–0x01FFFFFF`
  - 32M
  - Static Memory (boot-up default = flash CE2 alias); becomes **SDRAM after re-map** (AHBC8C[0]=1)
* - `0x14000000` (in `0x1000_0000–0x15FF_FFFF`)
  - 96M
  - Static Memory window; CE2 SPI-NOR boot flash decodes here [CULVERT-G3](#sources)
* - `0x16000000–0x17FFFFFF`
  - 32M
  - Static Memory Controller (SMC) registers
* - `0x1E600000–0x1E61FFFF`
  - 128K
  - **AHB Bus Controller (AHBC)** — remap + AHB-unlock key
* - `0x1E6A0000–0x1E6BFFFF`
  - 128K
  - **USB2.0 Virtual Hub (device) at `0x1E6A0000`** + **USB1.1 UHCI host at
    `0x1E6B0000`** (two distinct blocks in this window; no EHCI host on G3 —
    see {doc}`display-usb`)
* - `0x1E6C0000–0x1E6DFFFF`
  - 128K
  - **Vector Interrupt Controller (VIC)**
* - `0x1E6E0000–0x1E6E0FFF`
  - 4K
  - SDRAM Controller (MMC)
* - `0x1E6E2000–0x1E6E2FFF`
  - 4K
  - **System Control Unit (SCU)**
* - `0x1E700000–0x1E71FFFF`
  - 128K
  - **Video Engine**
* - `0x1E720000–0x1E73FFFF`
  - 128K
  - **AHB-to-PCI (P-Bus) Bridge Controller (A2P)**
* - `0x1E780000–0x1E780FFF`
  - 4K
  - GPIO Controller
* - `0x1E781000–0x1E781FFF`
  - 4K
  - Real-Time Clock (RTC)
* - `0x1E782000–0x1E782FFF`
  - 4K
  - **Timer #1/#2/#3 Controller**
* - `0x1E783000–0x1E783FFF`
  - 4K
  - **UART #1**
* - `0x1E784000–0x1E784FFF`
  - 4K
  - **UART #2**
* - `0x1E785000–0x1E785FFF`
  - 4K
  - Watchdog Timer (WDT)
* - `0x1E787000–0x1E787FFF`
  - 4K
  - Virtual UART (VUART)
* - `0x1E788000–0x1E788FFF`
  - 4K
  - Pass-through UART (PUART)
* - `0x1E789000–0x1E789FFF`
  - 4K
  - **LPC Controller** (holds the iLPC-to-AHB bridge regs)
* - `0x40000000–0x4FFFFFFF`
  - 256M
  - SDRAM (DDR2; 64 MB populated on the KGPE-D16 BMC) [P2A-BOOT](#sources)
```

```{admonition} Silicon identity
:class: note

`SCU7C` (Silicon Revision ID, `0x1E6E207C`) reads **`0x00000202`** on the
KGPE-D16 board = AST2050-A2/A3 (and AST1100-A2/A3 share the same code).
[DS §18 p.220](#sources), [CULVERT-G3](#sources)
```

Clock gates and PLLs relevant to these blocks live in the SCU
(`base 0x1E6E2000`), covered in the {doc}`SCU register reference <scu-clock-reset>` and summarised in the SCU-posture table on {doc}`pcie-vga-usb-bridges`.
Key gates: `SCU0C[15]` UARTCLK, `SCU0C[5]` VGA DCLK, `SCU0C[4]` PCI-slave BCLK,
`SCU0C[14]` USB2.0 clock, `SCU0C[0]` Video-Engine ECLK. [DS §18 p.209-210](#sources)

---

## UARTs (16550)

The AST2050 integrates **two** 16550-compatible UARTs, each with a 16×8
transmit/receive FIFO and a programmable baud generator, plus the LPC-side
Virtual UART / Pass-through UART (`0x1E787000` / `0x1E788000`, §29 — not detailed
here). [DS §26 p.279](#sources), [`ast2050.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/ast2050.h)

```{list-table} UART instances
:header-rows: 1
:widths: 16 22 62

* - Instance
  - Base address
  - Notes
* - **UART1**
  - `0x1E783000`
  - Dedicated flow-control pins. Reserved to UART1 in rev A1; can be muxed to
    UART2 pins via `SCU2C[14]` in rev A2+. **Not physically connected** on the
    KGPE-D16 BMC debug header (0 edges when driven). [P2A-BOOT](#sources)
* - **UART2**
  - `0x1E784000`
  - Flow-control pins shared with GPIO. **This is the KGPE-D16 BMC console.**
    Raptor's U-Boot `.Done` debug output goes here (`CONFIG_CONS_INDEX 2`).
    [`ast2050.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/ast2050.h), [P2A-BOOT](#sources)
```

The two units share one register layout; the register address is
`base + offset`. [DS §26.3 p.280](#sources)

### UART register map

```{list-table} UART register set (offsets from UART base)
:header-rows: 1
:widths: 10 16 8 12 54

* - Offset
  - Register
  - DLAB
  - Access
  - Function
* - `0x00`
  - **RBR**
  - 0
  - R
  - Receive Buffer Register (head of RX FIFO when FIFOs on). Valid only when `LSR.DR=1`.
* - `0x00`
  - **THR**
  - 0
  - W
  - Transmit Holding Register. Write when `LSR.THRE=1`; up to 16 bytes with FIFO on.
* - `0x00`
  - **DLL**
  - 1
  - RW
  - Divisor Latch Low (LSB of baud divisor).
* - `0x04`
  - **IER**
  - 0
  - RW
  - Interrupt Enable Register.
* - `0x04`
  - **DLH**
  - 1
  - RW
  - Divisor Latch High (MSB of baud divisor).
* - `0x08`
  - **IIR**
  - x
  - R
  - Interrupt Identity Register (read).
* - `0x08`
  - **FCR**
  - x
  - W
  - FIFO Control Register (write).
* - `0x0C`
  - **LCR**
  - x
  - RW
  - Line Control Register (holds the DLAB bit, bit 7).
* - `0x10`
  - **MCR**
  - x
  - RW
  - Modem Control Register.
* - `0x14`
  - **LSR**
  - x
  - R
  - Line Status Register (init `0x60`).
* - `0x18`
  - **MSR**
  - x
  - R
  - Modem Status Register.
* - `0x1C`
  - **SCR**
  - x
  - RW
  - Scratch Register (8-bit scratchpad, no HW effect).
```

Bits `[31:8]` of every UART register are Reserved (0). The DLL/DLH latches
**alias** RBR/THR/IER at offsets `0x00`/`0x04` and are selected by `LCR[7]`
(DLAB); restore `LCR[7]=0` after setting the divisor to regain access to the
other registers. [DS §26.3.1 p.285](#sources)

### Bitfield detail

```{list-table} IER (0x04, DLAB=0)
:header-rows: 1
:widths: 12 20 68

* - Bit
  - Name
  - Meaning
* - 7
  - PTIME
  - Enable programmable THRE interrupt mode (1=enable).
* - 6:4
  - —
  - Reserved (0)
* - 3
  - EDSSI
  - Enable Modem Status interrupt
* - 2
  - ELSI
  - Enable Receiver Line Status interrupt
* - 1
  - ETBEI
  - Enable Transmitter Holding Register Empty interrupt
* - 0
  - ERBFI
  - Enable Received Data Available interrupt
```

```{list-table} IIR (read, 0x08) — init 0x01
:header-rows: 1
:widths: 12 20 68

* - Bit
  - Name
  - Meaning
* - 7:6
  - FIFO-enabled
  - `00`=FIFOs disabled, `11`=FIFOs enabled
* - 5:4
  - —
  - Reserved (0)
* - 3:1
  - Interrupt ID
  - `011`=Rx line status (highest) · `010`=Rx data available · `110`=char timeout · `001`=THR empty · `000`=modem status (lowest)
* - 0
  - Pending
  - `0`=an interrupt is pending, `1`=none pending
```

```{list-table} FCR (write, 0x08)
:header-rows: 1
:widths: 12 22 66

* - Bit
  - Name
  - Meaning
* - 7:6
  - RX trigger
  - `00`=1 · `01`=4 · `10`=8 · `11`=14 bytes received
* - 5:4
  - TX trigger
  - `00`=empty · `01`=2 · `10`=1/4 · `11`=1/2 full
* - 3
  - —
  - Reserved (0)
* - 2
  - TX FIFO reset
  - Write 1 clears the TX FIFO
* - 1
  - RX FIFO reset
  - Write 1 clears the RX FIFO
* - 0
  - FIFO enable
  - `0`=disable, `1`=enable (changing this always resets the FIFOs)
```

```{list-table} LCR (0x0C)
:header-rows: 1
:widths: 12 16 72

* - Bit
  - Name
  - Meaning
* - 7
  - DLAB
  - Divisor Latch Access: `1`=access DLL/DLH at `0x00`/`0x04`; must be `0` for normal registers
* - 6
  - Break
  - `1`=force serial-out to break (logic 0)
* - 5
  - —
  - Reserved (0)
* - 4
  - EPS
  - Parity select: `0`=odd, `1`=even
* - 3
  - PEN
  - Parity enable
* - 2
  - STOP
  - Stop bits: `0`=1, `1`=1.5 (5-bit char) / 2 (otherwise)
* - 1:0
  - CLS
  - Char length: `00`=5 · `01`=6 · `10`=7 · `11`=8 bits
```

For 8N1 set `LCR=0x03`; to enter the divisor latch, `LCR=0x83`. [P2A-BOOT](#sources)

```{list-table} MCR (0x10)
:header-rows: 1
:widths: 12 16 72

* - Bit
  - Name
  - Meaning
* - 31:5
  - —
  - Reserved (0)
* - 4
  - Loopback
  - `1`=diagnostic loopback (TXD forced high; DTR→DSR, RTS→CTS, Out1→RI, Out2→DCD internally)
* - 3
  - Out2
  - In loopback, drives DCD input
* - 2
  - Out1
  - In loopback, drives RI input
* - 1
  - RTS
  - Request To Send (`1`=nRTS asserted low)
* - 0
  - DTR
  - Data Terminal Ready (`1`=nDTR asserted low)
```

```{list-table} LSR (0x14) — init 0x60
:header-rows: 1
:widths: 12 14 74

* - Bit
  - Name
  - Meaning
* - 7
  - Error-in-FIFO
  - ≥1 parity/framing/break error in the RX FIFO (FIFO mode); cleared on LSR read
* - 6
  - TEMT
  - THR/FIFO **and** shift register both empty
* - 5
  - THRE
  - Transmitter Holding Register empty (ok to write THR)
* - 4
  - BI
  - Break interrupt
* - 3
  - FE
  - Framing error
* - 2
  - PE
  - Parity error
* - 1
  - OE
  - Overrun error
* - 0
  - DR
  - Data ready (≥1 char in RBR/RX FIFO)
```

```{list-table} MSR (0x18)
:header-rows: 1
:widths: 12 14 74

* - Bit
  - Name
  - Meaning
* - 7
  - nDCD
  - Complement of nDCD input (or Out2 in loopback)
* - 6
  - nRI
  - Complement of nRI input (or Out1 in loopback)
* - 5
  - nDSR
  - Complement of nDSR input (or DTR in loopback)
* - 4
  - nCTS
  - Complement of nCTS input (or RTS in loopback)
* - 3
  - DDCD
  - Delta Data Carrier Detect (changed since last MSR read)
* - 2
  - TERI
  - Trailing-edge Ring Indicator
* - 1
  - DDSR
  - Delta Data Set Ready
* - 0
  - DCTS
  - Delta Clear To Send
```

`DLL` (0x00, DLAB=1) and `DLH` (0x04, DLAB=1) each carry 8 bits `[7:0]` of the
16-bit baud divisor; `[31:8]` Reserved. Write DLH (MSB) first, then DLL (LSB) —
the internal counter starts when the DLL LSB is written. [DS §26.3.1 p.285-286](#sources)

### Baud rate and the UART clock gate

The reference clock is 24 MHz (shared with the USB reference). [DS §18 p.212](#sources)

$$
\text{Baud} = \frac{24\,\text{MHz}}{16 \times \text{divisor}}
$$

[DS §26.3.1 p.285](#sources)

```{list-table} Divisor examples (24 MHz UARTCLK, SCU2C[12]=0)
:header-rows: 1
:widths: 18 18 20 44

* - Baud
  - Divisor
  - DLH / DLL
  - Where used
* - **1200**
  - **1250** (`0x04E2`)
  - `0x04` / `0xE2`
  - **KGPE-D16 BMC console (UART2)** as observed on the rig [P2A-BOOT](#sources) — but the
    firmware config is 115200 (see the baud-discrepancy note below)
* - 115200
  - 13 (`0x000D`)
  - `0x00` / `0x0D`
  - Raptor U-Boot default `CONFIG_BAUDRATE` [`ast2050.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/ast2050.h), [P2A-BOOT](#sources)
```

```{admonition} Two things that make the console look dead
:class: warning

1. **Baud (unresolved)** — the Raptor firmware configures UART2 at **115200**
   (`console=ttyS1,115200`; 38400 for DRAM-init), but the rig bring-up observed
   the console at **1200** (divisor 1250). Both are documented; probe before
   relying on one. [P2A-BOOT](#sources), [`ast2050.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/ast2050.h) (see {doc}`../../systems/kgpe-d16` §2.2)
2. **Clock gate** — the UART clock is gated by `SCU0C[15]` **Stop UARTCLK**
   (`0`=running, `1`=stopped; default running). It must be running (and
   `SCU2C[12]=0` for the plain 24 MHz reference) for either UART to clock out.
   [DS §18 p.210, p.213](#sources), [P2A-BOOT](#sources)
```

`SCU2C` (Misc. Control) also holds the UART routing/clock-select bits
(rev A2+ additions): [DS §18 p.213](#sources)

```{list-table} SCU2C bits affecting the UARTs
:header-rows: 1
:widths: 14 62 24

* - Bit
  - Function
  - Reset
* - 15
  - Enable internal link UART1↔UART2 (UART1 pins driven from UART2 signals)
  - 0
* - 14
  - Enable MUX of UART1 pins (UART1+UART2 share the UART1 pins/connector)
  - 0
* - 12
  - Reference-clock divider: `0` → $\text{baud} = \frac{24\,\text{MHz}}{16 \cdot \text{div}}$; `1` → $\text{baud} = \frac{24\,\text{MHz}/13}{16 \cdot \text{div}}$
  - 0
```

UART1/UART2 also raise the two VIC "alarm" interrupts (INT#9 / INT#10 —
level-high; see the [interrupt source table](#interrupt-source-table-table-36)).

---

## Interrupt controller (VIC)

The G3 VIC is an AMBA slave on the AHB bus that interrupts the ARM926EJ-S with
two priority classes — **FIQ** (high priority / low latency) and **IRQ**
(general). It supports **32** interrupt sources, each independently programmable
for edge/level and polarity. [DS §16.1 p.179](#sources)

```{admonition} Base address 0x1E6C0000 — compact, non-interleaved
:class: important

`Base of VIC = 0x1E6C0000`; physical = base + offset. [DS §16.1 p.179](#sources),
[`hwreg.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h) (`AST_IC_BASE`). This is a **single 32-bit word per register**
(non-interleaved), unlike the AST2400+ "new" VIC (interleaved high/low at
`0x1E6C0080`). Using the G4 driver/offsets on the G3 enables **no** interrupts —
the timer clockevent never fires, `hrtimers` hang, and boot stalls at
`local_irq_enable()`. [TIMER-RCA](#sources), [g3-vic patch](#sources)
```

### VIC register map

```{list-table} VIC registers (offsets from 0x1E6C0000)
:header-rows: 1
:widths: 10 12 10 68

* - Offset
  - Name
  - Access
  - Function
* - `0x00`
  - **VIC00** IRQ_STATUS
  - R
  - IRQ status *after* masking by VIC10/VIC0C; `1`=active, interrupts the CPU
* - `0x04`
  - **VIC04** FIQ_STATUS
  - R
  - FIQ status after masking by VIC10/VIC0C
* - `0x08`
  - **VIC08** RAW_STATUS
  - R
  - Raw interrupt status *before* masking
* - `0x0C`
  - **VIC0C** INT_SELECT
  - RW
  - Per source: `1`=route to FIQ, `0`=route to IRQ
* - `0x10`
  - **VIC10** INT_ENABLE
  - RW
  - Read = enable state; write `1` = enable source (write `0` = no effect)
* - `0x14`
  - **VIC14** INT_ENABLE_CLR
  - W
  - Write `1` clears the matching VIC10 bit (disable source)
* - `0x18`
  - **VIC18** SOFT_INT
  - RW
  - Write `1` raises a software interrupt for that source (before masking)
* - `0x1C`
  - **VIC1C** SOFT_INT_CLR
  - W
  - Write `1` clears the matching VIC18 bit
* - `0x20`
  - **VIC20** PROTECT
  - RW
  - Bit 0: `1` = only privileged-mode accesses may touch VIC regs (bits `31:1` reserved)
* - `0x24`
  - **VIC24** INT_SENSE
  - RW
  - Per source: `1`=level-sensitive, `0`=edge-triggered
* - `0x28`
  - **VIC28** INT_DUAL_EDGE
  - RW
  - Per source: `1`=both edges, `0`=single edge (ignored when SENSE=level)
* - `0x2C`
  - **VIC2C** INT_EVENT
  - RW
  - Per source: `1`=high-level / rising edge, `0`=low-level / falling edge
* - `0x30`
  - **VIC30** *Reserved*
  - —
  - **Reserved — do not access.** Any read/write "can cause incorrect operation" (init = X)
* - `0x34`
  - *(gap)*
  - —
  - **Undefined / reserved** (no register between VIC30 and VIC38)
* - `0x38`
  - **VIC38** EDGE_CLR
  - W
  - Write `1` clears the edge-detection latch for that source (W1C). For edge sources, clear here *before* enabling in VIC10, else a stale latched status re-fires
```

All defined registers reset to 0 (VIC30 = X). [DS §16.3 p.180-182](#sources)

The compact map corresponds one-to-one to the classic **ARM PrimeCell PL190**
VIC base registers (VICIRQStatus/VICFIQStatus/VICRawIntr/VICIntSelect/
VICIntEnable/VICIntEnClear/VICSoftInt/VICSoftIntClear/VICProtection), *plus*
Aspeed's programmable **SENSE/DUAL/EVENT** and the **EDGE_CLR** at `0x38`.
Raptor's U-Boot [`platform.S`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/platform.S) already drives this base — it polls Timer3 status at
`0x1E6C0008` and clears it via `0x1E6C0038`. [TIMER-RCA](#sources), [`hwreg.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h),
[ARM PL190 TRM][pl190]

### Interrupt source table (Table 36)

The 32 sources and their **hardware-fixed trigger attributes**. This table drives
the SENSE/EVENT/DUAL configuration below. [DS §10 p.99](#sources)

```{list-table} AST2050 interrupt sources — Table 36
:header-rows: 1
:widths: 8 42 50

* - INT#
  - Source
  - Attribute
* - 0
  - *Reserved*
  - Reserved
* - 1
  - MIC (Memory Integrity Check)
  - level-sensitive, high
* - 2
  - MAC1 (Ethernet)
  - level-sensitive, high
* - 3
  - MAC2 (Ethernet)
  - level-sensitive, high
* - 4
  - Crypto (HACE)
  - level-sensitive, high
* - 5
  - USB 2.0
  - level-sensitive, high
* - 6
  - MDMA
  - level-sensitive, high
* - 7
  - Video Engine
  - level-sensitive, high
* - 8
  - LPC
  - level-sensitive, high
* - 9
  - **UART1 alarm**
  - level-sensitive, high
* - 10
  - **UART2 alarm**
  - level-sensitive, high
* - 11
  - *Reserved*
  - Reserved
* - 12
  - I2C / SMBus
  - level-sensitive, high
* - 13
  - *Reserved*
  - Reserved
* - 14
  - *Reserved*
  - Reserved
* - 15
  - PECI
  - level-sensitive, high
* - 16
  - **Timer #1 (1st counter)**
  - **rising-edge**
* - 17
  - **Timer #2 (2nd counter)**
  - **rising-edge**
* - 18
  - **Timer #3 (3rd counter)**
  - **rising-edge**
* - 19
  - SMC (static memory / flash)
  - level-sensitive, high
* - 20
  - GPIO
  - level-sensitive, high
* - 21
  - SCU
  - level-sensitive, high
* - 22
  - RTC second
  - edge-trigger, both edges
* - 23
  - RTC day
  - edge-trigger, both edges
* - 24
  - RTC hour
  - edge-trigger, both edges
* - 25
  - RTC minute
  - edge-trigger, both edges
* - 26
  - RTC alarm
  - edge-trigger, both edges
* - 27
  - **WDT alarm**
  - **rising-edge**
* - 28
  - Tachometer
  - level-sensitive, high
* - 29
  - *Reserved*
  - Reserved
* - 30
  - *Reserved*
  - Reserved
* - 31
  - AHBC (AHB controller)
  - level-sensitive, high
```

```{admonition} The timer interrupt is a rising-edge pulse — polarity matters
:class: note

INT#16–18 are **rising-edge**. The FTTMR010 asserts a brief rising edge at
match (count reaches the match value / zero) and holds the line until the ISR
acks it via **VIC38**. If the VIC is left at its power-on default (SENSE/EVENT
all 0 → *falling*-edge on every source), the timer edge is never latched and the
clockevent is dead. The reset-boot path has no vendor firmware to program the
VIC, so the driver must set it up itself. [TIMER-RCA](#sources), [g3-vic patch](#sources)
```

### Config values and their derivation

From Table 36, with `SENSE 1=level`, `EVENT 1=high/rising`, `DUAL 1=both-edge`:
[g3-vic patch](#sources)

```{list-table} G3 VIC power-on configuration (driver-programmed)
:header-rows: 1
:widths: 14 20 26 40

* - Register
  - Value
  - Sources set
  - Derivation
* - **VIC24** SENSE
  - `0x903897FE`
  - level-high: 1–10, 12, 15, 19, 20, 21, 28, 31
  - all "level-sensitive, high" rows of Table 36
* - **VIC2C** EVENT
  - `0x983F97FE`
  - level-high **+** rising: 16, 17, 18 (timers), 27 (WDT)
  - level-high sources, plus the rising-edge timer/WDT bits
* - **VIC28** DUAL
  - `0x07C00000`
  - both-edge: 22–26 (RTC)
  - the five RTC "both edges" rows of Table 36
```

Bit-sum check for `SENSE`: bits 1–10 (`0x7FE`) + 12 (`0x1000`) + 15 (`0x8000`) +
19 (`0x80000`) + 20 (`0x100000`) + 21 (`0x200000`) + 28 (`0x10000000`) + 31
(`0x80000000`) = **`0x903897FE`**. `EVENT` adds bits 16/17/18 (`0x70000`) + 27
(`0x08000000`) → **`0x983F97FE`**. `DUAL` = bits 22–26 = **`0x07C00000`**.
(Reserved sources 0, 11, 13, 14, 29, 30 stay 0 in all three.) [g3-vic patch](#sources)

### Bring-up sequence (no firmware present)

The verified G3 VIC init (`g3vic_init_hw`): [g3-vic patch](#sources)

1. `VIC14 = 0xFFFFFFFF` (disable all) and `VIC1C = 0xFFFFFFFF` (clear soft ints).
2. `VIC0C = 0` (all sources as IRQ, none FIQ).
3. `VIC24 = 0x903897FE`, `VIC2C = 0x983F97FE`, `VIC28 = 0x07C00000`.
4. `VIC38 = 0xFFFFFFFF` (clear every edge-detection latch before enabling).
5. Per source: enable with `VIC10 = (1<<hwirq)`, mask with `VIC14 = (1<<hwirq)`;
   in the handler, for edge sources ack by writing `VIC38 = (1<<hwirq)`; read
   pending from `VIC00` and dispatch `ffs(status)-1`.

Hardware result: clockevent ticks ~1 kHz, `eth0` links with real interrupts,
kernel IP-config completes. [TIMER-RCA](#sources), [g3-vic patch](#sources)

```{admonition} The P2A "VGA" window is BLIND to the VIC block
:class: warning

The Aspeed P2A bridge **filters the `0x1E6C0000` interrupt-controller block out of
the VGA window**: over `culvert p2a vga`, the whole `0x1E6C0000–0x1E6C0070` range
reads `0x00000000` and writes go nowhere — regardless of the real VIC state —
while P2A concurrently reads/writes DRAM, SCU and the timer fine. Every VIC
observation must come from the **ARM core itself** (in-band), never from P2A; a
long stretch of this project's early "the timer IRQ never reaches the VIC"
analysis was reading phantom zeros. [TIMER-RCA](#sources)
```

DT binding used on hardware: `compatible = "aspeed,ast2050-vic"`,
`reg = <0x1E6C0000 0x1000>`, `#interrupt-cells = <1>` (or two-cell via
`irq_domain_xlate_onetwocell`). [g3-vic patch](#sources)

---

## Timers (FTTMR010)

Three independent 32-bit **down-counters** (Faraday FTTMR010 block). Each counter
has a reload value, two match registers, and a status (current-count) register,
plus one shared control register. Interrupts can be generated on match and/or on
overflow (count reaching zero → reload). The clock source is per-counter
selectable: APB `PCLK` or an external 1 MHz. [DS §25.1-25.2 p.275](#sources),
[Faraday FTTMR010 / timer-fttmr010.c][fttmr]

```{admonition} Base address 0x1E782000
:class: note

`Base of Timer = 0x1E782000`; physical = base + offset. [DS §25.3 p.275](#sources),
[`hwreg.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h) (`AST_TIMER_BASE`). Raptor's U-Boot uses Timer1 here with the 1 MHz
external clock (`CONFIG_SYS_HZ = 1e6`). [`ast2050.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/ast2050.h)
```

### Timer register map

```{list-table} Timer registers (offsets from 0x1E782000)
:header-rows: 1
:widths: 10 14 10 66

* - Offset
  - Name
  - Access
  - Function
* - `0x00`
  - **TMC00**
  - RW
  - Counter #1 status (current count; decrements when TMC30[0]=1; CPU may modify anytime)
* - `0x04`
  - **TMC04**
  - RW
  - Counter #1 reload value (loaded on decrement to zero)
* - `0x08`
  - **TMC08**
  - RW
  - Counter #1 First Match — edge-triggered interrupt when count == this
* - `0x0C`
  - **TMC0C**
  - RW
  - Counter #1 Second Match — edge-triggered interrupt when count == this
* - `0x10`
  - **TMC10**
  - RW
  - Counter #2 status
* - `0x14`
  - **TMC14**
  - RW
  - Counter #2 reload value
* - `0x18`
  - **TMC18**
  - RW
  - Counter #2 First Match
* - `0x1C`
  - **TMC1C**
  - RW
  - Counter #2 Second Match
* - `0x20`
  - **TMC20**
  - RW
  - Counter #3 status
* - `0x24`
  - **TMC24**
  - RW
  - Counter #3 reload value
* - `0x28`
  - **TMC28**
  - RW
  - Counter #3 First Match
* - `0x2C`
  - **TMC2C**
  - RW
  - Counter #3 Second Match
* - `0x30`
  - **TMC30**
  - RW
  - Combined control register (per-counter enable / clock-select / overflow-int)
```

Offsets `0x34`–end of the 4K block are unused / reserved. [DS §25.3 p.275-277](#sources)

### TMC30 — control register

```{list-table} TMC30 Control Register (0x30)
:header-rows: 1
:widths: 12 42 46

* - Bit
  - Name
  - Meaning
* - 31:11
  - —
  - Reserved (0)
* - 10
  - T3 overflow-int enable
  - `1`=interrupt on Counter #3 overflow
* - 9
  - T3 clock select
  - `0`=APB PCLK, `1`=external 1 MHz
* - 8
  - T3 enable
  - `1`=run Counter #3 (disable gates count/reload/interrupt)
* - 7
  - —
  - Reserved (0)
* - 6
  - T2 overflow-int enable
  - `1`=interrupt on Counter #2 overflow
* - 5
  - T2 clock select
  - `0`=APB PCLK, `1`=external 1 MHz
* - 4
  - T2 enable
  - `1`=run Counter #2
* - 3
  - —
  - Reserved (0)
* - 2
  - T1 overflow-int enable
  - `1`=interrupt on Counter #1 overflow
* - 1
  - T1 clock select
  - `0`=APB PCLK, `1`=external 1 MHz
* - 0
  - T1 enable
  - `1`=run Counter #1
```

### Operation and the match / one-pulse behaviour

Programming sequence (per counter): set **Reload**, set the overflow-int enable
(`TMC30[2/6/10]` if using overflow), then **enable** the counter. When Reload = N,
the count sequence is N, …, 2, 1, 0, N, …. A **match** or reaching **zero**
generates an **edge-triggered** interrupt to the CPU — which is exactly why the
VIC lists timer INT#16–18 as *rising-edge*. [DS §25.4 p.278](#sources),
[timer-fttmr010.c][fttmr]

```{admonition} Programming notes (two real footguns)
:class: warning

- **`TMC30[2]` (the "interrupt enable") does not gate the *match* interrupt** —
  it only gates the *overflow* interrupt. If you are not using the match
  registers, write them to `0xFFFFFFFF` so they never coincidentally fire.
  [DS §25.5 p.278](#sources)
- The clockevent uses a **match at 0** producing one rising pulse per period; the
  VIC must be edge/rising for INT#16 and the ISR must ack via `VIC38`, or the
  pulse is lost. [TIMER-RCA](#sources)
```

Timekeeping split observed on hardware: the FTTMR010 registers a read-based
**clocksource** on TIMER2 (works with no interrupts) and a **clockevent** on
TIMER1 (needs the VIC edge path). Early boot reaches userspace on the clocksource
+ `udelay`; the first `hrtimer`/`usleep_range` hangs until the clockevent's VIC
delivery is fixed. [TIMER-RCA](#sources)

---

## See also

**Related pages**

- {doc}`/hardware/registers/pcie-vga-usb-bridges` — the sibling host-facing endpoint and AHB debug bridges split off from this page
- {doc}`/hardware/registers/scu-clock-reset` — PCLK/UARTCLK generation and the watchdog's `HRST_N` reset domain
- {doc}`/hardware/registers/control-blocks` — the VUART/PUART 16550 variants and the RTC alarms that raise VIC lines
- {doc}`/hardware/soc-ast2050` — the compact G3 VIC and why the mainline G4 VIC driver misses it

**External references**

- [Linux serial/TTY driver API](https://docs.kernel.org/driver-api/serial/index.html) — the serial-core the 16550 UART driver sits under
- [Linux IRQ handling (core API)](https://docs.kernel.org/core-api/irq/index.html) — irqchip/irqdomain model behind a VIC driver
- [8250/16550 UART device-tree binding](https://github.com/torvalds/linux/blob/master/Documentation/devicetree/bindings/serial/8250.yaml) — the binding for this 16550-compatible UART
- [QEMU Aspeed SoC documentation](https://www.qemu.org/docs/master/system/arm/aspeed.html) — how QEMU models the Aspeed UART/VIC/timer blocks

## Sources

- **[AST2050/AST1100 A3 Datasheet, V1.05](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/datasheets/aspeed/AST2050_AST1100_A3_Datasheet_V1.05.pdf)** (25 May 2010), in-repo PDF. Chapters
  used here: §9 ARM Address Space (p.97-98), §10 Interrupt Source Table / Table 36
  (p.99), §16 Interrupt Controller / VIC (p.179-182), §18 SCU (p.204-220), §25
  Timer Controller (p.275-278), §26 UART 16550 (p.279-286).
- **[`0003-irqchip-add-aspeed-ast2050-vic-g3.patch`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/kernel/patches/0003-irqchip-add-aspeed-ast2050-vic-g3.patch)** — hardware-verified G3 VIC
  driver: the compact register map, the SENSE/EVENT/DUAL config values and their
  Table-36 derivation, edge-ack via VIC38.
- **[`TIMER-CLOCKEVENT-ROOT-CAUSE.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/TIMER-CLOCKEVENT-ROOT-CAUSE.md)** — hardware-verified VIC/timer analysis and
  the P2A-blind-to-VIC finding.
- **[`P2A-DRAM-BOOT-SEQUENCE.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/P2A-DRAM-BOOT-SEQUENCE.md)** — UART2 console at 1200 baud; `SCU70[1:0]`.
- **[`hwreg.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h), [`ast2050.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/ast2050.h)** — Raptor Engineering reverse-engineered register
  bases (VIC `0x1E6C0000`, Timer `0x1E782000`, UART1/2).
- [ARM PrimeCell PL190 VIC TRM (DDI0181)][pl190] and the [ARM VIC DT binding][vicdt]
  — confirm the PL190 base-register layout the G3 compact map follows.
- [Linux `timer-fttmr010.c`][fttmr] and the [`faraday,fttmr010` DT binding][fttmrdt]
  — FTTMR010 match/reload/count semantics.
- [Mainline `irq-aspeed-vic.c`][aspeedvic] — the AST2400+ interleaved VIC that does
  *not* match the G3.

[pl190]: https://developer.arm.com/documentation/ddi0181/latest/
[vicdt]: https://www.kernel.org/doc/Documentation/devicetree/bindings/interrupt-controller/arm,vic.txt
[fttmr]: https://github.com/torvalds/linux/blob/master/drivers/clocksource/timer-fttmr010.c
[fttmrdt]: https://github.com/torvalds/linux/blob/master/Documentation/devicetree/bindings/timer/faraday%2Cfttmr010.yaml
[aspeedvic]: https://github.com/torvalds/linux/blob/master/drivers/irqchip/irq-aspeed-vic.c
