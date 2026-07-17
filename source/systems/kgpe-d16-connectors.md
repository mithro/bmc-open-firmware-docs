# KGPE-D16 connectors & headers (BMC-wired)

Physical pinout diagrams and full signal tables for every connector, header,
socket and jumper on the ASUS KGPE-D16 that connects to the AST2050 BMC. Pin
numbers and nets are read from the schematic netlist (provenance:
{doc}`kgpe-d16-wiring`); the source document is
[`BMC-CONNECTORS.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/BMC-CONNECTORS.md),
and each SVG is generated from the netlist by
[`tools/connector_svg.py`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/tools/connector_svg.py).

```{admonition} Reading the diagrams — and one safety rule
:class: warning

Dual-row 0.1″ headers follow the standard convention: odd pins on the top row,
even on the bottom, **pin 1 marked with the red square pad**. Pins are
colour-coded by function (power / ground / signal / JTAG / strap /
no-connect). Always verify pin 1 against the board silkscreen before wiring
anything — a wrong pin-1 assumption on a live board can back-feed the
AST2050 ({doc}`kgpe-d16` §2 records the confidence system used during
bring-up, from before the schematic became available).
```

## At a glance

```{list-table}
:header-rows: 1
:widths: 16 16 40 28

* - Connector
  - Type
  - What it is
  - BMC involvement
* - `VGA1`
  - HD-15 (female)
  - on-board VGA output
  - integrated video: RGB DAC, DDC, sync (§1)
* - `AST_UART1`
  - 1×4 header
  - BMC serial console
  - SoC UART2 (`AST_TXD2/RXD2`) (§2)
* - `AST_JTAG1`
  - 2×10 header
  - BMC ARM926 JTAG
  - full JTAG + `SRST#` (§3)
* - `BMC_FW1`
  - 2×7 DIP socket
  - BMC firmware flash (socketed)
  - SPI bus + feature straps (§4)
* - `PANEL1`
  - 2×10 header
  - system front panel
  - power/reset buttons, message LED, NMI (§5)
* - `AUX_PANEL1`
  - 2×10 header
  - ASUS auxiliary panel
  - locator LED/button, I²C8, LAN LEDs (§6)
* - `PSUSMB1`
  - 1×5 header
  - PSU SMBus/PMBus
  - BMC `I2C1` + alert (§7)
* - `TPM1`
  - 2×10 header
  - TPM module (LPC)
  - shares the BMC's LPC bus (§8)
* - `VGA_SW1` · `IPMI_SEL1` · `RECOVERY1`
  - 1×3 jumpers
  - reset-source / IPMI / recovery straps
  - BMC strap and reset selection (§9)
```

Source: [BMC-CONNECTORS "Connectors at a glance"](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/BMC-CONNECTORS.md#connectors-at-a-glance).

## 1. `VGA1` — VGA output (HD-15)

Driven by the AST2050's integrated video ({doc}`kgpe-d16-wiring` §9): analog
RGB via buffer transistors `QD3/4/5`, DDC/EDID I²C direct, H/V sync buffered
by `QU6`.

```{figure} /_static/diagrams/kgpe-d16-vga1.svg
:alt: VGA1 HD-15 pinout — RGB on pins 1-3 from BMC balls E1/D1/C1, DDC data/clock on pins 12/15 from balls B2/B1, H/V sync on pins 13/14 via the QU6 buffer, +5V DDC power on pin 9, grounds on 5-8/10.
:width: 90%
```

```{list-table}
:header-rows: 1
:widths: 12 24 28 36

* - Pin
  - Net
  - Function
  - Connects to
* - 1
  - `L_AST_DACR`
  - red analog
  - BMC `E1` (`DACR`) via `QD3`
* - 2
  - `L_AST_DACG`
  - green analog
  - BMC `D1` (`DACG`) via `QD4`
* - 3
  - `L_AST_DACB`
  - blue analog
  - BMC `C1` (`DACB`) via `QD5`
* - 4, 11
  - —
  - NC (monitor ID2 / ID0)
  - —
* - 5–8, 10
  - `GND`
  - grounds (signal + RGB returns)
  - —
* - 9
  - `+VGA_5V_F`
  - +5 V DDC power
  - fused +5 V
* - 12
  - `AST_DDCDAT_R_T`
  - DDC data (SDA)
  - BMC `B2` (`DDCADAT`)
* - 13
  - `AST_HSYNC_R_B`
  - H-sync
  - BMC `U2` via `QU6` pin 8
* - 14
  - `AST_VSYNC_R_B`
  - V-sync
  - BMC `R4` via `QU6` pin 11
* - 15
  - `AST_DDCCLK_R_T`
  - DDC clock (SCL)
  - BMC `B1` (`DDCACLK`)
```

Source: [BMC-CONNECTORS `VGA1`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/BMC-CONNECTORS.md#vga1--vga-output-hd-15).

## 2. `AST_UART1` — BMC serial console

The dedicated header for the **BMC's own console** — SoC **UART2**
(`0x1E784000` = Linux `ttyS1`), standby-powered so it works with the host
off. It is distinct from the host Serial-over-LAN path
({doc}`kgpe-d16-wiring` §10).

```{figure} /_static/diagrams/kgpe-d16-ast-uart1.svg
:alt: AST_UART1 4-pin pinout from the schematic — pin 1 +5VSB, pin 2 BMC TXD (ball U21), pin 3 BMC RXD (ball U20), pin 4 GND.
:width: 60%
```

```{list-table}
:header-rows: 1
:widths: 12 26 30 32

* - Pin
  - Net
  - Function
  - Connects to
* - 1
  - `+5VSB`
  - +5 V standby
  - standby rail
* - 2
  - `AST_TXD2_R`
  - BMC transmit
  - BMC `U21` (`TXD2`)
* - 3
  - `AST_RXD2_R`
  - BMC receive
  - BMC `U20` (`RXD2`)
* - 4
  - `GND`
  - ground
  - —
```

```{admonition} Correction to the pre-schematic bring-up notes
:class: important

The netlist shows **pin 1 is `+5VSB`**, not the +3.3 V the earlier
photo-derived bring-up documentation assumed ({doc}`kgpe-d16` §2.2's header
table predates the schematic work). The signal pins remain 3.3 V TTL — the
rule "never connect pin 1 to an RPi" stands, and is now *more* important, not
less: +5 V would exceed the Pi's absolute maximum.
[[BMC-CONNECTORS `AST_UART1`]](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/BMC-CONNECTORS.md#ast_uart1--bmc-serial-console)
```

The RPi4 crossover wiring recipe stays on {doc}`kgpe-d16` §2.2, and the
115200-vs-1200 baud question is tracked there too.

## 3. `AST_JTAG1` — BMC ARM JTAG debug

Standard 20-pin ARM JTAG header for the AST2050's ARM926EJ-S core — the header
the {doc}`OpenOCD run-control work </debug/jtag-uart>` drives. Odd pins carry
the signals; even pins are ground (except 1–2 = Vref).

```{figure} /_static/diagrams/kgpe-d16-ast-jtag1.svg
:alt: AST_JTAG1 20-pin ARM JTAG pinout with RPi4 bit-bang wiring per signal — nTRST pin 3, TDI 5, TMS 7, TCK 9, RTCK 11, TDO 13, nSRST 15; even pins ground; pins 1-2 Vref 3.3V.
:width: 85%
```

```{list-table}
:header-rows: 1
:widths: 14 22 22 42

* - Pin
  - Net
  - Function
  - BMC ball
* - 1, 2
  - `+3V3_AUX`
  - Vref / power sense
  - —
* - 3
  - `AST_NTRST`
  - TAP reset
  - `T20` (`NTRST`)
* - 5
  - `AST_TDI`
  - test data in
  - `T21` (`TDI`)
* - 7
  - `AST_TMS`
  - test mode select
  - `T19` (`TMS`)
* - 9
  - `AST_TCK`
  - test clock
  - `U22` (`TCK`)
* - 11
  - `AST_RTCK`
  - return test clock
  - `T22` (`RTCK`)
* - 13
  - `AST_TDO`
  - test data out
  - `R19` (`TDO`)
* - 15
  - `AST_SRST#`
  - system reset
  - `R20` (`SRST#`) — the global BMC/PHY reset
* - 17, 19
  - —
  - NC
  - —
* - 4–20 even
  - `GND`
  - ground
  - —
```

Source: [BMC-CONNECTORS `AST_JTAG1`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/BMC-CONNECTORS.md#ast_jtag1--bmc-arm-jtag-debug).
This confirms, from the netlist, the pinout that bring-up had verified
electrically (TAP IDCODE `0x07926f0f` — {doc}`kgpe-d16` §2.1).

## 4. `BMC_FW1` — BMC SPI firmware socket

The **socketed** 2×7 DIP holding the BMC's SPI firmware flash — the chip is
field-replaceable, which is the natural reflash path for the open firmware
this program builds. Beyond the SPI bus it carries three feature straps
sampled by the BMC.

```{figure} /_static/diagrams/kgpe-d16-bmc-fw1.svg
:alt: BMC_FW1 2x7 socket pinout — SPI MOSI/CLK/MISO/CS0/CS2 to BMC balls Y1/Y2/AA4/AB9/W7, +3V3_AUX power, and the IKVMEN#, SOLEN# and BMC_PRESENT# straps; pins 5/9/11 NC, pin 13 GND.
:width: 90%
```

```{list-table}
:header-rows: 1
:widths: 12 26 34 28

* - Pin
  - Net
  - Function
  - BMC ball
* - 1
  - `AST_SPIDO`
  - SPI MOSI
  - `Y1` (`ROMD1`)
* - 2
  - `+3V3_AUX`
  - flash power (standby)
  - —
* - 3
  - `AST_IKVMEN#`
  - strap: enable iKVM
  - `W1`
* - 4
  - `AST_SPICS#2`
  - SPI chip-select 2
  - `W7` (`ROMCS2#`)
* - 6
  - `AST_SPIDI`
  - SPI MISO
  - `AA4` (`ROMD2`)
* - 7
  - `BMC_PRESENT#`
  - strap: BMC present (also the SOL-mux select)
  - `A10`/`D11`/`AA9`
* - 8
  - `AST_SPICLK`
  - SPI clock
  - `Y2` (`ROMD0`)
* - 10
  - `AST_SOLEN#`
  - strap: enable Serial-over-LAN
  - `W2`
* - 12
  - `AST_SPICS#0`
  - SPI chip-select 0 (main firmware)
  - `AB9` (`ROMCS0#`)
* - 5, 9, 11
  - —
  - NC
  - —
* - 13
  - `GND`
  - ground
  - —
```

```{admonition} Identity resolved
:class: note

Before the schematic work, this socket was documented only from the ASUS
manual as the "ASMB4/5 management-module slot" with an unpublished pinout, and
its SPI role was an unconfirmed rumour ({doc}`kgpe-d16` §2.3 preserved that
history). The netlist settles it: `BMC_FW1` is the BMC's SPI firmware socket,
with the pinout above.
[[BMC-CONNECTORS `BMC_FW1`]](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/BMC-CONNECTORS.md#bmc_fw1--bmc-spi-firmware-socket)
```

## 5. `PANEL1` — system front panel

The main front-panel header. The BMC sees the power/reset/NMI buttons and
drives the message LED; the power/HDD LEDs belong to the chipset. Pin 5 is
the keyed/absent slot.

```{figure} /_static/diagrams/kgpe-d16-panel1.svg
:alt: PANEL1 2x10 front-panel pinout — HDD LED, power LED, NMI button to BMC T1/U1, message LED from BMC R3, power button to BMC A11/C11, reset button to BMC C10/D10, speaker, +5V, grounds.
:width: 90%
```

```{list-table}
:header-rows: 1
:widths: 12 26 32 30

* - Pin
  - Net
  - Function
  - Connects to
* - 1
  - `FP_HDLED+`
  - HDD-activity LED anode
  - chipset
* - 6
  - `FP_PLED-`
  - power-LED cathode
  - chipset
* - 7
  - `FP_NMIBNT#`
  - NMI button
  - BMC `T1`/`U1`
* - 10
  - `FP_MLED`
  - message / heartbeat LED
  - BMC `R3` (`AST_MLED`)
* - 11
  - `R_FP_PWRBTN#`
  - power button
  - BMC `A11`/`C11`
* - 17
  - `FP_RESET#`
  - reset button
  - BMC `C10`/`D10`
* - 20
  - `SPKOUT`
  - chassis speaker
  - `BUZZ1` pin 2
* - 14
  - `+5V`
  - +5 V
  - —
* - 3, 9, 13, 16, 18, 19
  - `GND`
  - ground
  - —
* - 4, 12, 15
  - —
  - NC
  - —
```

Source: [BMC-CONNECTORS `PANEL1`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/BMC-CONNECTORS.md#panel1--system-front-panel).
The BMC-side meaning of these nets is in the {doc}`platform-control GPIO map
<kgpe-d16-wiring>` (§11).

## 6. `AUX_PANEL1` — auxiliary panel (Q-connector)

The ASUS auxiliary front-panel header: the BMC chassis-locator LED and
button, the front `I2C8` segment (routed through the mux fabric —
{doc}`kgpe-d16-i2c` §2), chassis intrusion, and LAN link/activity LEDs.

```{figure} /_static/diagrams/kgpe-d16-aux-panel1.svg
:alt: AUX_PANEL1 2x10 pinout — +5VSB, front I2C8 clock/data into the QU5/QU9 mux fabric, BMC locator LED (BMC Y4) and button (BMC Y3), LAN1/LAN2 link LEDs, chassis intrusion, grounds.
:width: 90%
```

```{list-table}
:header-rows: 1
:widths: 12 28 32 28

* - Pin
  - Net
  - Function
  - Connects to
* - 1
  - `+5VSB`
  - +5 V standby
  - —
* - 4
  - `I2C8SCL`
  - front I²C8 clock
  - `QU5` pin 12, `QU9` pin 11
* - 10
  - `I2C8SDA`
  - front I²C8 data
  - `QU5` pin 1, `QU9` pin 14
* - 11, 17
  - `AUX_BMCLOCLED#`
  - BMC locator LED
  - BMC `Y4` (`AST_IDLEDSTATUS`)
* - 13
  - `AUX_BMCLOCBNT#`
  - BMC locator button
  - BMC `Y3` (`AST_IDBNT#`)
* - 14
  - `AUX_LAN1LINK#`
  - LAN1 link LED
  - `LQ3` pin 3
* - 20
  - `AUX_LAN2LINK#`
  - LAN2 link LED
  - `LQ5` pin 3
* - 5
  - `AUX_CHASSIS#`
  - chassis intrusion
  - —
* - 9, 16, 18, 19
  - LED nets
  - locator / LAN-activity LEDs
  - —
* - 3, 7, 8, 15
  - `GND`
  - ground
  - —
```

Source: [BMC-CONNECTORS `AUX_PANEL1`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/BMC-CONNECTORS.md#aux_panel1--auxiliary-panel-q-connector).

## 7. `PSUSMB1` — PSU SMBus

The power-supply SMBus/PMBus header, on the BMC's **`I2C1`** so the BMC can
read PSU telemetry ({doc}`kgpe-d16-i2c` §4.1).

```{figure} /_static/diagrams/kgpe-d16-psusmb1.svg
:alt: PSUSMB1 1x5 pinout — SCL to BMC B15, SDA to BMC A15, SMBus alert to BMC B12, GND, +3.3V.
:width: 75%
```

```{list-table}
:header-rows: 1
:widths: 12 26 30 32

* - Pin
  - Net
  - Function
  - Connects to
* - 1
  - `I2C1SCL`
  - SMBus clock
  - BMC `B15` (`SCL1`)
* - 2
  - `I2C1SDA`
  - SMBus data
  - BMC `A15` (`SDA1`)
* - 3
  - `N37658829`
  - SMBus alert
  - BMC `B12` (`SCL7/SALT1`)
* - 4
  - `GND`
  - ground
  - —
* - 5
  - `+3V3`
  - +3.3 V
  - —
```

Source: [BMC-CONNECTORS `PSUSMB1`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/BMC-CONNECTORS.md#psusmb1--psu-smbus).

## 8. `TPM1` — TPM module header (LPC peer)

A 2×10 header (pin 4 keyed) for a plug-in TPM module on the SP5100's LPC bus.
The BMC never addresses the TPM — the TPM is a *third peripheral on the same
LPC wires* as the BMC and Super-I/O ({doc}`kgpe-d16-wiring` §5), so they share
signal integrity, reset and clocking but nothing else. The TPM gets its own
clock (`LPC_CLK1`, distinct from the BMC's `LPC_CLK0`) and its reset from the
Super-I/O's `RSTOUT0#`.

```{figure} /_static/diagrams/kgpe-d16-tpm1.svg
:alt: TPM1 2x10 pinout — LPC_CLK1, LFRAME#, LAD0-3 and SERIRQ shared with the BMC's LPC bus, LRESET# from the Super-I/O, +3.3V, grounds, reserved pull-ups; pin 4 keyed.
:width: 90%
```

```{list-table}
:header-rows: 1
:widths: 12 24 34 30

* - Pin
  - Net
  - Function
  - Shared with BMC?
* - 1
  - `LPC_CLK1`
  - LPC clock (TPM's own)
  - no — BMC uses `LPC_CLK0`
* - 3
  - `LPC_FRAME#`
  - LPC frame
  - **yes** — BMC `B16`
* - 5
  - `SIO_RSTOUT#0`
  - LPC reset (`LRESET#`)
  - from Super-I/O `RSTOUT0#`
* - 7 / 8
  - `LPC_LAD3` / `LPC_LAD2`
  - LPC AD 3 / 2
  - **yes** — BMC `C16` / `D16`
* - 10 / 11
  - `LPC_LAD1` / `LPC_LAD0`
  - LPC AD 1 / 0
  - **yes** — BMC `A17` / `B17`
* - 16
  - `LPC_SERIRQ`
  - serialized IRQ
  - **yes** — BMC `C15`
* - 9
  - `+3V3`
  - +3.3 V
  - —
* - 2, 12, 17
  - `GND`
  - ground
  - —
* - 4
  - —
  - key (no pin)
  - —
* - 6, 13–15, 18–20
  - `N37…` nets
  - reserved / pull networks (`RN13`)
  - —
```

Source: [BMC-CONNECTORS `TPM1`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/BMC-CONNECTORS.md#tpm1--tpm-module-header-lpc-shared-with-the-bmc).

## 9. Jumpers — `VGA_SW1`, `IPMI_SEL1`, `RECOVERY1`

Three 1×3 straps that steer BMC behaviour:

```{figure} /_static/diagrams/kgpe-d16-vga-sw1.svg
:alt: VGA_SW1 jumper — pin 1 SB_PCI_RST# (chipset PCI reset, also BMC B10), pin 2 AST_BRST# (BMC P21), pin 3 GND.
:width: 65%
```

```{figure} /_static/diagrams/kgpe-d16-ipmi-sel1.svg
:alt: IPMI_SEL1 jumper — pin 2 is the IPMI_SEL strap read by BMC ball A8.
:width: 65%
```

```{figure} /_static/diagrams/kgpe-d16-recovery1.svg
:alt: RECOVERY1 jumper — pin 2 BIOS_RECOVERY#, sensed by BMC ball C9; pin 3 GND.
:width: 65%
```

```{list-table}
:header-rows: 1
:widths: 18 34 48

* - Jumper
  - Selects
  - BMC connection
* - `VGA_SW1`
  - which reset drives the VGA/iKVM PCI function: the chipset's `SB_PCI_RST#` (pin 1) or the BMC's own `AST_BRST#` (pin 2)
  - `SB_PCI_RST#` also lands on BMC `B10`; `AST_BRST#` is BMC `P21`
* - `IPMI_SEL1`
  - the `IPMI_SEL` feature strap
  - read on BMC `A8` (`GPIOC5/PWM4`)
* - `RECOVERY1`
  - asserts `BIOS_RECOVERY#` (pin 3 = GND side)
  - sensed on BMC `C9` (`GPIOB7`) to trigger BIOS recovery
```

Source: [BMC-CONNECTORS jumper sections](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/BMC-CONNECTORS.md#vga_sw1--vga-reset-source-jumper).

## See also

**Related pages**

- {doc}`kgpe-d16` — board overview; the RPi4 wiring recipes for `AST_JTAG1`/`AST_UART1` live there
- {doc}`kgpe-d16-wiring` — where every net in these tables terminates on the BMC
- {doc}`kgpe-d16-i2c` — the bus fabric behind `PSUSMB1` and the `AUX_PANEL1` I²C8 pins
- {doc}`/debug/jtag-uart` — driving `AST_JTAG1` with OpenOCD

**External references**

- [`BMC-CONNECTORS.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/BMC-CONNECTORS.md) — the source document, including regeneration instructions

## Sources

- **[`BMC-CONNECTORS.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/BMC-CONNECTORS.md)** — connector pinouts and nets, read from
  the KGPE-D16 `.FZ` schematic netlist.
- **[`pinmaps/QU1_pins.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/pinmaps/QU1_pins.md)** — the BMC-ball ends of every net above.
- Diagrams generated by **[`tools/connector_svg.py`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/tools/connector_svg.py)** from the same netlist.
