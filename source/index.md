# Open BMC & Firmware

Open-source firmware, emulation, and driver documentation for three pieces of
legacy management hardware, replacing their proprietary firmware with open
alternatives (OpenBMC on Linux, WallaBMC on Zephyr) and providing full QEMU
emulation, upstream Linux/U-Boot support, and a hardware-in-the-loop test bench.

```{list-table}
:header-rows: 1
:widths: 22 18 14 46

* - System
  - SoC
  - CPU core
  - Role
* - {doc}`systems/kgpe-d16`
  - Aspeed AST2050
  - ARM926EJ-S (ARMv5TE)
  - ASUS server-motherboard BMC
* - {doc}`systems/dell-c410x`
  - Aspeed AST2050
  - ARM926EJ-S
  - Dell 16-slot PCIe GPU expansion chassis BMC
* - {doc}`systems/hpe-ipdu`
  - Digi NS9360
  - ARM926EJ-S
  - HPE intelligent PDU (AF531A)
```

Two of the three boards share the **Aspeed AST2050** SoC, so the SoC-level work
(kernel drivers, U-Boot, QEMU model) is shared and each board contributes only
its own device tree / board description. The third board (Digi NS9360) is a
separate but same-core (ARM926EJ-S) track.

## What this documentation covers

This site is written to be **enough to build both QEMU models and drivers** for
every component, and to bring up every layer of the software stack:

- {doc}`hardware/index` — SoC and peripheral register/interface reference
  (I2C topology, sensors, fan controllers, PCIe switches, power, SPI flash).
- {doc}`emulation/index` — the QEMU machine models and the per-component test
  benches that verify them.
- {doc}`drivers/index` — Linux, U-Boot, and Zephyr driver notes and the
  upstream patch-series/rebase workflow.
- {doc}`firmware/index` — the OpenBMC (Linux) and WallaBMC (Zephyr) firmware
  tracks: Redfish, power, sensors, fans, PCIe control, SoL, and footprint work.
- {doc}`debug/index` — JTAG/UART/SPI bring-up and the hardware-in-the-loop rig.

## Start here

```{list-table}
:header-rows: 1
:widths: 34 66

* - If you are…
  - Start with
* - Writing a **QEMU device model**
  - {doc}`hardware/registers/index` (the AST2050 register maps) → {doc}`emulation/qemu` → {doc}`emulation/testbench`
* - Writing a **Linux / Zephyr driver**
  - {doc}`drivers/peripheral-map` (block → driver → daemon) → the relevant {doc}`hardware/registers/index` page → {doc}`drivers/linux`
* - Building **OpenBMC / WallaBMC firmware**
  - {doc}`firmware/openbmc` / {doc}`firmware/wallabmc` → {doc}`drivers/peripheral-map`
* - Doing **bench bring-up** on real silicon
  - {doc}`debug/bring-up` (P2A + JTAG) → {doc}`debug/jtag-uart` → the board page under {doc}`systems/index`
```

```{admonition} Status — much of this is now hardware-verified
:class: important

Key milestones are proven on a real ASUS KGPE-D16 AST2050, not just in emulation:
JTAG run-control and a P2A cold-boot path onto a firmware-less BMC
({doc}`debug/bring-up`), a modern Linux kernel booting with the G3 interrupt
controller and MAC fixes ({doc}`drivers/linux`), and **OpenBMC answering Redfish
v1.17.0 on the board itself** ({doc}`firmware/openbmc`). The `kgpe-d16-bmc` QEMU
machine meets all four of its boot criteria ({doc}`emulation/qemu`).

This is still an actively developed program. Pages (or rows) marked *(planned)*
describe work that is scaffolded but not yet complete; each carries an acceptance
criterion so progress is unambiguous. The authoritative implementation history
lives in the (private) program repository — see {doc}`about`.
```

```{toctree}
:hidden:
:caption: Systems

systems/index
```

```{toctree}
:hidden:
:caption: Hardware reference

hardware/index
```

```{toctree}
:hidden:
:caption: Emulation & test

emulation/index
```

```{toctree}
:hidden:
:caption: Drivers

drivers/index
```

```{toctree}
:hidden:
:caption: Firmware

firmware/index
```

```{toctree}
:hidden:
:caption: Bring-up & debug

debug/index
```

```{toctree}
:hidden:
:caption: Project

references
contributing
about
```
