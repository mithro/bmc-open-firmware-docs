# AST2050 register reference

Register-by-register documentation of the Aspeed AST2050 (G3) SoC blocks,
written to be sufficient to implement **both** a QEMU device model and a
Linux/Zephyr/U-Boot driver. Every documented register — including reserved and
currently-unused ones — carries its offset, reset value, access type, and a
description traceable to at least one primary source.

Two boards in this program share this SoC (the ASUS KGPE-D16 and the Dell
C410X), so this SoC-level reference is shared; each board page then documents
only its own wiring, straps, and off-chip peripherals.

```{admonition} Coverage status — which blocks are fully transcribed
:class: note

The blocks a firmware port must drive are fully register-mapped in the pages
below: SCU / clock / reset / watchdog, DDR2/SDRAM (+ cold-init), MAC / MDIO /
PHY, the I2C/SMBus, SPI/SMC and LPC buses, GPIO, the interrupt controller (VIC),
the timers, the UARTs, the PCI-slave/VGA endpoint, USB, and the P2A / iLPC AHB
bridges.

A set of AST2050 on-chip blocks that are **unused on both boards** are, at time
of writing, referenced (via their SCU reset/clock bits and VIC interrupt lines)
but **not yet transcribed register-by-register**: the PWM & fan-tachometer
controller (§28), the RTC (§24), PECI (§32), the virtual/pass-through UARTs
(§29), the HACE crypto engine (§19), the MIC (§13), the MDMA engine (§22), the
outbound AHB→PCI (A2P) bridge (§21), the 2D graphics accelerator (§35), and the
hardware cursor (§37); the USB endpoint, Video-Engine and VGA-CRTC register files
are given at overview level. These are listed explicitly so they are visibly
*pending*, not silently omitted — full transcription is tracked as follow-up work.
```

## How to read these tables

```{list-table}
:header-rows: 1
:widths: 18 82

* - Notation
  - Meaning
* - **Offset**
  - Byte offset from the block's base address (given in each section heading).
    All addresses are physical.
* - **Reset**
  - The value a model must return after power-on-reset, before any write. `—`
    means the datasheet does not specify / undefined.
* - **Access** `RO`
  - Read-only; writes ignored.
* - **Access** `RW`
  - Readable and writable.
* - **Access** `WO`
  - Write-only; reads return undefined or a different (status) value.
* - **Access** `W1C`
  - Write-1-to-clear: writing a 1 to a bit clears it; writing 0 has no effect.
* - **Access** `RWK`
  - Write-protected behind a key/unlock register (SCU, SDRAM controller).
* - *reserved*
  - Not assigned in the datasheet. A faithful model should preserve written
    values or return the documented reset value; drivers must not rely on them.
```

Each block section lists its **base address** and, where the block is
lock-protected, its **unlock key**. Bitfield tables follow the register map for
the control/status registers a model or driver must get exactly right. Every
row cites its source — `[DS §x.y p.N]` for the AST2050/AST1100 datasheet, a
repository file for reverse-engineered values, or a URL for cross-checked
external references (mainline drivers, JEDEC, component datasheets). These are
exactly the behaviours the {doc}`../../emulation/testbench` qtest benches assert.

```{toctree}
:maxdepth: 1
:caption: SoC blocks

scu-clock-reset
ddr2-sdram
network-mac-phy
buses-gpio
uart-vic-timers
pcie-vga-usb-bridges
control-blocks
engines-blocks
```
