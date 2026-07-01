# ASUS KGPE-D16

A dual-socket AMD Opteron (Socket G34) server motherboard whose BMC is an
**Aspeed AST2050**. It is the *source of truth* for AST2050 SoC-level bring-up,
because it maps directly onto Raptor Engineering's known-good AST2050 Linux
port.

```{list-table}
:header-rows: 0
:widths: 30 70

* - BMC SoC
  - Aspeed AST2050 (also sold as AST1100)
* - CPU core
  - ARM926EJ-S (ARMv5TE)
* - DRAM
  - DDR2, mapped at `0x40000000`
* - Boot flash
  - SPI NOR at `0x14000000`
* - Console
  - UART, 115200 8N1
* - Debug
  - `AST_JTAG1` (BMC JTAG) + AMD HDT (host CPU); see {doc}`../debug/jtag-uart`
```

## Why this board leads the SoC work

The AST2050 is **not supported by mainline Linux** — the earliest supported
Aspeed generation is the AST2400 ("G4"). Raptor Engineering shipped a working
Linux 2.6.28.9 AST2050 port, which gives a reference for every SoC block (clock,
SDRAM, SMC/flash, MAC, GPIO, I2C, watchdog). The upstream path is a new
`aspeed-g3.dtsi` include plus `aspeed,ast2050-*` compatibles on the existing
mainline Aspeed drivers — see {doc}`../hardware/soc-ast2050` and
{doc}`../drivers/linux`.

## Emulation & firmware status

- **QEMU** — a custom `kgpe-d16-bmc` machine + new `ast2050` SoC boots U-Boot →
  Linux → SSH, and also boots the Raptor 2.6.28.9 + musl stack. See
  {doc}`../emulation/qemu`.
- **OpenBMC / WallaBMC** — planned; the board reuses the shared AST2050 layers.

The KGPE-D16 has no public proprietary BMC image, so proprietary-firmware
emulation proofs use the Dell C410X image (also AST2050) on the same machine.
