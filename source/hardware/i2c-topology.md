# Dell C410X I2C topology

The AST2050 BMC manages every board peripheral over **7 I2C buses**. This map is
the reverse-engineered ground truth that the reconstructed device tree, the
`c410x-bmc` QEMU machine, and the OpenBMC entity-manager configuration all mirror.

```text
AST2050 BMC
│
├── Bus 0xF0 ─── 16x INA219 current/power monitors (addr 0x40-0x4F)
│                 └─ One per PCIe slot, measures GPU power draw
│
├── Bus 0xF1 ─┬─ PCA9544A 4-ch mux (addr 0x70)
│             │   ├── Ch 0 → ADT7462 #1 (addr 0x58)  ─ fans 1-4, voltages, temps
│             │   └── Ch 1 → ADT7462 #2 (addr 0x5C)  ─ fans 5-8, voltages, temps
│             │
│             └─ PCA9555 #5 (addr 0x20)  ─ PSU management, fan status LEDs
│
├── Bus 0xF2 ─── AT24C256 EEPROM (addr 0x50)  ─ FRU data (serial, part number)
│
├── Bus 0xF3 ─── PEX8696 + PEX8647 PCIe switches (SMBus management)
│
├── Bus 0xF4 ─┬─ PCA9548 #1 8-ch mux (addr 0x70)
│             │   └── Ch 0-7 → TMP75 slots 1-8 (addr 0x5C each)
│             │
│             └─ PCA9548 #2 8-ch mux (addr 0x71)
│                 └── Ch 0-7 → TMP75 slots 9-16 (addr 0x5C each)
│
├── Bus 0xF5 ─── PMBus to 4x hot-swap PSUs
│
└── Bus 0xF6 ─┬─ PCA9555 #1 (addr 0x20)  ─ Card presence detect (16 slots)
              ├─ PCA9555 #2 (addr 0x21)  ─ Per-slot power-good feedback
              ├─ PCA9555 #3 (addr 0x22)  ─ Attention buttons + slot power control
              ├─ PCA9555 #4 (addr 0x23)  ─ MRL (Manual Retention Latch) sensors
              └─ LM75 (addr 0x4F)        ─ Front board ambient temperature
```

## Device count summary

```{list-table}
:header-rows: 1
:widths: 30 14 56

* - Device
  - Qty
  - Function
* - {doc}`peripherals/ina219`
  - 16
  - per-slot current/power (bus 0xF0)
* - {doc}`peripherals/adt7462`
  - 2
  - temp/voltage monitor + 4-ch PWM fan control (bus 0xF1)
* - {doc}`peripherals/tmp75-lm75`
  - 16 + 1
  - per-slot temps (muxed, 0xF4) + front ambient (0xF6)
* - {doc}`peripherals/pca9555`
  - 5
  - GPIO expanders: presence, power-good, buttons, MRL, PSU/LED
* - {doc}`peripherals/pca954x-mux`
  - 2 + 1
  - PCA9548 8-ch (0xF4) + PCA9544 4-ch (0xF1) muxes
* - {doc}`peripherals/pex8696-8647`
  - 4 + 2
  - PLX PCIe switches (bus 0xF3)
* - AT24C256 EEPROM
  - 1
  - FRU data (bus 0xF2)
```

Verifying that a QEMU boot produces exactly this map (`i2cdetect` on all 7 buses)
is the `c410x-board-bench` acceptance test — see {doc}`../emulation/testbench`.
