# KGPE-D16 I2C / SMBus / PMBus topology

The complete management-bus map of the ASUS KGPE-D16 — every I2C, SMBus and
PMBus connection, every master, every mux, and the exact steps the AST2050 BMC
must take to reach each device. Extracted from the board's schematic netlist
(see the provenance note on {doc}`kgpe-d16-wiring`); the source documents are
[`I2C-SMBUS-TOPOLOGY.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/I2C-SMBUS-TOPOLOGY.md)
and [`AST2050-BMC-WIRING.md` §10](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md#10-i²c--smbus-topology-traced-through-every-mux--expander).

```{admonition} Address confidence
:class: note

The schematic fixes the *wiring* and the address-strap pins. The 7-bit
addresses quoted below are the standard values from each part's datasheet (or
JEDEC, for DIMM SPD/TSOD) — treat them as datasheet-derived, not read from
silicon, except where a page linked below records a live-board observation
(e.g. the W83795G at `0x2F` seen by lm-sensors).
[I2C-TOPOLOGY](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/I2C-SMBUS-TOPOLOGY.md)
```

```{figure} /_static/diagrams/kgpe-d16-bmc-i2c-topology.svg
:alt: The KGPE-D16 BMC I2C fabric — the AST2050's eight I2C controllers fanning through the QU9 FET switch, the QU5 dual 4-channel analog mux and the U23 source-select buffer to the W83795G hardware monitor, the two W83601G DIMM-LED expanders, the HT24LC08 FRU EEPROM, the PSU header and the 16 DIMM SPD/TSOD banks.
:width: 95%

The BMC-centric view of the switching fabric — the {ref}`per-bus diagrams below
<kgpe-i2c-per-bus>` expand each segment.
```

## 1. Masters

Seven controllers can drive management buses on this board
[I2C-TOPOLOGY §1](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/I2C-SMBUS-TOPOLOGY.md#1-masters):

```{list-table}
:header-rows: 1
:widths: 26 10 30 34

* - Master
  - Ref
  - Buses it drives
  - Role
* - Aspeed AST2050 BMC
  - `QU1`
  - `I2C1`–`I2C8` (§3)
  - out-of-band management: sensors, SPD, FRU, PSU
* - AMD SP5100 southbridge
  - `SU1`
  - `SMBus0`–`SMBus3`
  - host SMBus: VR control, in-band sensors
* - AMD SR5690 northbridge
  - `NU1`
  - PCIe hot-plug SMBus
  - PCIe slot hot-plug / debug header
* - Winbond W83795G
  - `QU4`
  - SB-TSI (master to the CPUs)
  - reads CPU die temperature — {doc}`/hardware/peripherals/w83795g` §1.11
* - LSI FW322 1394a
  - `ZU1`
  - private serial-EEPROM bus
  - loads its own FireWire GUID/config at power-up
* - W83667HG-A Super-I/O
  - `OU1`
  - `GP37`/`GP50` straps only
  - LAN-disable straps (GPIO, not a live bus)
* - SP5100 `DDC1` pair
  - `SU1`
  - `FANCURVE0/1` straps only
  - fan-curve select straps (GPIO, not a live bus)
```

The AST2050 side is eight hardware I2C controllers (`SDA1/SCL1` …
`SDA7/SCL7` on dedicated balls, plus a muxed eighth segment); their register
interface is documented in {doc}`/hardware/registers/buses-gpio`, and the AC
timing they need on real G3 silicon is the vendor `0x77700300` value the
program's kernel patches program ({doc}`/drivers/linux`).

## 2. The switching fabric

Three analog parts sit between the BMC and the end devices. None of them is
I2C-addressable — they are transparent switches steered by GPIO nets — so
"selecting a channel" means driving pins, not sending bus transactions.
[BMC-WIRING §10.3](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md#103-how-the-muxes-are-controlled-the-steps-in-detail)

```{list-table} Mux fabric parts (all non-addressable)
:header-rows: 1
:widths: 10 22 68

* - Ref
  - Part
  - Function on this board
* - `QU9`
  - TI **SN74CBTLV3125** quad FET bus switch
  - All four `OE#` inputs tied to `I2CMUX_ENABLE#` (driven through inverter `U8`). When low, switches 1–2 connect the BMC's `I2C2` onto the mux common `I2C7`, and switches 3–4 connect `I2C8`↔`I2C8_SW`. Being a FET switch it just makes/breaks the wire — no protocol involved.
