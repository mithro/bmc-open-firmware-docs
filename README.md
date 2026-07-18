# Tim's Random Documentation for his Open BMC & Firmware

Read the Docs / Sphinx source for the open BMC & firmware program covering the
Aspeed AST2050 boards (ASUS KGPE-D16, Dell PowerEdge C410X) and the Digi NS9360
board (HPE iPDU AF531A).

Rendered: <https://bmc-open-firmware-docs.readthedocs.io/>. Every pushed
branch is also published as its own live version, and pull requests get a
preview build linked from their status checks.

## Build locally

```sh
uv run --with-requirements requirements.txt sphinx-build -M html source _build -W --keep-going
uv run --with-requirements requirements.txt sphinx-build -M linkcheck source _build
```

Open `_build/html/index.html`.

## Layout

```
source/
  index.md              landing + toctrees
  systems/              the three boards; KGPE-D16 also has schematic-derived
                        wiring, I2C-topology, and connector pin-out pages
  hardware/             SoC + peripheral reference
    soc-*.md              AST2050 and NS9360 SoC overviews
    registers/            AST2050 register-block reference
    peripherals/          per-IC register pages (W83795G, W83667HG-A,
                          RTL8201N, 82574L, PEX8696, ...)
  emulation/            QEMU machines + test benches
  drivers/              Linux / U-Boot / Zephyr + upstream patch workflow
  firmware/             OpenBMC (Linux) + WallaBMC (Zephyr)
  debug/                JTAG/UART/SPI + hardware-in-the-loop
  linking.md            linking & citation policy for doc authors
  references.md         external reference material
```

## CI

Every push runs the GitHub Actions `docs` workflow: the Sphinx HTML build with
warnings-as-errors, then the external link check. `source/conf.py` documents
the linkcheck ignore classes (JS-rendered GitHub `#Lnn` line anchors, hosts
that throttle or bot-block CI runners). Pull requests from branches in this
repo are covered by the push-triggered run; the `pull_request` job only runs
for fork PRs.

## Contributing

See [`source/contributing.md`](source/contributing.md). Every page must be
reachable from a `toctree` and cross-references must resolve — the build fails
on warnings. Links and citations follow the policy in
[`source/linking.md`](source/linking.md).

## License

Apache-2.0 (code) / CC-BY-4.0 (documentation prose).
