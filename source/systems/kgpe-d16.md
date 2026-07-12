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
  - DDR2, mapped at `0x40000000`
* - Boot flash
  - SPI NOR at `0x14000000`
* - Console
  - UART2 (`0x1E784000`); **1200 8N1** on this board (see {doc}`../hardware/registers/uart-vic-timers`)
* - Debug
  - `AST_JTAG1` (BMC JTAG) + AMD HDT (host CPU); see {doc}`../debug/jtag-uart`
```

## Why this board leads the SoC work

The AST2050 is **not supported by mainline Linux** — the earliest supported
Aspeed generation is the AST2400 ("G4"). Raptor Engineering shipped a working
Linux 2.6.28.9 AST2050 port, which gives a reference for every SoC block (clock,
SDRAM, SMC/flash, MAC, GPIO, I2C, watchdog). The upstream path is a new
`aspeed-g3.dtsi` include plus `aspeed,ast2050-*` compatibles on the existing
mainline Aspeed drivers — see {doc}`../hardware/soc-ast2050` and
{doc}`../drivers/linux`.

## Emulation & firmware status

- **QEMU** — a custom `kgpe-d16-bmc` machine + new `ast2050` SoC boots U-Boot →
  Linux → SSH, and also boots the Raptor 2.6.28.9 + musl stack. See
  {doc}`../emulation/qemu`.
- **OpenBMC / WallaBMC** — planned; the board reuses the shared AST2050 layers.

The KGPE-D16 has no public proprietary BMC image, so proprietary-firmware
emulation proofs use the Dell C410X image (also AST2050) on the same machine.

## Debug / JTAG / UART / BMC headers


The KGPE-D16 has several **unpopulated** debug footprints, not documented in the
ASUS user manual, confirmed by Raptor Engineering. [JTAG-HEADERS.md:1-19] Two are
BMC-side (`AST_JTAG1`, `AST_UART1`), the rest are host/CPU-side.

```{admonition} Confidence + pin-1 safety
:class: warning

A wrong pin-1 assumption on a live board back-feeds the AST2050. **✅ VERIFIED** =
from a cited source; **🔶 STANDARD** = a documented standard the header follows
(confirm pin 1 by eye); **⚠️ TEMPLATE** = shape only, probe your board. Both
`AST_*` headers are **unpopulated footprints** above the AST2050 — you solder
headers in. [HEADER-PINOUTS.md:8-29] Both BMC-side sides are **3.3 V**; the RPi4
is **not** 5 V tolerant. [RPI4-OPENOCD-JTAG-WIRING.md:41-44]
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
  - ASMB4/5 management-module / firmware slot
  - flashrom (SPI) — verify
  - 🔶 / ⚠️
* - NB_JTAG_HEADER
  - AMD HDT (CPU/NB debug), 20-pin HDT+ (1.27 mm)
  - proprietary probe only
  - ⚠️ not OpenOCD
* - NB_DEBUG_HEADER
  - 2nd HDT? / POST / LPC — unconfirmed
  - identify first
  - ⚠️
* - TEST_CON1 / TEST_CON2
  - factory ICT test pads
  - unknown
  - ⚠️ probe first
