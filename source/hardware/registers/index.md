# AST2050 register reference

Register-by-register documentation of the Aspeed AST2050 (G3) SoC blocks,
written to be sufficient to implement **both** a QEMU device model and a
Linux/Zephyr/U-Boot driver. Every documented register — including reserved and
currently-unused ones — carries its offset, reset value, access type, and a
description traceable to at least one primary source.

Two boards in this program share this SoC (the ASUS KGPE-D16 and the Dell
C410X), so this SoC-level reference is shared; each board page then documents
only its own wiring, straps, and off-chip peripherals.

```{admonition} Coverage status — every on-chip block is register-mapped
:class: note

**Every** AST2050 on-chip register block is transcribed register-by-register
across the pages below. That includes the blocks a firmware port drives (SCU /
clock / reset / watchdog, DDR2/SDRAM + cold-init, MAC / MDIO / PHY, the
I2C·SMBus·SPI-SMC·LPC buses, GPIO, the VIC, timers, UARTs, the PCI-slave/VGA
endpoint, and the P2A / iLPC AHB bridges) **and** the blocks that are unused on
both boards but documented anyway: the PWM & fan-tachometer controller (§28),
the RTC (§24), PECI (§32), the virtual / pass-through UARTs (§29), the HACE
crypto engine (§19), the MIC (§13), the MDMA engine (§22), the outbound AHB→PCI
(A2P) bridge (§21), the 2D graphics accelerator (§35), the hardware cursor (§37),
and the full USB-endpoint / Video-Engine / VGA + extended-CRT register files.

The only items given below register level are ones the datasheet itself does not
define at that level: the eight USB SETUP data buffers (raw 8-byte packet scratch
areas with no bit structure), two reserved Video-Engine registers, and the A2P
bridge (specified as address windows plus an enable strap, with no per-register
bitfields). Each is called out where it occurs — nothing is silently omitted.
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

## The pages at a glance

Each row links to the register page; the {doc}`../../drivers/peripheral-map`
maps every block to its Linux/Zephyr/QEMU driver and OpenBMC daemon.

```{list-table}
:header-rows: 1
:widths: 40 30 30

* - Block(s)
  - Base address(es)
  - Page
* - SCU · clock/PLL · reset · watchdog
  - `0x1E6E2000` · `0x1E785000`
  - {doc}`scu-clock-reset`
* - DDR2 / SDRAM controller + cold-init
  - `0x1E6E0000`
  - {doc}`ddr2-sdram`
* - Ethernet MAC · MDIO/MII · PHY
  - `0x1E660000` / `0x1E680000`
  - {doc}`network-mac-phy`
* - I2C/SMBus · SPI/SMC flash · LPC · GPIO
  - `0x1E78A000` · `0x16000000` · `0x1E789000` · `0x1E780000`
  - {doc}`buses-gpio`
* - UARTs · interrupt controller (VIC) · timers
  - `0x1E783000`/`0x1E784000` · `0x1E6C0000` · `0x1E782000`
  - {doc}`uart-vic-timers`
* - PCI-slave/VGA endpoint · USB hub · P2A/iLPC AHB bridges
  - `0x1E600000` · `0x1E6A0000` · `0x1E720000`
  - {doc}`pcie-vga-usb-bridges`
* - USB 2.0 · Video Engine · VGA + extended-CRT (full maps)
  - `0x1E6A0000` · `0x1E700000`
  - {doc}`display-usb`
* - PWM & fan-tach · RTC · PECI · VUART/PUART
  - `0x1E786000` · `0x1E781000` · `0x1E78B000` · `0x1E787000`
  - {doc}`control-blocks`
* - HACE · MIC · MDMA · A2P bridge · 2D engine · HW cursor
  - `0x1E6E3000` · `0x1E640000` · `0x1E740000` · `0x1E720000`
  - {doc}`engines-blocks`
```

```{toctree}
:maxdepth: 1
:caption: SoC blocks

scu-clock-reset
ddr2-sdram
network-mac-phy
buses-gpio
uart-vic-timers
pcie-vga-usb-bridges
display-usb
control-blocks
engines-blocks
```

## See also

**Related pages**

- {doc}`/hardware/soc-ast2050` — the SoC-level orientation this register reference sits under
- {doc}`/drivers/peripheral-map` — every block mapped to its Linux/Zephyr/QEMU driver and OpenBMC daemon
- {doc}`/emulation/testbench` — the qtest benches that assert these register behaviours
- {doc}`/drivers/linux` — the G3 mainline-Linux driver work

**External references**

- [QEMU Aspeed SoC documentation](https://www.qemu.org/docs/master/system/arm/aspeed.html) — the machine models that emulate this SoC's registers
- [Linux driver API index](https://docs.kernel.org/driver-api/index.html) — the subsystem driver docs the per-block pages link into
- [Device Tree usage model](https://docs.kernel.org/devicetree/usage-model.html) — how these register blocks are described to Linux via DT
