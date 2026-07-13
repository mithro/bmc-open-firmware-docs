# QEMU machines

All QEMU work lives in the `mithro/qemu` fork and is pulled into the program as a
submodule, built from source in CI. Upstream QEMU models the AST2400/2500/2600
but **not** the AST2050 (G3) or the NS9360, so both are new machines.

## `kgpe-d16-bmc` (AST2050)

A new `ast2050` SoC type plus a `kgpe-d16-bmc` machine (branch
`d16-ast2050-machine`). Models the ARM926EJ-S core, SCU (with unlock key), SDRAM
controller, SPI NOR (FMC) at `0x14000000`, DRAM at `0x40000000`, UART console,
and the ftgmac100 MAC.

Four boot criteria are met and wired to CI:

```{list-table}
:header-rows: 1
:widths: 8 92

* - #
  - Criterion (all met)
* - C1
  - the machine builds from source in CI
* - C2
  - a from-source mainline U-Boot → Linux → BusyBox/dropbear boots to **SSH**
* - C3
  - the vintage **Raptor 2.6.28.9** AST2050 kernel + musl userspace boots to SSH
* - C4
  - the proprietary Dell C410X BMC image boots its whole stack to a **serving
    web service** (`curl` → HTTP 301, `Server: Mbedthis-Appweb`) — the
    proprietary-firmware emulation proof
```

## Faithful G3 model

Alongside the "make it boot" machine above, a parallel effort models the AST2050
*faithfully* — per-peripheral, against the datasheet, so the model reproduces the
real part's quirks rather than approximating them with G4 blocks. Modelled
faithfully so far: the **SMC** (static-memory / SPI read path), the **PLL/SCU**
clocking, and the **single-bank G3 VIC** wired by default. Each peripheral has a
bare-metal firmware-test (`fwtest`) harness plus pytest integration and a
datasheet chapter.

Two findings from this track fed real fixes: the timer emits one rising-edge
pulse per expiry (an earlier toggle-model caused a spurious hang that was wrongly
blamed on the VIC), and the ftgmac100 model reproduces the `FAST_MODE` RX bug
({doc}`../drivers/linux`) so the driver fix could be developed QEMU-first before
being confirmed on silicon.

## Modern OpenBMC in QEMU (Redfish)

Modern OpenBMC (Linux 6.18.x + `bmcweb`) builds from source and runs in QEMU,
answering **Redfish v1.17.0** with a working remote power-control path
(`POST .../ComputerSystem.Reset` → HTTP 204, `PowerState` transitions through
phosphor-state-manager) and an advertised vKVM. This is the QEMU vehicle behind
the {doc}`../firmware/openbmc` track; the same image path was subsequently taken
to the real AST2050.

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

## See also

**Related pages**

- {doc}`/emulation/testbench` — the qtest + `firmware-testbench` harness driving these machines
- {doc}`/hardware/soc-ast2050` — the AST2050 SoC the `kgpe-d16-bmc` model reproduces
- {doc}`/hardware/soc-ns9360` — the SoC behind the `ns9360` machine
- {doc}`/firmware/openbmc` — the OpenBMC/Redfish-in-QEMU vehicle
- {doc}`/drivers/linux` — the `FAST_MODE`/VIC fixes developed QEMU-first

**External references**

- [QEMU Aspeed machines](https://www.qemu.org/docs/master/system/arm/aspeed.html) — the upstream AST24xx/25xx/2600 models the AST2050 machine extends
- [QEMU Arm system emulation](https://www.qemu.org/docs/master/system/target-arm.html) — the Arm target these machines build on
- [QEMU `qtest` framework](https://www.qemu.org/docs/master/devel/testing/qtest.html) — the device-model test protocol used by the benches
