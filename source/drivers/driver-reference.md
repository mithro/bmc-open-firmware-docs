# Driver reference

The complete driver reference for the program: every Linux (and platform)
driver the documentation names, with its **verified** upstream source, the
device-tree `compatible` string(s) it binds on, the hardware block it drives
(cross-linked to the register/peripheral reference), and any
G3 / AST2050 / board-specific caveat. Two boards in this program share the
AST2050 (G3) SoC (ASUS KGPE-D16, Dell C410X); the Digi NS9360 board (HPE iPDU)
is a different SoC with no mainline support.

Every entry in the **Source** column is a real link to the file (or, for a
multi-file driver, the directory) on `torvalds/linux`, checked to resolve
(HTTP 200) at author time. Program-repo drivers are part of the AST2050 G3 patch
series and are documented in the register pages rather than upstream — their
Source cell says so and links the mainline driver they derive from or patch.

```{admonition} How to read the caveat column
:class: note

Mainline Aspeed drivers carry `aspeed,ast2400-*` / `aspeed,ast2500-*`
`compatible` strings. The program's patch series (the [Linux driver page][program-linux])
adds `aspeed,ast2050-*` where a G3 part diverges, and adds the two G3-only
drivers (`irq-aspeed-g3-vic`, plus the [`ftgmac100`](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.c) `FAST_MODE` RX fix and the
[`clk-aspeed`](https://github.com/torvalds/linux/blob/master/drivers/clk/aspeed/clk-aspeed.c) AST2050 clock patch). "Not register-compatible" means the mainline
driver's register layout does **not** match the G3 block and a G3-specific
driver/compatible is required, not just an added match-table entry.
```

## Master table

