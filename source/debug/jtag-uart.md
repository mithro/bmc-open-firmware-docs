# JTAG / UART / SPI

The AST2050 exposes an ARM926EJ-S EmbeddedICE-RT debug port (raw JTAG,
IDCODE `0x07926f0f`, 4-bit IR). A Raspberry Pi 4 wired to the board's debug
headers provides JTAG debug, a serial console, and SPI flash programming.

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
  - `AST_UART1` (4-pin)
  - 3.3V / TX / RX / GND, 115200 8N1
* - SPI flash
  - `BMC_FW1`
  - in-system SPI programming of the boot flash
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
`RPI4-OPENOCD-JTAG-WIRING.md` / `openocd/` reference and drive the HIL backend.
