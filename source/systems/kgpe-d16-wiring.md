# KGPE-D16 BMC wiring (schematic-derived)

How the ASUS KGPE-D16 wires its Aspeed AST2050 BMC (board reference designator
**`QU1`**, TFBGA-355) to everything else on the board — every ball, traced
through the series resistors, muxes, expanders and buffers to its far end. This
page condenses the program's pin-level reverse engineering of the board's
schematic netlist; the {doc}`kgpe-d16` overview covers the board as a whole, and
two companion pages cover the {doc}`I2C/SMBus topology <kgpe-d16-i2c>` and the
{doc}`connectors and headers <kgpe-d16-connectors>`.

```{admonition} Provenance — netlist, not inference
:class: note

Everything here is extracted from the board's OpenBoardView `.FZ` schematic
export (`KGPE-D16 r1.04B(59SB0010-MB0D06S).FZ`), an RC6-encrypted netlist that
carries full part descriptions — so every support-chip identity is **quoted from
the schematic's part-description field**, not guessed from board photos. The
extraction/diagram tools and the regeneration procedure are in the program
repo's [`schematic-wiring/`](https://github.com/mithro/ai-shenanigans-for-bmcs/tree/main/asus-kgpe-d16-firmware/schematic-wiring)
directory ([README](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/README.md));
the narrative source documents are
[`AST2050-BMC-WIRING.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md)
and the machine-generated all-355-ball table
[`pinmaps/QU1_pins.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/pinmaps/QU1_pins.md).
```

## 1. At a glance

```{list-table}
:header-rows: 0
:widths: 30 70

* - Part
  - ASPEED **AST2050A3-GP** ({doc}`SoC detail </hardware/soc-ast2050>`), TFBGA-355, ref `QU1`
* - Balls
  - 355 populated (columns A–AB × rows 1–22)
* - Supplies
  - `+1V2_AUX` core (20 balls) · `+1V8_AUX` DDR2 I/O (6) · `+3V3_AUX` I/O (18) · 66 ground balls
* - External DRAM
  - `QU2` — Hynix **HY5PS121621CFP-25**, DDR2 32M×16, 1.8 V = **64 MiB**
* - Firmware
  - `BMC_FW1` — **socketed** SPI flash ({doc}`pinout <kgpe-d16-connectors>`)
* - Always-on?
  - **Yes** — every BMC rail is a standby (`_AUX`) rail fed from PSU `+5VSB`
```

The AST2050 is wired with three distinct "personalities"
[BMC-WIRING §1](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md#1-high-level-block-diagram):

- **Baseboard controller** — LPC, PCI-33 and GPIO to the chipset for power
  sequencing, reset control and sensor access (§4–§6, §11 below, and the
  {doc}`I2C topology page <kgpe-d16-i2c>`).
- **Remote-KVM engine** — its own DDR2 frame buffer (§3), a VGA output (§9), a
  USB *device* port for virtual keyboard/mouse/media (§7), and a PCI attachment
  used to capture host video (§6).
- **Network stack** — a dedicated management PHY *and* an NC-SI-style sideband
  into both host NICs, simultaneously (§8).

### Ball budget by function

```{list-table}
:header-rows: 1
:widths: 55 15 30

* - Function block
  - Balls
  - Section
* - DDR2 memory (→ `QU2`)
  - 48
  - §3
* - SPI / ROM flash (→ `BMC_FW1`)
  - 27
  - §2
* - LPC host bus (→ SP5100 + Super-I/O)
  - 10
  - §4
* - PCI 33 MHz (VGA / iKVM)
  - 45
  - §6
* - USB device port (→ SP5100)
  - 6
  - §7
* - Ethernet RMII / NC-SI
  - 18
  - §8
* - VGA / video out
  - 14
  - §9
* - I2C / SMBus (8 controllers)
  - 16
  - {doc}`kgpe-d16-i2c`
* - Serial / SOL (UART)
  - 11
  - §10
* - Power / reset / platform control
  - 17
  - §11
* - JTAG / test · LEDs · clock · straps
  - 11 + 6 + 1 + 2
  - §12
* - Other / GPIO / analog
  - 9
  - —
* - Power / decoupling · ground
  - 48 · 66
  - §2
```

Source: [`QU1_pins.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/pinmaps/QU1_pins.md)
(the per-section ball tables; totals as tabulated in
[BMC-WIRING "Ball count by function"](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md#ball-count-by-function)).

## 2. Power — every rail is standby

The BMC runs whenever the PSU has AC: all its rails cascade from the ATX
`+5VSB` standby output, so the host power state is irrelevant. Two UPI
**UP7706U8** LDOs make the low rails:

- `+5VSB` → **`PU28`** (UP7706U8, enabled by `+5VSB` itself) → **`+1V8_AUX`**
  (DDR2 I/O ring, shared with the `QU2` SDRAM)
- `+1V8_AUX` → **`PU22`** (UP7706U8) → **`+1V2_AUX`** (digital core)
- `+5VSB` → auxiliary 3.3 V regulator → **`+3V3_AUX`** (general I/O ring, plus
  the flash, PHY, hardware monitor and NIC standby wells)

The analog supplies are ferrite/RC-filtered taps of those rails:

```{list-table} AST2050 power balls
:header-rows: 1
:widths: 22 10 14 34 20

* - Rail
  - Volt
  - Balls
  - Purpose
  - Source
* - `+1V2_AUX`
  - 1.2 V
  - 20
  - digital core
  - `PU22` (from `+1V8_AUX`)
* - `+1V8_AUX`
  - 1.8 V
  - 6
  - DDR2 I/O ring (shared with `QU2`)
  - `PU28` (from `+5VSB`)
* - `+3V3_AUX`
  - 3.3 V
  - 18
  - general I/O ring
  - aux 3.3 V reg (from `+5VSB`)
* - `AST_V1PLLV12`
  - 1.2 V
  - J2 J4
  - core-PLL analog
  - filtered `+1V2_AUX`
* - `AST_MPLLAV33`
  - 3.3 V
  - K2 L4
  - memory-PLL analog
  - filtered `+3V3_AUX`
* - `AST_HPLLAV33`
  - 3.3 V
  - M2 M4
  - host/video-PLL analog
  - filtered `+3V3_AUX`
* - `AST_DACAV33`
  - 3.3 V
  - D3 E3 F1 G1 H3
  - video-DAC analog
  - filtered `+3V3_AUX`
* - `AST_USBV33`
  - 3.3 V
  - B18 B20
  - USB-PHY analog
  - filtered `+3V3_AUX`
* - `AST_VREFSSTL`
  - 0.9 V
  - T18 AB12
  - DDR2 SSTL reference
  - resistor divider (½·1.8 V)
```

Source: [BMC-WIRING §2](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md#2-power-supply).
The always-on design is why the board behaves as "power-on-with-AC" on the
bench rig ({doc}`kgpe-d16` §3.2) — the BMC and its {doc}`SCU straps
</hardware/registers/scu-clock-reset>` come up as soon as mains is applied.

## 3. DDR2 memory → `QU2` (64 MiB)

The BMC's private DRAM is a single Hynix **HY5PS121621CFP-25** — DDR2, 32M×16,
1.8 V, i.e. **64 MiB on a 16-bit bus**. It serves as BMC system RAM *and* the
remote-KVM frame buffer. Every data/strobe/address/control line runs through
isolated series-resistor networks (`QRN1`–`QRN12`, nets `AST_MEMxx` →
`R_AST_MEMxx`) for source-series termination.
[BMC-WIRING §3](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md#3-ddr2-memory-interface--qu2)

Key control balls: `CS#`=W16, `RAS#`=AA16, `CAS#`=AB16, `WE#`=W17,
`CK/CK#`=AA19/AB19, `CKE`=AB18, `ODT`=AB21; `DQ0–15` sit across the W/Y/AA/AB
rows 10–15. The full 48-ball table with per-net `QU2` endpoints is in
[`QU1_pins.md` § DDR2 memory](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/pinmaps/QU1_pins.md#ddr2-memory-48).

This is the physical confirmation of the **64 MiB constraint** that shapes the
firmware track: a stripped, Redfish-only OpenBMC build is required to fit
({doc}`/firmware/openbmc`), and the SDRAM controller programming for exactly
this part (4-bank, ×16, DLL) is what the DDR2-init bring-up work derived
({doc}`/hardware/registers/ddr2-sdram`).

```{admonition} Two different "DDR thermal" signals — don't conflate
:class: warning

Balls **T2/T3** carry `AST_P1/P0_DDR_THERM#` — BMC GPIO inputs monitoring the
*host's* DDR3 DIMM/CPU thermal alarms (§11). They have nothing to do with the
BMC's own DDR2 interface above.
[BMC-WIRING §3](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md#3-ddr2-memory-interface--qu2)
```

## 4. SPI firmware flash → `BMC_FW1`

The BMC boots from a **socketed** SPI flash in the 2×7 DIP socket `BMC_FW1` —
field-replaceable, which is exactly what the open-firmware reflashing this
program targets. The socket also carries three feature straps the BMC samples
(§12). Full socket pinout: {doc}`kgpe-d16-connectors`.

```{list-table} SPI flash signals
:header-rows: 1
:widths: 18 18 24 40

* - BMC ball
  - Pin name
  - Net
  - Role
* - Y2
  - `ROMD0`
  - `AST_SPICLK`
  - SPI clock
* - Y1
  - `ROMD1`
  - `AST_SPIDO`
  - SPI MOSI
* - AA4
  - `ROMD2`
  - `AST_SPIDI`
  - SPI MISO
* - AB9
  - `ROMCS0#`
  - `AST_SPICS#0`
  - chip-select 0 (main firmware)
* - W7
  - `ROMCS2#`
  - `AST_SPICS#2`
  - chip-select 2 (second device / recovery)
```

The legacy parallel-ROM address bus `AST_ROMA0`–`AST_ROMA23` (balls W5–AB8) is
only series-terminated — SPI mode is used, and those pins are spare GPIO.
Source: [BMC-WIRING §4](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md#4-spi-firmware-flash--bmc_fw1);
controller-side detail in the {doc}`SMC/flash register documentation
</hardware/registers/control-blocks>`.

## 5. LPC — peripheral on the SP5100's bus

The AST2050 is an **LPC peripheral** of the AMD SP5100 southbridge (`SU1`),
sharing the bus with the Nuvoton {doc}`W83667HG-A Super-I/O
</hardware/peripherals/w83667hg>` (`OU1`) and the TPM module header (`TPM1`).
This bus carries the host's KCS/IPMI, mailbox and virtual-UART register access
into the BMC.
[BMC-WIRING §5](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md#5-lpc-host-bus--sp5100-su1--super-io-ou1)

```{list-table} LPC bus — same net, three peers
:header-rows: 1
:widths: 16 16 20 16 16 16

* - Signal
  - Net
  - BMC ball
  - SP5100 ball
  - Super-I/O pin
  - TPM1 pin
* - `LCLK`
  - `LPC_CLK0`
  - A16
  - G22
  - — (own clock)
  - — (`LPC_CLK1`)
* - `LFRAME#`
  - `LPC_FRAME#`
  - B16
  - H25
  - 25
  - 3
* - `LAD0`
  - `LPC_LAD0`
  - B17
  - H24
  - 23
  - 11
* - `LAD1`
  - `LPC_LAD1`
  - A17
  - H23
  - 22
  - 10
* - `LAD2`
  - `LPC_LAD2`
  - D16
  - J25
  - 21
  - 8
* - `LAD3`
  - `LPC_LAD3`
  - C16
  - J24
  - 20
  - 7
* - `SERIRQ`
  - `LPC_SERIRQ`
  - C15
  - V15
  - 19
  - 16
```

Sources: [BMC-WIRING §5](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md#5-lpc-host-bus--sp5100-su1--super-io-ou1),
[W83667HG-SUPERIO-WIRING §3](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/W83667HG-SUPERIO-WIRING.md#3-lpc-host-bus-shared-with-bmc--tpm),
[BMC-CONNECTORS (TPM1)](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/BMC-CONNECTORS.md#tpm1--tpm-module-header-lpc-shared-with-the-bmc).
The three peripherals never address each other — they are independent LPC
devices selected by address; they share only signal integrity, reset and
clocking. The BMC-side LPC/KCS register interface is documented with the
{doc}`AST2050 control blocks </hardware/registers/control-blocks>`, and the
IPMI-over-KCS path is exercised by the {doc}`emulation testbench
</emulation/testbench>`.

## 6. PCI 33 MHz — the VGA/iKVM attachment

The AST2050's integrated VGA + video-capture engine appears as a **PCI device
on the SP5100's 33 MHz bus**, shared with the physical PCI slots. The BMC
drives the full multiplexed interface (`AD0–31`, `C/BE0–3#`, `FRAME#`,
`IRDY#`, `TRDY#`, `DEVSEL#`, `STOP#`, `PAR`, `IDSEL`), clocked by
`SB_PCI_CLK1` (ball P22) with reset `SB_PCI_RST#` (ball B10) — 45 balls in
all.
[BMC-WIRING §6](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md#6-pci-33-mhz-bus-vga--ikvm--sp5100-su1--pci-slots)

This is the datapath behind two things documented elsewhere:

- the host sees the BMC as **ASPEED Graphics `[1a03:2000]`**, whose 8 MB BAR is
  the **P2A (PCIe→AHB) doorway** used for out-of-band bring-up
  ({doc}`/debug/bring-up`);
- the iKVM engine captures host video over this bus
  ({doc}`/hardware/registers/pcie-vga-usb-bridges`).

Which reset drives the VGA/iKVM function is jumper-selectable (`VGA_SW1`:
`AST_BRST#` from the BMC, ball P21, vs `SB_PCI_RST#` from the chipset) — see
{doc}`kgpe-d16-connectors`.

## 7. USB device port → SP5100

A single USB port wired as a **device** (the remote-KVM virtual
keyboard/mouse/CD), connected to the SP5100's USB host controller:
`AST_USB+` = B22 and `AST_USB-` = A21 → `SU1` **C10/D10** (`USB_HSD8P/N`,
high-speed pair 8), with the `AST_USBRPU` pull-up strap on B21 and USB analog
power on B18/B20.
[QU1_pins § USB](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/pinmaps/QU1_pins.md#usb-6)
[SU1_pins § USB](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/pinmaps/SU1_pins.md#usb-37)
(The narrative source
[BMC-WIRING §9](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md#9-usb-device-port--sp5100-su1)
says "SU1 E12/E14", but the machine-generated pinmaps show E12/E14 =
`USB_HSD6P/N` going to the `USB78` header — the BMC pair is C10/D10; this
page follows the netlist tables.) The BMC-side USB device controller (the
virtual hub) is documented in {doc}`/hardware/registers/display-usb`.

## 8. Ethernet — dedicated PHY plus NC-SI sideband

The AST2050 MAC is wired **two ways at once** through its pin-mux
[BMC-WIRING §7](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md#7-ethernet--dual-channel-dedicated-phy--nc-si-sideband):

- **Channel 1 — dedicated management port.** The `AST_RMII1*` nets plus
  MDIO/MDC run to `U5`, a Realtek **RTL8201N-GR**
  ({doc}`part page </hardware/peripherals/rtl8201n>`) driving the physically
  separate management RJ-45. This resolves what was previously an open
  question in the board docs — the schematic's part-description field names
  the exact PHY.
- **Channel 2 — NC-SI-style sideband.** The `AST_RMII2*` nets are **bussed to
  both** Intel **82574L** host NICs (`LU1` = LAN1, `LU2` = LAN2;
  {doc}`part page </hardware/peripherals/intel-82574l>`), so the BMC can share
  the host's network ports.

Both channels are clocked at 50 MHz from a dedicated management clock
generator `CU2` (ICS **ICS9112AM-16LFT**): nets `C_MNG_50M_AST_RMII1RXCLK`
(ball A7) and `C_MNG_50M_AST_RMII2RXCLK` (ball B7).
[QU1_pins § Ethernet](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/pinmaps/QU1_pins.md#ethernet-rmii--nc-si-18)

```{list-table} Ethernet balls (18)
:header-rows: 1
:widths: 20 14 22 44

* - Signal
  - BMC ball
  - Channel
  - Endpoint
* - `MDIO` / `MDC`
  - A2 / A3
  - MII management
  - `U5` pins 31 / 30
* - `RMII1 TXD0/TXD1`
  - A4 / B4
  - ch 1 (mgmt PHY)
  - `U5` 25 / 26
* - `RMII1 TXEN`
  - C5
  - ch 1
  - `U5` 29
* - `RMII1 RXD0/RXD1`
  - C6 / D6
  - ch 1
  - `U5` 17 / 19
* - `RMII1 RXER` · `CRSDV`
  - C7 · D7
  - ch 1
  - `U5` 35 · 16
* - `RMII1 REFCLK`
  - A7
  - ch 1
  - `CU2` pin 7 (50 MHz)
* - `RMII2 RXD0/RXD1`
  - A5 / B5
  - ch 2 (NC-SI)
  - `LU1`+`LU2` pins 6 / 5
* - `RMII2 CRSDV`
  - B6
  - ch 2
  - `LU1`+`LU2` pin 3
* - `RMII2 TXD0/TXD1`
  - C4 / D4
  - ch 2
  - `LU1`+`LU2` pins 9 / 8
* - `RMII2 TXEN`
  - D5
  - ch 2
  - `LU1`+`LU2` pin 7
* - `RMII2 REFCLK`
  - B7
  - ch 2
  - `CU2` pin 5 (50 MHz)
* - `RMII2 RXER`
  - A6
  - ch 2
  - unconnected
```

Source: [`QU1_pins.md` § Ethernet](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/pinmaps/QU1_pins.md#ethernet-rmii--nc-si-18).
The MAC-side register interface (FTGMAC100, MDIO access, and the
RMII/`FAST_MODE` behaviour verified on this exact board) is in
{doc}`/hardware/registers/network-mac-phy`.

## 9. VGA output → `VGA1`

The on-chip VGA DAC drives the rear HD-15 (`VGA1`, plus the `VGA_HDR1`
header): analog RGB from balls E1/D1/C1 through buffer transistors
`QD3/QD4/QD5`, H/V sync (U2/R4) through the Toshiba **TC74VHCT125AF** quad
buffer `QU6`, and the DDC/EDID I2C pair on B1/B2 direct to the connector.
[BMC-WIRING §8](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md#8-vga--video-output--vga1)
Connector pinout: {doc}`kgpe-d16-connectors`; the display-engine registers are
in {doc}`/hardware/registers/display-usb`.

## 10. Serial and Serial-over-LAN

Two separate serial paths leave the BMC
[BMC-WIRING §12](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md#12-serial--serial-over-lan-sol):

- **BMC console** — SoC **UART2** (`TXD2`=U21, `RXD2`=U20) runs to the 4-pin
  `AST_UART1` header. This is the `ttyS1` console used throughout the
  bring-up work ({doc}`kgpe-d16` §2.2, {doc}`/debug/jtag-uart`).
- **SOL mux** — SoC **UART1** (`TXD1`=Y22, `RXD1`=AA22, `NRTS1`=V21,
  `NCTS1`=W22) feeds a 2:1 mux `QU8` (Pericom **PI5C3257**) together with the
  host's UART-B from the {doc}`Super-I/O </hardware/peripherals/w83667hg>`
  (via BCD **AZ75232** RS-232 transceivers `U12`/`U13`). The mux select is the
  `BMC_PRESENT#` strap — so the same physical serial console belongs to either
  the host or the BMC depending on whether a BMC module is present.

The remaining UART1 modem-control balls (`NDTR1`=U19, `NDCD1`=V19,
`NDSR1`=V20, `NRI1`=V22) are unconnected.
[QU1_pins § Serial](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/pinmaps/QU1_pins.md#serial--sol-uart-11)
UART programming detail: {doc}`/hardware/registers/uart-vic-timers`.

## 11. Power / reset / platform control GPIO

These 17 balls are what make the AST2050 a *baseboard* controller — they can
power the host on and off, drive and observe resets, watch fatal-thermal
events and disable CPUs. (`P0`/`P1` refer to the two Opteron sockets.)

```{list-table} Platform-control GPIO map
:header-rows: 1
:widths: 10 22 22 22 24

* - Ball
  - Pin name
  - Net
  - Reaches
  - Meaning
* - A9
  - `GPIOC1/PECIO`
  - `AST_ATXPSON#`
  - glue `U8` → PSU `PS_ON#`
  - **soft power on/off**
* - D9
  - `GPIOB6/VBDO/WDTRST`
  - `SYS_PWRGD`
  - `U8`, `SU1`, FETs
  - system power-good
* - A11
  - `GPIOB1/FLBUSY#`
  - `AST_PWRBTN#`
  - `PANEL1`, `QU4` pin 38
  - front-panel power button
* - D10
  - `GPIOB2/FLWP#`
  - `AST_SYSRESET#`
  - `PANEL1`, `SU1`
  - system reset
* - B10
  - `GPIOB4/VBCS/LRST#`
  - `SB_PCI_RST#`
  - `SU1`, `VGA_SW1`
  - PCI/LPC reset from the southbridge
* - C9
  - `GPIOB7/VBDI/EXTRST#`
  - `AST_BIOSREVRY#`
  - `RECOVERY1`, `SU1`
  - BIOS-recovery request
* - B9
  - `GPIOC0/PECII`
  - `AST_CLRTC#`
  - `SQ8`
  - clear CMOS/RTC
* - D8
  - `GPIOC2/PWM1`
  - `AST_CPU0DISABLE#`
  - socket-0 CPU
  - disable the socket-0 CPU
* - C8
  - `GPIOC3/PWM2`
  - `AST_CPU1DISABLE#`
  - socket-1 CPU
  - disable the socket-1 CPU
* - V4
  - `VP8/GPIOF0/TACH8`
  - `TTL_P0_THERMTRIP#`
  - CPUs, `SU1` J6
  - socket-0 THERMTRIP# (fatal)
* - V3
  - `VP9/GPIOF1/TACH9`
  - `TTL_P1_THERMTRIP#`
  - CPUs, `SU1` J6
  - socket-1 THERMTRIP#
* - V2
  - `VP10/GPIOF2/TACH10`
  - `TTL_P0_PROCHOT#`
  - socket-0 CPU
  - socket-0 PROCHOT# monitor
* - V1
  - `VP11/GPIOF3/TACH11`
  - `TTL_P1_PROCHOT#`
  - socket-1 CPU
  - socket-1 PROCHOT# monitor
* - T3
  - `VP4/GPIOE4/TACH4`
  - `AST_P0_DDR_THERM#`
  - socket-0 CPU + DIMM A–D
  - socket-0 DIMM/CPU thermal
* - T2
  - `VP5/GPIOE5/TACH5`
  - `AST_P1_DDR_THERM#`
  - socket-1 CPU + DIMM E–H
  - socket-1 DIMM/CPU thermal
* - T1
  - `VPACLK/GPIOH7`
  - `AST_NMI#`
  - `PANEL1`, `ND1`
  - NMI generation/sense
* - R20
  - `SRST#`
  - `AST_SRST#`
  - Super-I/O, `SU1`, `U5`, `U7`
  - global BMC/PHY reset (also on the JTAG header)
```

Source: [BMC-WIRING §11](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md#11-power--reset--platform-control-gpio)
(§13 for `AST_SRST#`); net-name strings verified against
[QU1_pins § Power / reset](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/pinmaps/QU1_pins.md#power--reset--platform-control-17).
The netlist numbers the sockets **0-based** in these net names
(`AST_CPU0DISABLE#`, `TTL_P0_*`); the narrative source's §11 table renders
the same nets 1-based (`CPU1DISABLE`, `P1_*`) — this table uses the literal
netlist strings so a grep of the netlist lands on the right ball. The southbridge half of this handshake — the ACPI sleep
states, `RSMRST#`, `PWR_GOOD` and the power-button flip-flop — is tabulated in
[SP5100-SOUTHBRIDGE-WIRING §11](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/SP5100-SOUTHBRIDGE-WIRING.md#11-power--reset--acpi-state-machine)
and [W83667HG-SUPERIO-WIRING §6](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/W83667HG-SUPERIO-WIRING.md#6-power--reset--acpi-sequencing);
the AST2050 GPIO controller registers are in
{doc}`/hardware/registers/buses-gpio`, and the conditional GPIO-A4
initialisation Raptor's U-Boot applies on this board is quoted in
{doc}`kgpe-d16` §3.1.

```{admonition} These nets are the remote-power-control ground truth
:class: important

`AST_ATXPSON#` (A9) driving PS_ON# through the `U8` glue is the physical basis
of the BMC power on/off/reset capability exercised in the program's
functionality matrix (QEMU F2 power tests and the silicon-verified
`kgpe-power.sh` path) — and `SYS_PWRGD` (D9) is the feedback the firmware
polls. See {doc}`/emulation/testbench` for how those are exercised in CI.
```

## 12. JTAG, LEDs, clock, straps

- **JTAG** — `TCK`=U22, `TMS`=T19, `TDI`=T21, `TDO`=R19, `NTRST`=T20,
  `RTCK`=T22, brought to the `AST_JTAG1` header ({doc}`kgpe-d16-connectors`;
  RPi4/OpenOCD wiring in {doc}`kgpe-d16` §2.1 and {doc}`/debug/jtag-uart`).
- **LEDs** — `AST_BMCRDYLED`=R2 (→ `BMC_LED1`), `AST_CPU1ERRLED`=T4 /
  `AST_CPU2ERRLED`=R1, `AST_MLED`=R3 (front-panel message/heartbeat LED),
  `AST_IDLEDSTATUS`=Y4 and `AST_IDBNT#`=Y3 (chassis-locator LED/button on
  `AUX_PANEL1`).
- **Clock** — `AST_24M_CLKIN`=R22 from crystal oscillator `QOSC1`: the 24 MHz
  SoC reference that everything in {doc}`/hardware/registers/scu-clock-reset`
  multiplies up.
- **Straps** — `IPMI_SEL`=A8 (from the `IPMI_SEL1` jumper), `AST_IKVMEN#`=W1
  and `AST_SOLEN#`=W2 (feature-enable straps carried on the `BMC_FW1` flash
  socket), and `BMC_PRESENT#` (socket pin 7, also the SOL-mux select, fanning
  to balls A10/D11/AA9).

Sources: [BMC-WIRING §13](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md#13-jtag--test-leds-clock-straps),
[BMC-CONNECTORS (BMC_FW1)](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/BMC-CONNECTORS.md#bmc_fw1--bmc-spi-firmware-socket).

## 13. Chip inventory around the BMC

Every identity below is quoted from the schematic's part-description field
[README](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/README.md#confirmed-chip-inventory-from-the-schematic):

```{list-table}
:header-rows: 1
:widths: 14 34 52

* - Ref
  - Part
  - Role
* - `QU2`
  - Hynix HY5PS121621CFP-25
  - BMC DDR2 SDRAM, 64 MiB (§3)
* - `BMC_FW1`
  - socketed SPI flash
  - BMC firmware (§4)
* - `U5`
  - Realtek RTL8201N-GR
  - management LAN PHY — {doc}`/hardware/peripherals/rtl8201n`
* - `LU1` / `LU2`
  - Intel WG82574L ×2
  - host GbE NICs + NC-SI sideband — {doc}`/hardware/peripherals/intel-82574l`
* - `QU4`
  - Winbond W83795G
  - hardware monitor — {doc}`/hardware/peripherals/w83795g`
* - `U27` / `U28`
  - Winbond W83601G ×2
  - DIMM error-LED I2C GPIO expanders — {doc}`/hardware/peripherals/w83601g`
* - `U25`
  - Holtek HT24LC08
  - board FRU EEPROM — {doc}`/hardware/peripherals/ht24lc08`
* - `QU9`
  - TI SN74CBTLV3125
  - I2C FET bus switch — {doc}`kgpe-d16-i2c`
* - `QU5`
  - 74HC4052
  - dual 4-channel I2C mux (DIMM SPD fan-out) — {doc}`kgpe-d16-i2c`
* - `U23`
  - 74LVC125
  - BMC-vs-southbridge I2C source-select — {doc}`kgpe-d16-i2c`
* - `QU8`
  - Pericom PI5C3257
  - 2:1 UART mux (SOL selection, §10)
* - `QU6`
  - Toshiba TC74VHCT125AF
  - VGA sync buffer (§9)
* - `U12` / `U13`
  - BCD AZ75232 ×2
  - RS-232 transceivers (§10)
* - `U6` / `U7` / `U8`
  - 74LVC07A / TC74LCX74 / 74LVC14A
  - power-sequencing / reset glue (§11)
* - `PU22` / `PU28`
  - UPI UP7706U8 ×2
  - +1V2_AUX / +1V8_AUX LDOs (§2)
* - `CU1`
  - IDT ICS932S890
  - main clock generator (host + Super-I/O clocks)
* - `CU2`
  - ICS ICS9112AM-16LFT
  - 50 MHz management-Ethernet clocks (§8)
* - `SU1`
  - AMD SP5100
  - southbridge / LPC-PCI-USB host — wiring in [SP5100-SOUTHBRIDGE-WIRING.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/SP5100-SOUTHBRIDGE-WIRING.md), context in {doc}`kgpe-d16` §4
* - `OU1`
  - Nuvoton W83667HG-A
  - Super-I/O — {doc}`/hardware/peripherals/w83667hg`
* - `NU1`
  - AMD SR5690
  - northbridge (A-Link uplink partner of the SP5100)
```

The bus-switch/mux/buffer parts (`QU9`, `QU5`, `U23`, `QU8`, `QU6`, the glue
logic, the LDOs and the clock generators) are **non-addressable analog/logic
parts — they have no register interface**; the BMC controls them only through
the select/enable nets documented in {doc}`kgpe-d16-i2c` (I2C fabric) and §10
(SOL mux).

## See also

**Related pages**

- {doc}`kgpe-d16` — board overview, debug headers, bring-up status
- {doc}`kgpe-d16-i2c` — the I2C/SMBus/PMBus topology this page only summarises
- {doc}`kgpe-d16-connectors` — pinout diagrams for every BMC-wired connector
- {doc}`/hardware/soc-ast2050` — the AST2050 SoC itself
- {doc}`/hardware/registers/index` — the per-block register documentation
- {doc}`/debug/bring-up` — how these wires were first exercised out-of-band

**External references**

- [`schematic-wiring/`](https://github.com/mithro/ai-shenanigans-for-bmcs/tree/main/asus-kgpe-d16-firmware/schematic-wiring) — the program's full pin-level wiring analysis this page condenses
- [OpenBoardView](https://openboardview.org/) — the boardview-file viewer ecosystem whose `.FZ` format the schematic export uses

## Sources

- **[`AST2050-BMC-WIRING.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md)** — the narrative per-function wiring
  documentation of all 355 BMC balls (sections §1–§16 cited throughout).
- **[`pinmaps/QU1_pins.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/pinmaps/QU1_pins.md)** — the machine-generated exhaustive
  per-ball table (ball → pin name → net → far-end pins) this page's ball
  numbers are drawn from.
- **[`SP5100-SOUTHBRIDGE-WIRING.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/SP5100-SOUTHBRIDGE-WIRING.md)** and
  **[`W83667HG-SUPERIO-WIRING.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/W83667HG-SUPERIO-WIRING.md)** — the far ends of the LPC,
  power-sequencing and SOL nets.
- **[`BMC-CONNECTORS.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/BMC-CONNECTORS.md)** — connector/header/jumper pinouts.
- **[`schematic-wiring/README.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/README.md)** — provenance, chip inventory, and the
  `.FZ` extraction/regeneration tooling.
