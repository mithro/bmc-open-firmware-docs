# Aspeed AST2050 (G3) SoC

The AST2050 (also sold as AST1100) is a third-generation Aspeed BMC SoC: an
ARM926EJ-S (ARMv5TE) core with integrated VGA, Ethernet MAC, I2C, GPIO, USB, and
SPI. It predates mainline Linux Aspeed support (which starts at the AST2400 /
"G4"), so both the QEMU model and the kernel treat it as a **G3** part that is
register-compatible enough with the G4 to reuse most peripheral models/drivers,
with SoC-specific deltas in the clock (SCU) and memory controllers.

## Memory map

```{list-table}
:header-rows: 1
:widths: 26 22 52

* - Region
  - Base
  - Notes
* - SPI NOR (FMC)
  - `0x14000000`
  - boot flash; U-Boot at flash base
* - DRAM
  - `0x40000000`
  - DDR2; 64–128 MiB depending on board
* - SDRAM controller
  - `0x1E6E0000`
  - unlock key `0xFC600309`
* - System Control Unit (SCU)
  - `0x1E6E2000`
  - unlock key `0x1688A8A8`; clocking + strap
* - GPIO controller
  - `0x1E780000`
  - GPIOA…GPIOP 8-bit port groups
* - MAC0 / MAC1 (ftgmac100)
  - `0x1E660000` / `0x1E680000`
  - 10/100 Ethernet
* - UART (console)
  - `0x1E783000` / `0x1E784000`
  - 16550-compatible, 115200 8N1
```

```{admonition} SCU / SDRAM unlock keys
:class: important

The SCU and SDRAM controllers are lock-protected: software must write the
unlock key to the first register before other registers accept writes. A QEMU
model must honour this (writes are ignored until unlocked) or vendor init code
mis-detects the part.
```

## G3 vs. G4 deltas that matter

- **SCU clocking** — H-PLL post-divider layout and hardware-strap bit positions
  differ from the AST2400. This is the primary reason a stock `palmetto-bmc`
  (AST2400) machine is only a smoke-test stand-in, not the target.
- **SDRAM / static-memory controllers** — different register semantics; only
  relevant to from-scratch DRAM init (U-Boot), not to a warm-booted kernel.
- **Everything else** (MAC, GPIO, I2C, watchdog, SMC read path, UART) is close
  enough that the G4 models/drivers bind unchanged with `aspeed,ast2050-*`
  compatibles.

## Upstreaming shape (Linux)

The clean series is: (1) a `clk-aspeed` change adding AST2050 support, (2) a new
`aspeed-g3.dtsi` SoC include, (3) `aspeed,ast2050-*` compatibles on the affected
drivers, then (4) the two board `.dts` files include the G3 dtsi. See
{doc}`../drivers/linux`.

```{admonition} Register detail source
:class: note

Full register-bit detail lives in the program's `ast2050.h` / `hwreg.h`
(U-Boot-style config + hardware register headers) and the Aspeed AST2050
datasheet. This page captures the SoC-level map a model/driver needs; per-block
bit tables are added as each block is modelled.
```
