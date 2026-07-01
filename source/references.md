# References

## Datasheets

Component datasheets are archived in the program repository under each board's
`datasheets/` directory. Key parts:

- **SoCs:** Aspeed AST2050/AST1100; Digi NS9360 (HW Reference 90000675, datasheet
  91001326).
- **Sensors/power:** INA219, ADT7462, TMP75, LM75, MAXQ3180.
- **I2C expanders/muxes:** PCA9555, PCA9548A, PCA9544A, AT24C256.
- **PCIe switches:** PLX PEX8696, PEX8647.
- **SPI flash:** M25P64/M25P128, S25FL128P, MX25L12835F, W25X64.

## Upstream projects

- OpenBMC — <https://github.com/openbmc/openbmc>
- WallaBMC — <https://github.com/tenstorrent-riscv-software/wallabmc>
- Zephyr — <https://github.com/zephyrproject-rtos/zephyr>
- U-Boot — <https://github.com/u-boot/u-boot>
- QEMU — <https://gitlab.com/qemu-project/qemu>
- Linux — <https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git>

## Prior art

- Raptor Engineering's AST2050 Linux 2.6.28.9 port — the reference for AST2050
  SoC bring-up.
- Aspeed mainline support (AST2400/2500/2600) by Joel Stanley and the OpenBMC
  project — the base the AST2050 (G3) work extends.
