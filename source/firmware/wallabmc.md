# WallaBMC (Zephyr)

[WallaBMC](https://github.com/tenstorrent-riscv-software/wallabmc) is a
lightweight, Zephyr-based BMC firmware (Redfish API, web UI over http/https, host
power control, serial console, persistent config). It is the program's
**second, lighter BMC stack**, complementary to OpenBMC, targeting the most
constrained parts where the full OpenBMC image is impractical.

## What it takes to run here

Upstream WallaBMC targets Cortex-M / RISC-V microcontrollers — not the ARM926EJ-S
(ARMv5TE) in these boards. So the WallaBMC track depends on the Zephyr **ARMv5
architecture port** ({doc}`../drivers/zephyr`). Bring-up order:

1. Validate WallaBMC on an existing Zephyr-supported QEMU target (reference).
2. Stand up the ARM926 arch + `soc-ast2050` / `soc-ns9360` in
   [`mithro/zephyr`](https://github.com/mithro/zephyr).
3. Port WallaBMC's board layer (in a [`mithro/wallabmc`](https://github.com/mithro/wallabmc) fork) to each board.

## Functionality gap to close

Upstream WallaBMC provides Redfish, power, and console, but **not** sensor
monitoring, fan control, or PCIe management. For these boards those are required,
so the track either extends WallaBMC with the needed sensor/fan/PCIe support
(reusing the same device knowledge as the OpenBMC daemons) or documents the
deliberate scope limit per board.

**Acceptance:** the same `firmware-testbench` Redfish/power/console benches pass
on the WallaBMC image in QEMU, at a **smaller flash/RAM footprint** than the
OpenBMC image — the footprint delta is the track's reason to exist.

## License

WallaBMC is Apache-2.0 (code) / CC (docs), matching this program's licensing.

## See also

**Related pages**

- {doc}`/drivers/zephyr` — the ARMv5 architecture port this track depends on
- {doc}`/firmware/openbmc` — the heavier, complementary Linux BMC stack
- {doc}`/emulation/qemu` — the QEMU `ast2050` / `ns9360` targets used to validate it
- {doc}`/emulation/testbench` — the shared Redfish/power/console benches it must pass
- {doc}`/drivers/peripheral-map` — the sensor/fan/PCIe gaps it must close

**External references**

- [Zephyr documentation](https://docs.zephyrproject.org/latest/) — the RTOS WallaBMC is built on
- [Zephyr architecture-porting guide](https://docs.zephyrproject.org/latest/hardware/porting/arch.html) — the ARMv5 port prerequisite
- [DMTF Redfish standard](https://www.dmtf.org/standards/redfish) — the API WallaBMC exposes
