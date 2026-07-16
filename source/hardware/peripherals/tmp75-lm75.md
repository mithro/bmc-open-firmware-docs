# TMP75 / LM75 — digital temperature sensors

Both the TI **TMP75** (datasheet SBOS288M, shared with TMP175) and the
National/TI **LM75** (datasheet SNIS153D, LM75B/LM75C) are LM75-class I2C digital
temperature sensors with a thermostat/over-temperature output. They share an
identical 4-register layout selected by an 8-bit pointer, differing mainly in
resolution and a few configuration bits (detailed below). [TMP75 DS p.16](#sources) [LM75 DS p.16](#sources)

On the C410X:

- **16× per-slot TMP75-class sensors** on bus `0xF4` (`&i2c4`), all at 7-bit `0x5C`,
  behind two PCA9548 8-channel muxes (`0x70` = slots 1–8, `0x71` = slots 9–16).
  The firmware mux index is `0x00`–`0x07` for mux #1 and `0x10`–`0x17` for mux #2.
  IPMI sensors `0x07`–`0x16` read the Temperature register. The firmware driver is
  `G_sOEMTMP100_I2CTEMP_IOSAPI`; the DT binds `ti,tmp75`.
  [IS_fl.bin.md:102-129](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/io-tables/IS_fl.bin.md#L102-L129) [dts:733-851](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/aspeed-bmc-dell-c410x.dts#L733-L851) [ANALYSIS.md:499](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/ANALYSIS.md#L499)
- **1× LM75 front-board sensor** on bus `0xF6` (`&i2c6`) at 7-bit `0x4F` (8-bit
  `0x9E`). IPMI sensor `0x17` ("FB Temp"). Firmware driver
  `G_sLM75_I2CTEMP_IOSAPI`; the DT binds `national,lm75`.
  [IS_fl.bin.md:131-139](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/io-tables/IS_fl.bin.md#L131-L139) [dts:1104-1119](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/aspeed-bmc-dell-c410x.dts#L1104-L1119) [ANALYSIS.md:501](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/ANALYSIS.md#L501)

(See the chip-identity caveat above: the per-slot part is addressed at `0x5C`,
outside the standard LM75/TMP75 `0x48`–`0x4F` range, so it is a register-compatible
LM75-class variant rather than a stock TMP75.) [dts:739-743](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/aspeed-bmc-dell-c410x.dts#L739-L743) [TMP75 DS p.11](#sources)

## Register map (pointer-selected)

An 8-bit **pointer register** selects one of four data registers; only the two low
bits P1:P0 are used (all higher bits 0), reset value 00 → Temperature. Every write
begins with the pointer byte; reads return the pointed register MSB-first, and the
pointer is retained across reads. [TMP75 DS p.11,16](#sources) [LM75 DS p.15-16](#sources)

```{list-table} TMP75 / LM75 register set (P1:P0 pointer)
:header-rows: 1
:widths: 10 12 26 26 12 14

* - Pointer
  - Access
  - TMP75 name
  - LM75 name
  - Reset
  - Width
* - `0x00`
  - RO
  - Temperature
  - Temperature
  - 0 °C
  - 12-bit / 9-bit
* - `0x01`
  - RW
  - Configuration
  - Configuration
  - `0x00`
  - 8-bit
* - `0x02`
  - RW
  - T_LOW
  - T_HYST Set Point
  - 75 °C
  - 12-bit / 9-bit
* - `0x03`
  - RW
  - T_HIGH
  - T_OS Set Point
  - 80 °C
  - 12-bit / 9-bit
```
[TMP75 DS p.16,20](#sources) [LM75 DS p.16-17](#sources)

The `0x02`/`0x03` pair are the low/high thermostat limits with a built-in
hysteresis band (T_LOW/T_HYST is the lower trip, T_HIGH/T_OS the upper); this
common layout is why one Linux driver serves both. [TMP75 DS p.20](#sources) [LM75 DS p.14](#sources)

## Temperature register (0x00) & conversion

Read-only, two bytes, MSB byte first, left-justified two's-complement; reads 0 °C
until the first conversion completes. [TMP75 DS p.17](#sources) [LM75 DS p.16](#sources)

- **TMP75:** 12-bit. Byte 1 = T11..T4, Byte 2 = T3..T0 in bits [7:4], bits [3:0] = 0.
  Convert: $T(\text{°C}) = \operatorname{sign\_extend12}(\text{word} \gg 4) \times \text{LSB}$. LSB depends on the resolution
  setting (0.5 / 0.25 / 0.125 / 0.0625 °C). Example: −25 °C → `0xE70`
  (`0xE70` $= 3696 - 4096 = -400$; $-400 \times 0.0625 = -25\,\text{°C}$). [TMP75 DS p.9,17,19](#sources)
- **LM75:** 9-bit. Bits D15 (MSB)..D7 (LSB) hold the value; D6..D0 undefined.
  Convert: $T(\text{°C}) = \operatorname{sign\_extend9}(\text{word} \gg 7) \times 0.5$. Example: −25 °C → `0x1CE`
  (`0x1CE` $= 462 - 512 = -50$; $-50 \times 0.5 = -25\,\text{°C}$). [LM75 DS p.14,16](#sources)

## Configuration register (0x01) bitfields

Both reset to `0x00`. The TMP75 uses all 8 bits; the LM75 leaves bits 7:5 as
reserved (keep 0) and has no resolution or one-shot control. [TMP75 DS p.17](#sources) [LM75 DS p.16](#sources)

```{list-table} Configuration register (0x01) fields
:header-rows: 1
:widths: 8 16 34 42

* - Bit
  - TMP75 field
  - TMP75 function
  - LM75 field / function
* - 7
  - OS
  - One-shot: write 1 while shut down to start a single conversion; always reads 0. [TMP75 DS p.19](#sources)
  - Reserved — keep 0 (LM75 has no one-shot). [LM75 DS p.16](#sources)
* - 6
  - R1
  - Converter resolution MSB (see table). [TMP75 DS p.19](#sources)
  - Reserved — keep 0. [LM75 DS p.16](#sources)
* - 5
  - R0
  - Converter resolution LSB (see table). [TMP75 DS p.19](#sources)
  - Reserved — keep 0. [LM75 DS p.16](#sources)
* - 4
  - F1
  - Fault-queue count MSB (see table). [TMP75 DS p.18](#sources)
  - Fault-queue count MSB. [LM75 DS p.16](#sources)
* - 3
  - F0
  - Fault-queue count LSB (see table). [TMP75 DS p.18](#sources)
  - Fault-queue count LSB. [LM75 DS p.16](#sources)
* - 2
  - POL
  - ALERT polarity: 0 = active-low (default), 1 = active-high. [TMP75 DS p.18](#sources)
  - O.S. polarity: 0 = active-low, 1 = active-high. [LM75 DS p.16](#sources)
* - 1
  - TM
  - Thermostat mode: 0 = comparator, 1 = interrupt. [TMP75 DS p.17](#sources)
  - Cmp/Int: 0 = comparator, 1 = interrupt. [LM75 DS p.16](#sources)
* - 0
  - SD
  - Shutdown: 1 = shutdown (< 0.1 µA) after current conversion; 0 = continuous. [TMP75 DS p.18](#sources)
  - Shutdown: 1 = low-power shutdown; 0 = continuous. [LM75 DS p.16](#sources)
```

```{list-table} TMP75 converter resolution R1:R0 (TMP75 only)
:header-rows: 1
:widths: 16 20 20 44

* - R1:R0
  - Resolution
  - LSB
  - Conversion time (typ)
* - `00`
  - 9-bit (default)
  - 0.5 °C
  - 27.5 ms
* - `01`
  - 10-bit
  - 0.25 °C
  - 55 ms
* - `10`
  - 11-bit
  - 0.125 °C
  - 110 ms
* - `11`
  - 12-bit
  - 0.0625 °C
  - 220 ms
```
[TMP75 DS p.19](#sources) (LM75 is fixed 9-bit / 0.5 °C, ~100 ms typ. [LM75 DS p.5,12](#sources))

```{list-table} Fault-queue F1:F0 (consecutive faults before ALERT/O.S.)
:header-rows: 1
:widths: 14 28 28 30

* - F1:F0
  - TMP75
  - TMP175
  - LM75
* - `00`
  - 1
  - 1
  - 1 (default)
* - `01`
  - 2
  - 2
  - 2
* - `10`
  - 3
  - 4
  - 4
* - `11`
  - 4
  - 6
  - 6
```
[TMP75 DS p.18](#sources) [LM75 DS p.16-17](#sources)

## Limit registers (0x02, 0x03) & thermostat behaviour

The T_LOW/T_HYST (`0x02`) and T_HIGH/T_OS (`0x03`) registers share the temperature
register's format and byte order. Reset defaults are **75 °C** (low/hyst) and
**80 °C** (high/OS) on both chips — a ready-to-use standalone thermostat.
[TMP75 DS p.20](#sources) [LM75 DS p.5,13,17](#sources)

- **Comparator mode (TM/Cmp-Int = 0):** the ALERT/O.S. output asserts when temp
  ≥ T_HIGH/T_OS (after the programmed fault count) and de-asserts only when temp
  falls below T_LOW/T_HYST — a hysteresis band. Shutdown does *not* clear it.
  [TMP75 DS p.19](#sources) [LM75 DS p.14](#sources)
- **Interrupt mode (TM/Cmp-Int = 1):** asserts on crossing the high limit, but is
  cleared by any register read (or entering shutdown); after clearing it re-asserts
  when temp drops below the low limit, again cleared by a read; the cycle repeats.
  [TMP75 DS p.19](#sources) [LM75 DS p.14-15](#sources)
- **POL** inverts the output polarity (default active-low). The LM75 O.S. pin is
  open-drain in all modes. The TMP75 ALERT can additionally act as an SMBus Alert
  responder (Alert command `0x19`), which the LM75 O.S. output cannot. [TMP75 DS p.18,11](#sources) [LM75 DS p.15](#sources)

## Address pins

Both use a fixed `1001` prefix plus three address pins A2/A1/A0 → **`0x48`–`0x4F`**
(up to 8 devices per bus). The TMP175 variant additionally allows a floating pin
state for 27 addresses. [TMP75 DS p.11](#sources) [LM75 DS p.13](#sources)

```{list-table} TMP75 / LM75 address strapping (A2 A1 A0)
:header-rows: 1
:widths: 34 33 33

* - A2 A1 A0
  - 7-bit address
  - Binary
* - `0 0 0`
  - `0x48`
  - `1001000`
* - `0 0 1`
  - `0x49`
  - `1001001`
* - `0 1 0`
  - `0x4A`
  - `1001010`
* - `0 1 1`
  - `0x4B`
  - `1001011`
* - `1 0 0`
  - `0x4C`
  - `1001100`
* - `1 0 1`
  - `0x4D`
  - `1001101`
* - `1 1 0`
  - `0x4E`
  - `1001110`
* - `1 1 1`
  - `0x4F`
  - `1001111`
```
[TMP75 DS p.11](#sources) [LM75 DS p.13](#sources)

## TMP75 vs LM75 differences

```{list-table} Key TMP75-vs-LM75 differences
:header-rows: 1
:widths: 26 37 37

* - Aspect
  - TMP75 / TMP175
  - LM75 (B/C)
* - Resolution
  - 9/10/11/12-bit, selectable (R1:R0)
  - Fixed 9-bit
* - Best LSB
  - 0.0625 °C (12-bit)
  - 0.5 °C
* - One-shot (OS bit)
  - Yes
  - None
* - Config bits used
  - 8 (OS, R1, R0, F1, F0, POL, TM, SD)
  - 5 (F1, F0, POL, Cmp/Int, SD); 7:5 reserved
* - Fault-queue max
  - 4 (TMP75) / 6 (TMP175)
  - 6
* - Conversion time
  - 27.5 ms (9-bit) … 220 ms (12-bit)
  - ~100 ms typ / 300 ms max
* - Max bus speed
  - 2 MHz (HS mode)
  - 400 kHz
* - SMBus Alert responder
  - Yes (ALERT + cmd `0x19`)
  - No (plain thermostat O.S.)
* - Accuracy
  - ±1 °C typ (TMP175 ±0.5 typ)
  - ±2 °C max (−25…100 °C)
* - Supply
  - 2.7–5.5 V
  - 3–5.5 V
* - Output pin name
  - ALERT
  - O.S. (over-temp shutdown)
```
[TMP75 DS p.3-5,9-12,17-20](#sources) [LM75 DS p.1,3-5,12-17](#sources)

## Linux binding ([`lm75`](https://github.com/torvalds/linux/blob/master/drivers/hwmon/lm75.c))

Mainline Linux drives both with the `hwmon`/[`lm75`](https://github.com/torvalds/linux/blob/master/drivers/hwmon/lm75.c) driver via a chip-type table.
The C410X uses `compatible = "ti,tmp75"` (per-slot) and `compatible =
"national,lm75"` (front board). [dts:769,1116](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/aspeed-bmc-dell-c410x.dts#L769) [lm75.c](https://github.com/torvalds/linux/blob/master/drivers/hwmon/lm75.c) The driver's registers are
`LM75_REG_TEMP` 0x00, `LM75_REG_CONF` 0x01, `LM75_REG_HYST` 0x02, `LM75_REG_MAX`
0x03 — matching the datasheet map. It exposes `temp1_input` (RO), `temp1_max`
(= T_OS / T_HIGH, RW, reset 80 °C) and `temp1_max_hyst` (= T_HYST / T_LOW, RW,
reset 75 °C); for `tmp75`/`tmp175` it also exposes a writable `update_interval`
mapped to R1:R0, and at probe it sets R1:R0 = 12-bit and clears the OS bit
(`set_mask = 3<<5`, `clr_mask = 1<<7`). [lm75.c](https://github.com/torvalds/linux/blob/master/drivers/hwmon/lm75.c)

```{admonition} Two binding caveats
:class: warning

- The devicetree binding file is now `lm75.yaml` (the older `national,lm75.yaml`
  path 404s on current mainline); the `national,lm75` *compatible* is unchanged.
  [lm75.yaml](https://github.com/torvalds/linux/blob/master/Documentation/devicetree/bindings/hwmon/lm75.yaml)
- The driver's `lm75b` type models the **NXP LM75B (11-bit)**, which is *not* the
  TI/National LM75B in this datasheet (a 9-bit National LM75 re-badge). For the
  datasheet part, use `national,lm75` (9-bit), **not** `national,lm75b`. [lm75.c](https://github.com/torvalds/linux/blob/master/drivers/hwmon/lm75.c)
```

## See also

**Related pages**

- {doc}`/hardware/peripherals/pca954x-mux` — the two PCA9548 muxes that reach the 16 per-slot sensors
- {doc}`/hardware/i2c-topology` — buses `0xF4`/`0xF6` in the C410X I2C tree
- {doc}`/hardware/registers/buses-gpio` — the AST2050 I2C controller upstream
- {doc}`/systems/dell-c410x` — the board (16 per-slot + 1 front-board sensor)

**External references**

- [TI TMP75 product page](https://www.ti.com/product/TMP75) — the vendor product/datasheet page (TMP75/TMP175)
- [TI LM75B product page](https://www.ti.com/product/LM75B) — the LM75-class part vendor page
- [Linux hwmon: lm75](https://docs.kernel.org/hwmon/lm75.html) — the mainline driver documentation (`ti,tmp75` / `national,lm75`)
- [Devicetree binding: lm75.yaml](https://github.com/torvalds/linux/blob/master/Documentation/devicetree/bindings/hwmon/lm75.yaml) — the DT binding (current mainline path)

## Sources

- **[TMP75 datasheet](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/datasheets/TMP75_Datasheet.pdf)** (TI SBOS288) and **[LM75 datasheet](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/datasheets/LM75_Datasheet.pdf)** (National/TI SNIS153)
  — the pointer + 4 registers, resolution, and OS/ALERT behaviour (in-repo PDFs).
- **[`dell-c410x-firmware/io-tables/`](https://github.com/mithro/ai-shenanigans-for-bmcs/tree/main/dell-c410x-firmware/io-tables)** + [`ANALYSIS.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/dell-c410x-firmware/ANALYSIS.md) — the per-slot sensors
  behind two PCA9548 muxes (firmware calls them TMP100 @ 0x5C; the DTS binds the
  register-compatible `ti,tmp75`) and the front-board LM75 @ 0x4F.
- Linux [`drivers/hwmon/lm75.c`](https://github.com/torvalds/linux/blob/master/drivers/hwmon/lm75.c) (`ti,tmp75` / `national,lm75`) — the binding
  (use `national,lm75` for the 9-bit TI/National part, not the NXP `lm75b`).
