# Dell PowerEdge C410X

A 3U, 16-slot **PCIe GPU expansion chassis** — not a server. It has no host CPU;
the entire chassis is managed by its **Aspeed AST2050** BMC, which runs the
proprietary Avocent MergePoint firmware (Linux 2.6.23.1). Because the BMC drives
*everything* (slot power sequencing, hot-plug, PCIe switch routing, thermal), it
is the richest board for peripheral modelling and OpenBMC feature work.

```{list-table}
:header-rows: 0
:widths: 30 70

* - BMC SoC
  - Aspeed AST2050
* - PCIe slots
  - 16× x16 (GPUs/accelerators)
* - PCIe switches
  - 4× PLX PEX8696 (96-lane) + 2× PLX PEX8647 (48-lane)
* - Power
  - 4× hot-swap PSUs
* - Cooling
  - 8 fans, 2× ADT7462 controllers
* - Stock firmware
  - Avocent MergePoint v1.35 (fully reverse-engineered)
```

## Peripheral inventory (fully reverse-engineered)

The stock firmware's five binary config tables were decoded to **192 hardware
devices, 72 IPMI sensors, and 118 GPIO pins**. The result is a complete,
reconstructed Linux device tree and a documented I2C topology:

- {doc}`../hardware/i2c-topology` — the 7-bus map (INA219 ×16, ADT7462 ×2,
  TMP75 ×16 behind muxes, PCA9555 ×5, PCA9548 ×2, PCA9544, EEPROM, LM75).
- {doc}`../hardware/peripherals/pex8696-8647` — the PLX switch I2C management
  protocol (slot power, hot-plug, multi-host routing).
- Power sequencing — a 12-step GPIO/PCA9555 flow (documented in the device
  tree GPIO hogs).

## Emulation & firmware status

- **QEMU** — boots on the shared `kgpe-d16-bmc` AST2050 machine; a dedicated
  `c410x-bmc` machine that wires the full I2C/GPIO topology is planned. The
  proprietary firmware boots to a serving BMC web service in QEMU (C4).
- **Linux** — reconstructed `aspeed-bmc-dell-c410x.dts`, AST2050 clock support,
  and a CI job that cross-compiles kernel + BusyBox initramfs and TFTP-boots it.
- **OpenBMC** — this is the lead board for the OpenBMC feature set (Redfish,
  all sensors/fans, PCIe switch control). See {doc}`../firmware/openbmc`.
