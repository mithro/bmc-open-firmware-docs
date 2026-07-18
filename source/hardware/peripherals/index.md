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
* - {doc}`rtl8201n`
  - Ethernet PHY
  - KGPE-D16
  - Realtek 10/100 RMII PHY — the BMC's dedicated management LAN
* - {doc}`intel-82574l`
  - NIC (NC-SI)
  - KGPE-D16
  - Intel host GbE ×2; NC-SI sideband shared with the BMC
* - {doc}`w83601g`
  - GPIO expander
  - KGPE-D16
  - Winbond 2-wire GPIO ×2 — the 16 DIMM error LEDs
* - {doc}`ht24lc08`
  - EEPROM
  - KGPE-D16
  - Holtek 24Cxx-class board FRU (+ FireWire config) EEPROMs
* - {doc}`dimm-spd-tsod`
  - DIMM devices
  - KGPE-D16
  - JEDEC SPD EEPROMs + TSOD temp sensors, 16 slots via mux
* - {doc}`w83667hg`
  - Super-I/O
  - KGPE-D16
  - Nuvoton LPC Super-I/O — the BMC's LPC peer and SOL partner
* - {doc}`ics1893`
  - Ethernet PHY
  - iPDU
  - IDT 10/100 clause-22 MII PHY for the NS9360 MAC
* - {doc}`tmp89`
  - sub-MCU
  - iPDU
  - Toshiba TLCS-870/C1 display/bezel controller
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
rtl8201n
intel-82574l
w83601g
ht24lc08
dimm-spd-tsod
w83667hg
ics1893
tmp89
```

## Modelling order

Models are built highest-multiplicity-first, because that maximises reuse and
unblocks the most downstream work: **INA219** (×16) and a **PCA954x mux** first,
then ADT7462, TMP75/LM75, PCA9555, and finally the PEX switch (the hardest).
Each lands as a documentation → model → qtest *triplet*
(see {doc}`../../emulation/testbench`).

## See also

**Related pages**

- {doc}`/hardware/i2c-topology` — how these I2C devices connect on each board
- {doc}`/hardware/registers/buses-gpio` — the AST2050 I2C controller most of them sit on
- {doc}`/drivers/peripheral-map` — which mainline driver covers each peripheral
- {doc}`/hardware/index` — the hardware overview
- {doc}`/emulation/index` — the QEMU / testbench modelling programme

**External references**

- [Linux hwmon subsystem](https://docs.kernel.org/hwmon/index.html) — the sysfs interface for the sensor/monitor devices catalogued here
- [Linux I2C subsystem](https://docs.kernel.org/i2c/index.html) — the bus most of these devices share
- [Zephyr sensor API](https://docs.zephyrproject.org/latest/hardware/peripherals/sensor/index.html) — the WallaBMC/Zephyr sensor driver model
