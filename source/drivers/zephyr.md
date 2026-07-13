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

## See also

**Related pages**

- {doc}`/firmware/wallabmc` — the BMC firmware built on this Zephyr track
- {doc}`/drivers/peripheral-map` — the "port needed" Zephyr column per peripheral
- {doc}`/hardware/soc-ast2050` — one SoC-layer target for the arch port
- {doc}`/hardware/soc-ns9360` — the other SoC-layer target
- {doc}`/emulation/qemu` — the QEMU machines used to validate the port

**External references**

- [Zephyr documentation](https://docs.zephyrproject.org/latest/) — upstream Zephyr project docs
- [Zephyr architecture-porting guide](https://docs.zephyrproject.org/latest/hardware/porting/arch.html) — how to add the ARMv5 / ARM926EJ-S architecture
- [Zephyr SoC-porting guide](https://docs.zephyrproject.org/latest/hardware/porting/soc_porting.html) — adding the `soc-ast2050` / `soc-ns9360` layers
- [Zephyr board-porting guide](https://docs.zephyrproject.org/latest/hardware/porting/board_porting.html) — adding each board definition
- [WallaBMC repository](https://github.com/tenstorrent-riscv-software/wallabmc) — the Zephyr BMC application ported on top
