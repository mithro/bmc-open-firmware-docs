# Drivers

Driver work for the three software stacks — Linux, U-Boot, and Zephyr — plus the
patch-series and rebase workflow that keeps everything on latest upstream while
staying cleanly upstreamable.

```{toctree}
:maxdepth: 1

peripheral-map
driver-reference
linux
uboot
zephyr
```

## Upstream patch-series & rebase workflow

All upstream-track work lives in public forks
([`mithro/linux`](https://github.com/mithro/linux),
[`mithro/u-boot`](https://github.com/mithro/u-boot),
[`mithro/qemu`](https://github.com/mithro/qemu),
[`mithro/zephyr`](https://github.com/mithro/zephyr)) as **one topic branch per
subsystem**, each a
clean, small, rebasable `git format-patch` series on top of upstream. The
program tracks **two variants of every stack simultaneously**:

- a **`…-stable`** variant on the latest upstream *release tag*, and
- a **`…-master`** variant on upstream *master HEAD*.

A scheduled rebase bot rebases both variants onto new upstream, regenerates the
applied `*.patch` files, re-runs the boot/bench suite, and opens a PR on any
conflict or regression. Upstream PRs are **never** opened automatically.

```{admonition} Why two variants
:class: note

The stable variant is what firmware images ship against; the master variant
surfaces upstream breakage early so the series stays upstreamable across the
multi-year effort. The applied patches in the program repo are always
*generated* from the fork branches, never hand-edited.
```
