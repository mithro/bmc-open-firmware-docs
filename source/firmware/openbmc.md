# OpenBMC (Linux)

The full-featured firmware track, built in the `mithro/openbmc` fork with a
`meta-<board>` layer per board on top of `meta-aspeed`. Images are verified in
QEMU (and on real hardware) via the {doc}`../emulation/testbench`.

## Running on the real AST2050

Modern OpenBMC has been brought up on a **real ASUS KGPE-D16 AST2050** BMC:
booted over the P2A path ({doc}`../debug/bring-up`) with an NFS-root userspace,
its `bmcweb` answers **Redfish v1.17.0** over HTTPS on the board's own network
interface. This required the two hardware-verified kernel fixes — the G3 VIC
irqchip driver and the ftgmac100 `FAST_MODE` RX fix ({doc}`../drivers/linux`) —
before the network stack would carry Redfish traffic on silicon.

```{admonition} The 64 MiB constraint
:class: important

The AST2050 on this board has **64 MiB of DRAM** (hardware-verified). A modern,
full OpenBMC image does not fit in 64 MiB. The target is therefore a **stripped,
Redfish-only (`bmcweb`) image** served over NFS on the bench, with the QEMU model
and board DTS both pinned to 64 MiB so the size budget is enforced the same way
in emulation and on hardware. This — not XIP polish — is the real footprint gate.
```

## BMC feature build-out

Nine BMC feature areas were built out on the OpenBMC/AST2050 stack, each with a
CI job. All are demonstrated in QEMU; several are additionally proven on real
silicon. The table records that distinction honestly.

```{list-table}
:header-rows: 1
:widths: 22 48 30

* - Feature
  - Implementation
  - Status
* - Redfish API
  - `bmcweb`
  - **silicon** — Redfish v1.17.0 answers on the real BMC
* - System identity
  - populated FRU / `MachineName`
  - **silicon**
* - Sensors
  - `dbus-sensors` (hwmon) → Redfish/IPMI SDR
  - **silicon** — populated SDR from the D-Bus sensor values
* - Power control
  - `phosphor-state-manager` → GPIO
  - QEMU (Redfish `Reset` drives the modelled power-state GPIO)
* - Serial-over-LAN
  - `obmc-console`
  - **silicon** — SOL session operational
* - IPMI
  - IPMI-over-LAN and host-local IPMI via **KCS**
  - **silicon** — `ipmitool` returns ASUSTek / KGPE-D16
* - USB, NC-SI, KVM, firmware update
  - obmc-ikvm / phosphor-ipmi / update flows
  - QEMU-demonstrated; see faithfulness notes below
```

```{admonition} Faithfulness findings
:class: note

Building against the real board corrected several assumptions, in keeping with
the program's "model the real hardware" rule:

- host↔BMC IPMI on this board is **KCS**, not NC-SI;
- there is **no USB host** exposed to the BMC on this board;
- the BIOS is not directly BMC-reachable.

These are recorded as hardware facts, not worked around — the emulation and
firmware are shaped to match them.
```

## Sensor-rich board: Dell C410X

The Dell C410X is the sensor-dense target (16× INA219, 2× ADT7462, 16× TMP75,
5× PCA9555, the PEX8696/8647 PCIe switches) — its 72-sensor topology
({doc}`../hardware/i2c-topology`) drives the `dbus-sensors` / `entity-manager`
and PCIe-switch-daemon work. The hardware demonstration to date is on the
KGPE-D16 (the board on the bench); the C410X contributes the rich I2C/sensor
model that the same daemons consume.

## Footprint work

The AST2050's 64 MiB budget is met by stripping the image to the Redfish-only
feature set above rather than shipping full OpenBMC. Execute-in-place (XIP) of the
read-only rootfs from SPI NOR remains a further RAM-saving option once a serving
boot flash is in place. WallaBMC ({doc}`wallabmc`) is the lighter Zephyr fallback
where even a stripped OpenBMC cannot fit.

## See also

**Related pages**

- {doc}`/firmware/wallabmc` — the lighter Zephyr BMC alternative
- {doc}`/drivers/linux` — the G3 VIC and ftgmac100 fixes that let Redfish run on silicon
- {doc}`/drivers/peripheral-map` — the feature → daemon → hardware-path map
- {doc}`/debug/bring-up` — the P2A path used to boot OpenBMC on the real AST2050
- {doc}`/emulation/qemu` — the QEMU vehicle for the modern-OpenBMC/Redfish work

**External references**

- [OpenBMC documentation](https://github.com/openbmc/docs) — the upstream project docs
- [OpenBMC project site](https://www.openbmc.org/) — project overview and governance
- [`bmcweb`](https://github.com/openbmc/bmcweb) — the Redfish/web daemon used here
- [DMTF Redfish standard](https://www.dmtf.org/standards/redfish) — the Redfish API specification `bmcweb` implements
- [`phosphor-state-manager`](https://github.com/openbmc/phosphor-state-manager) — the power/host-state daemon
- [`dbus-sensors`](https://github.com/openbmc/dbus-sensors) — the sensor daemon behind the SDR
