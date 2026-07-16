# Dell PowerEdge C410X

A 16-slot PCIe GPU expansion chassis with **no host CPU** — it is managed entirely by its Aspeed AST2050 BMC. This page covers the board-level integration: the I2C topology, the power-on sequence, and the GPIO map. The SoC itself is {doc}`../hardware/soc-ast2050`; the off-chip devices are in {doc}`../hardware/peripherals/index`.

## Full 7-bus I2C topology

```{figure} /_static/diagrams/c410x-i2c-topology.svg
:alt: The C410X I2C topology — the AST2050 I2C engine fanning out to seven buses (0xF0-0xF6), through PCA9544A/PCA9548A muxes to the INA219, TMP75, ADT7462, PCA9555, PEX8696/8647 and EEPROM/PSU devices, with interrupt routes to BMC GPIO.
:width: 100%

The C410X seven-bus I2C topology: the AST2050 I2C engine → muxes → the sensor,
GPIO-expander and PEX-switch devices, with interrupt lines routed back to BMC
GPIO. Device multiplicities are shown per branch.
```


```{list-table} AST2050 I2C bus map [io-tables](#sources), [gpio-map](#sources), [PEX-I2C](#sources)
:header-rows: 1
:widths: 10 30 60

* - Bus
  - Devices
  - Notes
* - `0xF0`
  - 16× INA219 (`0x40`–`0x4F`)
  - Per-slot 12 V current/power; gated by AST2050 GPIOE3 bus buffer
* - `0xF1`
  - PCA9544A mux (`0x70`) → 2× ADT7462; PCA9555 #5 (`0x20`)
  - Fan/board-temp control + PSU/fan-LED GPIO; mux `INT` AND-gate; PCA9555 `INT` → GPIOA5
* - `0xF2`
  - 24Cxx / AT24C256 EEPROM (`0x50` / `0xA0` 8-bit)
  - FRU data (serial, part number)
* - `0xF3`
  - 4× PEX8696 (`0x18/0x19/0x1A/0x1B`) + 2× PEX8647 (`0x68/0x6A`)
  - PCIe-switch management, **no mux**; 4-byte PLX command protocol
* - `0xF4`
  - PCA9548A #1 (`0x70`) + #2 (`0x71`)
  - Two 8-ch muxes → 16 per-slot temp sensors (shared address)
* - `0xF5`
  - PMBus to 4× hot-swap PSUs
  - PSU power/status; PMBus `ALERT#` → GPIOB2
* - `0xF6`
  - PCA9555 #1–#4 (`0x20`–`0x23`) + front-board temp sensor (`0x4F`/`0x9E`)
  - Slot presence / power-good / attention+power / MRL; front ambient
```

Text tree:


`i2cdetect` across all seven buses reproducing this exact map is the natural
acceptance test for a faithful QEMU model [io-tables](#sources).

---

## Power-on sequence (documented 12 steps)


The reverse-engineered end-to-end power-on flow, from front-panel button to
steady-green, mixing AST2050 on-chip GPIO, PCA9555 #5 outputs, and PEX8696 I2C.

```{list-table} C410X 12-step power-on
:header-rows: 1
:widths: 8 40 52

* - Step
  - Signal / action
  - Effect
* - 1
  - Power button on GPIOE4 (or IPMI Chassis Control)
  - Debounced press starts the sequence
* - 2
  - Assert **GPIOE1**
  - Enable the PS_ON# buffer (hardware interlock)
* - 3
  - Clear **PCA9555 #5 P0.4** (`ps_on_pull_down`)
  - Drive PS_ON# low → all PSUs deliver 12 V
* - 4
  - Wait for **GPIOE2 = high** (PWRGD)
  - System 12 V rail confirmed stable (else "System ON fail")
* - 5
  - Assert **GPIOE3**
  - Enable the I2C `0xF0` buffer to the 16 INA219 sensors
