# Emulation & test

Full QEMU emulation of each system and the per-component test benches that verify
the models are complete and correct. Emulation is a prerequisite for confidently
building and CI-verifying every firmware layer.

```{toctree}
:maxdepth: 1

qemu
testbench
```

## Principle: model → bench → firmware

Each peripheral is landed as a **triplet**: a hardware-reference page
({doc}`../hardware/index`), a QEMU model, and a qtest bench. Firmware is then
verified against the board-complete machine through a single test bench that runs
against either the QEMU backend (in CI) or real hardware (HIL) — see
{doc}`testbench`.
