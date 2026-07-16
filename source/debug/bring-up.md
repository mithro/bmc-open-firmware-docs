# Silicon bring-up & out-of-band access

Reaching a "dead" AST2050 BMC — one with no working firmware in its boot flash —
without desoldering anything. Two independent access paths were brought up on a
real ASUS KGPE-D16 and cross-check each other; both are host-side and remote.

```{admonition} Status
:class: important

Everything on this page is hardware-verified against a real AST2050. The two
paths agree on the SoC revision register (`SCU7C = 0x00000202`) read
independently, which is the cross-check that each path is genuinely talking to
the silicon.
```

## Path 1 — P2A (PCIe-to-AHB), no debug hardware

```{figure} /_static/diagrams/ast2050-p2a-boot.svg
:alt: Ten-step P2A cold-boot flow — host drives the P2A window, enables the bridge, inits DDR2 over AHB, siphons the payload to 0x40000000, remaps DRAM to 0x0, freezes the ARM via SCU70, issues a watchdog HRST_N reset, re-applies the remap, and re-enables the ARM to run. DDR2 and the SCU survive the reset; the AHBC remap is cleared and re-applied.
:width: 100%

The P2A cold-boot sequence. Steps 6–8 highlight the reset behaviour: DDR2 and the
SCU survive the watchdog `HRST_N`, while the AHBC boot-remap is cleared and must
be re-applied before the ARM is released.
```

The AST2050's VGA/PCIe endpoint exposes a **P2A bridge** onto the BMC's internal
AHB bus. From the x86 host (booted into a rescue Linux) the
[`culvert`](https://github.com/mithro/culvert) tool — ported to recognise the G3
— drives that bridge to read and write BMC memory and registers directly. No
JTAG, no SPI flash emulator, no serial console is required.

That primitive is enough to **cold-boot the BMC from the host**, entirely over
P2A:

1. **Initialise DDR2** by replaying a faithful vendor init sequence over P2A
   (the 4-bank / 64 MiB / final-DLL-block corrections from
   {doc}`../hardware/soc-ast2050` are what make this reliable).
2. **Siphon a payload** (U-Boot, or a kernel + initramfs) into DRAM.
3. **Remap DRAM to `0x0`** and use the SoC's ARM-disable strap plus a watchdog
   `HRST_N` to hold the core at reset while the remap is set, then re-enable the
   core so it fetches the payload from DRAM.

This has booted, over P2A alone:

- the Raptor AST2050 **U-Boot** to an interactive `boot#` prompt;
- a modern **Linux 6.6** kernel to an NFS-root userspace with SSH; and
- `culvert` running **in-band** on the booted BMC (its `devmem` bridge verified:
  `SCU7C = 0x00000202`).

```{admonition} Why the ARM-disable dance
:class: note

Simply setting the remap while the core runs does not work — the ARM has already
slid off `0x0`. The reliable sequence disables the ARM via the SCU strap (which
survives `HRST_N` because the SCU is on a different reset domain), pulses the
watchdog reset, re-applies the DRAM remap, then re-enables the ARM so it fetches
its reset vector from DRAM. DDR2 and the SCU survive the reset; the x86 host
survives too because the VGA/PCIe endpoint is on a separate reset line.
```

## Path 2 — JTAG run-control

A Raspberry Pi 4 bit-bangs the ARM926EJ-S EmbeddedICE-RT port over its GPIO
header (`linuxgpiod`), giving true run-control: halt/resume, register and AHB
memory access, and even a DDR2 init driven from an OpenOCD `.tcl`. See
{doc}`jtag-uart` for wiring and OpenOCD invocation.

JTAG is valuable precisely *because* it is independent of P2A: when the two paths
report the same AHB register values, a finding is trustworthy. It also reaches
blocks P2A cannot — notably the interrupt-controller region at `0x1E6C0000`,
which the P2A "VGA" window filters to zero ({doc}`../drivers/linux`).

## The two access paths at a glance

```{list-table}
:header-rows: 1
:widths: 20 40 40

* - Path
  - Needs
  - Reaches
* - P2A
  - x86 host booted to rescue Linux; `culvert`
  - BMC DRAM, SCU, timers, MAC; can cold-boot the BMC. **Blind** to the VIC
    region.
* - JTAG
  - RPi4 on the ARM debug header; OpenOCD
  - full core run-control + all AHB, including the VIC region
```

## SPI flash

On a bench board with no serving firmware the SMC flash-read window returns zero
(the SMC is not clocked on a dead BMC), so flash **dumping** on such a board uses
an external SPI emulator ([spispy](https://github.com/osresearch/spispy) on an
FPGA) rather than P2A. Once the BMC runs
the program's own firmware, in-band flash access via `culvert` becomes available.

## See also

**Related pages**

- {doc}`/debug/jtag-uart` — the JTAG run-control path in detail (wiring, OpenOCD)
- {doc}`/hardware/soc-ast2050` — the DDR2 init corrections that make P2A boot reliable
- {doc}`/systems/kgpe-d16` — the board these two access paths were verified on
- {doc}`/drivers/linux` — the VIC blind-spot lesson (P2A reads zero at `0x1E6C0000`)
- {doc}`/firmware/openbmc` — the OpenBMC image booted over P2A on silicon

**External references**

- [`culvert` (upstream)](https://github.com/amboar/culvert) — the Aspeed AHB-bridge tool, upstream of the G3-ported fork
- [OpenOCD](https://openocd.org/) — the JTAG run-control tool for the second access path
- [ARM9 processor family](https://en.wikipedia.org/wiki/ARM9) — the ARM926EJ-S core and its EmbeddedICE-RT debug
