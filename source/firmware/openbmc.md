# OpenBMC (Linux)

The full-featured firmware track, built in the `mithro/openbmc` fork with a
`meta-<board>` layer per board on top of `meta-aspeed`. Images are verified in
QEMU (and later on HIL) via the {doc}`../emulation/testbench`.

## Feature build-out (C410X leads)

```{list-table}
:header-rows: 1
:widths: 30 44 26

* - Feature
  - Implementation
  - Verified by
* - Redfish API
  - `bmcweb`
  - `GET /redfish/v1` in CI
* - Sensors
  - `dbus-sensors` (hwmon) + entity-manager for the 72 C410X sensors
  - Redfish sensor enumeration
* - Fans
  - `phosphor-pid-control` (ADT7462 curves)
  - PWM/tach response
* - Power
  - `phosphor-state-manager` driving the 12-step GPIO/PCA9555 sequence
  - ordered GPIO transitions on the model
* - PCIe switches
  - a phosphor-style PEX8696/8647 I2C daemon
  - qtest of the switch model
* - Serial-over-LAN
  - `obmc-console` over the modelled UART
  - console attach
* - Networking
  - ssh + https reachable via slirp hostfwd
  - CI reachability
```

## Footprint work (XIP + stripping)

The AST2050 is RAM/flash constrained, so after a functional (non-XIP) image
boots, the OpenBMC image is size-optimised:

- **XIP** the read-only rootfs directly from the modelled SPI NOR to cut RAM use;
- **strip** authentication and unneeded features to fit the flash-partition and
  RAM budgets defined by the board device tree.

**Acceptance:** `openbmc-c410x-xip` builds an image that fits the flash budget and
boots to Redfish in QEMU with `-m` set to the board's real RAM size. This is the
hardest OpenBMC item; WallaBMC is the lighter fallback where OpenBMC cannot fit.
