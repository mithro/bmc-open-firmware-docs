# Hardware reference

Register- and interface-level reference for the SoCs and every board peripheral,
written to be sufficient to implement **both** a QEMU device model and a driver.
Each peripheral page follows the same layout: bus/address, register map, reset
values, behaviour, and the datasheet it derives from.

```{toctree}
:maxdepth: 1
:caption: SoCs

soc-ast2050
soc-ns9360
```

```{toctree}
:maxdepth: 1
:caption: Board topology

i2c-topology
```

```{toctree}
:maxdepth: 2
:caption: Peripherals

peripherals/index
```

## Conventions

- **Addresses** are physical. I2C addresses are given 7-bit unless noted.
- **Reset values** are what a model must return before any write.
- Each register table marks access as R, W, or R/W and notes side effects
  (clear-on-read, write-1-to-clear, mux-gated, etc.) — these are exactly the
  behaviours the {doc}`../emulation/testbench` qtest benches assert.
