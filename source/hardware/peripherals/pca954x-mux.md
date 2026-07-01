# PCA9548 / PCA9544 — I2C bus multiplexers

I2C bus multiplexers that fan one upstream bus out to several downstream
segments, so many devices can share the same address. The C410X uses **2×
PCA9548** (8-channel, bus `0xF4`, addresses `0x70`/`0x71`) to reach the 16
same-address TMP75 sensors, and **1× PCA9544** (4-channel, bus `0xF1`, address
`0x70`) in front of the two ADT7462 controllers.

```{list-table}
:header-rows: 0
:widths: 30 70

* - PCA9548
  - 8-channel mux; control byte bit N enables channel N (any subset)
* - PCA9544
  - 4-channel mux/switch; control byte selects one channel + interrupt bits
* - Reset state
  - all channels disabled (no downstream device visible)
```

## Model / driver notes

- A single-byte I2C write to the mux sets the channel-enable byte; a read
  returns it.
- While a channel is enabled, downstream devices at their own addresses become
  visible on the parent bus; the model must gate downstream access on the
  currently selected channel(s).
- Mainline Linux binds `i2c-mux-pca954x` (`nxp,pca9548` / `nxp,pca9544`); the
  device tree nests the downstream sensor nodes under each channel.
- This is why the mux model is built early (alongside INA219): almost every
  sensor test must first select the right channel.
