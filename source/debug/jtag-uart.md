# JTAG / UART / SPI

The AST2050 exposes an ARM926EJ-S EmbeddedICE-RT debug port (raw JTAG,
IDCODE `0x07926f0f`, 4-bit IR). A Raspberry Pi 4 wired to the board's debug
headers provides JTAG debug, a serial console, and SPI flash programming.

```{admonition} Status — JTAG run-control is hardware-verified
:class: important

Full JTAG run-control works on a real AST2050 over RPi4 bit-bang (`linuxgpiod`):
IDCODE `0x07926f0f`, RTCK echo 64/64, halt/resume, and AHB memory access over
JTAG (`SCU7C` reads `0x00000202`, matching the P2A path independently). DDR2 can
even be initialised over JTAG. JTAG is a second, independent access path to the
BMC alongside P2A — see {doc}`bring-up`.
```

## Connections (KGPE-D16)

```{list-table}
:header-rows: 1
:widths: 30 35 35

* - Function
  - Header
  - Notes
* - BMC JTAG
  - `AST_JTAG1` (20-pin ARM)
  - TCK/TMS/TDI/TDO/nTRST/nSRST; 3.3 V only
* - Console
  - BMC UART (4-pin), 3.3 V / TX / RX / GND
  - Wired to the SoC **UART2** (`0x1E784000` = Linux `ttyS1`). Baud is a
    documented discrepancy — see the note below.
* - SPI flash
  - `BMC_FW1`
  - in-system SPI programming of the boot flash
```

```{admonition} Console baud — a known discrepancy
:class: warning

The KGPE-D16 BMC console is SoC UART2 (`ttyS1`). Its baud is **not settled**: the
Raptor firmware configures **115200** (`console=ttyS1,115200`; 38400 for the
DRAM-init debug path), but the rig bring-up over P2A observed the console at
**1200**. If the console reads as garbage, try both rates
(`stty -F <dev> 115200` / `1200`). Full detail: {doc}`../systems/kgpe-d16` §2.2.
```

```{admonition} Electrical safety
:class: warning

Both sides are 3.3 V; the RPi4 is **not** 5 V tolerant. Verify header pin 1 /
VTref (~3.3 V) before connecting, wire ground first, keep leads short, and start
JTAG at ~100 kHz.
```

## OpenOCD

The program ships verified OpenOCD configs (`ast2050.cfg`, `rpi4-jtag.cfg`,
board `.cfg`) using the `linuxgpiod` bit-bang driver. The NS9360 (iPDU) has an
equivalent J1–J6 header set and its own config.

```sh
# Scan the JTAG chain to verify wiring:
sudo openocd -f rpi4-jtag.cfg -f ast2050.cfg -c "init; scan_chain; shutdown"
```

These configs and the wiring detail are maintained in the program's
[`RPI4-OPENOCD-JTAG-WIRING.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/RPI4-OPENOCD-JTAG-WIRING.md) / `openocd/` reference and drive the HIL backend.

## See also

**Related pages**

- {doc}`/debug/bring-up` — the two independent access paths (P2A + JTAG) overview
- {doc}`/systems/kgpe-d16` — the AST2050 header pinouts and RPi4 wiring in full
- {doc}`/systems/hpe-ipdu` — the NS9360 J1–J6 debug/JTAG header set
- {doc}`/hardware/registers/uart-vic-timers` — the UART instance / `ttyS1` detail
- {doc}`/emulation/testbench` — the HIL backend these OpenOCD configs drive

**External references**

- [OpenOCD](https://openocd.org/) — the on-chip debugger used with the `linuxgpiod` bit-bang driver
- [OpenOCD User Guide](https://openocd.org/doc/html/index.html) — adapter drivers, `scan_chain`, and reset handling
- [ARM9 processor family](https://en.wikipedia.org/wiki/ARM9) — the ARM926EJ-S core and its EmbeddedICE-RT (raw-JTAG) debug
