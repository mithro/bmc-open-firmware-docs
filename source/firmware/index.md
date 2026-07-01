# Firmware

Two open BMC firmware tracks, both targeting all three boards:

- **{doc}`openbmc`** — the full-featured, Linux-based stack (OpenBMC): Redfish,
  all sensors and fans, PCIe switch control, power control, SoL, ssh/https.
- **{doc}`wallabmc`** — the lightweight, Zephyr-based stack (WallaBMC): a smaller
  Redfish/power/console footprint for the most constrained parts.

```{toctree}
:maxdepth: 1

openbmc
wallabmc
```

## Feature matrix (target)

```{list-table}
:header-rows: 1
:widths: 40 30 30

* - Capability
  - OpenBMC (Linux)
  - WallaBMC (Zephyr)
* - Redfish API
  - ✅ full
  - ✅ core
* - Power control
  - ✅
  - ✅
* - Sensor reading
  - ✅ all (72 on C410X)
  - ➕ to be extended
* - Fan control
  - ✅
  - ➕ to be extended
* - PCIe switch control
  - ✅ (PEX daemon)
  - ➕ to be extended
* - Serial-over-LAN
  - ✅
  - ✅ (console)
* - ssh / https
  - ✅
  - ✅ (https/web)
* - XIP from SPI flash
  - ✅ (footprint work)
  - n/a (small by design)
```

Upstream WallaBMC lacks sensor/fan/PCIe support; extending it (or documenting the
deliberate gap) is part of the WallaBMC track.
