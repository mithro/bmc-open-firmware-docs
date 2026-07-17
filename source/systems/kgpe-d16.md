# ASUS KGPE-D16

A dual-socket AMD Opteron (Socket G34) server motherboard whose BMC is an
**Aspeed AST2050**. It is the *source of truth* for AST2050 SoC-level bring-up,
because it maps directly onto Raptor Engineering's known-good AST2050 Linux
port.

```{list-table}
:header-rows: 0
:widths: 30 70

* - BMC SoC
  - Aspeed AST2050 (also sold as AST1100)
* - CPU core
  - ARM926EJ-S (ARMv5TE)
* - DRAM
  - DDR2, mapped at `0x40000000` — Hynix HY5PS121621CFP-25 (`QU2`), 32M×16 = **64 MiB** ({doc}`kgpe-d16-wiring` §3)
* - Boot flash
  - SPI NOR at `0x14000000`, in the **socketed** `BMC_FW1` carrier (§2.3; pinout on {doc}`kgpe-d16-connectors`)
* - Power
  - **always-on**: every BMC rail is standby (`_AUX`), cascaded from PSU `+5VSB` ({doc}`kgpe-d16-wiring` §2)
* - Console
  - SoC **UART2** (`0x1E784000`) = Linux `ttyS1`; firmware **115200 8N1** (the rig bring-up observed 1200 — see the console note in §2.2)
* - Debug
  - `AST_JTAG1` (BMC JTAG) + AMD HDT (host CPU); see {doc}`../debug/jtag-uart`
```

```{admonition} Schematic-derived wiring pages
:class: seealso

The board's schematic netlist has been reverse-engineered pin-by-pin
([`schematic-wiring/`](https://github.com/mithro/ai-shenanigans-for-bmcs/tree/main/asus-kgpe-d16-firmware/schematic-wiring)
in the program repo), giving three companion pages with the wiring ground
truth this overview summarises: {doc}`kgpe-d16-wiring` (every AST2050 ball, by
function), {doc}`kgpe-d16-i2c` (the complete I2C/SMBus/PMBus topology) and
{doc}`kgpe-d16-connectors` (pinouts for every BMC-wired header). Where the
older bring-up notes below disagreed with the netlist, the corrections are
flagged inline.
```

```{toctree}
:hidden:

kgpe-d16-wiring
kgpe-d16-i2c
kgpe-d16-connectors
```

## 1. Why this board leads the SoC work

The AST2050 is **not supported by mainline Linux** — the earliest supported
Aspeed generation is the AST2400 ("G4"). Raptor Engineering shipped a working
Linux 2.6.28.9 AST2050 port, which gives a reference for every SoC block (clock,
SDRAM, SMC/flash, MAC, GPIO, I2C, watchdog). The upstream path is a new
`aspeed-g3.dtsi` include plus `aspeed,ast2050-*` compatibles on the existing
mainline Aspeed drivers — see {doc}`../hardware/soc-ast2050` and
{doc}`../drivers/linux`.

### 1.1 Emulation & firmware status

- **QEMU** — a custom `kgpe-d16-bmc` machine + new `ast2050` SoC boots U-Boot →
  Linux → SSH, and also boots the Raptor 2.6.28.9 + musl stack. See
  {doc}`../emulation/qemu`.
- **OpenBMC / WallaBMC** — planned; the board reuses the shared AST2050 layers.

The KGPE-D16 has no public proprietary BMC image, so proprietary-firmware
emulation proofs use the Dell C410X image (also AST2050) on the same machine.

## 2. Debug / JTAG / UART / BMC headers

```{figure} /_static/diagrams/kgpe-d16-ast-jtag1.svg
:alt: AST_JTAG1 BMC 20-pin ARM JTAG header pinout — odd pins carry the JTAG/reset signals with their RPi4 BCM GPIO / physical-pin / direction wiring; even pins are GND; pin 1 marked. Verified IDCODE 0x07926f0f.
:width: 80%

**AST_JTAG1** — the BMC 20-pin ARM JTAG header, with the exact RPi4 bit-bang
wiring on each signal pin (verified TAP IDCODE `0x07926f0f`).
```