```{list-table}
:header-rows: 1
:widths: 16 12 20 22 16 14

* - Driver
  - Subsystem
  - Source
  - Compatible
  - Drives
  - G3 caveat
* - [`ftgmac100`](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.c)
  - net
  - [ftgmac100.c][ftgmac100] · [.h][ftgmac100-h]
  - `faraday,ftgmac100`; `aspeed,ast2400-mac`; program `aspeed,ast2050-mac`
  - [MAC / MDIO / PHY][reg-mac]
  - program adds `ast2050-mac` + `FAST_MODE` RX fix + MACCLK-default patch
* - [`i2c-aspeed`](https://github.com/torvalds/linux/blob/master/drivers/i2c/busses/i2c-aspeed.c)
  - i2c
  - [i2c-aspeed.c][i2c-aspeed]
  - `aspeed,ast2400-i2c-bus`; `aspeed,ast2500-i2c-bus`
  - [I2C / SMBus][reg-buses]
  - G3 binds on `ast2400-i2c-bus`; 14-bus engine
* - [`spi-aspeed-smc`](https://github.com/torvalds/linux/blob/master/drivers/spi/spi-aspeed-smc.c)
  - spi / mtd
  - [spi-aspeed-smc.c][spi-aspeed-smc]
  - `aspeed,ast2400-fmc` / `-spi` … `aspeed,ast2600-fmc` / `-spi`
  - [SPI / SMC flash][reg-buses]
  - targets the AST2400+ **FMC**, not the legacy G3 SMC at `0x16000000`
* - [`gpio-aspeed`](https://github.com/torvalds/linux/blob/master/drivers/gpio/gpio-aspeed.c)
  - gpio
  - [gpio-aspeed.c][gpio-aspeed]
  - `aspeed,ast2400-gpio` … `aspeed,ast2700-gpio`
  - [GPIO][reg-buses]
  - G3 binds on `ast2400-gpio`; pairs with [`pinctrl-aspeed`](https://github.com/torvalds/linux/tree/master/drivers/pinctrl/aspeed)
* - [`pinctrl-aspeed`](https://github.com/torvalds/linux/tree/master/drivers/pinctrl/aspeed)
  - pinctrl
  - [pinctrl/aspeed/][pinctrl-aspeed]
  - `aspeed,ast2400-pinctrl` (g4); `aspeed,ast2500-pinctrl` (g5)
  - [GPIO / pinmux][reg-buses]
  - no G3-specific compatible; G3 pinmux is SCU-strap driven
* - [`clk-aspeed`](https://github.com/torvalds/linux/blob/master/drivers/clk/aspeed/clk-aspeed.c)
  - clk
  - [clk-aspeed.c][clk-aspeed]
  - `aspeed,ast2400-scu`; `aspeed,ast2500-scu`
  - [SCU / clock / reset][reg-scu]
  - program patch adds AST2050 H-PLL / derived-clock support
* - [`timer-fttmr010`](https://github.com/torvalds/linux/blob/master/drivers/clocksource/timer-fttmr010.c)
  - clocksource
  - [timer-fttmr010.c][timer-fttmr010]
  - `faraday,fttmr010`; `aspeed,ast2400-timer`; `aspeed,ast2500-timer`
  - [Timers (FTTMR010)][reg-uvt]
  - G3 relies on the one-pulse match behaviour; single-shot clockevent
* - [`8250`](https://github.com/torvalds/linux/tree/master/drivers/tty/serial/8250) (core)
  - tty / serial
  - [tty/serial/8250/][uart-8250]
  - `ns16550a` (SoC UART node)
  - [UARTs (16550)][reg-uvt]
  - G3 UARTs are standard 16550; no G3 quirk
* - [`8250_aspeed_vuart`](https://github.com/torvalds/linux/blob/master/drivers/tty/serial/8250/8250_aspeed_vuart.c)
  - tty / serial
  - [8250_aspeed_vuart.c][vuart]
  - `aspeed,ast2400-vuart`; `aspeed,ast2500-vuart`
  - [Virtual UART][reg-ctrl]
  - LPC host-visible VUART (base `0x1E787000`); unused on both boards
* - [`aspeed-pwm-tacho`](https://github.com/torvalds/linux/blob/master/drivers/hwmon/aspeed-pwm-tacho.c)
  - hwmon
  - [aspeed-pwm-tacho.c][pwm-tacho]
  - `aspeed,ast2400-pwm-tacho`; `aspeed,ast2500-pwm-tacho`
  - [PWM / fan-tach][reg-ctrl]
  - base `0x1E786000`; unused on both boards (C410X fans via ADT7462)
* - [`rtc-aspeed`](https://github.com/torvalds/linux/blob/master/drivers/rtc/rtc-aspeed.c)
  - rtc
  - [rtc-aspeed.c][rtc-aspeed]
  - `aspeed,ast2400-rtc` … `aspeed,ast2700-rtc`
  - [RTC][reg-ctrl]
  - **not register-compatible** with the G3 RTC (base `0x1E781000`)
* - [`peci-aspeed`](https://github.com/torvalds/linux/blob/master/drivers/peci/controller/peci-aspeed.c)
  - peci
  - [peci-aspeed.c][peci-aspeed]
  - `aspeed,ast2400-peci`; `aspeed,ast2500-peci`; `aspeed,ast2600-peci`
  - [PECI][reg-ctrl]
  - G3 base `0x1E78B000`; unused on both boards
* - [`aspeed-wdt`](https://github.com/torvalds/linux/blob/master/drivers/watchdog/aspeed_wdt.c)
  - watchdog
  - [aspeed_wdt.c](https://github.com/torvalds/linux/blob/master/drivers/watchdog/aspeed_wdt.c)
  - `aspeed,ast2400-wdt`; `aspeed,ast2500-wdt`
  - [Watchdog][reg-scu]
  - G3 binds on `ast2400-wdt`; WDT block adjacent to the SCU
* - [`aspeed-lpc-ctrl`](https://github.com/torvalds/linux/blob/master/drivers/soc/aspeed/aspeed-lpc-ctrl.c)
  - soc / lpc
  - [aspeed-lpc-ctrl.c](https://github.com/torvalds/linux/blob/master/drivers/soc/aspeed/aspeed-lpc-ctrl.c)
  - `aspeed,ast2400-lpc-ctrl`; `aspeed,ast2500-lpc-ctrl`
  - [LPC][reg-buses]
  - host↔BMC LPC firmware/mailbox windows
* - [`aspeed-lpc-snoop`](https://github.com/torvalds/linux/blob/master/drivers/soc/aspeed/aspeed-lpc-snoop.c)
  - soc / lpc
  - [aspeed-lpc-snoop.c](https://github.com/torvalds/linux/blob/master/drivers/soc/aspeed/aspeed-lpc-snoop.c)
  - `aspeed,ast2400-lpc-snoop`; `aspeed,ast2500-lpc-snoop`
  - [LPC][reg-buses]
  - snoops host I/O-port writes (BIOS POST codes)
* - [`kcs_bmc_aspeed`](https://github.com/torvalds/linux/blob/master/drivers/char/ipmi/kcs_bmc_aspeed.c)
  - ipmi / kcs
  - [kcs_bmc_aspeed.c](https://github.com/torvalds/linux/blob/master/drivers/char/ipmi/kcs_bmc_aspeed.c)
  - `aspeed,ast2400-kcs-bmc`; `aspeed,ast2500-kcs-bmc-v2`
  - [LPC][reg-buses]
  - host-side IPMI over KCS (LPC) — **silicon-proven** on the KGPE-D16
* - [`realtek`](https://github.com/torvalds/linux/tree/master/drivers/net/phy/realtek) / generic clause-22 PHY
  - net / phy
  - [realtek/](https://github.com/torvalds/linux/tree/master/drivers/net/phy/realtek)
  - clause-22 PHY ID (generic `genphy` fallback)
  - [MAC / MDIO / PHY][reg-mac]
  - the RTL8201CP binds the realtek / generic clause-22 driver over the MAC's MDIO
* - [`aspeed-vhub`](https://github.com/torvalds/linux/tree/master/drivers/usb/gadget/udc/aspeed-vhub)
  - usb / gadget (udc)
  - [aspeed-vhub/][aspeed-vhub] · [vhub.h][vhub-h]
  - `aspeed,ast2400-usb-vhub` … `aspeed,ast2700-usb-vhub`
  - [USB 2.0 virtual hub][reg-disp]
  - base `0x1E6A0000`; the vKVM HID path
* - [`uhci-hcd`](https://github.com/torvalds/linux/blob/master/drivers/usb/host/uhci-hcd.c)
  - usb / host
  - [uhci-hcd.c](https://github.com/torvalds/linux/blob/master/drivers/usb/host/uhci-hcd.c)
  - `aspeed,ast2400-uhci`, `generic-uhci`
  - [USB 1.1 UHCI host][reg-disp]
  - standard Intel UHCI at `0x1E6B0000`; **no EHCI host on G3**
* - [`aspeed-video`](https://github.com/torvalds/linux/blob/master/drivers/media/platform/aspeed/aspeed-video.c)
  - media (V4L2)
  - [aspeed-video.c][aspeed-video]
  - `aspeed,ast2400-video-engine` … `aspeed,ast2600-video-engine`
  - [Video Engine][reg-disp]
  - base `0x1E700000`; the vKVM capture path
* - [`drm/ast`](https://github.com/torvalds/linux/tree/master/drivers/gpu/drm/ast)
  - gpu / drm
  - [gpu/drm/ast/][drm-ast]
  - PCI-matched (no DT `compatible`)
  - [VGA display controller][reg-disp]
  - **host-side** KMS driver for the BMC's VGA PCI function — not BMC-side
* - [`drm/aspeed`](https://github.com/torvalds/linux/tree/master/drivers/gpu/drm/aspeed)
  - gpu / drm
  - [gpu/drm/aspeed/][drm-aspeed]
  - `aspeed,ast2400-gfx`; `aspeed,ast2500-gfx`; `aspeed,ast2600-gfx`
  - [SoC display / CRTC][reg-disp]
  - the **BMC-side** SoC framebuffer (`aspeed-gfx`); runs on the AST2050
* - [`pca953x`](https://github.com/torvalds/linux/blob/master/drivers/gpio/gpio-pca953x.c) ([`gpio-pca953x`](https://github.com/torvalds/linux/blob/master/drivers/gpio/gpio-pca953x.c))
  - gpio
  - [gpio-pca953x.c][pca953x]
  - `nxp,pca9555`
  - [PCA9555][per-pca9555]
  - off-chip; C410X ×5
* - [`i2c-mux-pca954x`](https://github.com/torvalds/linux/blob/master/drivers/i2c/muxes/i2c-mux-pca954x.c)
  - i2c (mux)
  - [i2c-mux-pca954x.c][pca954x]
  - `nxp,pca9548`; `nxp,pca9544`
  - [PCA9548 / PCA9544][per-pca954x]
  - off-chip; C410X I2C fan-out
* - [`ina2xx`](https://github.com/torvalds/linux/blob/master/drivers/hwmon/ina2xx.c)
  - hwmon
  - [ina2xx.c][ina2xx]
  - `ti,ina219` (i2c id `ina219`)
  - [INA219][per-ina219]
  - off-chip; C410X ×16 rail monitors
* - [`adt7462`](https://github.com/torvalds/linux/blob/master/drivers/hwmon/adt7462.c)
  - hwmon
  - [adt7462.c][adt7462]
  - `adi,adt7462` (i2c id [`adt7462`](https://github.com/torvalds/linux/blob/master/drivers/hwmon/adt7462.c))
  - [ADT7462][per-adt7462]
  - off-chip; C410X ×2; fan/PWM + temp
* - [`lm75`](https://github.com/torvalds/linux/blob/master/drivers/hwmon/lm75.c)
  - hwmon
  - [lm75.c][lm75]
  - `ti,tmp75`; `national,lm75`
  - [TMP75 / LM75][per-tmp75]
  - off-chip; C410X ×16 board temps
* - [`w83795`](https://github.com/torvalds/linux/blob/master/drivers/hwmon/w83795.c)
  - hwmon
  - [w83795.c][w83795]
  - i2c ids `w83795g` / `w83795adg`
  - [W83795G][per-w83795]
  - KGPE-D16 **host-side** (SP5100 SMBus); not BMC-managed
* - `irq-aspeed-g3-vic`
  - irqchip
  - program patch — base [irq-aspeed-vic.c][vic-mainline]
  - `aspeed,ast2050-vic`
  - [Interrupt controller (VIC)][reg-uvt]
  - **program driver**: mainline VIC targets the AST2400+ block at `0x1E6C0080`; G3 VIC is the compact block at `0x1E6C0000`
* - [`ftgmac100`](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.c) `FAST_MODE` fix
  - net (patch)
  - patch on [ftgmac100.c][ftgmac100]
  - (same as [`ftgmac100`](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.c))
  - [MAC / MDIO / PHY][reg-mac]
  - **program patch**: G3 MAC SW-reset clears `MACCR[19]` (`FAST_MODE`) → `rx=0`
* - [`clk-aspeed`](https://github.com/torvalds/linux/blob/master/drivers/clk/aspeed/clk-aspeed.c) AST2050 patch
  - clk (patch)
  - patch on [clk-aspeed.c][clk-aspeed]
  - (adds AST2050 data)
  - [SCU / clock / reset][reg-scu]
  - **program patch**: adds the G3 H-PLL / derived clocks
* - NS9360 ([`mach-ns9xxx`](https://github.com/torvalds/linux/tree/v2.6.39/arch/arm/mach-ns9xxx))
  - arch / platform
  - [mach-ns9xxx @ v2.6.39][mach-ns9xxx]
  - none (pre-DT board files)
  - iPDU SoC (NS9360)
  - **no mainline driver** since v2.6.39; open path is a U-Boot port
```

