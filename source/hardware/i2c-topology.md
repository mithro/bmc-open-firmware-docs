# Dell C410X I2C topology

The AST2050 BMC manages every board peripheral over **7 I2C buses**. This map is
the reverse-engineered ground truth that the
[reconstructed device tree](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/aspeed-bmc-dell-c410x.dts),
the `c410x-bmc` QEMU machine, and the OpenBMC entity-manager configuration all
mirror.

```{figure} /_static/diagrams/c410x-i2c-topology.svg
:alt: The C410X I2C topology — the AST2050 I2C engine fanning out to seven buses through PCA9544A/PCA9548A muxes to the sensor, GPIO-expander and PEX-switch devices.
:width: 90%

The C410X seven-bus I2C topology (see {doc}`../systems/dell-c410x` for the full device inventory and interrupt routing).
```

```{admonition} Scope — this page is C410X-specific
:class: note

This topology is the **Dell C410X** BMC I2C map. The other two program boards
have their own: the **KGPE-D16** map is now fully characterised from the
board's schematic netlist — eight AST2050 controllers reaching the W83795G,
the DIMM SPD/TSOD banks, the FRU EEPROM and the PSU through an *analog*
switch fabric shared multi-master with the host SP5100 — documented on
{doc}`../systems/kgpe-d16-i2c`. (Earlier revisions of this note said those
sensors were reachable only from the host SMBus; the netlist shows the bus is
shared.) The **iPDU** uses the Digi NS9360's I2C controller
({doc}`soc-ns9360-memory-serial`) to reach its extension-bar connectors,
covered on {doc}`../systems/hpe-ipdu`.
```

## Device count summary

```{list-table}
:header-rows: 1
:widths: 30 14 56

* - Device
  - Qty
  - Function
* - {doc}`peripherals/ina219`
  - 16
  - per-slot current/power (bus 0xF0)
* - {doc}`peripherals/adt7462`
  - 2
  - temp/voltage monitor + 4-ch PWM fan control (bus 0xF1)
* - {doc}`peripherals/tmp75-lm75`
  - 16 + 1
  - per-slot temps (muxed, 0xF4) + front ambient (0xF6)
* - {doc}`peripherals/pca9555`
  - 5
  - GPIO expanders: presence, power-good, buttons, MRL, PSU/LED
* - {doc}`peripherals/pca954x-mux`
  - 2 + 1
  - PCA9548 8-ch (0xF4) + PCA9544 4-ch (0xF1) muxes
* - {doc}`peripherals/pex8696-8647`
  - 4 + 2
  - PLX PCIe switches (bus 0xF3)
* - [AT24C256 EEPROM](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/datasheets/AT24C256_Datasheet.pdf)
  - 1
  - FRU data (bus 0xF2)
```

Verifying that a QEMU boot produces exactly this map (`i2cdetect` on all 7 buses)
is the `c410x-board-bench` acceptance test — see {doc}`../emulation/testbench`.
