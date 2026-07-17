# Intel 82574L — host gigabit NICs with NC-SI sideband

## 1.1 Overview

The Intel **82574L** is a single-port PCIe (x1, Rev. 1.1) gigabit Ethernet
MAC+PHY in a 9 mm × 9 mm 64-pin QFN. [82574 DS §1.0 p.12](#sources) The
KGPE-D16 populates **two** of them as the host's LAN1/LAN2 ports — board
references **`LU1`** (LAN1) and **`LU2`** (LAN2), schematic part description
`WG82574L A1 QFN64//INTEL 898553/SLBA9`.
[QU1_pins.md:196-197](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/pinmaps/QU1_pins.md#L196-L197)

This page documents the part for its **BMC-relevant role only**: each 82574L
carries a manageability sideband — *"NC-SI or SMBus connection to a
Manageability Controller (MC)"*, with *"IPMI MC pass through; multi-drop
NC-SI"* [82574 DS §1.0 p.12](#sources) — and on this board the AST2050's
second RMII channel (RMII2) is **bussed to both NICs' NC-SI pins**, so the BMC
can share the host's network ports instead of (or in addition to) its
dedicated management PHY. The dedicated-PHY channel (RMII1 → Realtek RTL8201N,
{doc}`rtl8201n`) is a separate, point-to-point path and is not covered here.
General host-NIC features (descriptor rings, offloads, PCIe interface) are out
of scope — see the datasheet.

## 1.2 Board wiring — AST2050 RMII2 bussed to both NICs

The six RMII2 data/control nets leave the AST2050 (`QU1`) and land on **the
same pin of both `LU1` and `LU2`** — a multi-drop bus, not two point-to-point
links.
[AST2050-BMC-WIRING.md §7](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md#7-ethernet--dual-channel-dedicated-phy--nc-si-sideband)
[QU1_pins.md:205-219](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/pinmaps/QU1_pins.md#L205-L219)
The right-hand column gives the 82574L's own name for each QFN-64 pin, from
the datasheet pin table. [82574 DS §2.3.4 Table 10 p.23](#sources)

```{list-table} AST2050 RMII2 ↔ 82574L NC-SI pin map (netlist vs datasheet)
:header-rows: 1
:widths: 16 20 22 14 28

* - AST2050 ball
  - Ball name
  - Net
  - LU1/LU2 pin
  - 82574L pin name (direction)
* - A5
  - `MIIRXD2/RMII2RXD0/GPIOE2`
  - `AST_RMII2RXD0`
  - 6
  - `NC_SI_RXD0` (output — "Data signals to the Manageability Controller (MC)")
* - B5
  - `MIIRXD3/RMII2RXD1/GPIOE3`
  - `AST_RMII2RXD1`
  - 5
  - `NC_SI_RXD1` (output — data to the MC)
* - B6
  - `MIICRS/RMII2CRSDV/GPIOE6`
  - `AST_RMII2CRSDV`
  - 3
  - `NC_SI_CRS_DV` (output — "Carrier Sense/Receive Data Valid")
* - C4
  - `MIITXD2/RMII2TXD0/GPIOE0`
  - `R_AST_RMII2TXD0`
  - 9
  - `NC_SI_TXD0` (input — "Data signals from the MC")
* - D4
  - `MIITXD3/RMII2TXD1/GPIOE1`
  - `R_AST_RMII2TXD1`
  - 8
  - `NC_SI_TXD1` (input — data from the MC)
* - D5
  - `MIITXER/RMII2TXEN/GPIOE4`
  - `R_AST_RMII2TXEN`
  - 7
  - `NC_SI_TX_EN` (input)
```

Supporting details from the same netlist extract:

- **Reference clock.** The AST2050's RMII2 clock ball **B7** is fed by net
  `C_MNG_50M_AST_RMII2RXCLK` from clock generator **`CU2`**
  (ICS9112AM-16LFT).
  [QU1_pins.md:211](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/pinmaps/QU1_pins.md#L211)
  The datasheet requires the matching NIC-side input `NC_SI_CLK_IN` (pin 2) to
  be a *"synchronous clock reference … 50 MHz clock +/- 50 ppm"*, distributed
  to every device on the bus — exactly the buffered-clock arrangement Intel's
  multi-drop reference schematic shows. [82574 DS §2.3.4 p.23, §13.6.1.2
  p.456](#sources) (The BMC-side pin map does not trace the NIC-side clock
  net.)
- **No RX_ER.** The AST2050's `RMII2RXER` ball (A6) is **unconnected**.
  [QU1_pins.md:206](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/pinmaps/QU1_pins.md#L206)
  Consistently, the 82574L's NC-SI pin set defines no RX_ER output at all.
  [82574 DS §2.3.4 Table 10 p.23](#sources)
- **Per-NIC disable straps.** Super-I/O GPIOs `SIO_LAN1DISABLE#` (W83667HG-A
  GP37, pin 76) and `SIO_LAN2DISABLE#` (GP50, pin 75) run to `LU1`/`LU2`
  respectively, each via a `LAN_SW1`/`LAN_SW2` jumper — either NIC can be
  strapped off. The Super-I/O's `PME#` (pin 65) is bussed to both NICs and all
  PCIe slots.
  [W83667HG-SUPERIO-WIRING.md:209-211](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/W83667HG-SUPERIO-WIRING.md#L209-L211)

## 1.3 Sideband capability: NC-SI *or* SMBus — this board wires NC-SI

The critical question for an open BMC firmware is what protocol those pins
speak. The datasheet is explicit that the 82574L supports **both** sideband
protocols, but only one at a time:

> "The 82574L provides two different and mutually exclusive bus interfaces
> for manageability traffic. The first is the Intel® proprietary SMBus
> interface; … that operates at speeds of up to 400 KHz. The second interface
> is NC-SI, which is a new industry standard interface created by the DMTF
> specifically for routing manageability traffic to and from a MC. The NC-SI
> interface operates at 100 Mb/s full-duplex speeds."
> — [82574 DS §8.0 p.200](#sources)

> "Note that only one mode of sideband can be active at any given time. This
> configuration is done via an NVM setting."
> — [82574 DS §8.2 p.201](#sources)

NC-SI itself is the DMTF **DSP0222** standard: *"NC-SI uses a modified version
of the industry standard RMII interface for the physical layer as well as
defining a new logical layer."* [82574 DS §8.10 p.240](#sources)

**Verdict on the wiring label:** the schematic-wiring documents label this bus
"NC-SI", and the datasheet **confirms** it — every one of the six bussed nets
lands on a pin the datasheet names `NC_SI_*` (table above), the signal
directions match (NIC `NC_SI_RXD*`/`CRS_DV` outputs → BMC receive; BMC
transmit → NIC `NC_SI_TXD*`/`TX_EN` inputs), and the multi-drop two-NICs-on-
one-bus topology is only defined for NC-SI (SMBus pass-through is a separate
2-wire interface, and Intel's multi-drop reference design exists specifically
for NC-SI). [82574 DS §2.3.4 p.23, §13.6.1.2 p.456](#sources) No
contradiction — but note the wiring alone does not prove the sideband is
*enabled*: that depends on the NVM image in each NIC's flash/EEPROM (next
section), which has not been dumped in this program.

## 1.4 What the 82574L's NC-SI implementation provides

- **Compliance**: "The 82574L supports all the mandatory features of the
  NC-SI specification (rev 1.0.0a)." Supported commands include Clear Initial
  State, Get Version ID / Parameters / Link Status / Capabilities,
  Enable/Disable/Reset Channel, Enable/Disable VLAN and Broadcast, **Set MAC
  Address**, Set Link, AEN Enable, **Select/Deselect Package**,
  Enable/Disable Channel Network Tx, and OEM commands.
  [82574 DS §8.12.1 Table 71 p.245](#sources)
- **Capacities** (optional-features table): **one channel** per package
  (single-port device), **one MAC address filter** per port, two VLAN
  filters, broadcast filters for ARP/DHCP/NetBIOS, all-or-nothing multicast
  filtering, 7 KB buffering, **no NC-SI flow control** and — important for
  this board — **no NC-SI hardware arbitration**.
  [82574 DS Table 72 p.246](#sources)
- **Multi-drop implication.** `LU1` and `LU2` are two single-channel NC-SI
  *packages* on one bus. With hardware arbitration unsupported, only the
  MC-driven scheme remains: the BMC addresses each package by its Package ID
  and uses **Select Package / Deselect Package** so that exactly one package
  drives the shared RXD/CRS_DV lines at a time. [82574 DS §8.11.3.1 p.244,
  Table 71 p.245](#sources) Each NIC's Package ID comes from its own NVM
  (below), so the two NVM images must be programmed with distinct IDs for the
  bus to work.
- **Intel OEM NC-SI commands**: Get System MAC Address ("can be used for a
  shared MAC address mode"), Set/Get Intel Management Control, and TCO Reset.
  [82574 DS §8.12.2.1 p.246](#sources)

## 1.5 Manageability configuration (NVM) and traffic routing

How BMC traffic shares the port, per the datasheet:

- **Pass-through model.** "Pass-Through (PT) is the term used when referring
  to the process of sending and receiving Ethernet traffic over the sideband
  interface" — received frames can be "discarded, sent to host memory, sent
  to the external MC or to both the external MC and host memory."
  [82574 DS §8.2 p.200, §8.4.3 p.202](#sources)
- **Receive filtering.** In SMBus mode the filter set is RMCP/RMCP+ ports,
  flexible UDP/TCP port filters, 128-byte flexible filters, VLAN, IPv4/IPv6
  address and MAC address filters, steered by the MANC register
  (`RCV_TCO_EN`, `RCV_ALL`); the datasheet marks these SMBus-mode services as
  "not available in NC-SI mode" — in NC-SI mode the equivalent routing is
  configured through the NC-SI commands and filter capacities listed above
  (the BMC typically claims its own MAC address via *Set MAC Address*).
  [82574 DS §8.4.2-8.4.3 p.202, Table 72 p.246](#sources)
- **NVM configuration.** The sideband mode itself is an NVM (flash/EEPROM)
  setting [82574 DS §8.2 p.201](#sources), and the NC-SI/manageability
  firmware is *loaded from the NVM*: word `0x2A` points at the management
  (APT) firmware code, words `0x2B`/`0x2C` hold the firmware ID, word `0x2D`
  holds the NC-SI code size and RAM partitioning, and word `0x2E` carries the
  **NC-SI Package ID (bits 14:12)** plus the NC-SI code pointer.
  [82574 DS §6.2.1.6-6.2.2.4 p.127-128](#sources)

## 1.6 Access from the BMC side

The BMC end of this bus is the AST2050's second MAC (MAC2) with its pin-mux
set to RMII — the register-level programming model (MACCR, descriptor rings,
and the RMII/NC-SI mode selection) is documented in
{doc}`../registers/network-mac-phy`. Note there is no MDIO/MDC management pair
on this channel (NC-SI has no PHY-management wires; the netlist routes MDIO
only to the RTL8201N on channel 1), so link/speed handling follows the NC-SI
control protocol, not Clause-22 MDIO.
[QU1_pins.md:202-203](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/pinmaps/QU1_pins.md#L202-L203)

**Program status (honest):** NC-SI / shared-NIC operation has **not** been
brought up in this program — all BMC networking so far (Linux boot over NFS,
OpenBMC Redfish on silicon) runs over the dedicated RTL8201N port on MAC1.
Emulating true NC-SI (the 82574L's manageability engine behind the QEMU
`kgpe-d16-bmc` machine's second MAC) was assessed as out of scope for the
faithful QEMU model ({doc}`/emulation/qemu`). This section records the wiring
and datasheet facts a future bring-up would start from; nothing here has been
exercised on silicon.

## 1.7 Drivers

- **Host side**: the 82574L is driven by the mainline Linux
  [`e1000e`](https://github.com/torvalds/linux/tree/master/drivers/net/ethernet/intel/e1000e)
  driver (`drivers/net/ethernet/intel/e1000e`).
- **BMC side**: the AST2050 MAC uses
  [`ftgmac100.c`](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.c);
  for a shared-NIC configuration it would pair with the kernel's NC-SI stack
  ([`net/ncsi`](https://github.com/torvalds/linux/tree/master/net/ncsi),
  `CONFIG_NET_NCSI`, enabled per-MAC by the `use-ncsi` device-tree property).
  This combination is standard on later Aspeed BMCs but is untested on this
  board (see the status note above).

## See also

**Related pages**

- {doc}`/systems/kgpe-d16` — the board that populates `LU1`/`LU2`
- {doc}`/systems/kgpe-d16-wiring` — the full BMC wiring reference this page's netlist facts come from
- {doc}`rtl8201n` — the *other* BMC network channel (dedicated RTL8201N management PHY on MII/RMII1)
- {doc}`../registers/network-mac-phy` — the AST2050 MAC register model (BMC end of this bus)
- {doc}`index` — the peripheral catalogue

**External references**

- [DMTF DSP0222 1.0.1](https://www.dmtf.org/sites/default/files/standards/documents/DSP0222_1.0.1.pdf) — the NC-SI specification revision family the 82574L implements (datasheet states rev 1.0.0a)
- [DMTF DSP0222 1.1.1](https://www.dmtf.org/sites/default/files/standards/documents/DSP0222_1.1.1.pdf) — a later published NC-SI revision
- [Linux `e1000e`](https://github.com/torvalds/linux/tree/master/drivers/net/ethernet/intel/e1000e) — the host-side driver
- [Linux `net/ncsi`](https://github.com/torvalds/linux/tree/master/net/ncsi) — the kernel NC-SI protocol stack a BMC-side bring-up would use

## Sources

- **[Intel 82574 GbE Controller Family Datasheet](https://web.archive.org/web/20190710071029/https://www.intel.com/content/dam/doc/datasheet/82574l-gbe-controller-datasheet.pdf)**
  (revision 3.4, Intel document 317694; web.archive.org copy — Intel's
  original `intel.com/content/dam/doc/datasheet/82574l-gbe-controller-datasheet.pdf`
  URL now returns 404). Pin table §2.3.4 (p.23), manageability chapter §8
  (p.200-246), NVM map §6.2 (p.127-128), NC-SI design guidance §13.6 (p.455-456).
- **[`asus-kgpe-d16-firmware/schematic-wiring/`](https://github.com/mithro/ai-shenanigans-for-bmcs/tree/main/asus-kgpe-d16-firmware/schematic-wiring)** —
  the KGPE-D16 netlist extraction:
  [`AST2050-BMC-WIRING.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/AST2050-BMC-WIRING.md) §7 (Ethernet dual-channel),
  [`pinmaps/QU1_pins.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/pinmaps/QU1_pins.md) (per-ball nets, LU1/LU2 endpoints), and
  [`W83667HG-SUPERIO-WIRING.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/schematic-wiring/W83667HG-SUPERIO-WIRING.md) §7 (LAN-disable straps, PME#).
- **[DMTF DSP0222](https://www.dmtf.org/sites/default/files/standards/documents/DSP0222_1.0.1.pdf)** — Network Controller Sideband Interface (NC-SI) specification.
