# Aspeed AST2050 (G3) SoC

The AST2050 (also sold as AST1100) is a third-generation Aspeed BMC SoC: an
ARM926EJ-S (ARMv5TE) core with integrated VGA, Ethernet MAC, I2C, GPIO, USB, and
SPI. It predates mainline Linux Aspeed support (which starts at the AST2400 /
"G4"), so both the QEMU model and the kernel treat it as a **G3** part that is
register-compatible enough with the G4 to reuse most peripheral models/drivers,
with SoC-specific deltas in the clock (SCU) and memory controllers.

```{admonition} Full register reference
:class: seealso

This page is the SoC-level orientation. The **register-by-register** maps for
every block — SCU/clock/reset, DDR2, MAC/MDIO/PHY, the buses and GPIO, and the
UART/VIC/timers/PCIe/USB/bridges — live under
{doc}`registers/index`, each cross-referenced against the datasheet, the
mainline drivers, and the hardware-verified reverse-engineering.
```

## Memory map

```{figure} /_static/diagrams/ast2050-memory-map.svg
:alt: AST2050 ARM physical address map showing flash at 0x14000000, the 0x1E6xxxxx peripheral band, and DRAM at 0x40000000, with the on-chip peripheral blocks in address order.
:width: 100%

The AST2050 ARM physical address map. ★ marks the boot-critical G3 blocks (the
VIC at `0x1E6C0000` and the UART2 console).
```

```{list-table}
:header-rows: 1
:widths: 26 22 52

* - Region
  - Base
  - Notes
* - SPI NOR (FMC)
  - `0x14000000`
  - boot flash; U-Boot at flash base
* - DRAM
  - `0x40000000`
  - DDR2; 64–128 MiB depending on board
* - SDRAM controller
  - `0x1E6E0000`
  - unlock key `0xFC600309`
* - System Control Unit (SCU)
  - `0x1E6E2000`
  - unlock key `0x1688A8A8`; clocking + strap. `SCU7C` (silicon revision) reads
    `0x00000202` on the AST2050 — confirmed independently over both the P2A
    bridge and JTAG (see {doc}`../debug/bring-up`)
* - Interrupt controller (VIC)
  - `0x1E6C0000`
  - **compact G3 layout** — see below; *not* the AST2400+ interleaved map
* - GPIO controller
  - `0x1E780000`
  - GPIOA…GPIOH 8-bit port groups (**64 pins**; the G3 defines banks A–H only,
    not A–P — see {doc}`registers/buses-gpio`)
* - MAC0 / MAC1 (ftgmac100)
  - `0x1E660000` / `0x1E680000`
  - 10/100 Ethernet
* - UART (console)
  - `0x1E783000` / `0x1E784000`
  - 16550-compatible. The KGPE-D16 BMC console is **UART2** (`0x1E784000` =
    Linux `ttyS1`). Baud is a documented discrepancy — firmware 115200 vs a
    rig-observed 1200 (see {doc}`../systems/kgpe-d16` §2.2)
```

```{admonition} SCU / SDRAM unlock keys
:class: important

The SCU and SDRAM controllers are lock-protected: software must write the
unlock key to the first register before other registers accept writes. A QEMU
model must honour this (writes are ignored until unlocked) or vendor init code
mis-detects the part.
```

## G3 vs. G4 deltas that matter