* - `QU5`
  - **74HC4052** dual 4-channel analog mux
  - Routes the common pair (`I2C7SDA`/`I2C7SCL`, pins 3/13) to one of four channel pairs by selects `S1`/`S0` (pins 9/10). Channel map here: `Y0`→`I2C8` (aux panel), `Y1`→unused, `Y2`→`I2C10` (DIMM A–D), `Y3`→`I2C11` (DIMM E–H).
* - `U23`
  - **74LVC125** quad buffer
  - Source-select for `QU5`'s `S0`/`S1`: they are driven from **either** the BMC (`AST_I2CS0`=W4, `AST_I2CS1`=W3) **or** the SP5100 (`SB_I2CS0/1`), whichever buffer pair's `OE#` is enabled. This is the bus-ownership arbitration between BMC and host.
```

The 74HC4052 truth table gives the channel selection:
`S1:S0 = 00→Y0, 01→Y1, 10→Y2, 11→Y3` — so DIMM bank A–D = `10`, bank E–H =
`11`, aux front panel = `00`.
[BMC-WIRING §10.3](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md#103-how-the-muxes-are-controlled-the-steps-in-detail)

```{admonition} Why a mux at all?
:class: note

SPD EEPROMs live at fixed addresses `0x50`–`0x57`, so sixteen DIMMs would
collide on one bus. The `QU5` demux splits them into two eight-slot banks with
their own `0x50`–`0x57` spaces, and the board FRU EEPROM (also `0x50`-range)
is isolated on the separate `I2C5` segment for the same reason.
[BMC-WIRING §10.3](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md#103-how-the-muxes-are-controlled-the-steps-in-detail)
This is the same problem the Dell C410X solves with addressable PCA954x muxes
({doc}`/hardware/peripherals/pca954x-mux`) — the KGPE-D16 uses analog parts
steered by GPIO instead, so there is no mux device to probe on the bus.
```

### Worked example — reading DIMM C1's SPD

1. **Take ownership**: enable the BMC's `U23` buffer pair so `AST_I2CS0/1`
   (balls W4/W3) drive the select lines.
2. **Bridge the switch**: assert `I2CMUX_ENABLE#` low → `QU9` connects the
   BMC's `I2C2` to the mux common `I2C7`.
3. **Select the bank**: drive `AST_I2CS1:AST_I2CS0 = 1:0` → `QU5` channel `Y2`
   = segment `I2C10` (DIMM A–D).
4. **Transact**: on the `I2C2` controller, address `0x50 + <C1 slot index>`
   and read the SPD bytes (the C1 temperature sensor answers at
   `0x18 + <slot index>` in the same mux state).

[BMC-WIRING §10.3](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md#103-how-the-muxes-are-controlled-the-steps-in-detail)
The SPD/TSOD devices themselves are documented in
{doc}`/hardware/peripherals/dimm-spd-tsod`.

## 3. BMC bus assignments

```{list-table} AST2050 controllers — balls, far ends, devices
:header-rows: 1
:widths: 10 14 40 36

* - Bus
  - SDA / SCL
  - Far end (netlist)
  - Devices / role
* - `I2C1`
  - A15 / B15
  - `PSUSMB1` header
  - PSU SMBus/PMBus telemetry; alert lands on `SCL7/SALT1` (B12)
* - `I2C2`
  - C14 / D14
  - `QU4` pins 34/33, `QU9`, `SU1` K2/K1 (`SMBus1`)
  - the **shared platform sensor bus**: {doc}`W83795G </hardware/peripherals/w83795g>` at `0x2F` + entry to the DIMM mux
* - `I2C3`
  - A14 / B14
  - `SU1` F19/D21 (`SMBus2`)
  - dedicated BMC ↔ southbridge pair
* - `I2C4`
  - C13 / D13
  - `QU4` pins 30/29 via level-shift FETs `Q56`–`Q59`
  - CPU thermal: the W83795G's SB-TSI front-end (CPU0 `0x4C`, CPU1 `0x4D`)
* - `I2C5`
  - A13 / B13
  - `U25`, `U27`, `U28`
  - board inventory: {doc}`HT24LC08 FRU EEPROM </hardware/peripherals/ht24lc08>` (`0x50`–`0x53`) + two {doc}`W83601G DIMM-LED expanders </hardware/peripherals/w83601g>`
* - `I2C6`
  - C12 / D12
  - `SU1` B4/A4 (`VIN1/GPIO54`, `VIN0/GPIO53`), `QU4` pin 35
  - second BMC ↔ southbridge/hwmon pair (lands on SP5100 IMC VIN/GPIO pins)
* - `I2C7`
  - A12 / B12
  - `SALT2` → `Q60`/`Q61`; `SALT1` → `PSUSMB1` pin 3
  - the balls serve as **SMBus ALERT inputs**; the board net named `I2C7` is the `QU5` mux common, fed from `I2C2` through `QU9`
* - `I2C8`
  - (muxed)
  - via `QU9`/`QU5` channel `Y0`
  - front auxiliary-panel I2C on `AUX_PANEL1`
```

Sources: [BMC-WIRING §10.4](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md#104-bmc-ic-bus-assignments-quick-reference),
ball-level far ends from
[`QU1_pins.md` § I2C / SMBus](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/pinmaps/QU1_pins.md#i2c--smbus-16)
and [`SU1_pins.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/pinmaps/SU1_pins.md).

```{admonition} Multi-master arbitration on the sensor bus
:class: important

`I2C2`/`SMBus1` is electrically **one wire** shared by the BMC and the
southbridge — both can reach the W83795G and both can drive the DIMM mux (the
`U23` buffer decides whose select lines win). In practice the BMC owns the bus
for out-of-band monitoring while the host is off, and the SP5100/host takes it
during POST and runtime.
[SP5100-WIRING §9.2](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/SP5100-SOUTHBRIDGE-WIRING.md#92-shared-with-the-bmc-arbitration)
An open BMC firmware must treat every device on this segment as potentially
contended — a mid-transaction host grab is a real hazard the arbitration
hardware does not prevent.
```

(kgpe-i2c-per-bus)=
## 4. Per-bus topology

### 4.1 PSU SMBus — BMC `I2C1`

The BMC's dedicated link to the power supply for PMBus telemetry (voltages,
currents, fan, status); the PSU's alert line lands on the BMC's `SALT1` ball.
The header pinout is on {doc}`kgpe-d16-connectors`.
[I2C-TOPOLOGY §3.1](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/I2C-SMBUS-TOPOLOGY.md#31-bmc-i2c1--psu-smbus-pmbus)

```{figure} /_static/diagrams/kgpe-d16-i2c-bus-psu.svg
:alt: PSU SMBus topology — BMC I2C1 (balls A15/B15) direct to the PSUSMB1 header, alert on ball B12.
:width: 85%
```

### 4.2 Shared platform sensor bus (multi-master)

The core management bus: BMC `I2C2` and SP5100 `SMBus1` on one wire, reaching
the {doc}`W83795G </hardware/peripherals/w83795g>` hardware monitor and the
`QU9` entry to the DIMM-SPD fabric (the related pairs `I2C3`/`SMBus2` and
`I2C6` are point-to-point BMC↔southbridge links on adjacent nets — see the
table in §3).
[I2C-TOPOLOGY §3.2](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/I2C-SMBUS-TOPOLOGY.md#32-shared-platform-sensor-bus-multi-master)

```{figure} /_static/diagrams/kgpe-d16-i2c-bus-sensor.svg
:alt: Shared platform sensor bus — AST2050 I2C2/3/6 and SP5100 SMBus1/2 reaching the W83795G hardware monitor at 0x2F and the QU9 switch toward the DIMM mux.
:width: 95%
```

### 4.3 DIMM SPD / TSOD banks (via the mux)

Two eight-slot banks behind the `QU9`→`QU5` fabric (§2): bank A–D on segment
`I2C10`, bank E–H on `I2C11`; SPD at `0x50`–`0x57` and TSOD at `0x18`–`0x1F`
per bank. Device detail: {doc}`/hardware/peripherals/dimm-spd-tsod`.
[I2C-TOPOLOGY §3.3](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/I2C-SMBUS-TOPOLOGY.md#33-dimm-spd--tsod-buses-via-mux)

```{figure} /_static/diagrams/kgpe-d16-i2c-bus-dimm-spd.svg
:alt: DIMM SPD/TSOD topology — I2C2 through the QU9 FET switch onto the I2C7 common, the QU5 analog mux fanning to the A–D and E–H DIMM banks, with the U23 buffer arbitrating the select lines between BMC and SP5100.
:width: 95%
```

### 4.4 CPU thermal (SB-TSI) — BMC `I2C4`

The BMC's `I2C4` reaches the W83795G's TSI pins through level-shift FETs; the
hardware monitor in turn masters the AMD **SB-TSI** interface to each
processor's die-temperature endpoint (CPU0 `0x4C`, CPU1 `0x4D`). The SB-TSI
register interface is specified in the in-repo AMD Family 10h BKDG
[BKDG](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/datasheets/AMD_Family_10h_BKDG_31116.pdf),
and the W83795G side (Bank 3, DTS registers) in
{doc}`/hardware/peripherals/w83795g` §1.11.
[I2C-TOPOLOGY §3.4](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/I2C-SMBUS-TOPOLOGY.md#34-cpu-thermal-sb-tsi)

```{figure} /_static/diagrams/kgpe-d16-i2c-bus-cputemp.svg
:alt: CPU thermal topology — BMC I2C4 through level-shift FETs to the W83795G TSI pins, the W83795G mastering SB-TSI to CPU0 at 0x4C and CPU1 at 0x4D.
:width: 85%
```

### 4.5 Board inventory — BMC `I2C5`

The BMC's private inventory/indicator bus: the {doc}`HT24LC08 FRU EEPROM
</hardware/peripherals/ht24lc08>` and the two {doc}`W83601G expanders
</hardware/peripherals/w83601g>` that drive the sixteen per-DIMM error LEDs.
Both expanders are reset by the Super-I/O's `SIO_RSMRST#`.
[I2C-TOPOLOGY §3.5](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/I2C-SMBUS-TOPOLOGY.md#35-bmc-i2c5--board-inventory--dimm-led-expanders)

```{figure} /_static/diagrams/kgpe-d16-i2c-bus-inventory.svg
:alt: Inventory bus topology — BMC I2C5 to the HT24LC08 FRU EEPROM at 0x50-0x53 and the two W83601G DIMM-error-LED GPIO expanders.
:width: 85%
```

### 4.6 CPU/NB voltage regulators — SP5100 `SMBus0` (host-side)

The southbridge's private SVI/PMBus link to the two UPI multi-phase PWM
controllers making the processor rails: `PU2` (**ASP0902QGK**, CPU0 core) and
`PU7` (**ASP0906QGK**, CPU1/northbridge), supported by the `PU1` ASP0910 SVI
switch and `PU4`/`PU9`/`PU10` UP6282 bucks. The BMC has no path onto this
segment — it matters to BMC work only as context for what the host owns.
[I2C-TOPOLOGY §3.6](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/I2C-SMBUS-TOPOLOGY.md#36-sp5100-smbus0--cpunb-voltage-regulators)

```{figure} /_static/diagrams/kgpe-d16-i2c-bus-vr.svg
:alt: VR PMBus topology — SP5100 SMBus0 to the ASP0902QGK and ASP0906QGK voltage-regulator PWM controllers.
:width: 85%
```

### 4.7 Remaining segments and straps

[I2C-TOPOLOGY §3.7–3.9](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/I2C-SMBUS-TOPOLOGY.md#37-other-segments--straps)

- **SP5100 `SMBus3` (level-shifted)** — brought out on `SU1` E20/E21 but
  **unpopulated** on this board.
- **Fan-curve straps** — the SP5100's `DDC1_SCL/SDA` pins are repurposed as
  the `FANCURVE1/0` strap inputs, not a live bus.
- **LAN-disable straps** — Super-I/O `GP37`/`GP50` gate the two 82574L NICs
  via the `LAN_SW1/2` jumpers ({doc}`/hardware/peripherals/intel-82574l`), not
  a live bus.
- **SR5690 PCIe hot-plug SMBus** — the northbridge exposes `PCIE_HP_SCL/SDA`
  on its debug GPIOs, brought to `NB_DEBUG_HEADER1`.
- **FireWire config EEPROM** — the LSI FW322 (`ZU1`) reads its GUID/config
  from a private HT24LC02 (`ZU2`, `0x50`) at power-up, independent of the
  management fabric ({doc}`/hardware/peripherals/ht24lc08`).

```{figure} /_static/diagrams/kgpe-d16-i2c-bus-nbhotplug.svg
:alt: SR5690 northbridge PCIe hot-plug SMBus to the NB debug header.
:width: 80%
```

```{figure} /_static/diagrams/kgpe-d16-i2c-bus-firewire.svg
:alt: FireWire private EEPROM bus — LSI FW322 to its HT24LC02 config EEPROM at 0x50.
:width: 80%
```

## 5. All addressable devices (quick reference)

```{list-table}
:header-rows: 1
:widths: 24 10 22 16 28

* - Device
  - Ref
  - Part
  - Addr (7-bit)
  - Bus
* - hardware monitor
  - `QU4`
  - Winbond {doc}`W83795G </hardware/peripherals/w83795g>`
  - `0x2F` (strapped)
  - shared sensor bus (`I2C2`/`SMBus1`)
* - board FRU EEPROM
  - `U25`
  - Holtek {doc}`HT24LC08 </hardware/peripherals/ht24lc08>`
  - `0x50`–`0x53`
  - BMC `I2C5`
* - DIMM-LED expander
  - `U27`
  - Winbond {doc}`W83601G </hardware/peripherals/w83601g>`
  - `0x18`–`0x1F` (strapped `A0`–`A2`)
  - BMC `I2C5`
* - DIMM-LED expander
  - `U28`
  - Winbond {doc}`W83601G </hardware/peripherals/w83601g>`
  - `0x18`–`0x1F` (strapped, ≠ `U27`)
  - BMC `I2C5`
* - DIMM SPD ×16
  - `DIMM_A1`…`H2`
  - JEDEC {doc}`SPD EEPROM </hardware/peripherals/dimm-spd-tsod>`
  - `0x50`–`0x57`/bank
  - `I2C10` / `I2C11`
* - DIMM TSOD ×16
  - `DIMM_A1`…`H2`
  - JEDEC {doc}`TSOD </hardware/peripherals/dimm-spd-tsod>`
  - `0x18`–`0x1F`/bank
  - `I2C10` / `I2C11`
* - CPU thermal
  - CPU0/1
  - AMD SB-TSI endpoint
  - `0x4C` / `0x4D`
  - W83795G TSI (from BMC `I2C4`)
* - CPU0 core VR
  - `PU2`
  - UPI ASP0902QGK
  - PMBus (VR-specific)
  - SP5100 `SMBus0`
* - CPU1/NB VR
  - `PU7`
  - UPI ASP0906QGK
  - PMBus (VR-specific)
  - SP5100 `SMBus0`
* - FireWire EEPROM
  - `ZU2`
  - Holtek {doc}`HT24LC02 </hardware/peripherals/ht24lc08>`
  - `0x50`
  - FW322 private bus
* - PSU
  - `PSUSMB1`
  - PMBus device (PSU-specific)
  - PSU-specific
  - BMC `I2C1`
```

Source: [I2C-TOPOLOGY §2](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/I2C-SMBUS-TOPOLOGY.md#2-bus-inventory).

## See also

**Related pages**

- {doc}`kgpe-d16-wiring` — the BMC's full pin-level wiring (this page is its I2C chapter, expanded)
- {doc}`kgpe-d16-connectors` — the `PSUSMB1` and `AUX_PANEL1` header pinouts
- {doc}`/hardware/i2c-topology` — the Dell C410X equivalent of this map (addressable PCA954x muxes instead of analog switches)
- {doc}`/hardware/registers/buses-gpio` — the AST2050 I2C controller registers
- {doc}`/hardware/peripherals/index` — the device catalogue

**External references**

- [PMBus specification](https://pmbus.org/specification-archives/) — the protocol spoken on the PSU and VR segments
- [Linux I2C subsystem](https://docs.kernel.org/i2c/index.html) — the driver stack an open BMC firmware uses on these buses

## Sources

- **[`I2C-SMBUS-TOPOLOGY.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/I2C-SMBUS-TOPOLOGY.md)** — the board-wide bus/master/device
  map extracted from the schematic netlist (every pin named `SCL`/`SDA` traced
  through resistors and analog switches to its endpoints).
- **[`AST2050-BMC-WIRING.md` §10](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md#10-i²c--smbus-topology-traced-through-every-mux--expander)** — the BMC-centric fabric
  documentation: mux control, worked access sequences, per-device table.
- **[`SP5100-SOUTHBRIDGE-WIRING.md` §9](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/SP5100-SOUTHBRIDGE-WIRING.md#9-smbus--ic)** — the southbridge's four SMBus
  segments and the shared-bus arbitration.
- **[`pinmaps/QU1_pins.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/pinmaps/QU1_pins.md)** / **[`pinmaps/SU1_pins.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/pinmaps/SU1_pins.md)** — ball-level net endpoints.
- **[AMD Family 10h BKDG](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/datasheets/AMD_Family_10h_BKDG_31116.pdf)** (31116) — the SB-TSI protocol/register
  definition for the CPU-thermal segment.
