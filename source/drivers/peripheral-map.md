# Peripheral → driver & daemon map

The one-stop cross-reference from each documented hardware block to the software
that drives it: the **Linux** driver, the **U-Boot** touchpoint, the **Zephyr**
status (for the WallaBMC track), the **QEMU** model, and — for firmware — the
**OpenBMC** daemon. Each row links to its register reference so a driver author
can go from "which daemon" straight to "which registers".

```{admonition} Reading this map
:class: note

*Linux driver* names are mainline modules; `aspeed,ast2050-*` compatibles are
added by the program's patch series ({doc}`linux`). *Zephyr* entries are marked
*port needed* where no ARMv5 / ARM926EJ-S support exists yet — the WallaBMC
(Zephyr) track requires a first-class ARMv5 architecture port, so most SoC
drivers are greenfield there. *(planned)* marks a model/daemon that is scaffolded
but not yet complete.
```

## AST2050 SoC blocks

```{list-table}
:header-rows: 1
:widths: 20 26 18 18 18

* - Block
  - Linux driver
  - U-Boot
  - Zephyr (WallaBMC)
  - QEMU model
* - {doc}`SCU / clock <../hardware/registers/scu-clock-reset>`
  - [`clk-aspeed`](https://github.com/torvalds/linux/blob/master/drivers/clk/aspeed/clk-aspeed.c) (+ ast2050 patch)
  - board `platform.S`
  - port needed
  - `aspeed-scu` (part)
* - Reset control
  - `reset-aspeed` (auxiliary of clk)
  - `platform.S`
  - port needed
  - within SCU model
* - Watchdog
  - `aspeed-wdt`
  - optional
  - Zephyr `wdt` shim, port needed
  - `aspeed-wdt`
* - {doc}`DDR2 / SDRAM <../hardware/registers/ddr2-sdram>`
  - — (warm-booted; no runtime driver)
  - **`platform.S` init** (primary)
  - U-Boot-equivalent SPL needed
  - `aspeed-sdmc`
* - {doc}`MAC (ftgmac100) <../hardware/registers/network-mac-phy>`
  - [`ftgmac100`](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.c)
  - [`ftgmac100`](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.c) (tftp)
  - port needed
  - [`ftgmac100`](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.c)
* - MDIO / MII
  - [`ftgmac100`](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.c) internal MDIO / `mdio-aspeed`
  - within MAC
  - port needed
  - within MAC model
* - PHY (RTL8201CP)
  - `realtek` / generic clause-22 PHY
  - generic PHY
  - Zephyr `phy` clause-22
  - PHY-status model
* - {doc}`I2C / SMBus <../hardware/registers/buses-gpio>`
  - [`i2c-aspeed`](https://github.com/torvalds/linux/blob/master/drivers/i2c/busses/i2c-aspeed.c)
  - optional
  - port needed
  - `aspeed-i2c` (planned)
* - {doc}`SPI / SMC flash <../hardware/registers/buses-gpio>`
  - [`spi-aspeed-smc`](https://github.com/torvalds/linux/blob/master/drivers/spi/spi-aspeed-smc.c) (legacy-SMC caveat)
  - `spi_flash` / SMC
  - port needed
  - `aspeed-smc`
* - {doc}`LPC <../hardware/registers/buses-gpio>`
  - `aspeed-lpc-*` (KCS/SNOOP/etc.)
  - —
  - port needed
  - LPC (part)
* - {doc}`GPIO <../hardware/registers/buses-gpio>`
  - [`gpio-aspeed`](https://github.com/torvalds/linux/blob/master/drivers/gpio/gpio-aspeed.c) + [`pinctrl-aspeed`](https://github.com/torvalds/linux/tree/master/drivers/pinctrl/aspeed)
  - optional
  - Zephyr `gpio`, port needed
  - `aspeed-gpio` (planned)
* - {doc}`Interrupt controller (VIC) <../hardware/registers/uart-vic-timers>`
  - **`irq-aspeed-g3-vic`** (program driver)
  - `platform.S` polls
  - Zephyr `intc`, port needed
  - `aspeed-vic` (G3)
* - {doc}`Timers (FTTMR010) <../hardware/registers/uart-vic-timers>`
  - [`timer-fttmr010`](https://github.com/torvalds/linux/blob/master/drivers/clocksource/timer-fttmr010.c)
  - `platform.S`
  - Zephyr `timer`, port needed
  - `fttmr010`
* - {doc}`UART <../hardware/registers/uart-vic-timers>`
  - [`8250`](https://github.com/torvalds/linux/tree/master/drivers/tty/serial/8250) / `of_serial` (16550)
  - `ns16550`
  - Zephyr `uart_ns16550`
  - `serial-16550`
* - {doc}`VGA / Video Engine <../hardware/registers/pcie-vga-usb-bridges>`
  - [`drm/aspeed`](https://github.com/torvalds/linux/tree/master/drivers/gpu/drm/aspeed) (display); video-engine via [`aspeed-video`](https://github.com/torvalds/linux/blob/master/drivers/media/platform/aspeed/aspeed-video.c) (V4L2)
  - —
  - out of scope
  - VGA/PCIe endpoint (part)
* - {doc}`USB 2.0 hub <../hardware/registers/pcie-vga-usb-bridges>`
  - [`aspeed-vhub`](https://github.com/torvalds/linux/tree/master/drivers/usb/gadget/udc/aspeed-vhub) (UDC)
  - —
  - out of scope
  - — (planned)
* - {doc}`P2A / iLPC AHB bridges <../hardware/registers/pcie-vga-usb-bridges>`
  - — (out-of-band; `culvert` userspace)
  - —
  - —
  - endpoint model
```