```{figure} /_static/diagrams/kgpe-d16-ast-uart1.svg
:alt: AST_UART1 BMC console 4-pin header — 3.3V (do not wire), BMC TXD, BMC RXD, GND, with crossover-to-RPi labels.
:width: 60%

**AST_UART1** — the BMC console header (SoC UART2 / `ttyS1`; crossover TX/RX to
the adapter). See §2.2 for the 115200-vs-1200 baud discrepancy.
```

```{figure} /_static/diagrams/kgpe-d16-amd-hdt.svg
:alt: AMD HDT (NB_JTAG_HEADER) 20-pin host-CPU debug header pinout, 1.27mm, with all 20 signals; needs a proprietary AMD/ASSET probe, not OpenOCD.
:width: 80%

**AMD HDT** (`NB_JTAG_HEADER`) — the host-CPU debug header. Unlike the BMC JTAG,
this needs a proprietary AMD/ASSET probe, not OpenOCD.
```


The KGPE-D16 has several **unpopulated** debug footprints, not documented in the
ASUS user manual, confirmed by Raptor Engineering. [JTAG-HEADERS.md:1-19](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/JTAG-HEADERS.md#L1-L19) Two are
BMC-side (`AST_JTAG1`, `AST_UART1`), the rest are host/CPU-side.

```{admonition} Confidence + pin-1 safety
:class: warning

A wrong pin-1 assumption on a live board back-feeds the AST2050. **✅ VERIFIED** =
from a cited source; **🔶 STANDARD** = a documented standard the header follows
(confirm pin 1 by eye); **⚠️ TEMPLATE** = shape only, probe your board. Both
`AST_*` headers are **unpopulated footprints** above the AST2050 — you solder
headers in. [HEADER-PINOUTS.md:8-29](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/HEADER-PINOUTS.md#L8-L29) Both BMC-side sides are **3.3 V**; the RPi4
is **not** 5 V tolerant. [RPI4-OPENOCD-JTAG-WIRING.md:41-44](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/RPI4-OPENOCD-JTAG-WIRING.md#L41-L44)
```

```{list-table} KGPE-D16 debug/BMC headers at a glance
:header-rows: 1
:widths: 20 30 28 22

* - Header
  - What it is
  - Tool
  - Confidence
* - AST_JTAG1
  - AST2050 ARM926 JTAG, 20-pin ARM (2×10, 2.54 mm)
  - OpenOCD bit-bang
  - ✅ Raptor
* - AST_UART1
  - BMC console, 4-pin 3.3 V, 115200 8N1
  - USB-serial / Pi UART0
  - ✅ Raptor
* - BMC_FW1
  - BMC SPI firmware socket (2×7 DIP) + feature straps
  - flashrom (SPI)
  - ✅ schematic (§2.3)
* - NB_JTAG_HEADER
  - AMD HDT (CPU/NB debug), 20-pin HDT+ (1.27 mm)
  - proprietary probe only
  - ⚠️ not OpenOCD
* - NB_DEBUG_HEADER
  - SR5690 PCIe hot-plug/debug SMBus (`PCIE_HP_SCL/SDA`)
  - SMBus probe
  - ✅ schematic ({doc}`kgpe-d16-i2c` §4.7)
* - TEST_CON1 / TEST_CON2
  - factory ICT test pads
  - unknown
  - ⚠️ probe first
```

Source: [RPI4-OPENOCD-JTAG-WIRING.md:64-79](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/RPI4-OPENOCD-JTAG-WIRING.md#L64-L79) [HEADER-PINOUTS.md:17-24](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/HEADER-PINOUTS.md#L17-L24).

### 2.1 AST_JTAG1 — BMC JTAG (20-pin ARM, 2×10, 2.54 mm) ✅

Standard ARM 20-pin JTAG. Pin 1 = square pad (top-left); odd column = signal,
even column = GND (except pins 1–2). [HEADER-PINOUTS.md:37-66](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/HEADER-PINOUTS.md#L37-L66)

```{list-table} AST_JTAG1 → Raspberry Pi 4B wiring (direct 3.3 V)
:header-rows: 1
:widths: 18 18 20 20 24

* - Signal
  - JTAG pin
  - RPi4 BCM
  - RPi4 phys
  - Direction
* - VTref
  - 1
  - — (meter only)
  - —
  - target out ~3.3 V (never drive)
* - nTRST
  - 3
  - GPIO17
  - 11
  - Pi → BMC
* - TDI
  - 5
  - GPIO23
  - 16
  - Pi → BMC
* - TMS
  - 7
  - GPIO24
  - 18
  - Pi → BMC
* - TCK
  - 9
  - GPIO25
  - 22
  - Pi → BMC
* - RTCK
  - 11
  - GPIO27
  - 13
  - BMC → Pi (input-only monitor)
* - TDO
  - 13
  - GPIO22
  - 15
  - BMC → Pi
* - nSRST
  - 15
  - GPIO18
  - 12
  - Pi → BMC
* - GND
  - 4/6/8/…/20
  - GND
  - 6 (or any)
  - common (≥1, wire first)
```

Sources: [HEADER-PINOUTS.md:43-66](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/HEADER-PINOUTS.md#L43-L66) [RPI4-OPENOCD-JTAG-WIRING.md:110-136](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/RPI4-OPENOCD-JTAG-WIRING.md#L110-L136).

```{admonition} Verified JTAG facts (real hardware)
:class: note

- **TAP IDCODE `0x07926f0f`** — the ARM926EJ-S generic TAP (Raptor-confirmed on
  this exact AST2050). EmbeddedICE version **6**; **2** hardware breakpoint/
  watchpoint units. [JTAG-USAGE-GUIDE.md:128-137,437-439](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/JTAG-USAGE-GUIDE.md#L128-L137)
- Debug arch is **EmbeddedICE-RT over raw JTAG**, *not* CoreSight/SWD — use a
  raw-JTAG adapter (Pi bit-bang / FTDI / J-Link); SWD-only probes (ST-Link,
  CMSIS-DAP, Black Magic) will not work. [RPI4-OPENOCD-JTAG-WIRING.md:52-58](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/RPI4-OPENOCD-JTAG-WIRING.md#L52-L58)
- Reset topology is `trst_and_srst combined`: SRST also resets the EmbeddedICE
  logic **inside the silicon**, so a clean reset-vector halt is impossible;
  `reset halt` catches the core just past the vector. [JTAG-USAGE-GUIDE.md:217-233](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/JTAG-USAGE-GUIDE.md#L217-L233)
- Cross-check anchor: `SCU7C` (`0x1E6E207C`) reads **`0x00000202`** over JTAG,
  matching the value read over host P2A/culvert. [JTAG-USAGE-GUIDE.md:250-256](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/JTAG-USAGE-GUIDE.md#L250-L256)
- Raptor drove it with an **Olimex ARM-USB-TINY + OpenOCD** ("sufficient to bring
  up U-Boot"). [RPI4-OPENOCD-JTAG-WIRING.md:73-78](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/RPI4-OPENOCD-JTAG-WIRING.md#L73-L78)
```

### 2.2 AST_UART1 — BMC console (4-pin, 3.3 V) ✅

```{admonition} Which SoC UART, and at what baud — a partial discrepancy
:class: important

**Instance (resolved):** the header silk-labelled `AST_UART1` connects to the
SoC's **UART2** (`0x1E784000`) — Linux **`ttyS1`**, which is exactly what the
Raptor firmware's `console=ttyS1` selects. The `AST_UART1` name is a board label,
**not** the SoC UART1 instance (SoC UART1 at `0x1E783000` is a separate, unrouted
port — {doc}`../hardware/registers/uart-vic-timers` records it as reading 0 edges
when driven).

**Baud (unresolved):** the Raptor firmware configures **115200**
(`CONFIG_BAUDRATE`, `console=ttyS1,115200`; 38400 for the DRAM-init debug path).
The rig bring-up over P2A, however, observed the live console at **1200** baud.
That discrepancy is not fully explained (a UART-clock/divisor difference on the
bring-up path is the leading theory) and is documented rather than asserted
either way — treat both numbers as candidates and probe before relying on one.
```

A 1×4 header just above the AST2050. The schematic netlist has since settled
the pinout the bring-up had partially inferred from Raptor's photo: **pin 1 =
`+5VSB`** (not the +3.3 V the photo suggested), **pin 2 = BMC TXD**
(ball U21, `TXD2`), **pin 3 = BMC RXD** (ball U20, `RXD2`), **pin 4 = GND**
({doc}`kgpe-d16-connectors` §2). The signal pins remain **3.3 V TTL** (baud:
see the note above) — and the "never connect pin 1" rule is now even more
important, since +5 V exceeds an RPi's absolute maximum.
[HEADER-PINOUTS.md:98-126](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/HEADER-PINOUTS.md#L98-L126)
[BMC-CONNECTORS.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/BMC-CONNECTORS.md#ast_uart1--bmc-serial-console)

```{list-table} AST_UART1 → RPi4 (leave pin 1 unconnected; cross TX↔RX)
:header-rows: 1
:widths: 30 34 36

* - AST_UART1 pin
  - Signal
  - RPi4
* - 1
  - +5VSB (schematic-corrected; photo said +3.3 V)
  - — (do NOT connect)
* - 2
  - BMC TXD (`AST_TXD2_R`, ball U21)
  - GPIO15 / RXD, phys 10
* - 3
  - BMC RXD (`AST_RXD2_R`, ball U20)
  - GPIO14 / TXD, phys 8
* - 4
  - GND
  - GND, phys 6
```

Sources: [BMC-CONNECTORS.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/BMC-CONNECTORS.md#ast_uart1--bmc-serial-console)
(netlist pinout), [HEADER-PINOUTS.md:105-126](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/HEADER-PINOUTS.md#L105-L126) [RPI4-OPENOCD-JTAG-WIRING.md:211-238](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/RPI4-OPENOCD-JTAG-WIRING.md#L211-L238)
(the original bring-up wiring). This header is the SoC's **UART2** (NS16550 at
`0x1E784000` = Linux `ttyS1`), per the note above — not the SoC UART1 at
`0x1E783000`.
[RPI4-OPENOCD-JTAG-WIRING.md:236-238](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/RPI4-OPENOCD-JTAG-WIRING.md#L236-L238) Press **Delete** within ~3 s of U-Boot start
to reach the bootloader.

### 2.3 BMC_FW1 — BMC SPI firmware socket ✅

**Identity resolved by the schematic.** The ASUS manual (§2.7.2) shows only
its location, pin 1 at lower-left, and a note about the **ASMB4** iKVM module,
so the bring-up docs treated its rumoured SPI role as unconfirmed.
[HEADER-PINOUTS.md:73-94](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/HEADER-PINOUTS.md#L73-L94)
The netlist settles it: `BMC_FW1` is the BMC's **socketed SPI firmware
flash** — SPI clock/MOSI/MISO plus chip-selects 0 and 2 straight to the
AST2050's ROM-controller balls, powered from `+3V3_AUX`, and carrying the
`AST_IKVMEN#`, `AST_SOLEN#` and `BMC_PRESENT#` feature straps. Full pinout
and signal table: {doc}`kgpe-d16-connectors` §4; BMC-side balls:
{doc}`kgpe-d16-wiring` §4. A socketed firmware chip means reflashing needs no
soldering — e.g. the Pi's hardware SPI0 with Raptor's `ast2050-flashrom`
fork. [RPI4-OPENOCD-JTAG-WIRING.md:242-268](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/RPI4-OPENOCD-JTAG-WIRING.md#L242-L268)
[BMC-CONNECTORS.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/BMC-CONNECTORS.md#bmc_fw1--bmc-spi-firmware-socket)

```{figure} /_static/diagrams/kgpe-d16-bmc-fw1.svg
:alt: BMC_FW1 2x7 socket pinout from the schematic netlist — SPI MOSI/CLK/MISO/CS0/CS2 to BMC balls Y1/Y2/AA4/AB9/W7, +3V3_AUX flash power, and the IKVMEN#, SOLEN# and BMC_PRESENT# feature straps.
:width: 90%

**BMC_FW1** — the BMC SPI firmware socket, pinout read from the schematic
netlist (previously documented here as a proprietary-pinout template).
```

### 2.4 AMD HDT (NB_JTAG_HEADER) — CPU debug, 20-pin HDT+ (1.27 mm) ⚠️

The host/CPU debug port: **AMD HDT** (Hardware Debug Tool), a proprietary JTAG
dialect for the Opteron 6100/6200/6300 (Family 10h/15h). It is **not** OpenOCD-
or RPi-drivable (fine 1.27 mm pitch, proprietary probe/software required — ASSET
InterTech / AMD HDT kit). [JTAG-HEADERS.md:62-95,236-239](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/JTAG-HEADERS.md#L62-L95)

```{list-table} AMD HDT+ 20-pin pinout
:header-rows: 1
:widths: 12 26 26 36

* - Pin
  - Signal
  - Direction
  - Description
* - 1 / 19
  - VDDIO
  - power
  - I/O reference from target
* - 2
  - TCK
  - probe → CPU
  - JTAG test clock
* - 4
  - TMS
  - probe → CPU
  - JTAG test mode select
* - 6
  - TDI
  - probe → CPU
  - JTAG test data in
* - 8
  - TDO
  - CPU → probe
  - JTAG test data out
* - 9
  - TRST_L
  - probe → CPU
  - JTAG test reset (active low)
* - 10
  - PWROK_BUF
  - CPU → probe
  - Buffered power-OK
* - 11/13/14/15
  - DBRDY3/2/0/1
  - CPU → probe
  - Debug ready per core group
* - 12
  - RESET_L
  - probe → CPU
  - Processor reset (active low)
* - 16
  - DBREQ_L
  - probe → CPU
  - Debug request (active low)
* - 3/5/7/17
  - GND
  - ground
  - Ground
* - 18 / 20
  - TEST19 / TEST18
  - —
  - Reserved/test (may float)
```

Source: [JTAG-HEADERS.md:96-140](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/JTAG-HEADERS.md#L96-L140). A 26-pin (25-signal + key) 2.54 mm HDT variant
exists for older boards. [JTAG-HEADERS.md:142-171](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/JTAG-HEADERS.md#L142-L171) The likely on-board JTAG scan
chain is `CPU1 → CPU2 → SR5690 → SP5100` (order unconfirmed).
[JTAG-HEADERS.md:358-376](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/JTAG-HEADERS.md#L358-L376)

### 2.5 Other footprints — NB_DEBUG_HEADER ✅, TEST_CON1/2 ⚠️

**NB_DEBUG_HEADER** — long unidentified (2nd HDT? POST? LPC?) — is resolved
by the schematic as the **SR5690's PCIe hot-plug/debug SMBus**
(`NB_DEBUG_HEADER1`, nets `PCIE_HP_SCL/SDA`; {doc}`kgpe-d16-i2c` §4.7).
**TEST_CON1/2** remain unconfirmed factory-ICT candidates — identify before
driving.
[HEADER-PINOUTS.md:130-159](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/HEADER-PINOUTS.md#L130-L159)

---

## 3. BMC GPIO wiring and power control


### 3.1 GPIO bank A init (spurious-host-operation guard)

Raptor's AST2050 U-Boot conditionally initialises **GPIO bank A bit 4** to
prevent spurious operation of the host during BMC boot. The change reads the
GPIO **direction** register before driving, only setting the data + direction
bits if not already set: [RAPTOR_ENGINEERING_AST2050_ANALYSIS.md:812-832](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/RAPTOR_ENGINEERING_AST2050_ANALYSIS.md#L812-L832)

```c
/* board/aspeed/ast2050/ast2050.c (Raptor commit 323b3ac) */
if (!((*((volatile ulong*)(AST_GPIO_BASE + 0x04))) & 0x00000010)) {
    *((volatile ulong*)(AST_GPIO_BASE + 0x00)) |= 0x00000010; /* data  bit4 */
    *((volatile ulong*)(AST_GPIO_BASE + 0x04)) |= 0x00000010; /* dir   bit4 */
}
```

- `AST_GPIO_BASE + 0x00` = GPIO data register; `+ 0x04` = GPIO direction
  register; bit 4 (`0x10`) = **GPIOA4**. [RAPTOR_ENGINEERING_AST2050_ANALYSIS.md:823-828](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/RAPTOR_ENGINEERING_AST2050_ANALYSIS.md#L823-L828)
- Making the write **conditional** (test direction first) avoids clobbering a
  host-driven line — "conditional GPIO initialization prevents conflicts".
  [RAPTOR_ENGINEERING_AST2050_ANALYSIS.md:832](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/RAPTOR_ENGINEERING_AST2050_ANALYSIS.md#L832)

The AST2050 GPIO controller, serial GPIO (SGPIO), and PWM/fan blocks are all
present in the Raptor port (`dev-gpio.c`, `dev-sgpio.c`, `dev-pwm-fan.c`), so an
open-firmware port has full GPIO/PWM primitives to build power/reset/fan control
from. [RAPTOR_ENGINEERING_AST2050_ANALYSIS.md:235-246,670-676](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/RAPTOR_ENGINEERING_AST2050_ANALYSIS.md#L235-L246)

### 3.2 Board power sequencing and observation

```{admonition} KGPE-D16 is power-on-with-AC
:class: note

- Applying **AC mains** boots the host **and** the BMC together — there is no
  soft power button in the current rig; power is switched at an **AC smart plug**
  (query / ON / OFF / TOGGLE over HTTP). Governed by the BIOS *Restore on AC
  Power Loss* setting; warm cycles (reboot / Ctrl-Alt-Del) avoid the DRAM
  re-train delay. [HARDWARE-ACCESS.md:194-227](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/HARDWARE-ACCESS.md#L194-L227)
- POST order on the host serial console: `BMC is booting, please wait …` →
  (~100–130 s) `BMC failed …` (the AST2050 stock firmware is dead; host BIOS
  continues) → memory/PCI init → boot prompt → PXE. [HARDWARE-ACCESS.md:216-222](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/HARDWARE-ACCESS.md#L216-L222)
- The host reaches the BMC over PCI as **ASPEED Graphics `[1a03:2000]` at
  `01:01.0`** (driver `ast`, 8 MB BAR0) — that BAR is the **P2A (PCIe→AHB)**
  doorway. IPMI KCS is declared (I/O `0xCA2`) but the BMC does **not** answer
  (no functional firmware). [hardware-inventory/README.md:31-39](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hardware-inventory/README.md#L31-L39)
```

**Independent BMC observation/control paths** (all cross-validated on real
hardware): (1) **JTAG** run-control via `AST_JTAG1` (§2.1); (2)
{doc}`P2A/culvert </debug/bring-up>` over the PCI BAR; (3) the **BMC UART**
via `AST_UART1` (§2.2). SoC power/clock
state is visible in the SCU: `SCU7C = 0x00000202` (silicon rev),
`SCU04 = 0x000FFE5C` (the datasheet reset value of the reset-control register; a
live board reads a different value), `SCU14 = 0x00003EFF` (the **frequency-counter
measurement** register — the hardware straps are in `SCU70`, not `SCU14`).
[JTAG-USAGE-GUIDE.md:250-256,442-444](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/JTAG-USAGE-GUIDE.md#L250-L256) The DDR2 native window is `0x40000000`
(64 MiB); the SPI boot flash is at `0x14000000` (SMC controller `0x16000000`).
[JTAG-USAGE-GUIDE.md:444](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/JTAG-USAGE-GUIDE.md#L444) [datasheets/README.md:36-38](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/datasheets/README.md#L36-L38)

```{admonition} Crash-safety rule (AHB)
:class: warning

Never write `0x0` or the SMC flash window `0x14000000` while the DRAM→`0x0` remap
is **not** set — it stalls the AST2050 AHB and can hang the host's PCIe. Work in
the native DRAM window (`0x40000000`) and SoC register space.
[JTAG-USAGE-GUIDE.md:318-322](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/JTAG-USAGE-GUIDE.md#L318-L322)
```

### 3.3 BMC Ethernet — PHY resolved, plus an NC-SI sideband

**The PHY question is closed.** The AST2050 {doc}`MAC
<../hardware/registers/network-mac-phy>` uses **RMII** to a Realtek
**RTL8201N-GR** (board ref `U5`, QFN-64) — the identity is read from the
schematic's part-description field, confirming what public sources
([15h.org](https://15h.org/index.php/Home), [The Retro Web](https://theretroweb.com/))
had suggested and the in-repo analysis had held open pending physical
confirmation. [datasheets/README.md:152](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/datasheets/README.md#L152)
[schematic-wiring](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/pinmaps/QU1_pins.md#ethernet-rmii--nc-si-18)
The part's registers and wiring: {doc}`../hardware/peripherals/rtl8201n`.

The schematic also revealed a **second network channel**: the MAC's RMII2
nets are bussed to *both* Intel 82574L host NICs as an NC-SI sideband, so the
BMC can share the host's LAN ports — see
{doc}`../hardware/peripherals/intel-82574l` and {doc}`kgpe-d16-wiring` §8.

---

## 4. AMD SP5100 southbridge context


The **AMD SP5100** (SB700-family) is the KGPE-D16 southbridge (`SU1`,
FCBGA-528), paired with the **SR5690 (RD890)** northbridge
([in-repo register reference](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/datasheets/AMD_SR5690_Register_Reference_Guide_43871.pdf))
over A-Link Express II. It is host-platform silicon managed by coreboot, but
the schematic work showed the BMC meets it on **four buses** — the AST2050 is
an LPC peripheral, a PCI device and a USB device of the SP5100, and the two
share the multi-master sensor SMBus ({doc}`kgpe-d16-wiring`,
{doc}`kgpe-d16-i2c`). Its complete 528-ball wiring is documented in
[`SP5100-SOUTHBRIDGE-WIRING.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/SP5100-SOUTHBRIDGE-WIRING.md).
[datasheets/README.md:46-55,106-107](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/datasheets/README.md#L46-L55) [hardware-inventory/README.md:17-19](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hardware-inventory/README.md#L17-L19)

```{list-table} SP5100 interfaces relevant to BMC / board management
:header-rows: 1
:widths: 24 76

* - Interface
  - Relevance
* - SMBus controller
  - Four segments (`SMBus0`–`3`): `SMBus0` is the private CPU/NB voltage-regulator SVI link; **`SMBus1`/`SMBus2` are shared with the BMC** — the same wires as BMC `I2C2`/`I2C3`, reaching the **W83795G at 0x2F** (`i2c-piix4`, I/O base `0x0B00`) and the DIMM SPD mux; ownership arbitrated by the `U23` buffer ({doc}`kgpe-d16-i2c` §3). [SP5100-SOUTHBRIDGE-WIRING.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/SP5100-SOUTHBRIDGE-WIRING.md#9-smbus--ic) [hardware-inventory/README.md:42](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hardware-inventory/README.md#L42)
* - LPC bus
  - Hosts the **BMC (KCS/IPMI path)**, the **W83667HG-A Super I/O** ({doc}`../hardware/peripherals/w83667hg`) and the TPM header on one bus ({doc}`kgpe-d16-wiring` §5). [datasheets/README.md:53](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/datasheets/README.md#L53) [SP5100-SOUTHBRIDGE-WIRING.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/SP5100-SOUTHBRIDGE-WIRING.md#4-lpc-host-bus--bmc-qu1--super-io-ou1--tpm)
* - Power / reset
  - The ACPI power state machine (`SLP_S3#`/`SLP_S5#`, `PWR_GOOD`, `RSMRST#`) lives here, cooperating with the Super-I/O — and this is where the BMC's remote-power GPIOs physically land (`AST_ATXPSON#` → PSU, `SYS_PWRGD` → BMC ball D9; {doc}`kgpe-d16-wiring` §11). The ASF remote power path (W83795G §1.8) is a third, parallel control path via the NIC side-band. [SP5100-SOUTHBRIDGE-WIRING.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/SP5100-SOUTHBRIDGE-WIRING.md#11-power--reset--acpi-state-machine)
* - SPI BIOS flash
  - The **host BIOS** lives in `FU1`, a **socketed** DIP-8 SPI flash on the SP5100's SPI controller — separate from the BMC's own `BMC_FW1`, and powered from `+3V3_AUX` so it is readable with the host off. Both firmware chips being socketed is what makes this board so friendly to open-firmware experiments. [SP5100-SOUTHBRIDGE-WIRING.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/SP5100-SOUTHBRIDGE-WIRING.md#8-spi-bios-flash--fu1)
* - SATA / USB / GPIO
  - 6× SATA II, USB OHCI/EHCI, GPIO — host peripherals. [JTAG-HEADERS.md:410-417](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/JTAG-HEADERS.md#L410-L417) [hardware-inventory/README.md:17-19](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hardware-inventory/README.md#L17-L19)
* - Embedded 8051
  - The SP5100 (like the SR5690) contains an embedded microcontroller that "requires a firmware upload from the main platform firmware or via JTAG" to start; it may be reachable on the HDT scan chain. [JTAG-HEADERS.md:402-417](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/JTAG-HEADERS.md#L402-L417)
```

The SP5100's registers are documented in the in-repo **AMD SP5100 Register
Reference Guide (publication 44413, 317 pp)** [SP5100 RG](#sources); its coreboot driver is
[`southbridge/amd/sb700`](https://github.com/coreboot/coreboot/tree/4.11/src/southbridge/amd/sb700)
(coreboot 4.11, the last release carrying the KGPE-D16). [datasheets/README.md:107](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/datasheets/README.md#L107) For BMC firmware the key
takeaways are: the **hwmon (W83795G) sits on a bus the BMC and SP5100 share**
(so an open BMC firmware can read it directly, subject to the arbitration
hazards in {doc}`kgpe-d16-i2c` §3), the **host serial console is a Super I/O
UART behind SP5100 LPC** (distinct from the BMC's `AST_UART1`, but joinable
to the BMC through the SOL mux — {doc}`kgpe-d16-wiring` §10), and **platform
power/reset is a three-way handshake** between the SP5100's ACPI machine, the
Super-I/O's sequencing logic, and the BMC's platform-control GPIOs
({doc}`kgpe-d16-wiring` §11).

---

## See also

**Related pages**

- {doc}`kgpe-d16-wiring` · {doc}`kgpe-d16-i2c` · {doc}`kgpe-d16-connectors` — the schematic-derived wiring companion pages
- {doc}`/hardware/soc-ast2050` — the AST2050 SoC this board's BMC is built on
- {doc}`/debug/jtag-uart` — the JTAG/UART wiring and OpenOCD invocation
- {doc}`/debug/bring-up` — the P2A + JTAG out-of-band bring-up paths
- {doc}`/drivers/linux` — the G3 kernel fixes verified on this board
- {doc}`/firmware/openbmc` — OpenBMC brought up on this real AST2050

**External references**

- [Raptor Engineering](https://www.raptorengineering.com/) — author of the known-good AST2050 Linux 2.6.28.9 port this board follows
- [coreboot mainboard documentation](https://doc.coreboot.org/mainboard/index.html) — the KGPE-D16 is a supported coreboot mainboard
- [OpenBMC documentation](https://github.com/openbmc/docs) — the open BMC firmware target for this board

## Sources

- **[`asus-kgpe-d16-firmware/`](https://github.com/mithro/ai-shenanigans-for-bmcs/tree/main/asus-kgpe-d16-firmware)** — [`HEADER-PINOUTS.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/HEADER-PINOUTS.md), [`JTAG-HEADERS.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/JTAG-HEADERS.md),
  [`JTAG-USAGE-GUIDE.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/JTAG-USAGE-GUIDE.md), [`RPI4-OPENOCD-JTAG-WIRING.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/RPI4-OPENOCD-JTAG-WIRING.md) (header pinouts +
  RPi4 wiring), [`datasheets/README.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/datasheets/README.md),
  [`hardware-inventory/README.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hardware-inventory/README.md),
  [`HARDWARE-ACCESS.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/HARDWARE-ACCESS.md),
  and the AST2050 bring-up docs (GPIO/power, verified
  IDCODE `0x07926f0f`, `SCU7C=0x202`).
- **[`schematic-wiring/`](https://github.com/mithro/ai-shenanigans-for-bmcs/tree/main/asus-kgpe-d16-firmware/schematic-wiring)** — the pin-level netlist reverse
  engineering ([`AST2050-BMC-WIRING.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md),
  [`BMC-CONNECTORS.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/BMC-CONNECTORS.md),
  [`I2C-SMBUS-TOPOLOGY.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/I2C-SMBUS-TOPOLOGY.md),
  [`SP5100-SOUTHBRIDGE-WIRING.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/SP5100-SOUTHBRIDGE-WIRING.md)) —
  the source of the identity resolutions and corrections flagged on this page.
- **[AMD SP5100 Register Reference Guide](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/datasheets/AMD_SP5100_Register_Reference_Guide_44413.pdf)** (44413) — the southbridge.
- The on-board hardware monitor is documented at
  {doc}`../hardware/peripherals/w83795g`.