```{admonition} Driver names subsumed by another row
:class: note

A few driver names appear in the [peripheral map][program-linux] and the Linux
page but have no row of their own, because on the G3 they are **not** separate
bindable drivers:

- `reset-aspeed` — the reset controller is implemented *inside*
  [`clk-aspeed`][clk-aspeed] (reset ops on the same node), not a standalone driver.
- `mdio-aspeed` — an AST2600-only MDIO controller; on the G3 the MDIO bus is
  **internal to** [`ftgmac100`][ftgmac100], so no separate driver binds.
- `of_serial` / [`8250_of`](https://github.com/torvalds/linux/blob/master/drivers/tty/serial/8250/8250_of.c)
  — only the device-tree glue that instantiates the [`8250`][uart-8250] core for
  the SoC 16550 UARTs.

Each is covered by the linked row above.
```

## Per-driver notes

### AST2050 SoC drivers (mainline)

**[`ftgmac100`](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.c)** drives the Faraday-derived 10/100 MAC (with internal MDIO) that
the AST2050 exposes; it binds today on `aspeed,ast2400-mac` and the program adds
`aspeed,ast2050-mac`. Two G3-only fixes are required and hardware-verified: the
`FAST_MODE` RX fix (the G3 MAC software reset clears `MACCR` bit 19, mis-setting
a 100 Mbit link as 10 Mbit so `rx=0`) and a patch that leaves `MACCLK` at the
U-Boot default on G3. See [MAC / MDIO / PHY][reg-mac].