## Off-chip peripherals

```{list-table}
:header-rows: 1
:widths: 20 12 24 24 20

* - Device
  - Board
  - Linux driver
  - OpenBMC daemon
  - Zephyr (WallaBMC)
* - {doc}`INA219 <../hardware/peripherals/ina219>`
  - C410X
  - [`ina2xx`](https://github.com/torvalds/linux/blob/master/drivers/hwmon/ina2xx.c) (hwmon)
  - `dbus-sensors` (`psusensor`/`adcsensor`)
  - Zephyr `sensor/ina219`
* - {doc}`ADT7462 <../hardware/peripherals/adt7462>`
  - C410X
  - [`adt7462`](https://github.com/torvalds/linux/blob/master/drivers/hwmon/adt7462.c) (hwmon)
  - `dbus-sensors` + `phosphor-pid-control` (fans)
  - port needed
* - {doc}`TMP75 / LM75 <../hardware/peripherals/tmp75-lm75>`
  - C410X
  - [`lm75`](https://github.com/torvalds/linux/blob/master/drivers/hwmon/lm75.c)
  - `dbus-sensors`
  - Zephyr `sensor/tmp75` / [`lm75`](https://github.com/torvalds/linux/blob/master/drivers/hwmon/lm75.c)
* - {doc}`PCA9555 <../hardware/peripherals/pca9555>`
  - C410X
  - [`gpio-pca953x`](https://github.com/torvalds/linux/blob/master/drivers/gpio/gpio-pca953x.c)
  - `entity-manager` + `phosphor-gpio-monitor`
  - Zephyr `gpio/pca95xx`
* - {doc}`PCA9548/9544 <../hardware/peripherals/pca954x-mux>`
  - C410X
  - [`i2c-mux-pca954x`](https://github.com/torvalds/linux/blob/master/drivers/i2c/muxes/i2c-mux-pca954x.c)
  - (kernel mux; consumed transparently)
  - Zephyr `i2c_mux`
* - {doc}`PEX8696 / 8647 <../hardware/peripherals/pex8696-8647>`
  - C410X
  - — (userspace)
  - PEX I2C daemon (phosphor-style, *planned*)
  - custom
* - {doc}`W83795G <../hardware/peripherals/w83795g>`
  - KGPE-D16
  - [`w83795`](https://github.com/torvalds/linux/blob/master/drivers/hwmon/w83795.c) (hwmon; **host** SP5100 SMBus)
  - host-side; not BMC-managed on this board
  - n/a
* - {doc}`ICS1893 <../hardware/peripherals/ics1893>`
  - iPDU
  - generic clause-22 PHY
  - n/a (NS9360 board)
  - Zephyr `phy`
* - {doc}`MAXQ3180 <../hardware/peripherals/maxq3180>`
  - iPDU
  - — (no mainline driver; SPI AFE)
  - n/a
  - custom SPI driver
* - {doc}`TMP89 <../hardware/peripherals/tmp89>`
  - iPDU
  - — (sub-MCU; custom serial protocol)
  - n/a
  - custom
```

## OpenBMC feature → daemon

Which OpenBMC service implements each BMC feature, and the hardware path it uses
(see {doc}`../firmware/openbmc`):

```{list-table}
:header-rows: 1
:widths: 22 30 48

* - Feature
  - Daemon
  - Hardware path
* - Redfish / web
  - `bmcweb`
  - HTTPS → D-Bus
* - IPMI (LAN + host)
  - `phosphor-host-ipmid` / `phosphor-ipmi-net`
  - host IPMI over **KCS** (LPC); LAN over the MAC
* - Sensors
  - `dbus-sensors` + `entity-manager`
  - hwmon (INA219/ADT7462/LM75) over I2C
* - Fan control
  - `phosphor-pid-control`
  - ADT7462 PWM/tach
* - Power / state
  - `phosphor-state-manager`
  - GPIO ([`gpio-aspeed`](https://github.com/torvalds/linux/blob/master/drivers/gpio/gpio-aspeed.c) / PCA9555)
* - Serial-over-LAN
  - `obmc-console`
  - the SoC UART
* - System identity / FRU
  - `entity-manager` + FRU EEPROM
  - I2C EEPROM
* - vKVM
  - `obmc-ikvm`
  - Video Engine capture + USB HID
* - Firmware update
  - `phosphor-bmc-code-mgmt`
  - SPI/SMC flash
```

## WallaBMC (Zephyr) ARMv5 gap

Zephyr has **no ARM926EJ-S / ARMv5TE architecture support** — its ARM support
starts at ARMv6-M/ARMv7. Bringing WallaBMC (Tenstorrent's Zephyr BMC) to either
SoC in this program therefore requires a **first-class ARMv5 architecture port**
as a prerequisite deliverable, on top of which the per-peripheral Zephyr drivers
above are written. This is tracked as the highest-risk item of the WallaBMC
track; see {doc}`../firmware/wallabmc`.
