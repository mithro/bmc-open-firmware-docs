# HPE Intelligent Modular PDU (AF531A)

An intelligent **Power Distribution Unit**. Unlike the other two boards it uses a
**Digi NS9360** SoC (not Aspeed), and its stock firmware is **NET+OS** (a
ThreadX-based RTOS), not Linux. The same ARM926EJ-S core keeps it in-family for
toolchains and the Zephyr ARMv5 port.

```{list-table}
:header-rows: 0
:widths: 30 70

* - SoC
  - Digi NS9360
* - CPU core
  - ARM926EJ-S (ARMv5TE)
* - Power metering
  - MAXQ3180 metering AFE
* - Display
  - dedicated MCU over an "extension-bar" protocol
* - Boot flash
  - dual CFI NOR (8 MiB total)
* - Stock firmware
  - NET+OS / ThreadX (RomPager web server); reverse-engineered
```

## Open-firmware path

There is **no mainline Linux** for the NS9360, so this board's open-firmware
stack is built up in stages (all five layers are in scope):

1. **U-Boot** — an open NS9360 port (serial, GPIO, clock, I2C, Ethernet, CFI
   flash) that already boots in QEMU. See {doc}`../drivers/uboot`.
2. **Linux** — forward-port the archived `mach-ns9xxx` support toward a modern
   kernel. See {doc}`../drivers/linux`.
3. **Zephyr** — via the shared ARMv5 architecture port. See
   {doc}`../drivers/zephyr`.
4. **OpenBMC** on the Linux stack, and **WallaBMC** on the Zephyr stack.

## Emulation status

A QEMU `ns9360` machine (ARM926EJ-S, SDRAM, dual CFI flash) boots the U-Boot
port under a serial-socket smoke test. Board-complete modelling (MAXQ3180,
display MCU, Ethernet PHY) is planned — see {doc}`../emulation/qemu`.
