# Zephyr

Zephyr is the base for the **WallaBMC** firmware track. It does **not** currently
support the ARM926EJ-S / ARMv5TE core used by all three boards — upstream Zephyr
ARM support targets Cortex-M/A/R and RISC-V. So the Zephyr track begins with a
first-class architecture port.

## ARMv5 / ARM926EJ-S architecture port

Added as topic branches in `mithro/zephyr`:

1. **`arch-arm926ejs`** — ARMv5TE architecture support: exception/interrupt
   model, MMU/cache setup, system timer, boot/startup, and the interrupt
   controller glue. Validated first on a QEMU-friendly ARM926 target.
2. **`soc-ast2050`** and **`soc-ns9360`** — SoC layers (clocks, UART, I2C, GPIO,
   Ethernet) on top of the arch.
3. **Board definitions** — devicetree + pin config for each board.

```{admonition} Scope & risk
:class: warning

The ARMv5 architecture port is the single largest deliverable in the program.
It is de-risked by bringing WallaBMC up on an existing Zephyr-supported target
first (to validate the application), then standing up the ARM926 arch, then the
SoC/board layers.
```

**Acceptance:** Zephyr `hello_world` and then WallaBMC boot on the QEMU `ast2050`
(and `ns9360`) machines via the new arch/SoC/board support.
