# Test benches

Two layers of verification, sharing one philosophy: **the same test runs against
QEMU in CI and against real hardware on the bench.**

## Layer 1 — qtest (device-model correctness)

Per-component register-level benches live in the QEMU fork under
[`tests/qtest/`](https://github.com/mithro/qemu/tree/d16-ast2050-machine/tests/qtest) (C), run headless via `meson test --suite qtest` in the
`qemu-qtest` CI job. Each bench asserts:

- reset values of every documented register,
- read/write semantics and side effects (clear-on-read, write-1-to-clear),
- I2C addressing and mux gating.

A bench **fails** if a register returns the unimplemented-default where the
{doc}`../hardware/index` reference specifies a reset value — this is what
prevents "boots but silently incomplete" models.

## Layer 2 — `firmware-testbench` (integration, two backends)

A Python module abstracting a **`Target`** with a pluggable backend:

```{list-table}
:header-rows: 1
:widths: 20 40 40

* - Backend
  - Transport
  - Used by
* - `qemu`
  - `qemu-system-arm` + serial socket / hostfwd SSH
  - CI (every firmware job)
* - `hil`
  - RPi4/5 OpenOCD + UART + SPI rig
  - self-hosted runner on real boards
```

The `Target` exposes serial, SSH, `i2cdetect`, sensor (hwmon) reads, and GPIO
operations. Board-level benches — the C410X `i2cdetect` map
({doc}`../hardware/i2c-topology`), sensor reads, GPIO
presence lines, and the 12-step power-on sequence — are written **once** and run
against both backends. This is how QEMU and silicon are proven to behave
identically ({doc}`../debug/index`).

The existing bespoke harnesses ([`run-qemu.py`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/qemu-firmware/scripts/run-qemu.py), [`ssh-test.py`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/qemu-firmware/scripts/ssh-test.py), the NS9360
[`qemu_smoke_test.py`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/test/qemu_smoke_test.py)) are refactored onto this module so existing boot/SSH jobs
pass through it unchanged.

## Image verification (deliverable h)

Every firmware build job ends by booting its image through
`firmware-testbench --backend qemu --bench <board>` and asserting the board
bench (boot → SSH → Redfish → sensors → power). The identical command with
`--backend hil` gates promotion to real hardware.

## See also

**Related pages**

- {doc}`/emulation/qemu` — the QEMU machines the qtest benches exercise
- {doc}`/debug/index` — the real-hardware (HIL) side of the shared benches
- {doc}`/debug/jtag-uart` — the OpenOCD/UART rig behind the `hil` backend
- {doc}`/firmware/openbmc` — the board bench (boot → Redfish → sensors → power)
- {doc}`/hardware/index` — the register reset-values the qtest layer asserts

**External references**

- [QEMU `qtest` framework](https://www.qemu.org/docs/master/devel/testing/qtest.html) — the register-level device-model test protocol
- [QEMU testing guide](https://www.qemu.org/docs/master/devel/testing/index.html) — how QEMU's test suites are run
- [Meson unit tests](https://mesonbuild.com/Unit-tests.html) — the `meson test --suite qtest` runner
- [pytest documentation](https://docs.pytest.org/en/stable/) — the framework the `firmware-testbench` benches use
- [OpenOCD](https://openocd.org/) — the JTAG tool behind the HIL backend
