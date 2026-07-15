# HPE Intelligent Modular PDU (AF531A)

An intelligent **Power Distribution Unit**. Unlike the other two boards it uses a
**Digi NS9360** SoC (not Aspeed), and its stock firmware is **NET+OS** (a
ThreadX-based RTOS), not Linux. The same ARM926EJ-S core keeps it in-family for
toolchains and the Zephyr ARMv5 port.

```{list-table}
:header-rows: 0
:widths: 30 70

* - SoC
  - Digi NS9360
* - CPU core
  - ARM926EJ-S (ARMv5TE)
* - Power metering
  - MAXQ3180 metering AFE
* - Display
  - dedicated MCU over an "extension-bar" protocol
* - Boot flash
  - dual CFI NOR (8 MiB total)
* - Stock firmware
  - NET+OS / ThreadX (RomPager web server); reverse-engineered
```

## Open-firmware path

There is **no mainline Linux** for the NS9360, so this board's open-firmware
stack is built up in stages (all five layers are in scope):

1. **U-Boot** — an open NS9360 port (serial, GPIO, clock, I2C, Ethernet, CFI
   flash) that already boots in QEMU. See {doc}`../drivers/uboot`.
2. **Linux** — forward-port the archived [`mach-ns9xxx`](https://github.com/torvalds/linux/tree/v2.6.39/arch/arm/mach-ns9xxx) support toward a modern
   kernel. See {doc}`../drivers/linux`.
3. **Zephyr** — via the shared ARMv5 architecture port. See
   {doc}`../drivers/zephyr`.
4. **OpenBMC** on the Linux stack, and **WallaBMC** on the Zephyr stack.

## Emulation status

A QEMU `ns9360` machine (ARM926EJ-S, SDRAM, dual CFI flash) boots the U-Boot
port under a serial-socket smoke test. Board-complete modelling (MAXQ3180,
display MCU, Ethernet PHY) is planned — see {doc}`../emulation/qemu`.

## Board topology and headers

```{figure} /_static/diagrams/ipdu-j1-jtag.svg
:alt: HPE iPDU (Digi NS9360) J1 20-pin ARM JTAG header, standard Multi-ICE pinout, marked CANDIDATE (pin-to-signal map needs board tracing). NS9360 TAP IDCODE 0x09105031, bist_en_n strap.
:width: 80%

**J1** — the iPDU's 20-pin ARM JTAG header (standard Multi-ICE layout). Marked
*candidate* until the pin→signal map is confirmed by board tracing; the NS9360
TAP IDCODE is `0x09105031`.
```


The Core Unit controller board is a single-SoC design: the NS9360 is the only
general-purpose processor. The MAXQ3180 (metering) and TMP89FM42 (display) are
satellite devices on dedicated serial links, and the Ethernet PHY hangs off the
NS9360 MII/MAC. [`ANALYSIS.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/ANALYSIS.md)

```{list-table} Signal-chain overview
:header-rows: 1
:widths: 22 20 30 28

* - Peripheral
  - Ref des
  - Link to NS9360
  - Purpose
* - ICS1893AFLF Ethernet PHY
  - U10
  - MII/RMII + MDIO/MDC (SMI)
  - 10/100 RJ-45 management port
* - MAXQ3180-RAN metering AFE
  - U15
  - SPI (NS9360 = master), DMA-driven
  - Poly-phase V/I/P/energy/frequency
* - TMP89FM42LUG display MCU
  - U45
  - UART via MAX3243EI (RS-232)
  - Front-panel 7-seg/LED/buzzer bezel
* - Extension bars ("sticks")
  - J2/J29, J3/J30, J4/J31
  - Packet serial ("stick.Start/End")
  - Up to 6 sticks/core, 2 cores
* - Daisy-chain to next iPDU
  - conn 7
  - UART ("Core DC Proto")
  - Cascade / redundancy pairing
```

```{admonition} Extension-bar / daisy-chain protocols are out of scope for the port
:class: note

The outlet power-control (`stick.Start`/`stick.End`) and cascade (`Core DC
Proto`) packet protocols are **application-level NET+OS firmware** running on top
of the SoC's UART/serial blocks — they are named here for board context but not
register-mapped, because the open-firmware path for this board is a **U-Boot /
Linux / Zephyr SoC port** ({doc}`/drivers/uboot`), not a re-implementation of the
stock RTOS application. The SoC serial controllers those protocols ride on *are*
fully documented in {doc}`/hardware/soc-ns9360-memory-serial`.
```

```{figure} /_static/diagrams/ipdu-board-block.svg
:alt: HPE iPDU board signal chain: Ethernet magnetics and ICS1893 PHY to the NS9360 SoC, with the MAXQ3180 energy meter, TMP89 display/bezel MCU and daisy-chained extension bars.
:width: 90%

The HPE iPDU board signal chain around the NS9360.
```

### Header / connector inventory

```{list-table} Debug, bus and programming headers
:header-rows: 1
:widths: 12 20 40 28

* - Ref des
  - Silkscreen / label
  - Function
  - Connected device
* - J1
  - (none)
  - ARM JTAG debug — large ribbon, likely 2x10 (20-pin) 0.1"
  - NS9360 ARM926EJ-S TAP
* - J6
  - (none)
  - Secondary debug — black 2x5 (10-pin) header
  - NS9360 or a sub-MCU (needs tracing)
* - J25
  - "Digi UART"
  - Debug serial console, 115200/8/N/1
  - NS9360 Serial Port A
* - J11
  - "Mox SPI"
  - SPI bus access
  - MAXQ3180 or an SPI flash
* - J10
  - "PIC JTAG" (earlier read "PLC DIAG")
  - Sub-MCU JTAG / programming
  - TMP89FM42LUG (no PLC modem in firmware)
* - J27
  - "I2C"
  - I2C bus header
  - NS9360 I2C (gpio[34]=SCL, gpio[35]=SDA)
* - J2 / J29
  - (white pair)
  - Extension-bar bus connector pair
  - Power/outlet section
* - J3 / J30
  - (white pair)
  - Extension-bar bus connector pair
  - Power/outlet section
* - J4 / J31
  - (white pair)
  - Extension-bar bus connector pair
  - Power/outlet section
* - (test point)
  - "BIST EN"
  - ARM debug-mode enable strap
  - NS9360 `bist_en_n` (BGA V5)
```

Sources: [`ANALYSIS.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/ANALYSIS.md), [`HEADERS-J1-J6.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/HEADERS-J1-J6.md). Physical form factors are
confirmed from board photos; exact J1/J6 pin-to-signal mapping still requires
board tracing (open item in [`STATUS.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/STATUS.md)).

