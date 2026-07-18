# References

## Datasheets

Component datasheets are archived in the
[program repository](https://github.com/mithro/ai-shenanigans-for-bmcs) under
each board's `datasheets/` directory. Key parts:

- **SoCs:** Aspeed
  [AST2050/AST1100](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/datasheets/aspeed/AST2050_AST1100_A3_Datasheet_V1.05.pdf);
  Digi NS9360
  ([HW Reference 90000675](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/datasheets/NS9360_HW_Reference_90000675_J.pdf),
  [datasheet 91001326](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/datasheets/NS9360_datasheet_91001326_D.pdf)).
- **Sensors/power:**
  [INA219](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/datasheets/INA219_Datasheet.pdf),
  [ADT7462](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/datasheets/ADT7462_Datasheet.pdf),
  [TMP75](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/datasheets/TMP75_Datasheet.pdf),
  [LM75](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/datasheets/LM75_Datasheet.pdf),
  [MAXQ3180](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/datasheets/MAXQ3180_datasheet.pdf),
  [W83795G/ADG](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/datasheets/W83795G_W83795ADG_Datasheet.pdf).
- **I2C expanders/muxes:**
  [PCA9555](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/datasheets/PCA9555_Datasheet.pdf),
  [PCA9548A](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/datasheets/PCA9548A_Datasheet.pdf),
  [PCA9544A](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/datasheets/PCA9544A_Datasheet.pdf),
  [AT24C256](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/datasheets/AT24C256_Datasheet.pdf).
- **PCIe switches:** PLX
  [PEX8696](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/datasheets/PEX8696_ProductBrief.pdf),
  [PEX8647](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/datasheets/PEX8647_ProductBrief.pdf)
  (product briefs — family stand-ins; no register-level PEX86xx datasheet is in the repo).
- **SPI flash:**
  [M25P64](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/datasheets/M25P64_Datasheet.pdf)/[M25P128](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/datasheets/M25P128_Datasheet.pdf),
  [S25FL128P](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/datasheets/S25FL128P_Datasheet.pdf),
  [MX25L12835F](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/datasheets/MX25L12835F_Datasheet.pdf),
  [W25X64](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/datasheets/W25X64_Datasheet.pdf).

## Upstream projects

- OpenBMC — <https://github.com/openbmc/openbmc>
- WallaBMC — <https://github.com/tenstorrent-riscv-software/wallabmc>
- Zephyr — <https://github.com/zephyrproject-rtos/zephyr>
- U-Boot — <https://github.com/u-boot/u-boot>
- QEMU — <https://gitlab.com/qemu-project/qemu>
- Linux — <https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git>

## Prior art

- [Raptor Engineering](https://www.raptorengineering.com/)'s AST2050 Linux
  2.6.28.9 port — the reference for AST2050 SoC bring-up; analysed in-repo in
  [`RAPTOR_ENGINEERING_AST2050_ANALYSIS.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/RAPTOR_ENGINEERING_AST2050_ANALYSIS.md).
- Aspeed mainline support (AST2400/2500/2600) by Joel Stanley and the OpenBMC
  project ([`openbmc/linux`](https://github.com/openbmc/linux)) — the base the
  AST2050 (G3) work extends.
