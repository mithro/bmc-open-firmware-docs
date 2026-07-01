# Systems

The program targets three management boards. Two share the Aspeed AST2050 SoC;
the third uses the Digi NS9360. All three use the same ARM926EJ-S (ARMv5TE) CPU
core, which is why they can share toolchains, a QEMU CPU model, and (for the
Zephyr track) a single ARMv5 architecture port.

```{toctree}
:maxdepth: 1

kgpe-d16
dell-c410x
hpe-ipdu
```

## Shared vs. per-board work

```{list-table}
:header-rows: 1
:widths: 30 35 35

* - Layer
  - Shared
  - Per-board
* - QEMU
  - `ast2050` / `ns9360` SoC model
  - machine wiring (I2C topology, GPIO, flash)
* - Linux
  - `aspeed-g3.dtsi` + AST2050 drivers
  - board `.dts` (sensors, GPIO, LEDs)
* - U-Boot
  - AST2050 DRAM/SoC init
  - board config, environment, netboot
* - OpenBMC
  - `meta-aspeed` base, kernel/U-Boot
  - `meta-<board>` (entity-manager, power seq)
* - WallaBMC (Zephyr)
  - ARMv5 arch + SoC ports
  - board devicetree + Redfish inventory
```
