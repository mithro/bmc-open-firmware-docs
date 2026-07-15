# U-Boot (bootloader)

Both firmware tracks boot through **U-Boot**: it is the stage between the SoC's
boot flash and the {doc}`OpenBMC <openbmc>` kernel or {doc}`WallaBMC <wallabmc>`
image, and a firmware deliverable in its own right. On the HPE iPDU it is more
than that — the stock NS9360 firmware is a NET+OS RTOS image, so the U-Boot port
*is* the first open firmware to run on that board at all.

## Role in the boot chain

- **AST2050 (KGPE-D16 / C410X)** — SPI-NOR boot flash → U-Boot → Linux kernel
  (+ initramfs or NFS root) → OpenBMC userspace. The same U-Boot provides the
  TFTP netboot path (`tftpboot` → `bootm`) used by the board's network-boot
  harness, and the bench recovery path: the P2A cold-boot sequence
  ({doc}`../debug/bring-up`) siphons U-Boot into DRAM and launches it on a
  board with no working firmware — proven on the real KGPE-D16, where the
  AST2050 U-Boot reaches an interactive `boot#` prompt.
- **NS9360 (HPE iPDU)** — the open-firmware path replaces the proprietary
  NET+OS image with the [`hpe-ipdu-port`](https://github.com/mithro/u-boot/tree/hpe-ipdu-port)
  U-Boot (serial, GPIO, clock, I2C, Ethernet, CFI NOR flash), which boots under
  the QEMU `ns9360` machine.

## Deliverables

```{list-table}
:header-rows: 1
:widths: 24 44 32

* - Target
  - Port
  - Status / acceptance
* - AST2050 boards
  - [`mithro/u-boot`](https://github.com/mithro/u-boot)`@ast2050-port` — mainline-track topic branch (AST2400 base
    adapted to the AST2050)
  - `boot-uboot-ssh` (U-Boot → Linux → SSH) green on the latest U-Boot;
    `c410x-tftp-netboot` network-boots the kernel to SSH
* - AST2050 boards (interim)
  - OpenBMC U-Boot `v2019.04-aspeed-openbmc` (`evb-ast2400` base)
  - builds and boots the chain in QEMU today
* - HPE iPDU
  - [`mithro/u-boot@hpe-ipdu-port`](https://github.com/mithro/u-boot/tree/hpe-ipdu-port) — open NS9360 port
  - boots under the QEMU `ns9360` machine; serial-socket smoke test passes
```

The porting detail — which drivers each branch carries and how the DRAM/SoC
init was derived — lives in {doc}`../drivers/uboot`.

## See also

**Related pages**

- {doc}`/drivers/uboot` — the U-Boot porting/driver notes behind these deliverables
- {doc}`/debug/bring-up` — the P2A cold-boot that loads U-Boot on a dead board
- {doc}`/emulation/qemu` — the QEMU machines the U-Boot chains boot in CI
- {doc}`/firmware/openbmc` — the Linux stack U-Boot hands over to
- {doc}`/firmware/wallabmc` — the Zephyr stack for the most constrained parts

**External references**

- [U-Boot documentation](https://docs.u-boot.org/en/latest/) — upstream U-Boot manual
- [U-Boot Aspeed board documentation](https://docs.u-boot.org/en/latest/board/aspeed/index.html) — the Aspeed (AST24xx base) board port the AST2050 branch adapts