* - 6
  - Assert **GPION5**
  - Enable the PEX8696 hot-plug power controller
* - 7
  - Phase 1 — power on slots **1, 5, 9, 13** (`gpu_un_protect 0x11`)
  - One slot per switch, via PEX8696 I2C (bus `0xF3`)
* - 8
  - Phase 2 — power on slots **2, 6, 10, 14** (`0x33`)
  - One slot per switch
* - 9
  - Phase 3 — power on slots **3, 7, 11, 15** (`0x77`)
  - One slot per switch
* - 10
  - Phase 4 — power on slots **4, 8, 12, 16** (`0xFF`)
  - One slot per switch
* - 11
  - Verify per-slot PWRGD (PCA9555 #2), start INA219 monitoring
  - Confirm each slot's rail; begin power telemetry
* - 12
  - System Power LED → steady green; per-slot GPU LEDs → green
  - Boot complete, no faults
```

The staggered every-4th-slot phasing (§3.8) is what keeps the 4-phase order from
spiking inrush current across the power-distribution bus [gpio-map](#sources), [PEX-I2C](#sources).
Note the firmware's internal phase order (§3.8) begins with slots 4/8/12/16; the
gpio-pin-mapping flow lists 1/5/9/13 first — both describe the same
one-slot-per-switch-per-phase scheme; the `gpu_un_protect` masks disambiguate the
actual order (`0x11 → 0x33 → 0x77 → 0xFF`) [gpio-map](#sources), [PEX-I2C](#sources).

---

## GPIO pin map (control-relevant subset)


The AST2050 uses 38 on-chip GPIO lines; the ones that drive this control fabric
are:

```{list-table} Control-fabric AST2050 GPIO pins
:header-rows: 1
:widths: 14 12 48 26

* - Pin
  - Dir
  - Function
  - Connected to
* - GPIOA4
  - in (IRQ)
  - GPU card presence-change interrupt
  - PCA9555 #1 `INT` (`0xF6:0x20`)
* - GPIOA5
  - in (IRQ)
  - PSU present/fail interrupt
  - PCA9555 #5 `INT` (`0xF1:0x20`)
* - GPIOB0 / GPIOB1
  - in (IRQ)
  - ADT7462 #1 / #2 thermal alert
  - via PCA9544A (`0xF1:0x70`)
* - GPIOB4
  - in (IRQ)
  - Slot attention-button interrupt
  - PCA9555 #3 `INT` (`0xF6:0x22`)
* - GPIOB5
  - in (IRQ)
  - Slot power-good / MRL change
  - PCA9555 #2 & #4 `INT` (shared)
* - GPIOB6 / GPIOB7
  - in (IRQ)
  - PEX8696 / PEX8647 switch event
  - PEX `INT` outputs (bus `0xF3`)
* - GPIOE1
  - out
  - PS_ON# buffer enable (interlock)
  - PS_ON# path gate
* - GPIOE2
  - in
  - System 12 V power-good (PWRGD)
  - power-distribution feedback
* - GPIOE3
  - out
  - INA219 (`0xF0`) bus-buffer enable
  - isolates unpowered sensors
* - GPIOF6
  - out
  - PEX8696 hardware reset (#RESET)
  - primary PCIe switch
* - GPIOM0
  - out
  - PS_ON# gate (`ps_on_pull_down/up`)
  - master PSU turn-on
* - GPIOM1
  - out
  - Board-level reset (PEX switches, muxes)
  - resets non-BMC logic
* - GPION4
  - out
  - PEX8647 hardware reset (#RESET)
  - secondary PCIe switch
* - GPION5
  - out
  - GPU slot-power master enable
  - gates PEX8696 hot-plug controller
```

Interrupt routing summary (6 IRQ sources): GPIOA4 = card presence, GPIOA5 = PSU,
GPIOB7 = PEX8647 upstream, GPIOE2 = PWRGD, GPIOF6 = PEX8696 downstream, GPIOB4 =
attention button [gpio-map](#sources).

---

## Debug & console access

The C410X BMC is an AST2050, so it shares the SoC-level debug and out-of-band
access paths documented for the shared SoC — see {doc}`/debug/bring-up`
(cold-boot over the **P2A** PCIe-to-AHB bridge) and {doc}`/debug/jtag-uart`
(JTAG run-control). The board-specific access points that the stock firmware
uses are:

```{list-table}
:header-rows: 1
:widths: 26 22 52

* - Path
  - Location
  - Notes
* - Serial console
  - **UART0** `0x1E783000` (`ttyS0`)
  - 115200 8N1, vt100; the stock `bootargs` are `console=ttyS0,115200n8`
* - Serial-over-LAN (SOL)
  - **UART1** `0x1E784000`
  - remote serial console over IPMI (the second SoC UART)
* - vKVM
  - Video Engine + `avct_server`
  - Avocent virtual-KVM console server (`vkcs.ko`) — video capture + USB HID
* - Out-of-band AHB
  - P2A / iLPC bridges
  - the shared AST2050 backdoors ({doc}`/hardware/registers/pcie-vga-usb-bridges`);
    P2A is usable, iLPC is disabled on the boards examined
```

Unlike the KGPE-D16 (whose physical JTAG/UART header pinouts are reverse-engineered
in {doc}`/systems/kgpe-d16`), the C410X's on-board debug-header *locations* have
not been separately mapped here; the register-level access paths above are the
shared-SoC ones and apply unchanged. [ANALYSIS.md:322](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/ANALYSIS.md#L322)

---

## Coverage notes and gaps


- **PEX "product briefs" are family stand-ins.** The in-repo `PEX8696_ProductBrief.pdf`
  and `PEX8647_ProductBrief.pdf` actually contain the **PEX8619** and **PEX8648**
  briefs. They are same-generation ExpressLane 86xx Gen2 parts and are cited only
  for architecture common to the family; the exact PEX8696 (96-lane/24-port) and
  PEX8647 (48-lane/3-port) parameters are from Broadcom + the RE notes. A true
  PEX8696/PEX8647 datasheet (register-level) is **not** in the repo — the PLX
  register semantics here rest on the reverse-engineered firmware + `plxtools`.
- **PCA9544A channel numbers for the two ADT7462s** are not pinned to raw
  control-register values in the RE notes (firmware shows selector bytes `0xB0`/`0xB8`);
  the datasheet channel-select encoding is `0x04`–`0x07`.
- **PCA9555 #1/#3 8-bit address `0x44`** appears for two different devices on bus
  `0xF6`; the decompiled accessors are the authority. The 7-bit strap addresses
  (`0x20`, `0x22`) are datasheet-consistent and non-conflicting.
- **Phase ordering** differs cosmetically between the firmware trace (4/8/12/16
  first) and the gpio-pin-mapping flow (1/5/9/13 first); the `gpu_un_protect` masks
  resolve the real order.

---

## C410X sensor inventory at a glance


```{list-table} Sensor devices on the C410X BMC I2C buses
:header-rows: 1
:widths: 18 8 18 16 40

* - Device
  - Count
  - I2C bus (firmware / DT)
  - Address(es)
  - Role
* - INA219
  - 16
  - `0xF0` / `&i2c0` (base `0x1E78A040`)
  - `0x40`–`0x4F` (A1/A0 straps)
  - Per-PCIe-slot 12 V current/power monitor. [IS_fl.bin.md:165-195](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/io-tables/IS_fl.bin.md#L165-L195) [dts:402-411]
* - ADT7462
  - 2
  - `0xF1` / `&i2c1` (base `0x1E78A080`)
  - `0x58`, `0x5C` behind PCA9544A mux `0x70`
  - Board temperature zones + 8-fan tach/PWM control. [IS_fl.bin.md:81-95,141-163](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/io-tables/IS_fl.bin.md#L81-L95) [dts:596-663]
* - TMP75 (per-slot)
  - 16
  - `0xF4` / `&i2c4` (base `0x1E78A140`)
  - `0x5C`, behind 2× PCA9548 mux (`0x70`, `0x71`)
  - Per-PCIe-slot temperature. Firmware tables call these "TMP100"; DT uses `ti,tmp75`. [IS_fl.bin.md:102-129](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/io-tables/IS_fl.bin.md#L102-L129) [dts:733-851]
* - LM75 (front board)
  - 1
  - `0xF6` / `&i2c6`
  - `0x4F` (8-bit `0x9E`)
  - Front-board ambient temperature. [IS_fl.bin.md:131-139](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/io-tables/IS_fl.bin.md#L131-L139) [dts:1104-1119]
```

```{admonition} TMP100 vs TMP75 vs LM75 — chip-identity caveat
:class: warning

The C410X firmware IO tables and symbol table name the per-slot sensor driver
`G_sOEMTMP100_I2CTEMP_IOSAPI` and read them at **7-bit `0x5C`**.
[ANALYSIS.md:499](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/ANALYSIS.md#L499) [IS_fl.bin.md:106-107](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/io-tables/IS_fl.bin.md#L106-L107) The standard LM75/TMP75 address range is
`0x48`–`0x4F`; `0x5C` is outside it, so the physical part is a TMP75/LM75-*class*
device with non-standard strapping (or a TMP100/TMP1075 variant). The
reconstructed device tree models them with the register-compatible `ti,tmp75`
binding because all these chips share the same LM75 register layout (pointer +
temperature/config/T_LOW/T_HIGH). [dts:739-743,769] The front-board sensor at
`0x4F` is bound `national,lm75`. [dts:1115-1116] This document covers the TMP75
and LM75 register sets; the per-slot part is functionally one of them.
```

## See also

**Related pages**

- {doc}`/hardware/soc-ast2050` — the AST2050 BMC SoC that manages this chassis
- {doc}`/hardware/i2c-topology` — the full seven-bus I2C topology
- {doc}`/hardware/peripherals/index` — the off-chip sensor / GPIO / PEX devices
- {doc}`/firmware/openbmc` — the OpenBMC stack that consumes this sensor/power model
- {doc}`/emulation/qemu` — the planned board-complete `c410x-bmc` QEMU machine

**External references**

- [OpenBMC documentation](https://github.com/openbmc/docs) — the firmware target for this board
- [Linux hwmon subsystem](https://docs.kernel.org/hwmon/index.html) — the subsystem behind the INA219/ADT7462/TMP75/LM75 sensors
- [QEMU Aspeed machines](https://www.qemu.org/docs/master/system/arm/aspeed.html) — the Aspeed BMC family this board's SoC is emulated within

## Sources

- **[`dell-c410x-firmware/ANALYSIS.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/ANALYSIS.md)**, the decoded **[`io-tables/`](https://github.com/mithro/ai-shenanigans-for-bmcs/tree/main/dell-c410x-firmware/io-tables)**,
  **[`io-tables/gpio-pin-mapping.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/io-tables/gpio-pin-mapping.md)**, and **[`pex-i2c-analysis/`](https://github.com/mithro/ai-shenanigans-for-bmcs/tree/main/dell-c410x-firmware/pex-i2c-analysis)** — the
  reverse-engineered C410X I2C topology, power sequence, and GPIO map.
- Per-device references: {doc}`../hardware/peripherals/pca9555`,
  {doc}`../hardware/peripherals/pca954x-mux`,
  {doc}`../hardware/peripherals/pex8696-8647`,
  {doc}`../hardware/peripherals/ina219`, {doc}`../hardware/peripherals/adt7462`,
  {doc}`../hardware/peripherals/tmp75-lm75`.
