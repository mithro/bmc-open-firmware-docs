# Digi NS9360 SoC

The NS9360 is a Digi (NetSilicon) SoC built around the same **ARM926EJ-S**
(ARMv5TE) core as the AST2050, but with an entirely different peripheral set. It
powers the HPE iPDU, whose stock firmware is NET+OS/ThreadX.

```{list-table}
:header-rows: 0
:widths: 30 70

* - CPU core
  - ARM926EJ-S (ARMv5TE)
* - Memory
  - SDRAM controller + dual CFI NOR flash (8 MiB total)
* - Networking
  - integrated 10/100 MAC + external PHY (ICS1893)
* - Serial
  - multiple UARTs (console + metering/display links)
* - I2C / GPIO / SPI
  - standard peripheral complement
```

## Open-firmware relevance

- **U-Boot** — an open port exists (`mithro/u-boot@hpe-ipdu-port`) modelling
  serial, GPIO, clock, I2C, Ethernet, and CFI flash; it boots under the QEMU
  `ns9360` machine.
- **Linux** — the archived `arch/arm/mach-ns9xxx` support (last seen around
  Linux 2.6.39) is the starting point for a forward-port.
- **QEMU** — the `ns9360` machine models the core, SDRAM, and dual CFI flash;
  board-complete modelling of the MAXQ3180 metering AFE, display MCU, and PHY is
  planned.

```{admonition} Register detail source
:class: note

The NS9360 Hardware Reference and datasheet (Digi part numbers 90000675 and
91001326) are the authority for the register map; block-level tables are added
here as each block is modelled or driven.
```
