# PCA9548A / PCA9544A — I2C multiplexers

Both are **bidirectional translating** I2C switches controlled by a single
control register; they let many same-address devices share one upstream bus by
gating them onto downstream channels [PCA9548A DS p.1](#sources), [PCA9544A DS p.1](#sources). On
power-up **all channels are deselected** [PCA9548A DS p.1](#sources), [PCA9544A DS p.9](#sources).

## 2.1 PCA9548A — 8-channel switch with reset

- **Control register:** one 8-bit register; **bit N (B7..B0) = channel N enable**,
  1 = enabled. **Multiple channels may be enabled simultaneously** [PCA9548A DS p.15](#sources).
  A selected channel becomes active only after a STOP condition, which must follow
  immediately after the ACK cycle (keeps SDA/SCL high at connect time) [PCA9548A DS p.15](#sources).
- **Address:** fixed prefix `1110` + A2,A1,A0 → `0x70`–`0x77` [PCA9548A DS p.15](#sources).
- **RESET:** active-low `RESET` input; a low pulse ≥ `tWL` resets the register and
  deselects all channels; tie to `VCC` via pull-up if unused. Errata: keep the
  `RESET` voltage ≤ `VCC` or current flows RESET→VCC [PCA9548A DS p.14](#sources).
- **POR:** internal POR holds reset until `VCC ≥ VPORR`; to re-arm, drop `VCC`
  below `VPORF` [PCA9548A DS p.14](#sources). No interrupt logic.

```{list-table} PCA9548A control register — channel-enable byte
:header-rows: 1
:widths: 22 20 58

* - Bit
  - Name
  - Meaning
* - B7..B0
  - Channel 7..0 enable
  - 1 = downstream channel N connected to upstream; 0 = isolated. Any subset (e.g. `0x01` = ch0 only, `0x00` = none, POR default)
```

## 2.2 PCA9544A — 4-channel mux with interrupt logic

- **Control register:** low bits select the channel — **bit 2 = enable**, **bits
  1:0 = channel number (0–3)**; **only one channel at a time**. Bit 3 = don't-care.
  Bits 7:4 are **read-only interrupt-status** bits INT3..INT0 (one per channel)
  [PCA9544A DS p.14](#sources).
- **Address:** fixed prefix `1110` + A2,A1,A0 → `0x70`–`0x77`; strap pins have no
  internal pull-ups, so tie them high/low [PCA9544A DS p.13](#sources).
- **Interrupt AND-gate:** four active-low interrupt *inputs* `INT0`–`INT3` and one
  active-low `INT` *output* that is the AND of the four; a downstream device's
  interrupt is detected even when its channel is **not** selected, and sets the
  matching control-register status bit so the master can find it without polling
  every channel [PCA9544A DS p.1](#sources), [PCA9544A DS p.15](#sources).
- **POR:** puts registers in default state, no channel selected [PCA9544A DS p.9](#sources).

```{list-table} PCA9544A control register — channel select + status [PCA9544A DS p.14](#sources)
:header-rows: 1
:widths: 18 20 30 32

* - Bit(s)
  - Name
  - Access
  - Meaning
* - 7:4
  - INT3..INT0
  - Read-only
  - Interrupt pending on channel 3..0 (1 = active)
* - 3
  - D3
  - —
  - Don't care
* - 2
  - Enable
  - Read/write
  - 1 = a channel is selected; 0 = no channel selected
* - 1:0
  - B1,B0
  - Read/write
  - Selected channel number 0–3 (valid only when bit 2 = 1)
```

Channel-select write values: `0x04` = ch0, `0x05` = ch1, `0x06` = ch2, `0x07` =
ch3, `0x00` = none (POR default) [PCA9544A DS p.14](#sources).

## 2.3 How the C410X uses the muxes

```{list-table} C410X mux usage [io-tables](#sources), [gpio-map](#sources)
:header-rows: 1
:widths: 16 10 12 62

* - Part
  - Bus
  - Addr
  - Downstream
* - PCA9544A ×1
  - `0xF1`
  - `0x70`
  - Two ADT7462 fan/temp controllers behind the mux (chip #1 7-bit `0x58`, chip #2 `0x5C`); their `THERM`/`INT` outputs go to AST2050 GPIOB0 / GPIOB1. The bytes `0xB0` / `0xB8` in the IO tables are the ADT7462 **8-bit device addresses** (`0x58<<1` / `0x5C<<1`), *not* PCA9544A channel-select values (those are `0x04`–`0x07`); the exact channel each chip sits on is not pinned down in the RE notes.
* - PCA9548A #1
  - `0xF4`
  - `0x70`
  - Channels 0–7 → TMP100/TMP75 per-slot temp sensors, slots 1–8 (all at the same sensor address; the mux picks one at a time).
* - PCA9548A #2
  - `0xF4`
  - `0x71`
  - Channels 0–7 → per-slot temp sensors, slots 9–16.
```

The 16 per-slot temperature sensors all share one I2C address, so the two 8-channel
PCA9548As are mandatory to reach them one at a time; the two ADT7462s likewise share
an address behind the 4-channel PCA9544A [io-tables](#sources). (The exact PCA9544A raw
channel number for each ADT7462 is not pinned down in the RE notes — see §7 Gaps.)

## 2.4 Linux binding ([`i2c-mux-pca954x`](https://github.com/torvalds/linux/blob/master/drivers/i2c/muxes/i2c-mux-pca954x.c))

Mainline Linux drives both parts with **`drivers/i2c/muxes/i2c-mux-pca954x.c`**,
DT compatibles **`nxp,pca9548`** and **`nxp,pca9544`** [i2c-mux-pca954x](#sources). The mux
node nests one child `i2c` bus per channel (`reg = <N>`), under which the
downstream sensors live. Useful options: **`i2c-mux-idle-disconnect`** (deselect
all channels when idle — helps the shared-address sensors), `reset-gpios` (for the
PCA9548A `RESET`), and `idle-state` [i2c-mux-pca954x](#sources). A model must gate downstream
visibility on the currently selected channel(s).

---

## Sources

- **PCA9548A datasheet** (NXP SCPS143) and **PCA9544A datasheet** (NXP SCPS146) —
  channel-select registers, addressing, interrupt behaviour.
- **`dell-c410x-firmware/ANALYSIS.md`** / `io-tables/` — the C410X mux tree usage.
- Linux `drivers/i2c/muxes/i2c-mux-pca954x.c` (`nxp,pca9548`/`nxp,pca9544`).