```

Source: [RPI4-OPENOCD-JTAG-WIRING.md:64-79] [HEADER-PINOUTS.md:17-24].

### 2.1 AST_JTAG1 — BMC JTAG (20-pin ARM, 2×10, 2.54 mm) ✅

Standard ARM 20-pin JTAG. Pin 1 = square pad (top-left); odd column = signal,
even column = GND (except pins 1–2). [HEADER-PINOUTS.md:37-66] "diagram: TODO".

```
        AST_JTAG1  -  20-pin ARM JTAG (2x10, 0.1")
        component side - pin 1 = square pad (top-left)

          +---------+
 VTref  1 | @     o |  2  Vsupply (NC)
 nTRST  3 | o     o |  4  GND
   TDI  5 | o     o |  6  GND
   TMS  7 | o     o |  8  GND
   TCK  9 | o     o | 10  GND
  RTCK 11 | o     o | 12  GND
   TDO 13 | o     o | 14  GND
 nSRST 15 | o     o | 16  GND
 DBGRQ 17 | o     o | 18  GND
  (NC) 19 | o     o | 20  GND
          +---------+
        (@ = pin 1 / square pad)
```

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

Sources: [HEADER-PINOUTS.md:43-66] [RPI4-OPENOCD-JTAG-WIRING.md:110-136].

```{admonition} Verified JTAG facts (real hardware)
:class: note

- **TAP IDCODE `0x07926f0f`** — the ARM926EJ-S generic TAP (Raptor-confirmed on
  this exact AST2050). EmbeddedICE version **6**; **2** hardware breakpoint/
  watchpoint units. [JTAG-USAGE-GUIDE.md:128-137,437-439]
- Debug arch is **EmbeddedICE-RT over raw JTAG**, *not* CoreSight/SWD — use a
  raw-JTAG adapter (Pi bit-bang / FTDI / J-Link); SWD-only probes (ST-Link,
  CMSIS-DAP, Black Magic) will not work. [RPI4-OPENOCD-JTAG-WIRING.md:52-58]
- Reset topology is `trst_and_srst combined`: SRST also resets the EmbeddedICE
  logic **inside the silicon**, so a clean reset-vector halt is impossible;
  `reset halt` catches the core just past the vector. [JTAG-USAGE-GUIDE.md:217-233]
- Cross-check anchor: `SCU7C` (`0x1E6E207C`) reads **`0x00000202`** over JTAG,
  matching the value read over host P2A/culvert. [JTAG-USAGE-GUIDE.md:250-256]
- Raptor drove it with an **Olimex ARM-USB-TINY + OpenOCD** ("sufficient to bring
  up U-Boot"). [RPI4-OPENOCD-JTAG-WIRING.md:73-78]
```

### 2.2 AST_UART1 — BMC console (4-pin, 3.3 V) ✅

A 1×4 header just above the AST2050; ends fixed by Raptor's photo as **+3.3 V …
GND**, the two middle pins TX/RX (confirm by probing — BMC TXD idles high and
bursts at boot). **3.3 V TTL, 115200 8N1.** [HEADER-PINOUTS.md:98-126] "diagram:
TODO".

```
      AST_UART1 - 4-pin 3.3V ARM UART (1x4), pin1 = square pad
        +3.3V     TX/RX     RX/TX      GND
        pin1      pin2      pin3       pin4
```

```{list-table} AST_UART1 → RPi4 (leave +3.3 V unconnected; cross TX↔RX)
:header-rows: 1
:widths: 30 34 36

* - AST_UART1 pin
  - Signal
  - RPi4
* - 1
  - +3.3 V (BMC rail)
  - — (do NOT connect)
* - 2 or 3
  - BMC TXD
  - GPIO15 / RXD, phys 10
* - 3 or 2
  - BMC RXD
  - GPIO14 / TXD, phys 8
* - 4
  - GND
  - GND, phys 6
```

Sources: [HEADER-PINOUTS.md:105-126] [RPI4-OPENOCD-JTAG-WIRING.md:211-238]. This
is the AST2050 **UART1** (NS16550 at `0x1E783000`; UART2 is `0x1E784000`).
[RPI4-OPENOCD-JTAG-WIRING.md:236-238] Press **Delete** within ~3 s of U-Boot start
to reach the bootloader.

### 2.3 BMC_FW1 — ASMB4/5 module / firmware slot 🔶

The ASUS manual (§2.7.2) shows only its location and **pin 1 at lower-left**, with
the note that it supports an **ASUS Server Management Board 4 (ASMB4)** iKVM
module; no per-pin signals are published. [HEADER-PINOUTS.md:73-94] Its rumored
role as a BMC-SPI-flash recovery path is **unconfirmed** — treat it as a flashrom
(SPI) target only if continuity to the AST2050 boot flash (an SOIC-8 near the SoC)
is proven. If it is SPI, drive it from the Pi's hardware SPI0 with Raptor's
`ast2050-flashrom` fork. [RPI4-OPENOCD-JTAG-WIRING.md:242-268] "diagram: TODO".

```
        BMC_FW1  -  2-row header (ASMB4-iKVM slot)
        +-----------------------------+
        |  o  o  o  o  o  o  o  o ...  |   signals = PROPRIETARY (ASMB4)
        |  @  o  o  o  o  o  o  o ...  |   @ = pin 1 (lower-left)
        +-----------------------------+
```

### 2.4 AMD HDT (NB_JTAG_HEADER) — CPU debug, 20-pin HDT+ (1.27 mm) ⚠️

The host/CPU debug port: **AMD HDT** (Hardware Debug Tool), a proprietary JTAG
dialect for the Opteron 6100/6200/6300 (Family 10h/15h). It is **not** OpenOCD-
or RPi-drivable (fine 1.27 mm pitch, proprietary probe/software required — ASSET
InterTech / AMD HDT kit). [JTAG-HEADERS.md:62-95,236-239] "diagram: TODO".

```
        AMD HDT+ (20-pin, 2x10, 1.27 mm) - pin 1 top-left
 ┌─────────────────────────┐
 │  1 VDDIO    TCK     2  │
 │  3 GND      TMS     4  │
 │  5 GND      TDI     6  │
 │  7 GND      TDO     8  │
 │  9 TRST_L   PWROK  10  │
 │ 11 DBRDY3   RESET  12  │
 │ 13 DBRDY2   DBRDY0 14  │
 │ 15 DBRDY1   DBREQ  16  │
 │ 17 GND      TEST19 18  │
 │ 19 VDDIO    TEST18 20  │
 └─────────────────────────┘
```

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

Source: [JTAG-HEADERS.md:96-140]. A 26-pin (25-signal + key) 2.54 mm HDT variant
exists for older boards. [JTAG-HEADERS.md:142-171] The likely on-board JTAG scan
chain is `CPU1 → CPU2 → SR5690 → SP5100` (order unconfirmed).
[JTAG-HEADERS.md:358-376] **NB_DEBUG_HEADER** and **TEST_CON1/2** are unconfirmed
(possible 2nd HDT / POST / LPC / factory ICT) — identify before driving.
[HEADER-PINOUTS.md:130-159]

---

## BMC GPIO wiring and power control


### 3.1 GPIO bank A init (spurious-host-operation guard)

Raptor's AST2050 U-Boot conditionally initialises **GPIO bank A bit 4** to
prevent spurious operation of the host during BMC boot. The change reads the
GPIO **direction** register before driving, only setting the data + direction
bits if not already set: [RAPTOR_ENGINEERING_AST2050_ANALYSIS.md:812-832]

```c
/* board/aspeed/ast2050/ast2050.c (Raptor commit 323b3ac) */
if (!((*((volatile ulong*)(AST_GPIO_BASE + 0x04))) & 0x00000010)) {
    *((volatile ulong*)(AST_GPIO_BASE + 0x00)) |= 0x00000010; /* data  bit4 */
    *((volatile ulong*)(AST_GPIO_BASE + 0x04)) |= 0x00000010; /* dir   bit4 */
}
```

- `AST_GPIO_BASE + 0x00` = GPIO data register; `+ 0x04` = GPIO direction
  register; bit 4 (`0x10`) = **GPIOA4**. [RAPTOR_ENGINEERING_AST2050_ANALYSIS.md:823-828]
- Making the write **conditional** (test direction first) avoids clobbering a
  host-driven line — "conditional GPIO initialization prevents conflicts".
  [RAPTOR_ENGINEERING_AST2050_ANALYSIS.md:832]

The AST2050 GPIO controller, serial GPIO (SGPIO), and PWM/fan blocks are all
present in the Raptor port (`dev-gpio.c`, `dev-sgpio.c`, `dev-pwm-fan.c`), so an
open-firmware port has full GPIO/PWM primitives to build power/reset/fan control
from. [RAPTOR_ENGINEERING_AST2050_ANALYSIS.md:235-246,670-676]

### 3.2 Board power sequencing and observation

```{admonition} KGPE-D16 is power-on-with-AC
:class: note

- Applying **AC mains** boots the host **and** the BMC together — there is no
  soft power button in the current rig; power is switched at an **AC smart plug**
  (query / ON / OFF / TOGGLE over HTTP). Governed by the BIOS *Restore on AC
  Power Loss* setting; warm cycles (reboot / Ctrl-Alt-Del) avoid the DRAM
  re-train delay. [HARDWARE-ACCESS.md:194-227]
- POST order on the host serial console: `BMC is booting, please wait …` →
  (~100–130 s) `BMC failed …` (the AST2050 stock firmware is dead; host BIOS
  continues) → memory/PCI init → boot prompt → PXE. [HARDWARE-ACCESS.md:216-222]
- The host reaches the BMC over PCI as **ASPEED Graphics `[1a03:2000]` at
  `01:01.0`** (driver `ast`, 8 MB BAR0) — that BAR is the **P2A (PCIe→AHB)**
  doorway. IPMI KCS is declared (I/O `0xCA2`) but the BMC does **not** answer
  (no functional firmware). [hardware-inventory/README.md:31-39]
```

**Independent BMC observation/control paths** (all cross-validated on real
hardware): (1) **JTAG** run-control via `AST_JTAG1` (§2.1); (2) **P2A/culvert**
over the PCI BAR; (3) the **BMC UART** via `AST_UART1` (§2.2). SoC power/clock
state is visible in the SCU: `SCU7C = 0x00000202` (silicon rev),
`SCU04 = 0x000FFE5C`, `SCU14 = 0x00003EFF` (hardware strap/config).
[JTAG-USAGE-GUIDE.md:250-256,442-444] The DDR2 native window is `0x40000000`
(64 MB); the SPI boot flash is at `0x14000000` (SMC controller `0x16000000`).
[JTAG-USAGE-GUIDE.md:444] [datasheets/README.md:36-38]

```{admonition} Crash-safety rule (AHB)
:class: warning

Never write `0x0` or the SMC flash window `0x14000000` while the DRAM→`0x0` remap
is **not** set — it stalls the AST2050 AHB and can hang the host's PCIe. Work in
the native DRAM window (`0x40000000`) and SoC register space.
[JTAG-USAGE-GUIDE.md:318-322]
```

### 3.3 BMC Ethernet PHY

The AST2050 MAC0 uses **RMII** to an external Fast-Ethernet PHY. Public sources
(15h.org, The Retro Web) identify it as a **Realtek RTL8201N** class part.
[WebSearch: theretroweb / 15h.org] The in-repo analysis flags the exact PHY as an
**open question** — the RTL8201EL/RTL8211BN/RTL8201N names in the Raptor analysis
are the AST2050 driver's *supported* list, not a confirmed board ID; a board photo
/ ASMB schematic is needed to close it. [datasheets/README.md:152] Treat "RTL8201N"
as the strong candidate pending physical confirmation.

---

## AMD SP5100 southbridge context


The **AMD SP5100** (SB700-family) is the KGPE-D16 southbridge, paired with the
**SR5690 (RD890)** northbridge over A-Link Express II. It is host-platform
silicon managed by coreboot — **not** on the AST2050 BMC bus — but it is the
board's SMBus/LPC/power/reset hub and hosts the W83795G, so it matters to BMC
work. [datasheets/README.md:46-55,106-107] [hardware-inventory/README.md:17-19]

```{list-table} SP5100 interfaces relevant to BMC / board management
:header-rows: 1
:widths: 24 76

* - Interface
  - Relevance
* - SMBus controller
  - Hosts the **W83795G at 0x2F** (`i2c-piix4`, I/O base `0x0B00`) plus DIMM SPD `0x50-0x57`; driven by an embedded 8051 core. [datasheets/README.md:52-53] [hardware-inventory/README.md:42] [JTAG-HEADERS.md:402-408]
* - LPC bus
  - Connects the **W83667HG-A Super I/O** (host serial/COM, hwmon backup) and TPM; the LPC/Port-80 path is a candidate for the unidentified `NB_DEBUG_HEADER`. [datasheets/README.md:53] [HEADER-PINOUTS.md:141-144]
* - Power / reset
  - SB700-family power sequencing, ACPI/power-management, and platform reset live here; the ASF remote power path (W83795G §1.8) drives platform power via the NIC side-band, parallel to any BMC path.
* - SATA / USB / GPIO
  - 6× SATA II, USB OHCI/EHCI, GPIO — host peripherals. [JTAG-HEADERS.md:410-417] [hardware-inventory/README.md:17-19]
* - Embedded 8051
  - The SP5100 (like the SR5690) contains an embedded microcontroller that "requires a firmware upload from the main platform firmware or via JTAG" to start; it may be reachable on the HDT scan chain. [JTAG-HEADERS.md:402-417]
```

The SP5100's registers are documented in the in-repo **AMD SP5100 Register
Reference Guide (publication 44413, 317 pp)** [SP5100 RG]; its coreboot driver is
`southbridge/amd/sb700`. [datasheets/README.md:107] For BMC firmware the key
takeaways are: the **hwmon (W83795G) lives on the SP5100 SMBus**, the **host
serial console is a Super I/O behind SP5100 LPC** (distinct from the BMC's
`AST_UART1`), and **platform power/reset is an SP5100/ASF concern**, separate from
the AST2050's own GPIO/WDT reset primitives (§3).

---

## Sources

- **`asus-kgpe-d16-firmware/`** — `HEADER-PINOUTS.md`, `JTAG-HEADERS.md`,
  `JTAG-USAGE-GUIDE.md`, `RPI4-OPENOCD-JTAG-WIRING.md` (header pinouts +
  RPi4 wiring), and the AST2050 bring-up docs (GPIO/power, verified
  IDCODE `0x07926f0f`, `SCU7C=0x202`).
- **AMD SP5100 Register Reference Guide** (44413) — the southbridge.
- The on-board hardware monitor is documented at
  {doc}`../hardware/peripherals/w83795g`.
