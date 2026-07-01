# TMP75 / LM75 — temperature sensors

LM75-class I2C digital temperature sensors. The C410X uses **16× TMP75** (one per
slot, on bus `0xF4` behind two PCA9548 muxes, all at address `0x5C`) plus **1×
LM75** for front-board ambient (bus `0xF6`, address `0x4F`).

```{list-table}
:header-rows: 0
:widths: 30 70

* - Interface
  - I2C, 8-bit pointer, 16-bit temperature register
* - Registers
  - `0x00` temperature (R), `0x01` config (R/W), `0x02` T_HYST, `0x03` T_OS
* - TMP75 resolution
  - up to 0.0625 °C (12-bit)
```

## Model / driver notes

- Temperature register returns a signed value, MSB first, left-justified.
- Config register is R/W; T_HYST/T_OS are R/W limit registers.
- Mainline Linux binds `hwmon`/`lm75` (with the `ti,tmp75` compatible). The 16
  muxed sensors appear as 16 hwmon devices once the PCA9548 channels are
  enabled — see {doc}`pca954x-mux`.
- A model seeds the temperature register per test; the bench reads it back
  through the correct mux channel.
