# Peripherals

Every board peripheral, with a register-level page sufficient to build a QEMU
model and a driver. The catalog below is the shared device library: the same
model code and driver bindings are reused across boards.

```{list-table}
:header-rows: 1
:widths: 24 14 12 50

* - Device
  - Type
  - Boards
  - Summary
* - {doc}`ina219`
  - power monitor
  - C410X
  - I2C current/voltage/power sense, 16× per-slot
* - {doc}`adt7462`
  - thermal/fan
  - C410X
  - temp+voltage monitor, 4-ch PWM fan control
* - {doc}`tmp75-lm75`
  - temp sensor
  - C410X
  - LM75-class I2C temperature sensors
* - {doc}`pca9555`
  - GPIO expander
  - C410X
  - 16-bit I2C GPIO (presence, power, buttons, LEDs)
* - {doc}`pca954x-mux`
  - I2C mux
  - C410X
  - PCA9548 (8-ch) / PCA9544 (4-ch) bus multiplexers
* - {doc}`pex8696-8647`
  - PCIe switch
  - C410X
  - PLX PEX switches; I2C management protocol
* - {doc}`maxq3180`
  - metering AFE
  - iPDU
  - polyphase energy-metering front-end
* - {doc}`w83795g`
  - hwmon
  - KGPE-D16
  - Nuvoton voltage/temp/fan monitor + Smart-Fan control
```

```{toctree}
:hidden:

ina219
adt7462
tmp75-lm75
pca9555
pca954x-mux
pex8696-8647
maxq3180
w83795g
```

## Modelling order

Models are built highest-multiplicity-first, because that maximises reuse and
unblocks the most downstream work: **INA219** (×16) and a **PCA954x mux** first,
then ADT7462, TMP75/LM75, PCA9555, and finally the PEX switch (the hardest).
Each lands as a documentation → model → qtest *triplet*
(see {doc}`../../emulation/testbench`).
