# Tim's Random Documentation for his Open BMC & Firmware

Read the Docs / Sphinx source for the open BMC & firmware program covering the
Aspeed AST2050 boards (ASUS KGPE-D16, Dell PowerEdge C410X) and the Digi NS9360
board (HPE iPDU AF531A).

Rendered: <https://bmc-open-firmware-docs.readthedocs.io/>.

## Build locally

```sh
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
sphinx-build -W -b html source _build/html      # HTML (warnings are errors)
sphinx-build -b linkcheck source _build/link    # link check
```

Open `_build/html/index.html`.

## Layout

```
source/
  index.md              landing + toctrees
  systems/              the three boards
  hardware/             SoC + peripheral register/interface reference
  emulation/            QEMU machines + test benches
  drivers/              Linux / U-Boot / Zephyr + upstream patch workflow
  firmware/             OpenBMC (Linux) + WallaBMC (Zephyr)
  debug/                JTAG/UART/SPI + hardware-in-the-loop
```

## Contributing

See {doc}`source/contributing`. Every page must be reachable from a `toctree`
and cross-references must resolve — the Read the Docs build fails on warnings.

## License

Apache-2.0 (code) / CC-BY-4.0 (documentation prose).
