# Linux

## AST2050 (G3) support

Mainline Linux supports the AST2400 (G4) and later. AST2050 support is added as a
clean series in `mithro/linux`:

1. **`clk-aspeed`** — add AST2050 clock support (the H-PLL/derived clocks a G3
   part exposes).
2. **`aspeed-g3.dtsi`** — a new SoC include describing the AST2050 peripheral
   layout, mirroring `aspeed-g4.dtsi` with the G3 base addresses.
3. **`aspeed,ast2050-*` compatibles** on the affected drivers so they bind on G3.
4. **Board DTS** — `aspeed-bmc-asus-kgpe-d16.dts` and `aspeed-bmc-dell-c410x.dts`
   include the G3 dtsi.

```{admonition} Interim vs. target
:class: note

Until the G3 dtsi lands, the boards boot on `aspeed_g4_defconfig` + a clock patch
+ a board DTS based on `aspeed-g4.dtsi` (the AST2050 is register-compatible
enough). The clean G3 series is the upstreamable form.
```

## Peripheral drivers (all mainline)

Every C410X peripheral binds to an existing mainline driver — no out-of-tree
drivers are needed except the PCIe switch (handled in userspace):

```{list-table}
:header-rows: 1
:widths: 34 30 36

* - Device
  - Driver
  - Subsystem
* - INA219 ×16
  - `ina2xx`
  - hwmon
* - ADT7462 ×2
  - `adt7462`
  - hwmon
* - TMP75 ×16 / LM75
  - `lm75`
  - hwmon
* - PCA9555 ×5
  - `pca953x`
  - gpio
* - PCA9548 / PCA9544
  - `i2c-mux-pca954x`
  - i2c
* - ftgmac100 MAC
  - `ftgmac100`
  - net
* - SPI NOR (FMC)
  - `spi-aspeed-smc`
  - mtd/spi
* - I2C / GPIO / WDT
  - `i2c-aspeed` / `gpio-aspeed` / `aspeed-wdt`
  - —
* - PEX8696/8647
  - *(userspace daemon)*
  - see {doc}`../firmware/openbmc`
```

**Acceptance:** both board DTBs build and boot to SSH on the QEMU machine, on
both the stable and master kernel variants, and the `c410x-board-bench` confirms
every device above is bound (`i2cdetect`/`hwmon` map matches).

## NS9360 (iPDU)

No mainline support exists. The path is to forward-port the archived
`arch/arm/mach-ns9xxx` (≈ Linux 2.6.39) toward a modern kernel, device-tree-ifying
it. This is the highest-risk kernel item; the acceptance target is a console boot
on the QEMU `ns9360` machine.