### J1 — 20-pin ARM JTAG (standard Multi-ICE pinout)

J1's ribbon form factor matches the standard 20-pin ARM JTAG connector used in
the NS9360 reference design ("JTAG 20 PIN HEADER", `HEADER 10X2.1SP`). If J1
follows that standard, the pinout is: [`HEADERS-J1-J6.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/HEADERS-J1-J6.md)

```{list-table} J1 candidate pinout (standard ARM 20-pin JTAG)
:header-rows: 1
:widths: 12 26 12 26 24

* - Pin
  - Signal
  - Pin
  - Signal
  - Notes
* - 1
  - VTref (3.3 V)
  - 2
  - VCC / NC
  - VTref is a level-reference **input** to the debugger, not target power
* - 3
  - nTRST
  - 4
  - GND
  - Series R (≈33 Ω) in ref design
* - 5
  - TDI
  - 6
  - GND
  - —
* - 7
  - TMS
  - 8
  - GND
  - —
* - 9
  - TCK
  - 10
  - GND
  - —
* - 11
  - RTCK
  - 12
  - GND
  - Adaptive clocking return
* - 13
  - TDO
  - 14
  - GND
  - Series R (≈33 Ω)
* - 15
  - nSRST
  - 16
  - GND
  - MAX811 reset monitor in ref design
* - 17
  - DBGRQ
  - 18
  - GND
  - —
* - 19
  - 5V-Supply
  - 20
  - GND
  - Optional adapter power (<100 mA); not target power
```

### NS9360 JTAG TAP and debug-enable strap

```{list-table} NS9360 ARM926EJ-S JTAG signals (BGA272)
:header-rows: 1
:widths: 14 14 18 28 26

* - BGA ball
  - Signal
  - Direction
  - Pull / drive
  - Description
* - G18
  - tck
  - Input
  - none
  - Test clock
* - D20
  - tdi
  - Input
  - internal pull-up
  - Test data in
* - G19
  - tdo
  - Output
  - 2 mA
  - Test data out
* - F19
  - tms
  - Input
  - internal pull-up
  - Test mode select
* - F20
  - trst_n
  - Input
  - internal pull-up
  - Test reset (active low)
* - Y4
  - rtck
  - I/O
  - internal pull-up, 2 mA
  - Return test clock (adaptive)
* - V5
  - bist_en_n
  - Input strap
  - 2.4K down = normal / 10K up = debug
  - Board "BIST EN" test point
```

- TAP parameters (confirmed on the NS9360 via Amontec JTAGkey): **IRLen = 4,
  IDCODE = 0x09105031**, core = `arm926ejs`, little-endian. [`HEADERS-J1-J6.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/HEADERS-J1-J6.md)
