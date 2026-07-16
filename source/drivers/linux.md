# Linux

## AST2050 (G3) support

Mainline Linux supports the AST2400 (G4) and later. AST2050 support is added as a
clean series in [`mithro/linux`](https://github.com/mithro/linux):

1. **[`clk-aspeed`](https://github.com/torvalds/linux/blob/master/drivers/clk/aspeed/clk-aspeed.c)** — add AST2050 clock support (the H-PLL/derived clocks a G3
   part exposes).
2. **`aspeed-g3.dtsi`** — a new SoC include describing the AST2050 peripheral
   layout, mirroring [`aspeed-g4.dtsi`](https://github.com/torvalds/linux/blob/master/arch/arm/boot/dts/aspeed/aspeed-g4.dtsi) with the G3 base addresses.
3. **`aspeed,ast2050-*` compatibles** on the affected drivers so they bind on G3.
4. **Board DTS** — [`aspeed-bmc-asus-kgpe-d16.dts`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/qemu-firmware/dts/aspeed-bmc-asus-kgpe-d16.dts) and [`aspeed-bmc-dell-c410x.dts`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/aspeed-bmc-dell-c410x.dts)
   include the G3 dtsi.

```{admonition} Interim vs. target
:class: note

Until the G3 dtsi lands, the boards boot on
[`aspeed_g4_defconfig`](https://github.com/torvalds/linux/blob/master/arch/arm/configs/aspeed_g4_defconfig) + a
[clock patch](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/qemu-firmware/kernel/patches/0001-clk-aspeed-add-ast2050-support.patch)
+ a board DTS based on [`aspeed-g4.dtsi`](https://github.com/torvalds/linux/blob/master/arch/arm/boot/dts/aspeed/aspeed-g4.dtsi) (the AST2050 is register-compatible
enough). The clean G3 series is the upstreamable form.
```

### Hardware-verified G3 fixes

Booting a modern kernel (6.6.x) on a real AST2050 surfaced two G3-specific bugs,
both fixed and confirmed on silicon. The fixes are maintained as a patch series
in the program repo
([`asus-kgpe-d16-firmware/kernel/patches/`](https://github.com/mithro/ai-shenanigans-for-bmcs/tree/main/asus-kgpe-d16-firmware/kernel/patches),
applied on top of a Linux 6.6.70 base):

```{list-table}
:header-rows: 1
:widths: 40 60

* - Patch
  - What it fixes
* - [`0001-clk-aspeed-add-ast2050-support`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/qemu-firmware/kernel/patches/0001-clk-aspeed-add-ast2050-support.patch)
  - the G3 H-PLL / derived-clock support the SoC exposes
* - [`0002-ftgmac100-ast2050-macclk`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/kernel/patches/0002-ftgmac100-ast2050-macclk.patch)
  - leaves `MACCLK` at the U-Boot default on the G3 (the G3 U-Boot path never
    programs it); harmless on QEMU
* - [`0003-irqchip-add-aspeed-ast2050-vic-g3`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/kernel/patches/0003-irqchip-add-aspeed-ast2050-vic-g3.patch)
  - the compact G3 VIC driver (below) — the fix that unblocked the whole
    modern-kernel bring-up
```

#### `irq-aspeed-g3-vic.c` — the G3 interrupt controller

The single most important G3 fix. Mainline [`irq-aspeed-vic.c`](https://github.com/torvalds/linux/blob/master/drivers/irqchip/irq-aspeed-vic.c) targets the
AST2400+ interleaved VIC at `0x1E6C0080`; the AST2050's VIC is a compact block at
`0x1E6C0000` ({ref}`SoC detail <g3-vic>`). On the G3 the stock driver enables no
interrupts at all, so the timer clockevent never fires, hrtimers hang, and the
first `usleep_range()` in `ftgmac100_open()` hangs the boot. The new driver
(compatible `aspeed,ast2050-vic`, bound from the board DTS) programs
sense/event/dual-edge per the datasheet source table and ACKs edge sources via
`VIC38`. **Verified on real hardware:** the FTTMR010 clockevent fires (~1 kHz),
`eth0` links up on real interrupts, and IP-config completes to an NFS-root mount.

```{admonition} Debugging lesson
:class: tip

The P2A ("VGA") AHB window is *blind* to the `0x1E6C0000` VIC block (reads return
zero, writes are dropped) while DRAM/SCU/timer read back fine — so every
host-side observation of the VIC was a phantom zero. The only reliable observer
of the interrupt controller is the ARM core itself (kernel `pr_warn` plus an
interrupt-count `late_initcall`, read back out of `__log_buf`).
```

#### ftgmac100 RX and the `FAST_MODE` bit

With interrupts working, the MAC still received nothing (`rx=0`) while transmit
worked. Root cause: the G3 MAC software reset clears `MACCR` bit 19
(`FAST_MODE`), leaving a 100 Mbit link mis-configured as 10 Mbit so no frames are
accepted. The fix re-derives the speed from `cur_speed` in `start_hw` and restores
`FAST_MODE`. This was reproduced first in the QEMU MAC model, then confirmed on
silicon — after which OpenBMC-over-NFS with a live Redfish endpoint came up on the
real board (see {doc}`../firmware/openbmc`).

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
  - [`ina2xx`](https://github.com/torvalds/linux/blob/master/drivers/hwmon/ina2xx.c)
  - hwmon
* - ADT7462 ×2
  - [`adt7462`](https://github.com/torvalds/linux/blob/master/drivers/hwmon/adt7462.c)
  - hwmon
* - TMP75 ×16 / LM75
  - [`lm75`](https://github.com/torvalds/linux/blob/master/drivers/hwmon/lm75.c)
  - hwmon
* - PCA9555 ×5
  - [`pca953x`](https://github.com/torvalds/linux/blob/master/drivers/gpio/gpio-pca953x.c)
  - gpio
* - PCA9548 / PCA9544
  - [`i2c-mux-pca954x`](https://github.com/torvalds/linux/blob/master/drivers/i2c/muxes/i2c-mux-pca954x.c)
  - i2c
* - ftgmac100 MAC
  - [`ftgmac100`](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.c)
  - net
* - SPI NOR (FMC)
  - [`spi-aspeed-smc`](https://github.com/torvalds/linux/blob/master/drivers/spi/spi-aspeed-smc.c)
  - mtd/spi
* - I2C / GPIO / WDT
  - [`i2c-aspeed`](https://github.com/torvalds/linux/blob/master/drivers/i2c/busses/i2c-aspeed.c) / [`gpio-aspeed`](https://github.com/torvalds/linux/blob/master/drivers/gpio/gpio-aspeed.c) / [`aspeed-wdt`](https://github.com/torvalds/linux/blob/master/drivers/watchdog/aspeed_wdt.c)
  - —
* - PEX8696/8647
  - *(userspace daemon)*
  - see {doc}`../firmware/openbmc`
```

**Acceptance:** both board DTBs build and boot to SSH on the QEMU machine, on
both the stable and master kernel variants, and the `c410x-board-bench`
({doc}`/emulation/testbench`) confirms
every device above is bound (`i2cdetect`/`hwmon` map matches).

## NS9360 (iPDU)

No mainline support exists. The path is to forward-port the archived
[`arch/arm/mach-ns9xxx`](https://github.com/torvalds/linux/tree/v2.6.39/arch/arm/mach-ns9xxx) (≈ Linux 2.6.39) toward a modern kernel, device-tree-ifying
it. This is the highest-risk kernel item; the acceptance target is a console boot
on the QEMU `ns9360` machine ({doc}`/emulation/qemu`).

## See also

**Related pages**

- {doc}`/drivers/driver-reference` — the full verified driver table (source, `compatible`, caveats)
- {doc}`/drivers/peripheral-map` — peripheral → driver → daemon map
- {doc}`/hardware/soc-ast2050` — the AST2050 (G3) SoC these drivers bind to
- {doc}`/hardware/soc-ns9360` — the NS9360 SoC behind the mach-ns9xxx path
- {doc}`/firmware/openbmc` — the userspace these kernel fixes carry on silicon

**External references**

- [Devicetree usage model](https://docs.kernel.org/devicetree/usage-model.html) — how DT nodes bind to Linux drivers
- [Linux driver model](https://docs.kernel.org/driver-api/driver-model/index.html) — the bus/driver/device binding framework
- [Linux hwmon subsystem](https://docs.kernel.org/hwmon/index.html) — the subsystem behind the INA219/ADT7462/LM75 sensor drivers
- [Linux `arch/arm/mach-ns9xxx` (v2.6.39)](https://github.com/torvalds/linux/tree/v2.6.39/arch/arm/mach-ns9xxx) — the archived NS9360 platform tree to forward-port