- **Interrupt controller (VIC) — the big one.** The G3 VIC is a *compact*,
  non-interleaved block at `0x1E6C0000` (32 sources, one 32-bit word per
  register), whereas the AST2400+ "new" VIC that mainline [`irq-aspeed-vic.c`](https://github.com/torvalds/linux/blob/master/drivers/irqchip/irq-aspeed-vic.c)
  drives lives at `0x1E6C0080` with an interleaved high/low layout. The stock
  driver's register writes therefore miss the G3 entirely — no interrupt is ever
  enabled, the timer clockevent is dead, and boot hangs at the first
  `usleep_range()`. This was mis-diagnosed for days as a NIC or timer-routing
  fault before being isolated to the interrupt controller. See
  {ref}`the G3 VIC section <g3-vic>` below and {doc}`../drivers/linux`.
- **SCU clocking** — H-PLL post-divider layout and hardware-strap bit positions
  differ from the AST2400. This is the primary reason a stock `palmetto-bmc`
  (AST2400) machine is only a smoke-test stand-in, not the target.
- **SDRAM / static-memory controllers** — different register semantics; only
  relevant to from-scratch DRAM init (U-Boot), not to a warm-booted kernel.
- **Everything else** (MAC, GPIO, I2C, watchdog, SMC read path, UART) is close
  enough that the G4 models/drivers bind unchanged with `aspeed,ast2050-*`
  compatibles.

(g3-vic)=

## Interrupt controller — the compact G3 VIC

At `0x1E6C0000` the AST2050 has an Aspeed "old" VIC: 32 interrupt sources in a
non-interleaved register map (datasheet §16), functionally the same programmable
sense/event/dual-edge controller as the G4 but at a different base and layout:

```{list-table}
:header-rows: 1
:widths: 22 18 60

* - Register
  - Offset
  - Meaning
* - `VIC00` / `VIC08`
  - `0x00` / `0x08`
  - IRQ status / raw status
* - `VIC10` / `VIC14`
  - `0x10` / `0x14`
  - interrupt enable / enable-clear
* - `VIC24`
  - `0x24`
  - sense (1 = level, 0 = edge)
* - `VIC28`
  - `0x28`
  - dual-edge (1 = both edges)
* - `VIC2C`
  - `0x2C`
  - event (1 = high/rising)
* - `VIC38`
  - `0x38`
  - edge-clear (write-1-to-clear the edge latch)
```

Because the out-of-band boot path (loading directly into DRAM over the P2A
bridge) has no firmware to configure the VIC, the driver programs
sense/event/dual per the datasheet interrupt-source table itself: timers 16–18
and the watchdog (27) are rising-edge, the RTC sources (22–26) are both-edge, and
the peripherals are high-level. A dedicated Linux driver,
`irq-aspeed-g3-vic.c` (compatible `aspeed,ast2050-vic`), implements this — see
{doc}`../drivers/linux`.

## DRAM (DDR2)

The AST2050 memory controller drives DDR2 at `0x40000000`. On the KGPE-D16 BMC
the fitted size is **64 MiB, hardware-verified** — a size that matters because
modern full OpenBMC will not fit (see {doc}`../firmware/openbmc`). Bringing DRAM
up from cold on real silicon required a faithful re-creation of the vendor init
sequence with three corrections found empirically: a **4-bank** geometry, the
**64 MiB** size field, and the **final DLL training block** (the last of which,
when omitted, produced ~0.29 % data errors that silently corrupted large
transfers). With all three applied, a 1 MiB write/read-back is error-free.

## AHB debug bridges (out-of-band access)

The AST2050 exposes two backdoors from the host side onto the BMC's internal AHB
bus, which make it possible to inspect and even boot the BMC without a working
BMC firmware:

- **P2A (PCIe-to-AHB)** — present and usable; the primary out-of-band path on
  these boards. The full cold-boot-over-P2A chain (DDR2 init → load U-Boot/Linux
  into DRAM → run) is documented in {doc}`../debug/bring-up`.
- **iLPC (LPC-to-AHB)** — present but *disabled* on the boards examined (reads
  return all-ones), so it is correctly reported as unavailable rather than used.
- There is **no UART debug console backdoor** on the AST2050 (unlike some later
  parts).

The [`culvert`](https://github.com/mithro/culvert) tool was ported to recognise
and drive the G3 over these bridges; the port is hardware-verified against a real
AST2050.

## Upstreaming shape (Linux)

The clean series is: (1) a [`clk-aspeed`](https://github.com/torvalds/linux/blob/master/drivers/clk/aspeed/clk-aspeed.c) change adding AST2050 support, (2) a new
`aspeed-g3.dtsi` SoC include, (3) `aspeed,ast2050-*` compatibles on the affected
drivers, then (4) the two board `.dts` files include the G3 dtsi. See
{doc}`../drivers/linux`.

```{admonition} Register detail source
:class: note

Full register-bit detail lives in the program's [`ast2050.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/ast2050.h) / [`hwreg.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h)
(U-Boot-style config + hardware register headers) and the Aspeed AST2050
datasheet. This page captures the SoC-level map a model/driver needs; per-block
bit tables are added as each block is modelled.
```

## See also

**Related pages**

- {doc}`/hardware/registers/index` — the register-by-register maps for every on-chip block
- {doc}`/hardware/index` — the hardware section landing
- {doc}`/debug/bring-up` — the P2A cold-boot-into-DRAM chain referenced above
- {doc}`/drivers/linux` — the G3 VIC/clock driver work and the upstreaming shape
- {doc}`/systems/kgpe-d16` — the primary board carrying this SoC

**External references**

- [QEMU Aspeed SoC documentation](https://www.qemu.org/docs/master/system/arm/aspeed.html) — the Aspeed machine models (G4/G5 cousins of this G3 SoC)
- [ARM926EJ-S Technical Reference Manual](https://developer.arm.com/documentation/ddi0198/latest/) — the ARMv5TE CPU core at the heart of the AST2050
- [Linux Common Clock Framework](https://docs.kernel.org/driver-api/clk.html) — the clk framework the `clk-aspeed` driver plugs into
- [Linux IRQ handling (core API)](https://docs.kernel.org/core-api/irq/index.html) — the irqchip model behind the compact G3 VIC driver