- ARM debug is gated by `bist_en_n` (V5). Production boards strap it low
  (debug disabled) — OpenOCD then reads "unknown EmbeddedICE version (comms
  ctrl: 0x00000000)". Re-strapping the "BIST EN" test point to a pull-up
  enables halt-mode debug. [`HEADERS-J1-J6.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/HEADERS-J1-J6.md)
- The ARM926EJ-S uses **EmbeddedICE-RT over raw JTAG** (not CoreSight/SWD), so
  CMSIS-DAP / SWD-only probes cannot debug it; J-Link, FT2232H (TUMPA/JTAGkey),
  or an RPi `bcm2835gpio` bitbang adapter are required. [`HEADERS-J1-J6.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/HEADERS-J1-J6.md)

---

## See also

**Related pages**

- {doc}`/hardware/soc-ns9360` — the Digi NS9360 SoC this board is built on
- {doc}`/hardware/soc-ns9360-io` — the GPIO/serial I/O the board wires up
- {doc}`/hardware/peripherals/maxq3180` — the metering AFE (U15)
- {doc}`/hardware/peripherals/ics1893` — the Ethernet PHY (U10)
- {doc}`/drivers/uboot` — the open NS9360 U-Boot port for this board

**External references**

- [NS9360 Hardware Reference (Digi 90000675 rev J)](https://ftp1.digi.com/support/documentation/90000675_J.pdf) — the SoC register authority
- [NS9360 Datasheet (Digi 91001326 rev D)](https://ftp1.digi.com/support/documentation/91001326_D.pdf) — electrical/strap reference
- [Linux `arch/arm/mach-ns9xxx` (v2.6.39)](https://github.com/torvalds/linux/tree/v2.6.39/arch/arm/mach-ns9xxx) — the historical mainline NS9360 platform tree
- [U-Boot documentation](https://docs.u-boot.org/en/latest/) — upstream docs for the open-firmware path

## Sources

- **`hpe-ipdu-firmware/`** — [`ANALYSIS.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/ANALYSIS.md), [`HEADERS-J1-J6.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/HEADERS-J1-J6.md), [`STATUS.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/STATUS.md)
  (board inventory, J1-J6 headers, reverse-engineered protocols).
- Per-device references: {doc}`../hardware/peripherals/ics1893`,
  {doc}`../hardware/peripherals/maxq3180`, {doc}`../hardware/peripherals/tmp89`,
  and the SoC at {doc}`../hardware/soc-ns9360`.
