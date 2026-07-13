# Bring-up & debug

Physical bring-up, debug access, and the hardware-in-the-loop (HIL) rig that runs
the same test benches against real boards as CI runs against QEMU.

```{toctree}
:maxdepth: 1

bring-up
jtag-uart
```

## Hardware-in-the-loop

A Raspberry Pi acts as a remotely-accessible debug adapter (JTAG + UART + SPI) to
a target board. The `firmware-testbench` `hil` backend ({doc}`../emulation/testbench`)
drives this rig, so a board bench that passes in QEMU can be re-run on silicon by
changing one flag. Racks of Pi-connected boards (the `rpi4-pmod` / `rpi5-pmod` /
`rpi4-gwifi` pattern) extend this to CI on real hardware via self-hosted runners.