**[`i2c-aspeed`](https://github.com/torvalds/linux/blob/master/drivers/i2c/busses/i2c-aspeed.c)** drives the AST2050 I2C/SMBus engine (14 buses); on G3 it binds
on the `aspeed,ast2400-i2c-bus` compatible. It is the path to every off-chip
sensor and mux on the C410X. See [I2C / SMBus][reg-buses].

**[`spi-aspeed-smc`](https://github.com/torvalds/linux/blob/master/drivers/spi/spi-aspeed-smc.c)** is the mainline Aspeed SPI/flash controller driver, but it
targets the **FMC** (Firmware Memory Controller) introduced on the AST2400 and
its `aspeed,ast24/25/2600-fmc`/`-spi` compatibles. The AST2050's legacy **SMC**
at `0x16000000` is a different, older controller; this driver does not cover it
directly, so the G3 flash path needs the legacy-SMC handling noted in
[SPI / SMC flash][reg-buses].

**[`gpio-aspeed`](https://github.com/torvalds/linux/blob/master/drivers/gpio/gpio-aspeed.c)** drives the SoC GPIO banks (base `0x1E780000`) and binds on
`aspeed,ast2400-gpio` for G3; it works together with **[`pinctrl-aspeed`](https://github.com/torvalds/linux/tree/master/drivers/pinctrl/aspeed)** for
pin muxing. The G3 has no dedicated pinctrl compatible — its pin multiplexing is
strap/`SCU`-driven — so [`pinctrl-aspeed`](https://github.com/torvalds/linux/tree/master/drivers/pinctrl/aspeed)'s `aspeed,ast2400-pinctrl` (g4) is used
where a pinctrl node is needed. See [GPIO][reg-buses].

**[`clk-aspeed`](https://github.com/torvalds/linux/blob/master/drivers/clk/aspeed/clk-aspeed.c)** is the SCU clock driver (`aspeed,ast2400-scu` /
`aspeed,ast2500-scu`); the program's clock patch adds the AST2050 H-PLL and
derived clocks the G3 part exposes so the rest of the SoC probes. See
[SCU / clock / reset][reg-scu].

**[`timer-fttmr010`](https://github.com/torvalds/linux/blob/master/drivers/clocksource/timer-fttmr010.c)** drives the Faraday FTTMR010 timer block used for the system
clocksource/clockevent (`faraday,fttmr010`, `aspeed,ast2400-timer`). On G3 the
timer must emit a single rising-edge pulse per expiry into the VIC; the
one-pulse match behaviour is documented in [Timers (FTTMR010)][reg-uvt].

**[`8250`](https://github.com/torvalds/linux/tree/master/drivers/tty/serial/8250) / [`8250_aspeed_vuart`](https://github.com/torvalds/linux/blob/master/drivers/tty/serial/8250/8250_aspeed_vuart.c)** — the SoC UARTs are standard 16550s driven by
the generic [`8250`](https://github.com/torvalds/linux/tree/master/drivers/tty/serial/8250) core (DT `ns16550a`); the separate [`8250_aspeed_vuart`](https://github.com/torvalds/linux/blob/master/drivers/tty/serial/8250/8250_aspeed_vuart.c) driver
(`aspeed,ast2400-vuart`) handles the LPC host-visible **virtual UART** at
`0x1E787000`, which is unused on both program boards. See
[UARTs (16550)][reg-uvt] and [Virtual UART][reg-ctrl].

**[`aspeed-pwm-tacho`](https://github.com/torvalds/linux/blob/master/drivers/hwmon/aspeed-pwm-tacho.c)** drives the SoC PWM & fan-tachometer controller at
`0x1E786000` (`aspeed,ast2400-pwm-tacho`). It is documented for completeness but
unused on both boards — the C410X drives fans through the off-chip ADT7462s. See
[PWM / fan-tach][reg-ctrl].

**[`rtc-aspeed`](https://github.com/torvalds/linux/blob/master/drivers/rtc/rtc-aspeed.c)** drives the AST2400+ RTC (`aspeed,ast2400-rtc`). It is **not
register-compatible** with the AST2050's RTC at `0x1E781000`; a G3-specific RTC
driver/compatible is required rather than a match-table addition. See
[RTC][reg-ctrl].

**[`peci-aspeed`](https://github.com/torvalds/linux/blob/master/drivers/peci/controller/peci-aspeed.c)** drives the PECI controller (`aspeed,ast2400-peci`); the G3
block is at `0x1E78B000` and is unused on both boards. See [PECI][reg-ctrl].

**[`aspeed-vhub`](https://github.com/torvalds/linux/tree/master/drivers/usb/gadget/udc/aspeed-vhub)** drives the USB 2.0 virtual-hub UDC at `0x1E6A0000`
(`aspeed,ast2400-usb-vhub`) — the gadget side of the vKVM HID path — and
**[`aspeed-video`](https://github.com/torvalds/linux/blob/master/drivers/media/platform/aspeed/aspeed-video.c)** drives the Video (capture/compression) Engine at `0x1E700000`
(`aspeed,ast2400-video-engine`) that captures host framebuffers for vKVM. Both
are register-mapped in [USB 2.0 virtual hub / Video Engine][reg-disp].

**[`drm/ast`](https://github.com/torvalds/linux/tree/master/drivers/gpu/drm/ast) vs [`drm/aspeed`](https://github.com/torvalds/linux/tree/master/drivers/gpu/drm/aspeed)** — these are easy to confuse. [`drm/ast`](https://github.com/torvalds/linux/tree/master/drivers/gpu/drm/ast) is the
**host-side** KMS/DRM driver for the Aspeed BMC's VGA function as seen over PCIe
by the *host* CPU (matched by PCI ID, no DT `compatible`); it does not run on the
BMC. [`drm/aspeed`](https://github.com/torvalds/linux/tree/master/drivers/gpu/drm/aspeed) (the `aspeed-gfx` driver, `aspeed,ast2400-gfx` /
`aspeed,ast2500-gfx`) is the **BMC-side** SoC display/CRTC that scans the SoC
framebuffer out to the analog VGA connector — this is the one that runs on the
AST2050. Both relate to the [VGA / display registers][reg-disp].

### Off-chip peripheral drivers (mainline)

**[`pca953x`](https://github.com/torvalds/linux/blob/master/drivers/gpio/gpio-pca953x.c)** ([`gpio-pca953x`](https://github.com/torvalds/linux/blob/master/drivers/gpio/gpio-pca953x.c), `nxp,pca9555`) drives the five PCA9555 I2C GPIO
expanders on the C410X ([PCA9555][per-pca9555]). **[`i2c-mux-pca954x`](https://github.com/torvalds/linux/blob/master/drivers/i2c/muxes/i2c-mux-pca954x.c)**
(`nxp,pca9548` / `nxp,pca9544`) drives the C410X I2C mux fan-out
([PCA9548 / PCA9544][per-pca954x]). **[`ina2xx`](https://github.com/torvalds/linux/blob/master/drivers/hwmon/ina2xx.c)** (`ti,ina219`) drives the
sixteen INA219 rail monitors ([INA219][per-ina219]). **[`adt7462`](https://github.com/torvalds/linux/blob/master/drivers/hwmon/adt7462.c)**
(`adi,adt7462`, matched by the [`adt7462`](https://github.com/torvalds/linux/blob/master/drivers/hwmon/adt7462.c) I2C client name) drives the two ADT7462
fan/temp controllers ([ADT7462][per-adt7462]). **[`lm75`](https://github.com/torvalds/linux/blob/master/drivers/hwmon/lm75.c)** (`ti,tmp75`) drives the
sixteen TMP75 board-temperature sensors ([TMP75 / LM75][per-tmp75]). **[`w83795`](https://github.com/torvalds/linux/blob/master/drivers/hwmon/w83795.c)**
(i2c ids `w83795g` / `w83795adg`) is the KGPE-D16 Super-I/O hardware monitor, but
it hangs off the **host** SP5100 SMBus and is not BMC-managed on that board
([W83795G][per-w83795]).

### Program-repo drivers (AST2050 G3 patch series)

**`irq-aspeed-g3-vic`** is the program's own G3 interrupt-controller driver
(`aspeed,ast2050-vic`). Mainline [`irq-aspeed-vic.c`][vic-mainline] targets the
AST2400+ "new" VIC at `0x1E6C0080`; the AST2050's VIC is the compact block at
`0x1E6C0000`, on which the stock driver enables no interrupts at all (the
timer clockevent never fires and boot hangs in `ftgmac100_open()`). The G3
driver programs sense/event/dual-edge per the datasheet source table and ACKs
edge sources via `VIC38`; it is hardware-verified. See
[Interrupt controller (VIC)][reg-uvt]. The **[`ftgmac100`](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.c) `FAST_MODE` fix** and
the **[`clk-aspeed`](https://github.com/torvalds/linux/blob/master/drivers/clk/aspeed/clk-aspeed.c) AST2050 patch** are patches to the mainline drivers above
rather than new drivers; both are maintained in the program's kernel patch
series and are hardware-verified.

### No mainline driver

The Digi **NS9360** SoC (HPE iPDU) has no current mainline support — the
platform code ([`arch/arm/mach-ns9xxx`][mach-ns9xxx]) was archived and removed
after Linux **v2.6.39**, and it predates device tree. The board's stock firmware
is NET+OS (a ThreadX RTOS), and the open-firmware path chosen for it is a
**U-Boot port** based on the Digi **CC9P9360** vendor U-Boot (no mainline
U-Boot support), not OpenBMC/Linux. Two iPDU sensors likewise have no mainline
driver: the **MAXQ3180** energy-measurement AFE (SPI) and the **TMP89** sub-MCU
(custom serial protocol); both require custom drivers.

## See also

**Related pages**

- {doc}`/drivers/linux` — the G3 patch-series narrative behind these compatibles
- {doc}`/drivers/peripheral-map` — peripheral → driver → daemon map
- {doc}`/hardware/registers/index` — the register pages the "Drives" column links
- {doc}`/hardware/soc-ast2050` — the AST2050 (G3) SoC most rows target
- {doc}`/hardware/peripherals/index` — the off-chip devices in the lower rows

**External references**

- [Linux driver model](https://docs.kernel.org/driver-api/driver-model/index.html) — how these drivers bind to devices
- [Devicetree usage model](https://docs.kernel.org/devicetree/usage-model.html) — how the `compatible` strings match
- [Linux hwmon subsystem](https://docs.kernel.org/hwmon/index.html) — the subsystem for the sensor drivers

## Sources

<!-- Mainline Linux driver sources (verified HTTP 200 against torvalds/linux master) -->
[ftgmac100]: https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.c
[ftgmac100-h]: https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.h
[i2c-aspeed]: https://github.com/torvalds/linux/blob/master/drivers/i2c/busses/i2c-aspeed.c
[spi-aspeed-smc]: https://github.com/torvalds/linux/blob/master/drivers/spi/spi-aspeed-smc.c
[gpio-aspeed]: https://github.com/torvalds/linux/blob/master/drivers/gpio/gpio-aspeed.c
[pinctrl-aspeed]: https://github.com/torvalds/linux/tree/master/drivers/pinctrl/aspeed
[clk-aspeed]: https://github.com/torvalds/linux/blob/master/drivers/clk/aspeed/clk-aspeed.c
[timer-fttmr010]: https://github.com/torvalds/linux/blob/master/drivers/clocksource/timer-fttmr010.c
[uart-8250]: https://github.com/torvalds/linux/tree/master/drivers/tty/serial/8250
[vuart]: https://github.com/torvalds/linux/blob/master/drivers/tty/serial/8250/8250_aspeed_vuart.c
[pwm-tacho]: https://github.com/torvalds/linux/blob/master/drivers/hwmon/aspeed-pwm-tacho.c
[rtc-aspeed]: https://github.com/torvalds/linux/blob/master/drivers/rtc/rtc-aspeed.c
[peci-aspeed]: https://github.com/torvalds/linux/blob/master/drivers/peci/controller/peci-aspeed.c
[aspeed-vhub]: https://github.com/torvalds/linux/tree/master/drivers/usb/gadget/udc/aspeed-vhub
[vhub-h]: https://github.com/torvalds/linux/blob/master/drivers/usb/gadget/udc/aspeed-vhub/vhub.h
[aspeed-video]: https://github.com/torvalds/linux/blob/master/drivers/media/platform/aspeed/aspeed-video.c
[drm-ast]: https://github.com/torvalds/linux/tree/master/drivers/gpu/drm/ast
[drm-aspeed]: https://github.com/torvalds/linux/tree/master/drivers/gpu/drm/aspeed
[pca953x]: https://github.com/torvalds/linux/blob/master/drivers/gpio/gpio-pca953x.c
[pca954x]: https://github.com/torvalds/linux/blob/master/drivers/i2c/muxes/i2c-mux-pca954x.c
[ina2xx]: https://github.com/torvalds/linux/blob/master/drivers/hwmon/ina2xx.c
[adt7462]: https://github.com/torvalds/linux/blob/master/drivers/hwmon/adt7462.c
[lm75]: https://github.com/torvalds/linux/blob/master/drivers/hwmon/lm75.c
[w83795]: https://github.com/torvalds/linux/blob/master/drivers/hwmon/w83795.c
[vic-mainline]: https://github.com/torvalds/linux/blob/master/drivers/irqchip/irq-aspeed-vic.c
[mach-ns9xxx]: https://github.com/torvalds/linux/tree/v2.6.39/arch/arm/mach-ns9xxx

<!-- Register / peripheral reference pages (this docs site) -->
[program-linux]: linux.md
[reg-scu]: ../hardware/registers/scu-clock-reset.md
[reg-mac]: ../hardware/registers/network-mac-phy.md
[reg-buses]: ../hardware/registers/buses-gpio.md
[reg-uvt]: ../hardware/registers/uart-vic-timers.md
[reg-ctrl]: ../hardware/registers/control-blocks.md
[reg-disp]: ../hardware/registers/display-usb.md
[per-ina219]: ../hardware/peripherals/ina219.md
[per-adt7462]: ../hardware/peripherals/adt7462.md
[per-tmp75]: ../hardware/peripherals/tmp75-lm75.md
[per-pca9555]: ../hardware/peripherals/pca9555.md
[per-pca954x]: ../hardware/peripherals/pca954x-mux.md
[per-w83795]: ../hardware/peripherals/w83795g.md
