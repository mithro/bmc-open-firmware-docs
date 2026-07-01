# QEMU machines

All QEMU work lives in the `mithro/qemu` fork and is pulled into the program as a
submodule, built from source in CI. Upstream QEMU models the AST2400/2500/2600
but **not** the AST2050 (G3) or the NS9360, so both are new machines.

## `kgpe-d16-bmc` (AST2050)

A new `ast2050` SoC type plus a `kgpe-d16-bmc` machine (branch
`d16-ast2050-machine`). Models the ARM926EJ-S core, SCU (with unlock key), SDRAM
controller, SPI NOR (FMC) at `0x14000000`, DRAM at `0x40000000`, UART console,
and the ftgmac100 MAC. It boots:

- a from-source mainline U-Boot → Linux → BusyBox/dropbear → **SSH**;
- the vintage **Raptor 2.6.28.9** AST2050 kernel + musl userspace → SSH; and
- the proprietary Dell C410X BMC image to a **serving web service** (the
  proprietary-firmware emulation proof).

## `c410x-bmc` (AST2050, board-complete) — planned

Wires the shared I2C device-model library and GPIO/PCA9555 lines onto the C410X's
7-bus topology ({doc}`../hardware/i2c-topology`), so an `i2cdetect` produces the
exact expected device map and sensors/power sequencing are observable.

## `ns9360` (Digi NS9360)

Models the ARM926EJ-S core, SDRAM, and dual CFI NOR flash (branch
`ns9360-machine`); boots the U-Boot port under a serial-socket smoke test.
Board-complete modelling (MAXQ3180, display MCU, Ethernet PHY) is planned.

## Shared I2C device-model library — planned

One reusable `I2CSlave` model per device type (INA219, ADT7462, TMP75/LM75,
PCA9555, PCA9548/PCA9544, PEX8696/8647), shared by the KGPE-D16 and C410X
machines. Built highest-multiplicity-first; each ships with a qtest bench.
