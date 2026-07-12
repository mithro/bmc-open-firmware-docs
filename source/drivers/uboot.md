# U-Boot

## AST2050 (KGPE-D16 / C410X)

The target is mainline U-Boot on the latest tag/master, with an `ast2050-port`
topic branch in `mithro/u-boot` that adapts the Aspeed AST2400 base to the
AST2050 (DRAM/SoC init ported from the board's low-level [`platform.S`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/platform.S)).

- **Interim:** the OpenBMC U-Boot (`v2019.04-aspeed-openbmc`, `evb-ast2400`
  base) already builds and boots the chain in QEMU.
- **TFTP netboot:** the full network-boot path (`tftpboot` → `bootm`) is verified
  in QEMU with a slirp TFTP server and mirrored on real hardware by the board's
  TFTP boot harness.

**Acceptance:** `boot-uboot-ssh` (U-Boot → Linux → SSH) stays green on the latest
U-Boot, and a `c410x-tftp-netboot` job network-boots the kernel to SSH.

## NS9360 (iPDU)

`mithro/u-boot@hpe-ipdu-port` is an open NS9360 port (serial, GPIO, clock, I2C,
Ethernet, CFI NOR flash) that boots under the QEMU `ns9360` machine and passes a
serial-socket smoke test. It is rebased onto latest U-Boot alongside the AST2050
branch.
