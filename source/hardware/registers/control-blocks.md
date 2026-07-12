# AST2050 PWM/fan-tach, RTC, PECI & virtual UARTs

This is a register-by-register reference for four on-chip control blocks of the
Aspeed **AST2050 / AST1100 (A3, "G3")**:

1. the **PWM & Fan Tachometer Controller** (base `0x1E786000`),
2. the **Real-Time Clock (RTC)** (base `0x1E781000`),
3. the **PECI Controller** (base `0x1E78B000`), and
4. the **Virtual UART (VUART)** (base `0x1E787000`) and **Pass-through UART
   (PUART)** (base `0x1E788000`).

Every register in each block's 4 KiB APB window is documented — including the
offsets that are reserved / unimplemented — with bit-field tables for the
control and status registers. All four blocks are clocked from (or divided from)
the single external **24 MHz** oscillator; there is no separate 25/48 MHz or
32.768 KHz crystal on the AST2050. [DS §8.1 p.84](#sources)

The four bases and their 4 KiB regions come from the ARM address map (§9): RTC
`1E78:1000–1E78:1FFF`, PWM & Fan Tacho `1E78:6000–1E78:6FFF`, Virtual UART
`1E78:7000–1E78:7FFF`, Pass-through UART `1E78:8000–1E78:8FFF`, PECI
`1E78:B000–1E78:BFFF`. Every window supports 1/2/4-byte reads and writes.
[DS §9 p.97](#sources)

The AST2050 is **not** supported by mainline Linux; the earliest supported part
is the AST2400 (G4). The G4 drivers named below are used only to corroborate
register semantics and are flagged where the G3 block diverges from them.
[aspeed-driver-quick-reference.md:4,107,114](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/aspeed-driver-quick-reference.md#L4)

```{admonition} Conventions
:class: note

- **Access** column: `RO` read-only, `RW` read/write, `WO` write-only,
  `W1C` write-1-to-clear (status), `R/WSC` read + write-set / self-clearing.
- **Reset** ("Init") values are the datasheet power-on values. `X` = undefined
  after reset; `0bxx` = don't-care bits shown as `x`.
- Field bit ranges are inclusive `[msb:lsb]`.
- Offsets not listed in a block's register map are **reserved** on the G3 and
  must not be assumed to exist because a later Aspeed generation defines them.
  The datasheet explicitly notes that unsupported-mode access returns an
  unpredictable result. [DS §9 p.97](#sources)
```

## Interrupt & clock/reset summary

Each block's interrupt hooks into the 32-source Vector Interrupt Controller
(VIC) and its clock gate / reset control live in the SCU. [DS §10 p.99](#sources)
[DS §18 SCU04 p.205-206](#sources) [DS §18 SCU0C p.209](#sources)

```{list-table} Per-block VIC lines, clocks, reset & pin-mux
:header-rows: 1

* - Block
  - Base
  - VIC INT#
  - Clock (max, all ÷24 MHz)
  - SCU reset / clock gate
  - Pin-mux (SCU74)
* - PWM & Fan Tacho
  - 0x1E786000
  - 28 — Tachometer interrupt (sensitive high level) [DS §10 p.99](#sources)
  - PWMCLK 24 MHz, TACHCLK 6 MHz [DS §8.1 p.84](#sources)
  - SCU04[9] reset PWM (default = held in reset); block clock gated by PTCR00[0] [DS p.205](#sources)
  - PWM1–4 = GPIOC2–5 via SCU74[8]–SCU74[11]; tach inputs shared with GPIOE / DVO [DS §7 p.80](#sources) [DS §28.2 p.290](#sources)
* - RTC
  - 0x1E781000
  - 22 second, 23 day, 24 hour, 25 minute, 26 alarm (all edge / both-edge) [DS §10 p.99](#sources)
  - CLK1M 1 MHz [DS §8.1 p.84](#sources)
  - No dedicated SCU reset bit; software reset via RTC14 = 0x99 [DS p.272](#sources)
  - Dedicated pins (no mux) [DS §24 p.270](#sources)
* - PECI
  - 0x1E78B000
  - 15 — PECI interrupt (sensitive high level) [DS §10 p.99](#sources)
  - PECICLK 2 MHz [DS §8.1 p.84](#sources)
  - SCU04[10] reset PECI (default = held in reset); block clock gated by PECI00[0] [DS p.205](#sources)
  - PECII = GPIOC0, PECIO = GPIOC1, both via SCU74[7] [DS §7 p.80](#sources)
* - VUART / PUART
  - 0x1E787000 / 0x1E788000
  - none dedicated — ARM side via LPC INT #8; host side via LPC SerIRQ (see notes) [DS §10 p.99](#sources)
  - LCLK 33 MHz (LPC bus clock — sets the fixed baud) [DS §8.1 p.84](#sources)
  - SCU04[5] reset LPC/BMC; UARTCLK gate SCU0C[15], LCLK gate SCU0C[8] [DS p.206,209](#sources)
  - Data path only (PUART uses UART1/UART2 pins) [DS §29 p.296](#sources)
```

The AST2050 VIC has **no dedicated VUART or PUART source line** in the 32-entry
Interrupt Source Table (Table 36); the ARM (slave) side therefore raises its
interrupt through the shared LPC controller interrupt (INT #8), while the host
side is signalled over the LPC SerIRQ whose number is selected by
`VUART24[7:4]` / `PUART24[7:4]`. (The routing is inferred from Table 36 having no
VUART/PUART entry.) [DS §10 p.99](#sources) [DS §29 p.306,308](#sources)

---

## 1. PWM & Fan Tachometer Controller — base 0x1E786000

The PWM/Fan-Tacho block drives **4 PWM outputs** (duty 0–100 % in 1/256 steps,
selectable low- or high-frequency mode per port) and reads back **16 fan
tachometer inputs**. Each PWM port and each tach channel is assigned to one of
two clock/measurement profiles, **Type M** or **Type N**; the profile choice is
per-PWM-port (PTCR00[15:12]) and per-tach-channel (implied by the tach's PWM
source in PTCR20 and the type control registers). 4 tach inputs are dedicated
and 12 are shared with the DVO input pins. When PWM outputs are not needed the
pins revert to GPIO. [DS §28.1–28.2 p.290](#sources)

The block implements **15 registers** spanning `0x00`–`0x3C`, with **one gap at
offset `0x24`** (unimplemented — there is no register between PTCR20 at `0x20`
and PTCR28 at `0x28`). The revision history confirms the map ends at `0x3C`:
registers PTRC40–PTRC7C were removed in datasheet rev 0.92 because "they don't
exist". [DS §28.1 p.290](#sources) [DS revision history, v0.92 (Mar 05 2008)](#sources)

```{list-table} PWM & Fan Tacho register map (base 0x1E786000)
:header-rows: 1

* - Offset
  - Register
  - Reset
  - Access
  - Description
* - 0x00
  - PTCR00 General Control
  - 0xXXXXX000
  - RW
  - Per-channel fan-tach enables [31:16], per-port PWM type select [15:12], per-port PWM enables [11:8], global PWM & fan-tach clock enable [0]. [DS p.291](#sources)
* - 0x04
  - PTCR04 Clock Control
  - X
  - RW
  - Type N & Type M PWM period [7:0] and two-stage clock dividers (H = power-of-two ÷1…÷32768; L = even ÷1…÷30). [DS p.291-292](#sources)
* - 0x08
  - PTCR08 Duty Control 0
  - X
  - RW
  - PWM B falling [31:24] / rising [23:16] point, PWM A falling [15:8] / rising [7:0] point (in units of PWM period). [DS p.292](#sources)
* - 0x0C
  - PTCR0C Duty Control 1
  - X
  - RW
  - PWM D falling [31:24] / rising [23:16] point, PWM C falling [15:8] / rising [7:0] point. [DS p.292](#sources)
* - 0x10
  - PTCR10 Type M Control 0
  - X
  - RW
  - Type M fan-tach period [31:16], smart-fan-tach enable [7], edge mode [5:4], clock divide [3:1], tach enable [0]. [DS p.292-293](#sources)
* - 0x14
  - PTCR14 Type M Control 1
  - X
  - RW
  - Type M fan-tach falling point [31:16] / rising point [15:0] of period. [DS p.293](#sources)
* - 0x18
  - PTCR18 Type N Control 0
  - X
  - RW
  - Type N fan-tach period [31:16], smart-fan-tach enable [7], edge mode [5:4], clock divide [3:1], tach enable [0]. [DS p.293](#sources)
* - 0x1C
  - PTCR1C Type N Control 1
  - X
  - RW
  - Type N fan-tach falling point [31:16] / rising point [15:0] of period. [DS p.293](#sources)
* - 0x20
  - PTCR20 Tach Source
  - X
  - RW
  - 2 bits per tach channel selecting its PWM source (00=A,01=B,10=C,11=D); channel *n* uses bits [2n+1:2n]. [DS p.294](#sources)
* - 0x24
  - *(reserved / not implemented)*
  - —
  - —
  - **Gap.** No register at this offset. [DS §28.1 p.290 register list](#sources)
* - 0x28
  - PTCR28 Trigger
  - X
  - RW
  - 0-to-1 trigger to start a fan-tach read, one bit per channel [15:0]; upper half [31:16] reserved. [DS p.294](#sources)
* - 0x2C
  - PTCR2C Result
  - X
  - RO
  - Full-measurement status [31], measured tach value [19:0]; [30:20] reserved. [DS p.294](#sources)
* - 0x30
  - PTCR30 Interrupt Control
  - X
  - RW
  - Per-channel fan-tach interrupt enable [15:0]; [31:16] reserved. [DS p.294-295](#sources)
* - 0x34
  - PTCR34 Interrupt Status
  - X
  - RW
  - Per-channel fan-tach interrupt pending [15:0] (drives VIC #28); [31:16] reserved. [DS p.295](#sources)
* - 0x38
  - PTCR38 Type M Limit
  - X
  - RW
  - Type M fan-tach over-speed limit [19:0]; [31:20] reserved. [DS p.295](#sources)
* - 0x3C
  - PTCR3C Type N Limit
  - X
  - RW
  - Type N fan-tach over-speed limit [19:0]; [31:20] reserved. [DS p.295](#sources)
```

### PTCR00 — General Control (offset 0x00)

```{list-table} PTCR00 fields
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 31:16
  - Fan-tach #15…#0 enable
  - RW
  - One bit per channel; bit[16+n] enables tach #n. 0=disable, 1=enable. [DS p.291](#sources)
* - 15:12
  - PWM D/C/B/A type select
  - RW
  - Bit[15]=port D, [14]=C, [13]=B, [12]=A. 0=Type M, 1=Type N. [DS p.291](#sources)
* - 11:8
  - PWM D/C/B/A enable
  - RW
  - Bit[11]=port D, [10]=C, [9]=B, [8]=A. 0=disable, 1=enable. [DS p.291](#sources)
* - 7:1
  - Reserved
  - RW
  - Reserved. [DS p.291](#sources)
* - 0
  - PWM & Fan-Tach clock enable
  - RW
  - Global gate for the block. 0=disable, 1=enable. [DS p.291](#sources)
```

### PTCR04 — Clock Control (offset 0x04)

The **H** divider stage is power-of-two (`0000`=÷1, `0001`=÷2, `0010`=÷4 …
`1111`=÷32768); the **L** divider stage is even-valued (`0000`=÷1, `0001`=÷2,
`0010`=÷4, `0011`=÷6 … `1111`=÷30). $\text{PWMCLK} = 24\,\text{MHz} \div (H \times L)$. [DS p.291-292](#sources)

```{list-table} PTCR04 fields
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 31:24
  - Type N PWM period [7:0]
  - RW
  - PWM period in Type-N PWM clocks. [DS p.291](#sources)
* - 23:20
  - Type N clock divide H [3:0]
  - RW
  - Power-of-two divider ÷1…÷32768. [DS p.291](#sources)
* - 19:16
  - Type N clock divide L [3:0]
  - RW
  - Even divider ÷1…÷30. [DS p.292](#sources)
* - 15:8
  - Type M PWM period [7:0]
  - RW
  - PWM period in Type-M PWM clocks. [DS p.292](#sources)
* - 7:4
  - Type M clock divide H [3:0]
  - RW
  - Power-of-two divider ÷1…÷32768. [DS p.292](#sources)
* - 3:0
  - Type M clock divide L [3:0]
  - RW
  - Even divider ÷1…÷30. [DS p.292](#sources)
```

### PTCR10 / PTCR18 — Type M / Type N Control 0 (offsets 0x10 / 0x18)

Both registers share the identical layout; PTCR10 is Type M, PTCR18 is Type N.
[DS p.292-293](#sources)

```{list-table} PTCR10 / PTCR18 fields
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 31:16
  - Fan-tach period [15:0]
  - RW
  - Measurement window, in units of the type's PWM clock. [DS p.292](#sources)
* - 15:8
  - Reserved (0)
  - RO
  - Reserved. [DS p.292](#sources)
* - 7
  - Smart fan-tach enable
  - RW
  - 0=disable, 1=enable. [DS p.292](#sources)
* - 6
  - Reserved
  - RW
  - Reserved. [DS p.292](#sources)
* - 5:4
  - Fan-tach mode select
  - RW
  - 00=falling edge, 01=rising edge, 10=both edges, 11=reserved. [DS p.293](#sources)
* - 3:1
  - Fan-tach clock divide
  - RW
  - 000=÷4, 001=÷16, 010=÷64, 011=÷256 … 111=÷65536. [DS p.293](#sources)
* - 0
  - Fan-tach enable
  - RW
  - 0=disable, 1=enable. [DS p.293](#sources)
```

### PTCR20 — Tach Source (offset 0x20)

Two bits per fan-tach channel select which PWM output that channel is measured
against: channel *n* occupies bits `[2n+1:2n]`, encoded `00`=PWM A, `01`=PWM B,
`10`=PWM C, `11`=PWM D. The datasheet spells out channels #15–#12 (bits
[31:24]) and #0 (bits [1:0]); the intervening channels follow the same 2-bit
stride. [DS p.294](#sources)

```{list-table} PTCR20 fields (representative)
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 31:30
  - Tach #15 PWM source
  - RW
  - 00=A, 01=B, 10=C, 11=D. [DS p.294](#sources)
* - 29:28
  - Tach #14 PWM source
  - RW
  - 00=A, 01=B, 10=C, 11=D. [DS p.294](#sources)
* - 27:2
  - Tach #13…#1 PWM source
  - RW
  - Two bits per channel, same 00/01/10/11 = A/B/C/D encoding. [DS p.294](#sources)
* - 1:0
  - Tach #0 PWM source
  - RW
  - 00=A, 01=B, 10=C, 11=D. [DS p.294](#sources)
```

### PTCR2C — Result (offset 0x2C) and the RPM formula

```{list-table} PTCR2C fields
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 31
  - Full-measurement status
  - RO
  - 0=partial measurement, 1=full measurement. [DS p.294](#sources)
* - 30:20
  - Reserved (0)
  - RO
  - Reserved. [DS p.294](#sources)
* - 19:0
  - Measured tach value [19:0]
  - RO
  - Raw edge-count for the last triggered channel. [DS p.294](#sources)
```

Fan speed is derived from the raw value with the datasheet formula (printed as a
footnote to the register table):

> $\text{RPM} = \dfrac{24000000 \times 60}{2 \times \text{TachoValue} \times \text{TachoClkDivision}}$

where *TachoValue* is `PTCR2C[19:0]` and *TachoClkDivision* is the Type M/N
fan-tach clock divide from `PTCR10[3:1]` / `PTCR18[3:1]` (÷4…÷65536). [DS p.295](#sources)
The register offsets (`0x00` CTRL, `0x04` CLK, `0x08`/`0x0C` duty, `0x10`–`0x1C`
Type M/N, `0x20` tach source, `0x2C` result, `0x30`/`0x34` interrupt,
`0x38`/`0x3C` limits) and this RPM relationship match the mainline G4 driver
`drivers/hwmon/aspeed-pwm-tacho.c` (compatible `aspeed,ast2400-pwm-tacho`),
which is register-compatible with this G3 block. [aspeed-mainline-drivers-analysis.md:99,105](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/aspeed-mainline-drivers-analysis.md#L99)

### PTCR30 / PTCR34 — Interrupt Control / Status (offsets 0x30 / 0x34)

Both are 16-bit-wide (one bit per fan-tach channel, [15:0]; [31:16] reserved).
`PTCR30` enables per-channel interrupts; `PTCR34` shows per-channel pending
status (`1`=interrupt pending) and is the source of VIC line #28. [DS p.294-295](#sources)

```{list-table} PTCR30 / PTCR34 fields
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 31:16
  - Reserved (0)
  - RO
  - Reserved. [DS p.294](#sources)
* - 15:0
  - Per-channel enable (PTCR30) / pending (PTCR34)
  - RW
  - Bit *n* = fan-tach #n. PTCR30: 0=disable/1=enable. PTCR34: 0=no interrupt/1=pending. [DS p.295](#sources)
```

---

## 2. Real-Time Clock (RTC) — base 0x1E781000

The RTC is a 24-hour up-counter with **separate second, minute, hour and day
counters** (so firmware never has to carry/normalise), plus programmable
second / minute / hour / day alarms that raise the RTC VIC lines. It is clocked
from CLK1M (1 MHz, divided from the 24 MHz oscillator), keeps counting while
PCLK is gated in sleep, and has **no battery backup** — power loss loses the
time (Aspeed recommends an external I²C RTC if retention is required). Precision
is ≈ 50 ppm (~1 s per 12 h). [DS §24.1–24.2 p.270](#sources)

The block implements **6 registers** at offsets `0x00`–`0x14`; all higher
offsets in the 4 KiB window are reserved. [DS §24.1 p.270](#sources)

```{list-table} RTC register map (base 0x1E781000)
:header-rows: 1

* - Offset
  - Register
  - Reset
  - Access
  - Description
* - 0x00
  - RTC00 Counter Status
  - X
  - RO
  - Live counters: DayCnt [31:17], HourCnt [16:12] (0–23), MinuCnt [11:6] (0–59), SecCnt [5:0] (0–59). [DS p.270-271](#sources)
* - 0x04
  - RTC04 Clock Alarm
  - X
  - RW
  - Hour alarm [16:12], minute alarm [11:6], second alarm [5:0]. Out-of-range value = alarm never fires. [DS p.271](#sources)
* - 0x08
  - RTC08 Reload Value
  - X
  - RW
  - Day [31:17], hour [16:12], minute [11:6], second [5:0] loaded into the counters on restart. [DS p.271-272](#sources)
* - 0x0C
  - RTC0C Control
  - X
  - RW/RO
  - Restart-busy status [5] (RO), day/hour/minute/second alarm enables [4:1], RTC enable [0]. [DS p.272](#sources)
* - 0x10
  - RTC10 Restart
  - X
  - WO
  - Write `0x5A` [7:0] to reload the counters from RTC08 (whether or not RTC is enabled). [DS p.272](#sources)
* - 0x14
  - RTC14 Reset
  - X
  - RW
  - Write `0x99` [7:0] to reset the RTC immediately; write `0x00` to clear reset. [DS p.272](#sources)
```

### RTC00 — Counter Status (offset 0x00)

```{list-table} RTC00 fields
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 31:17
  - DayCnt
  - RO
  - Day counter; increments once per day, holds value when RTC disabled. [DS p.270](#sources)
* - 16:12
  - HourCnt
  - RO
  - Hour counter 0–23; wraps to 0 after 23. [DS p.270-271](#sources)
* - 11:6
  - MinuCnt
  - RO
  - Minute counter 0–59; wraps to 0 after 59. [DS p.271](#sources)
* - 5:0
  - SecCnt
  - RO
  - Second counter 0–59; wraps to 0 after 59. [DS p.271](#sources)
```

`RTC04` (alarm) and `RTC08` (reload) use the same hour/minute/second field
positions as `RTC00`, and `RTC08` adds the day reload in [31:17].

```{admonition} Datasheet erratum in RTC04
:class: warning

The V1.05 datasheet prints the RTC04 reserved range as **"31:13 Reserved (0)"**,
which overlaps the hour-alarm field at [16:12]. The consistent reading (matching
RTC00 / RTC08) is **reserved = [31:17]**, hour alarm = [16:12]. Treat [31:17] as
reserved. [DS p.271](#sources)
```

### RTC0C — Control (offset 0x0C)

```{list-table} RTC0C fields
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 31:6
  - Reserved (0)
  - RO
  - Reserved. [DS p.272](#sources)
* - 5
  - Restart status
  - RO
  - 1 = RTC is currently reloading the reload value into the counters; 0 = not in restart period. Self-clears. [DS p.272](#sources)
* - 4
  - Day alarm enable
  - RW
  - 0=disable, 1=enable → VIC #23 (day). [DS p.272](#sources)
* - 3
  - Hour alarm enable
  - RW
  - 0=disable, 1=enable → VIC #24 (hour). [DS p.272](#sources)
* - 2
  - Minute alarm enable
  - RW
  - 0=disable, 1=enable → VIC #25 (minute). [DS p.272](#sources)
* - 1
  - Second alarm enable
  - RW
  - 0=disable, 1=enable → VIC #22 (second). [DS p.272](#sources)
* - 0
  - RTC enable
  - RW
  - 0=disable (default), 1=enable counting. [DS p.272](#sources)
```

```{admonition} Programming order matters
:class: note

Updating the reload register while the RTC is in the reload-busy state
(`RTC0C[5]=1`) can dead-lock the RTC and require a long reset to recover. The
datasheet gives three safe sequences (reset `RTC14=0x99` → set `RTC08` → clear
reset `RTC14=0x00` → restart `RTC10=0x5A` → enable `RTC0C[0]=1`), differing only
in whether/when they poll `RTC0C[5]`. [DS §24.4 p.273-274](#sources)
```

The AST2050 RTC register map (control at `0x0C`, restart at `0x10`, reset at
`0x14`, no year counter) **differs from** the mainline G4 driver
`drivers/rtc/rtc-aspeed.c` (compatible `aspeed,ast2400-rtc`), which targets a
redesigned RTC block (year register + control at a different offset). The
mainline driver cannot bind to this block unmodified. [aspeed-mainline-drivers-analysis.md:150](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/aspeed-mainline-drivers-analysis.md#L150) [aspeed-driver-quick-reference.md:83](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/aspeed-driver-quick-reference.md#L83)

---

## 3. PECI Controller — base 0x1E78B000

The PECI (Platform Environment Control Interface) host controller is **Intel
PECI 2.0 / 1.1 compliant**, addresses **up to 4 CPUs (2 domains each)** for
CPU-temperature and related telemetry, and needs an external analog comparator
on the single-wire PECI bus. PECICLK is divided from 24 MHz (2 MHz max) and the
PECII/PECIO pins are shared with GPIOC0/GPIOC1. [DS §32.1–32.2 p.357](#sources)

The block implements **16 registers**, contiguous from `0x00` to `0x3C` (no
gaps). The 4 write-data and 4 read-data registers give a 16-byte payload window
each way. [DS §32.1 p.357](#sources)

```{list-table} PECI register map (base 0x1E78B000)
:header-rows: 1

* - Offset
  - Register
  - Reset
  - Access
  - Description
* - 0x00
  - PECI00 Control
  - 0x000XXX00
  - RW
  - Read sample point [19:16], read mode [13:12], PECI clock divider [11:8], I/O polarity [7:6], bus contention en [5], PECI enable [4], AW-FCS auto-gen [1], PECI clock enable [0]. [DS p.357-359](#sources)
* - 0x04
  - PECI04 Timing Negotiation
  - X
  - RW
  - Message timing negotiation [15:8], address timing negotiation [7:0] (unit = 4× PECI clock period). [DS p.359](#sources)
* - 0x08
  - PECI08 Command
  - 0
  - RW/RO
  - PECI pin monitor [31] (RO), controller FSM state [27:24] (RO), fire command [0]. [DS p.359](#sources)
* - 0x0C
  - PECI0C Read/Write Length
  - X
  - RW
  - AW-FCS-cycle enable [31], read length bytes [23:16], write length bytes [15:8], target address [7:0]. [DS p.359-360](#sources)
* - 0x10
  - PECI10 Expected FCS Data
  - X
  - RW/RO
  - Programmed AW FCS [31:24] (RW), expected read/AW/write FCS [23:0] (RO, debug). [DS p.360](#sources)
* - 0x14
  - PECI14 Captured FCS Data
  - X
  - RO
  - Captured read-command FCS [23:16], captured write-command FCS [7:0]. [DS p.360](#sources)
* - 0x18
  - PECI18 Interrupt (enable)
  - 0
  - RW
  - Timing-negotiation result select [31:30], enables: bus contention [3], write-FCS-bad [2], write-FCS-abort [1], command-done [0]. [DS p.360-361](#sources)
* - 0x1C
  - PECI1C Interrupt Status
  - 0xXXXX0000
  - R/W1C
  - Timing negotiation result [31:16] (RO), W1C status: contention [3], FCS-bad [2], FCS-abort [1], done [0] (source of VIC #15). [DS p.361](#sources)
* - 0x20
  - PECI20 Write Data #0
  - X
  - RW
  - Write data bits [31:0]. [DS p.361](#sources)
* - 0x24
  - PECI24 Write Data #1
  - X
  - RW
  - Write data bits [63:32]. [DS p.361](#sources)
* - 0x28
  - PECI28 Write Data #2
  - X
  - RW
  - Write data bits [95:64]. [DS p.361](#sources)
* - 0x2C
  - PECI2C Write Data #3
  - X
  - RW
  - Write data bits [127:96]. [DS p.361](#sources)
* - 0x30
  - PECI30 Read Data #0
  - X
  - RO
  - Read data bits [31:0]. [DS p.362](#sources)
* - 0x34
  - PECI34 Read Data #1
  - X
  - RO
  - Read data bits [63:32]. [DS p.362](#sources)
* - 0x38
  - PECI38 Read Data #2
  - X
  - RO
  - Read data bits [95:64]. [DS p.362](#sources)
* - 0x3C
  - PECI3C Read Data #3
  - X
  - RO
  - Read data bits [127:96]. [DS p.362](#sources)
```

### PECI00 — Control (offset 0x00)

```{list-table} PECI00 fields
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 31:20
  - Reserved (0)
  - RO
  - Reserved. [DS p.357](#sources)
* - 19:16
  - Read sampling point
  - RW
  - `0000`=0/16 … `1111`=15/16 of a bit-time; Point-Sampling mode only (middle is best). [DS p.358](#sources)
* - 15:14
  - Reserved
  - RW
  - Reserved. [DS p.358](#sources)
* - 13:12
  - Read mode
  - RW
  - 00=Point Sampling, 01=Pulse-Width Counting, 10=Debugging (ping only), 11=invalid. [DS p.358](#sources)
* - 11:8
  - PECI clock divider
  - RW
  - `0000`=÷1, `0001`=÷2, `0010`=÷4, `0011`=÷8 … `0111`=÷128; others invalid. Source = 24 MHz. [DS p.358](#sources)
* - 7
  - Inverse PECI output polarity
  - RW
  - 0=normal, 1=inverse. [DS p.358](#sources)
* - 6
  - Inverse PECI input polarity
  - RW
  - 0=normal, 1=inverse. [DS p.358](#sources)
* - 5
  - Enable bus contention
  - RW
  - 0=disable, 1=enable. [DS p.358](#sources)
* - 4
  - Enable PECI
  - RW
  - 0=disable, 1=enable. [DS p.358](#sources)
* - 3:2
  - Reserved
  - RW
  - Reserved. [DS p.358](#sources)
* - 1
  - Auto AW-FCS generation
  - RW
  - 1=hardware generates Assured-Write FCS; 0=use software value in PECI10[31:24]. [DS p.358](#sources)
* - 0
  - Enable PECI clock
  - RW
  - 0=stop 24 MHz source (power save), 1=enable. [DS p.359](#sources)
```

### PECI08 — Command (offset 0x08)

```{list-table} PECI08 fields
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 31
  - PECI pin monitor
  - RO
  - Reads back the live PECI wire level. [DS p.359](#sources)
* - 30:28
  - Reserved (0)
  - RO
  - Reserved. [DS p.359](#sources)
* - 27:24
  - Controller state
  - RO
  - FSM: 0000=idle, 0001=fire, 0010/0011=addr timing negotiation, 0100=address, 0101=msg timing negotiation, 0110=W/R length, 0111=write data, 1001=write FCS, 1010=read data, 1011=read FCS, 1100=stop; others reserved. [DS p.359](#sources)
* - 23:1
  - Reserved (0)
  - RO
  - Reserved. [DS p.359](#sources)
* - 0
  - Fire a PECI command
  - RW
  - 0=no-op, 1=fire the command configured in PECI0C/PECI20…. [DS p.359](#sources)
```

### PECI0C — Read/Write Length (offset 0x0C)

```{list-table} PECI0C fields
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 31
  - Enable AW-FCS cycle
  - RW
  - Write commands only: 1=append an AW-FCS cycle. [DS p.359](#sources)
* - 30:24
  - Reserved (0)
  - RO
  - Reserved. [DS p.359](#sources)
* - 23:16
  - Read data length (bytes)
  - RW
  - Bytes to read into PECI30–PECI3C (max 16 despite 8-bit field). [DS p.360](#sources)
* - 15:8
  - Write data length (bytes)
  - RW
  - Bytes to write from PECI20–PECI2C. [DS p.360](#sources)
* - 7:0
  - Target address
  - RW
  - 8-bit PECI client address for the fired command. [DS p.360](#sources)
```

### PECI18 / PECI1C — Interrupt enable / status (offsets 0x18 / 0x1C)

`PECI18` enables the four interrupt causes and selects which timing-negotiation
result is latched; `PECI1C` holds the latched result and the four **write-1-to-
clear** status bits (the OR of which is VIC #15). [DS p.360-361](#sources)

```{list-table} PECI18 (enable) fields
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 31:30
  - Timing-negotiation result select
  - RW
  - 00=1st addr-negotiation bit, 01=2nd addr-negotiation bit, 10=message negotiation, 11=reserved. [DS p.360](#sources)
* - 29:4
  - Reserved (0)
  - RO
  - Reserved. [DS p.360](#sources)
* - 3
  - Bus-contention interrupt enable
  - RW
  - 0=disable, 1=enable. [DS p.360](#sources)
* - 2
  - Write-FCS-bad interrupt enable
  - RW
  - 0=disable, 1=enable. [DS p.361](#sources)
* - 1
  - Write-FCS-abort interrupt enable
  - RW
  - 0=disable, 1=enable. [DS p.361](#sources)
* - 0
  - Command-done interrupt enable
  - RW
  - 0=disable, 1=enable. [DS p.361](#sources)
```

```{list-table} PECI1C (status) fields
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 31:16
  - Timing-negotiation result [15:0]
  - RO
  - Captured negotiation result selected by PECI18[31:30]. [DS p.361](#sources)
* - 15:4
  - Reserved (0)
  - RO
  - Reserved. [DS p.361](#sources)
* - 3
  - Bus-contention status
  - W1C
  - 1=pending; write 1 to clear. [DS p.361](#sources)
* - 2
  - Write-FCS-bad status
  - W1C
  - 1=pending; write 1 to clear. [DS p.361](#sources)
* - 1
  - Write-FCS-abort status
  - W1C
  - 1=pending; write 1 to clear. [DS p.361](#sources)
* - 0
  - Command-done status
  - W1C
  - 1=pending; write 1 to clear. [DS p.361](#sources)
```

The mainline PECI host driver is `drivers/peci/controller/peci-aspeed.c`
(compatibles `aspeed,ast2400-peci` / `ast2500-peci` / `ast2600-peci`); it does
not list an AST2050 compatible. [aspeed-mainline-drivers-analysis.md:38](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/aspeed-mainline-drivers-analysis.md#L38)

---

## 4. Virtual UART (VUART) & Pass-through UART (PUART)

The VUART is a fully **16550-compatible** UART with *two* register sets that
share one FIFO pair, giving a firmware-less serial link between the **host CPU
(via LPC)** and the **ARM/BMC CPU (via APB)** — no external wires. The PUART
instead splices the LPC bus straight through AHB/APB to the real **UART1 or
UART2**, so the host can drive a physical BMC COM port directly (a Super-I/O COM
replacement). Each has a 16×8 transmit and receive FIFO. [DS §29.1–29.2 p.296](#sources)

Because the host side is reached over LPC, the **baud rate is fixed at the LPC
clock (LCLK ≈ 33 MHz)**: the DLL/DLH divisor-latch registers exist only for
16550 software compatibility and do not change the actual rate. [DS p.297-298,301](#sources)
The LPC I/O base at which the host sees the VUART / PUART registers is
programmable by the ARM through `VUART28`/`VUART2C` and `PUART28`/`PUART2C`.
[DS p.296,305-306](#sources)

### 4.1 VUART registers — base 0x1E787000

Offsets `0x00`–`0x1C` exist as **two independent register sets** at the same
addresses — one seen by the host over LPC, one by the ARM over APB (the "Host"
and "Slave" columns below). Offsets `0x20`–`0x3C` are **ARM-only** extended
control registers (there is no host-visible register there). [DS §29.3 p.296-297](#sources)

```{list-table} VUART register map (base 0x1E787000)
:header-rows: 1

* - Offset
  - Register (Host / Slave)
  - Reset
  - Access
  - Description
* - 0x00
  - RBR (R) / THR (W) / DLL (DLAB=1)
  - X
  - RW
  - Receive-buffer / transmit-holding; DLL divisor-low when DLAB=1 (cosmetic — real baud = LCLK). Both sides. [DS p.297-298](#sources)
* - 0x04
  - IER (DLAB=0) / DLH (DLAB=1)
  - 0
  - RW
  - Interrupt enables (RX-data, THRE, RX-line-status, modem-status); host bit[7] = FIFO-½-full THRE mode (if VUART34[6]=1). DLH when DLAB=1. [DS p.298-299](#sources)
* - 0x08
  - IIR (R) / FCR (W)
  - 0xC1 / 0x01
  - RW
  - Interrupt-identity read / FIFO-control write (trigger level [7:6], TX-reset [2], RX-reset [1], FIFO-enable [0]). Both sides. [DS p.299-301](#sources)
* - 0x0C
  - LCR — Line Control
  - 0x03
  - RW
  - DLAB [7], break control [6], word length [1:0]; [5:2] reserved. Both sides. [DS p.301-302](#sources)
* - 0x10
  - MCR — Modem Control
  - 0
  - RW
  - Loopback [4], Out2 [3], Out1 [2], nRTS [1], nDTR [0]; **host adds** TX-FIFO-full status at bit[7] (RO). [DS p.303](#sources)
* - 0x14
  - LSR — Line Status
  - 0x60
  - RO
  - TX empty [6], THRE [5], break [4], overrun [1], data-ready [0]; [3:2] reserved. Both sides. [DS p.304](#sources)
* - 0x18
  - MSR — Modem Status
  - X
  - RO
  - nDSR/nDCD/nRI/nCTS complements [7:4] and delta bits DDCD [3], TERI [2], DDSR [1], DCTS [0]. Both sides. [DS p.304-305](#sources)
* - 0x1C
  - SCR — Scratch
  - X
  - RW
  - 8-bit scratch [7:0], no defined function. Both sides. [DS p.305](#sources)
* - 0x20
  - VUART20 General Control A (Slave)
  - 0b00x0xx00
  - RW/RO
  - Enable VUART [0], SIRQ polarity [1], slave timeout width [3:2], host-loopback status [4] (RO), disable Host-Tx-discard [5], host RX-FIFO-trigger status [7:6] (RO). ARM-only. [DS p.305-306](#sources)
* - 0x24
  - VUART24 General Control B (Slave)
  - 0bxxxx xx11
  - RW/RO
  - Host bits-per-char [1:0] (RO), host-side timeout [3:2], SIRQ number [7:4]. ARM-only. [DS p.306](#sources)
* - 0x28
  - VUART28 Address L (Slave)
  - X
  - RW
  - LPC base address low byte [7:0] for host access to VUART. ARM-only. [DS p.306](#sources)
* - 0x2C
  - VUART2C Address H (Slave)
  - X
  - RW
  - LPC base address high byte [15:8]. ARM-only. [DS p.306](#sources)
* - 0x30
  - VUART30 General Control E (Slave)
  - 0b0000 1110
  - RO
  - Slave TX-FIFO-full [7], THR read pointer [6:4], complement of host IIR status [3:0]. ARM-only. [DS p.307](#sources)
* - 0x34
  - VUART34 General Control F (Slave)
  - X
  - RW
  - Slave/host FIFO-½-full THRE mode [7]/[6], force-THRE [5], disable char-timeout slave [1]/host [0]; [4:2] reserved. ARM-only. [DS p.307](#sources)
* - 0x38
  - VUART38 General Control G (Slave)
  - X
  - RO
  - Slave-side THR read-back data [7:0]. ARM-only. [DS p.307](#sources)
* - 0x3C
  - VUART3C General Control H (Slave)
  - X
  - RO
  - Read-back of slave RX-FIFO interrupt trigger level [7:6]; [5:0] reserved. ARM-only. [DS p.307](#sources)
```

#### VUART08 (IIR read) — interrupt decoding

```{list-table} VUART08 IIR fields (read)
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 31:4
  - Reserved (0)
  - RO
  - Reserved. [DS p.299](#sources)
* - 3:1
  - Interrupt decode
  - RO
  - 000=modem-status, 001=THR empty, 010=RX-data available, 011=RX line status, 110=char timeout. [DS p.299-300](#sources)
* - 0
  - Interrupt pending (active-low)
  - RO
  - 0=an interrupt is pending, 1=none pending. [DS p.299](#sources)
```

Priority (highest→lowest): RX line status (011) → RX data available (010) →
char timeout (110) → THRE (001) → modem status (000). [DS p.299-300](#sources)

#### VUART10 (MCR) — Modem Control

```{list-table} VUART10 MCR fields (host set; slave set is identical minus bit 7)
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 31:8
  - Reserved (0)
  - RO
  - Reserved. [DS p.303](#sources)
* - 7
  - TX FIFO full (host only)
  - RO
  - 1=transmit FIFO full. On the slave set this bit is reserved. [DS p.303](#sources)
* - 6:5
  - Reserved (0)
  - RO
  - Reserved. [DS p.303](#sources)
* - 4
  - Loopback
  - RW
  - 1=loopback (nDTR→nDSR, nRTS→nCTS, Out1→nRI, Out2→nDCD). [DS p.303](#sources)
* - 3
  - Out2
  - RW
  - In loopback drives nDCD. [DS p.303](#sources)
* - 2
  - Out1
  - RW
  - In loopback drives nRI. [DS p.303](#sources)
* - 1
  - nRTS control
  - RW
  - 0→nRTS=1, 1→nRTS=0. [DS p.303](#sources)
* - 0
  - nDTR control
  - RW
  - 0→nDTR=1, 1→nDTR=0. [DS p.303](#sources)
```

#### VUART20 (GCRA) — the master enable

```{list-table} VUART20 General Control A fields (ARM-only)
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 31:8
  - Reserved (0)
  - RO
  - Reserved. [DS p.305](#sources)
* - 7:6
  - Host RX-FIFO trigger status
  - RO
  - Read-back of the host-side receiver FIFO trigger level. [DS p.305](#sources)
* - 5
  - Disable Host-Tx-discard mode
  - RW
  - 0=enable (slave auto-discards when host TX FIFO not empty), 1=disable. [DS p.305](#sources)
* - 4
  - Host loopback status
  - RO
  - Read-back of host-side loopback mode. [DS p.305](#sources)
* - 3:2
  - Slave-side timeout width
  - RW
  - 00/01/10/11 select 1/64…1/512 s (or scaled values per PUART34[3] & SCU2C[13]). [DS p.305-306](#sources)
* - 1
  - SerIRQ polarity
  - RW
  - Selects asserted/high-Z levels of the host SerIRQ output when the interrupt is set/cleared. [DS p.306](#sources)
* - 0
  - Enable virtual UART
  - RW
  - 0=disable, 1=enable the VUART. [DS p.306](#sources)
```

### 4.2 PUART registers — base 0x1E788000

The pass-through UART exposes **only the ARM-only extended registers**
`0x20`–`0x3C`; the actual data registers are those of UART1/UART2 (selected by
`PUART34[7]`), reached by the host over LPC. [DS §29.4 p.308](#sources)

```{list-table} PUART register map (base 0x1E788000)
:header-rows: 1

* - Offset
  - Register
  - Reset
  - Access
  - Description
* - 0x20
  - PUART20 General Control A
  - 0b00x0xx00
  - RW/RO
  - Host RX-FIFO trigger status [7:6] (RO), host loopback status [4] (RO), SIRQ polarity [1], enable pass-through UART [0]; [5],[3:2] reserved. [DS p.308](#sources)
* - 0x24
  - PUART24 General Control B
  - 0bxxxx xx11
  - RW/RO
  - SIRQ number [7:4], host bits-per-char [1:0] (RO); [3:2] reserved. [DS p.308](#sources)
* - 0x28
  - PUART28 Address L
  - X
  - RW
  - LPC base address low byte [7:0] for host access to the pass-through UART. [DS p.309](#sources)
* - 0x2C
  - PUART2C Address H
  - X
  - RW
  - LPC base address high byte [15:8]. [DS p.309](#sources)
* - 0x30
  - PUART30 General Control E
  - 0
  - RO
  - Complement of host LCR[7:2] in [5:0], host RX-data-int enable complement [6], host THRE-int enable complement [7]. [DS p.309](#sources)
* - 0x34
  - PUART34 General Control F
  - X
  - RW
  - Pass-through target select [7] (0=UART1, 1=UART2), VUART timeout-width control slave [3]/host [2]; [6:4],[1:0] reserved. [DS p.309-310](#sources)
* - 0x38
  - PUART38 General Control G
  - X
  - RO
  - Reserved. [DS p.310](#sources)
* - 0x3C
  - PUART3C General Control H
  - 0x00
  - RO
  - Complement of host modem-status-int enable [7], complement of host RX-line-status-int enable [6]; [5:0] reserved. [DS p.310](#sources)
```

#### PUART34 (GCRF) — pass-through target select

```{list-table} PUART34 General Control F fields (ARM-only)
:header-rows: 1

* - Bits
  - Field
  - Access
  - Meaning
* - 31:8
  - Reserved (0)
  - RO
  - Reserved. [DS p.309](#sources)
* - 7
  - Pass-through mode select
  - RW
  - 0=pass-through UART1, 1=pass-through UART2. [DS p.309](#sources)
* - 6:4
  - Reserved
  - RW
  - Reserved. [DS p.310](#sources)
* - 3
  - VUART timeout width control (slave)
  - RW
  - Selects the slave-side timeout scaling used by VUART20[3:2]. [DS p.310](#sources)
* - 2
  - VUART timeout width control (host)
  - RW
  - Selects the host-side timeout scaling used by VUART24[3:2]. [DS p.310](#sources)
* - 1:0
  - Reserved
  - RW
  - Reserved. [DS p.310](#sources)
```

```{admonition} Reset, routing & A1 errata
:class: note

- The VUART/PUART enable and SIRQ-polarity bits (`VUART20[0]`, `VUART20[1]`,
  `PUART20[0]`, `PUART20[1]`) are **reset when the ARM reboots** on A1 silicon,
  which can leave the host stuck; this is documented as A1 errata (fixed A2).
  [DS A1/A2 errata list, item "VUART and PUART reset when ARM reboots"](#sources)
- VUART/PUART function control is *also* exposed in the LPC controller's Host
  **LPC Host Control Register 0** (`LHCR0`)`[12:8]` — distinct from the Host
  Interface Control Register HICR0. [DS revision history, v1.03](#sources)
  [DS §30 p.311](#sources)
- Mainline `drivers/tty/serial/8250/8250_aspeed_vuart.c`
  (compat `aspeed,ast2400-vuart`) uses the same extended-register offsets
  (GCRA `0x20`, GCRB `0x24`, address `0x28`/`0x2C`); the standard 8250 core
  covers the `0x00`–`0x1C` block. There is no AST2050 compatible string.
  [aspeed-mainline-drivers-analysis.md:135](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/aspeed-mainline-drivers-analysis.md#L135) [aspeed-driver-quick-reference.md:96](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/aspeed-driver-quick-reference.md#L96)
```

## Sources

- **AST2050/AST1100 A3 Datasheet V1.05** (in-repo:
  `datasheets/aspeed/AST2050_AST1100_A3_Datasheet_V1.05.pdf`; page numbers are
  the printed datasheet page in the footer), cited inline as `[DS …](#sources)`:
  - §7 Multi-Function Pins — PWM1–4/PECII/PECIO pin-mux via SCU74 (mux table p.80).
  - §8.1 Clock Information — PWMCLK/TACHCLK/PECICLK/CLK1M/LCLK rates (p.84).
  - §9 ARM Address Space Mapping — the four block base addresses (p.97).
  - §10 Interrupt Source Table (Table 36) — VIC #15 PECI, #22-26 RTC, #28 tach (p.99).
  - §18 System Control Unit — SCU04 reset control (p.205-206), SCU0C clock-stop
    (p.209).
  - §24 Real Time Clock — RTC00-RTC14 + programming modes (p.270-274).
  - §28 PWM & Fan Tacho Controller — PTCR00-PTCR3C + RPM formula (p.290-295).
  - §29 Virtual UART & Pass-through UART — VUART00-3C / PUART20-3C (p.296-310).
  - §30 LPC Controller — HICR0 / VUART-PUART function control context (p.311).
  - §32 PECI Controller — PECI00-PECI3C (p.357-362).
  - Revision history & A1/A2 errata list (front matter) — PWM register removal
    (v0.92), VUART/PUART reset-on-reboot erratum, LHCR0 control note (v1.03).
- **In-repo Raptor Engineering AST2050 port** (`asus-kgpe-d16-firmware/`):
  - [`ast2050.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/ast2050.h) — 24 MHz UART reference clock, NS16550 base addresses.
  - [`hwreg.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h) — SCU / timer / UART / interrupt-controller register offsets
    (the PWM/RTC/PECI/VUART blocks are *not* defined here; datasheet-only).
- **In-repo mainline-driver analysis** (`dell-c410x-firmware/`), cited as
  `[aspeed-mainline-drivers-analysis.md:…](#sources)` / `[aspeed-driver-quick-reference.md:…](#sources)`:
  - PWM/tacho → `drivers/hwmon/aspeed-pwm-tacho.c` (`aspeed,ast2400-pwm-tacho`,
    register-compatible with this G3 block).
  - RTC → `drivers/rtc/rtc-aspeed.c` (`aspeed,ast2400-rtc`, **different** block).
  - PECI → `drivers/peci/controller/peci-aspeed.c` (`aspeed,ast2400-peci`).
  - VUART → `drivers/tty/serial/8250/8250_aspeed_vuart.c`
    (`aspeed,ast2400-vuart`) atop the generic 8250 core.
  - Overall finding: **no AST2050/AST1100 support in mainline; earliest is
    AST2400 (G4).**
- **Web cross-references** (mainline driver source, for register/formula
  corroboration only):
  - `drivers/hwmon/aspeed-pwm-tacho.c`:
    <https://codebrowser.dev/linux/linux/drivers/hwmon/aspeed-pwm-tacho.c.html>
  - `drivers/peci/controller/peci-aspeed.c`:
    <https://codebrowser.dev/linux/linux/drivers/peci/controller/peci-aspeed.c.html>
  - `drivers/tty/serial/8250/8250_aspeed_vuart.c`:
    <https://codebrowser.dev/linux/linux/drivers/tty/serial/8250/8250_aspeed_vuart.c.html>
