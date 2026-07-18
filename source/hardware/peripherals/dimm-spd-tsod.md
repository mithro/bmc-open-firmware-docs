# DIMM SPD EEPROM + TSOD — on-module management devices

Every DDR3 DIMM carries a small I2C management subsystem of its own: a
**256-byte SPD (Serial Presence Detect) EEPROM** holding the module's identity
and timing parameters per JEDEC Standard 21-C Annex K, and — on modules that
populate it — a **TSOD (Temperature Sensor On DIMM)**, a JEDEC JC-42.4 /
TSE2002-class thermal sensor integrated on the same die as the EEPROM.
[21-C Annex K §1.0](#sources) [TSE2002B3C DS p.1](#sources) The SPD advertises
the sensor's presence in **byte 32 bit 7** ("thermal sensor incorporated onto
this assembly", compliant with TSE2002 specifications).
[21-C Annex K byte 32](#sources)

On the KGPE-D16 these are the only on-DIMM devices the AST2050 BMC can reach:
**16 DIMM slots (`DIMM_A1`…`H2`)**, each presenting its SPD at `0x50`–`0x57`
and its TSOD at `0x18`–`0x1F`, split into two 8-slot banks behind an analog
mux ([WIRING §10.2](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md#102-device-by-device-breakdown)).
This page covers the on-DIMM devices themselves; the mux fabric that reaches
them is documented in {doc}`/systems/kgpe-d16-i2c`.

## 1.1 KGPE-D16 board topology

Sixteen SPDs would collide in one `0x50`–`0x57` address window, so the board
splits the slots into two 8-slot banks, each a separate physical I2C segment
behind the QU5 (74HC4052) analog mux; each bank gets its own full `0x50`–`0x57`
(SPD) and `0x18`–`0x1F` (TSOD) space.
[TOPOLOGY §3.3](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/I2C-SMBUS-TOPOLOGY.md#33-dimm-spd--tsod-buses-via-mux)
(For the same reason the board FRU EEPROM `U25`, also `0x50`-range, is isolated
on the separate `I2C5` segment.
[WIRING §10.3](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md#103-how-the-muxes-are-controlled-the-steps-in-detail))

```{list-table} DIMM SPD/TSOD banks behind the QU5 mux
:header-rows: 1
:widths: 12 30 22 12 12 12

* - Bank
  - Slots
  - QU5 channel (select)
  - Segment
  - SPD
  - TSOD
* - A–D
  - `DIMM_A1/A2/B1/B2/C1/C2/D1/D2`
  - `Y2` (`S1:S0 = 10`)
  - `I2C10`
  - `0x50`–`0x57`
  - `0x18`–`0x1F`
* - E–H
  - `DIMM_E1/E2/F1/F2/G1/G2/H1/H2`
  - `Y3` (`S1:S0 = 11`)
  - `I2C11`
  - `0x50`–`0x57`
  - `0x18`–`0x1F`
```

Source: [TOPOLOGY §3.3](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/I2C-SMBUS-TOPOLOGY.md#33-dimm-spd--tsod-buses-via-mux).
The SPD bus reaches each DIMM connector at **pins 238/118**
(`DIMM_A1…D2.pin238/118` in the wiring table), and each slot's low address
bits (the device's `SA2:SA0` strap inputs) are hard-wired by the slot so the
eight modules per bank enumerate as `0x50 + slot-index` / `0x18 + slot-index`.
[WIRING §10.2](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md#102-device-by-device-breakdown)
[TSE2002B3C DS p.13](#sources) The TSOD address answers only on modules that
actually populate a thermal sensor (check SPD byte 32 bit 7 first).
[21-C Annex K byte 32](#sources)

## 1.2 SPD EEPROM (JEDEC 21-C Annex K, DDR3)

### 1.2.1 Device and addressing

The DDR3 SPD device is a plain **24C02-class 256-byte EEPROM** — one flat
page, no bank switching — selected by device-type code `1010` plus the three
strap bits: `0x50`–`0x57`. Byte and page writes (16-byte pages) are supported;
reads are sequential with address roll-over.
[TSE2002B3C DS p.10,13](#sources) This is unlike DDR4, whose 512-byte EE1004
SPD is accessed through two 256-byte pages switched by the bus-global
`SPA0`/`SPA1` commands — do not confuse the two access methods.
[TSE2004GB2 DS](#sources)

Of the 256 bytes, manufacturers typically program 128 or 176 bytes; byte 0
encodes both the bytes-used count and the total SPD device size.
[21-C Annex K byte 0](#sources)

### 1.2.2 Byte-map highlights

```{list-table} DDR3 SPD byte map (JEDEC 21-C Annex K)
:header-rows: 1
:widths: 18 44 38

* - Bytes
  - Contents
  - Notes
* - 0
  - SPD bytes used / SPD device size / CRC coverage
  - size `001` = 256 bytes; used 128/176/256
* - 1
  - SPD revision
  - encoding level / additions level nibbles
* - 2
  - Key byte: DRAM device type
  - **`0x0B` = DDR3 SDRAM** — check first
* - 3
  - Key byte: module type
  - `0001` RDIMM, `0010` UDIMM, `1011` LRDIMM, …
* - 4–8
  - Density/banks, addressing, voltage, organization, bus width
  - from the DRAM datasheet
* - 9–59
  - Timebases + timing parameters
  - FTB/MTB dividers, tCKmin, CAS latencies, tAA, tFAW, …
* - 31–32
  - Thermal/refresh options; **module thermal sensor**
  - byte 32 bit 7 = TSOD present (TSE2002-compliant)
* - 60–116
  - Module-type-specific section
  - indexed by key byte 3 (RDIMM register data, …)
* - 117–125
  - Module ID: manufacturer (JEP-106), location, date, serial
  - bytes 117–125 form a unique 9-byte module identifier
* - 126–127
  - CRC-16 (poly `0x1021`)
  - covers bytes 0–125 or 0–116 per byte 0 bit 7
* - 128–145
  - Module part number (ASCII)
  - blanks = `0x20`
* - 146–175
  - Revision code, DRAM manufacturer ID, manufacturer data
  - optional fields
* - 176–255
  - Open for customer use
  - where e.g. Intel XMP 1.x profiles live on enthusiast DIMMs
```

Sources: [21-C Annex K §1.1, bytes 0–255](#sources); the XMP placement is
convention in the customer-use area, not part of the JEDEC standard
([Wikipedia SPD](https://en.wikipedia.org/wiki/Serial_presence_detect)).

### 1.2.3 Write protection

The critical first half of the array (bytes `0x00`–`0x7F` — everything the
memory controller needs) can be write-protected in hardware. Protection
commands use a *separate device-type code* `0110` (the `0x30`-range of the
bus) rather than a register: [TSE2002B3C DS p.10,13,15](#sources)

- **SWP** (Set Write Protection) — reversible; requires the programming
  voltage `VHV` (7–10 V [TSE2002B3C DS p.5](#sources)) on the `SA0` pin, with
  `SA2`/`SA1` low.
- **CWP** (Clear Write Protection) — undoes SWP; also `VHV`-gated
  (`SA1` high).
- **PSWP** (Permanently Set Write Protection) — irreversible; afterwards the
  device stops acknowledging the `0110` protection interface entirely.
- **Read SWP / Read PSWP** — protection status via the Ack/NoAck of a read.
  [TSE2002B3C DS p.16](#sources)

Because SWP/CWP demand a high voltage on a strap pin, in-system software
(including the BMC) normally cannot alter protection — vendors set it with an
external programmer, and a protected SPD is effectively read-only in the
field. [TSE2002B3C DS p.15](#sources) The protection state survives power
cycles. [TSE2002B3C DS p.15](#sources)

## 1.3 TSOD (JC-42.4 / TSE2002 temperature sensor)

### 1.3.1 Register map

The TS half of the device answers at device-type code `0011` (`0x18`–`0x1F`)
and exposes **16-bit big-endian registers behind an 8-bit pointer** (write the
pointer, then read/write two bytes MSB-first). [TSE2002B3C DS p.20,23](#sources)
The register set is common to all JC-42.4 parts (register names below from the
IDT TSE2002B3C; the Linux driver uses the same map):

```{list-table} JC-42.4 / TSE2002 TS register map (pointer-selected, 16-bit)
:header-rows: 1
:widths: 12 12 24 52

* - Pointer
  - Access
  - Register
  - Contents
* - `0x00`
  - RO
  - Capabilities
  - feature flags: accuracy class, range, resolution (TRES), EVENT support
* - `0x01`
  - RW
  - Configuration
  - EVENT pin control, limit-lock bits, shutdown, hysteresis `HYST[1:0]` = 0 / 1.5 / 3 / 6 °C
* - `0x02`
  - RW
  - High (alarm upper) limit
  - two's complement, 0.25 °C granularity (bits [12:2])
* - `0x03`
  - RW
  - Low (alarm lower) limit
  - as above
* - `0x04`
  - RW
  - TCRIT (critical) limit
  - as above
* - `0x05`
  - RO
  - Ambient temperature
  - live reading + limit-status flags (format below)
* - `0x06`
  - RO
  - Manufacturer ID
  - PCI-SIG vendor number (e.g. IDT = `0x00B3`)
* - `0x07`
  - RO
  - Device ID / Revision
  - device in high byte, revision in low (TSE2002B3C = `0x2903`)
* - `0x08`+
  - —
  - vendor-specific
  - e.g. TSE2002B3C resolution register (POR default 0.25 °C)
```

Sources: [TSE2002B3C DS p.23-25,28](#sources); hysteresis steps per JC 42.4
([docs.kernel.org jc42](#sources)).

### 1.3.2 Temperature format

The Temperature Data Register (`0x05`) packs status and value into one word:
**bit 15 = above TCRIT, bit 14 = above High limit, bit 13 = below Low limit;
bit 12 = sign; bits [11:2] = temperature in 0.25 °C steps, with bits [1:0]
adding 0.125 / 0.0625 °C when the part's resolution (TRES) supports it** —
i.e. a 13-bit two's-complement value with a **0.0625 °C LSB** at full
resolution. Unsupported low-order bits read 0. [TSE2002B3C DS p.26-27](#sources)
The limit registers use the same encoding restricted to 0.25 °C granularity,
and JC-42.4 class-B parts are accurate to ±1 °C over the 75–95 °C active
range. [TSE2002B3C DS p.24,27](#sources)

```{admonition} Reaching the DIMMs from the BMC (3-step mux sequence)
:class: note

The banks sit behind an analog mux the BMC does not own by default — full
mechanics and diagrams in {doc}`/systems/kgpe-d16-i2c`. In short:

1. **Own the select lines** — enable the BMC side of the U23 (74LVC125)
   source-select buffers so `AST_I2CS0/1` (balls W4/W3) drive the mux selects.
   The SP5100 southbridge can own them instead (`SB_I2CS0/1`); this is
   multi-master arbitration, so take the bus only when the other master is
   quiescent.
2. **Bridge the bus** — assert `I2CMUX_ENABLE#` low so the QU9
   (SN74CBTLV3125) FET switch transparently connects BMC `I2C2` onto the mux
   common `I2C7`.
3. **Select the bank and address the device** — drive
   `AST_I2CS1:AST_I2CS0 = 10` for bank A–D (`I2C10`) or `11` for bank E–H
   (`I2C11`), then address `0x50 + slot` (SPD) or `0x18 + slot` (TSOD) on
   `I2C2`.

[WIRING §10.3](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md#103-how-the-muxes-are-controlled-the-steps-in-detail)
[TOPOLOGY §3.3](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/I2C-SMBUS-TOPOLOGY.md#33-dimm-spd--tsod-buses-via-mux)
```

```{admonition} Linux driver binding
:class: note

- **SPD** — the [`at24`](https://github.com/torvalds/linux/blob/master/drivers/misc/eeprom/at24.c)
  EEPROM driver, device name `"spd"` / DT compatible `atmel,spd`: a 24c02
  entry flagged read-only ([at24.c:178-180](https://github.com/torvalds/linux/blob/master/drivers/misc/eeprom/at24.c#L178-L180)).
  On PC hosts the I2C core auto-instantiates it (`"spd"` for DDR/DDR2/DDR3,
  `"ee1004"` for DDR4) from SMBIOS DIMM data at `0x50 + n`
  ([i2c-smbus.c:426-462](https://github.com/torvalds/linux/blob/master/drivers/i2c/i2c-smbus.c#L426-L462));
  a BMC devicetree must declare the nodes itself. Decode the content with
  [`decode-dimms`](https://git.kernel.org/pub/scm/utils/i2c-tools/i2c-tools.git/tree/eeprom/decode-dimms)
  from i2c-tools. The [`ee1004`](https://github.com/torvalds/linux/blob/master/drivers/misc/eeprom/ee1004.c)
  driver is **DDR4-only** (SPA paging) — wrong for these DDR3 modules.
- **TSOD** — the [`jc42`](https://github.com/torvalds/linux/blob/master/drivers/hwmon/jc42.c)
  hwmon driver, DT compatible `jedec,jc-42.4-temp`
  ([jedec,jc42.yaml](https://github.com/torvalds/linux/blob/master/Documentation/devicetree/bindings/hwmon/jedec,jc42.yaml)),
  probing `0x18`–`0x1F`; it identifies parts by the Manufacturer/Device ID
  registers (its table spans IDT TSE2002/TS3000, NXP SE97/SE98, Microchip
  MCP98xx, ST STTS2002/424, ON CAT34TS02, Atmel AT30TS00, …) and exposes
  `temp1_input` plus min/max/crit limits and alarms.
  [docs.kernel.org jc42](#sources)
- **The mux** — QU5 is a GPIO-selected analog mux, not an addressable I2C
  switch, so a devicetree models it with
  [`i2c-mux-gpio`](https://github.com/torvalds/linux/blob/master/Documentation/devicetree/bindings/i2c/i2c-mux-gpio.yaml)
  (see {doc}`/systems/kgpe-d16-i2c`).
```

## See also

**Related pages**

- {doc}`/systems/kgpe-d16` — the board carrying the 16 DIMM slots
- {doc}`/systems/kgpe-d16-i2c` — the QU9/QU5/U23 mux fabric these banks sit behind
- {doc}`tmp75-lm75` — the other temperature-sensor class in this catalogue (C410X)
- {doc}`index` — the peripheral catalogue

**External references**

- [JEDEC 21-C Annex K (SPD for DDR3 SDRAM Modules)](https://www.jedec.org/standards-documents/docs/spd-4010211) — the standard's page (registration-gated; see Sources for an open mirror)
- [JEDEC TSE2002av definition](https://www.jedec.org/standards-documents/docs/spd-40104) — SPD EEPROM + TS device standard (registration-gated)
- [Linux hwmon: jc42](https://docs.kernel.org/hwmon/jc42.html) — the mainline TSOD driver documentation
- [Wikipedia: Serial presence detect](https://en.wikipedia.org/wiki/Serial_presence_detect) — open byte-map summary incl. the XMP convention

## Sources

- **[JEDEC Standard 21-C, 4.1.2.11 Annex K](https://ia601005.us.archive.org/10/items/4-01-02-11-r-24_202012/4_01_02_11R24.pdf)** (Release 24, archived mirror) — the
  DDR3 SPD byte map (bytes 0–255, CRC, module IDs, byte 32 thermal sensor).
  The [jedec.org original](https://www.jedec.org/standards-documents/docs/spd-4010211) is registration-gated.
- **[IDT TSE2002B3C datasheet](https://www.renesas.com/en/document/dst/tse2002b3c-datasheet)** — a JEDEC TSE2002av part: the 256-byte
  EEPROM + SWP/CWP/PSWP protection (device code `0110`, `VHV`-gated) and the
  full TS register map with the temperature-word format.
- **[Renesas TSE2004GB2B0 datasheet](https://www.renesas.com/en/document/dst/tse2004gb2b0-datasheet)** — the DDR4 (EE1004/SPA-paged)
  counterpart, cited only for the DDR3-vs-DDR4 access contrast.
- **[AST2050-BMC-WIRING.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md)** §10 and
  **[I2C-SMBUS-TOPOLOGY.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/I2C-SMBUS-TOPOLOGY.md)** §3.3 — the KGPE-D16 bank split,
  addresses, connector pins, and mux access sequence (schematic-traced).
- Linux [`drivers/hwmon/jc42.c`](https://github.com/torvalds/linux/blob/master/drivers/hwmon/jc42.c), [`drivers/misc/eeprom/at24.c`](https://github.com/torvalds/linux/blob/master/drivers/misc/eeprom/at24.c), and
  [`drivers/i2c/i2c-smbus.c`](https://github.com/torvalds/linux/blob/master/drivers/i2c/i2c-smbus.c) — the mainline TSOD/SPD bindings, plus
  [docs.kernel.org/hwmon/jc42](https://docs.kernel.org/hwmon/jc42.html).
