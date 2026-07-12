# AST2050 networking: MAC, MDIO/MII & PHY

Register-by-register reference for the Aspeed **AST2050 / AST1100 (G3)** networking
subsystem: the two Faraday **FTGMAC100** 10/100 Ethernet MAC modules, their built-in
**MDIO/MII management interface**, and a representative external PHY (the Realtek
**RTL8201CP** RMII 10/100 transceiver used on the KGPE-D16 BMC).

Every register field below is cross-referenced against **at least two independent
sources**: the Aspeed AST2050/AST1100 A3 datasheet (the hardware authority), the
mainline Linux [`ftgmac100`](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.c) driver / register header (the software view of the *same*
Faraday IP block), the Realtek RTL8201CP datasheet (for the PHY), and the project's
own reverse-engineering notes captured on real AST2050 hardware. Divergences between
the Aspeed datasheet and the generic Faraday header are called out explicitly because
they matter for a faithful re-implementation.

Citation keys:

- `[DS §x p.N](#sources)` — *ASPEED AST2050/AST1100 A3 Datasheet V1.05* (2010-05-25), the
  in-repo PDF (`datasheets/aspeed/AST2050_AST1100_A3_Datasheet_V1.05.pdf`, titled
  "AST1100 Software Programming Guide").
- `[ftgmac100.h](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.h)` / `[ftgmac100.c](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.c)` — mainline Linux
  `drivers/net/ethernet/faraday/ftgmac100.{h,c}`.
- `[RTL8201CP DS §x p.N](#sources)` — *Realtek RTL8201CP Single-Chip/Port 10/100 Fast Ethernet
  PHYceiver Datasheet*, Track ID JATR-1076-21 Rev. 1.24.
- Repo file references are given by path under the private analysis repo
  `ai-shenanigans-for-bmcs/`.

Full source list in [Sources](#sources).

---

## 1. Overview and address map

The AST2050 integrates **two identical** 10/100 Ethernet MAC modules. They are
enabled/disabled independently and differ only in base address. Each is a Faraday
FTGMAC100 IP block; the AST2050 datasheet documents a *superset* register map
(1000 Mbps / GMII fields are present in the definitions but **only 10/100 is
supported** on this chip). [DS §14.1 p.124](#sources)

:::{list-table} MAC module address & interrupt map
:header-rows: 1
:widths: 22 20 14 14 30

* - Module (datasheet / Linux)
  - Base address
  - Window size
  - Interrupt
  - Notes
* - MAC #1 / `mac0`
  - `0x1E66_0000`
  - 128 KiB (`0x1E66_0000`–`0x1E67_FFFF`)
  - VIC IRQ 2 (high-level)
  - `AST_MAC1_BASE` in repo [`hwreg.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h)
* - MAC #2 / `mac1`
  - `0x1E68_0000`
  - 128 KiB (`0x1E68_0000`–`0x1E69_FFFF`)
  - VIC IRQ 3 (high-level)
  - `AST_MAC2_BASE` in repo [`hwreg.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h)
:::

- Base addresses: [DS §14.3 p.125](#sources), memory map [DS §9 p.? "1E66:0000 … Fast Ethernet
  MAC Controller #1"], repo `asus-kgpe-d16-firmware/hwreg.h` (`AST_MAC1_BASE
  0x1E660000`, `AST_MAC2_BASE 0x1E680000`).
- Interrupts: VIC IRQ 2 = "MAC1 interrupt", IRQ 3 = "MAC2 interrupt", both
  *sensitive high-level trigger* [DS §16 interrupt table p.? "MAC1/MAC2 interrupt"](#sources);
  the Raptor port maps these as `IRQ 2: MAC0`, `IRQ 3: MAC1`
  (`asus-kgpe-d16-firmware/RAPTOR-PORTING-GUIDE.md`).
- Physical address = base + offset. [DS §14.3 p.125](#sources)
- Only **one GMII** interface exists (pin-count limited), so if GMII were used only
  one MAC could be enabled — moot on AST2050 which is 10/100 only. [DS §14.1 p.124](#sources)

Feature summary [DS §14.2 p.124]: dual IEEE 802.3 MAC; MII×1 / RMII×2 (GMII×1 in the
superset); AHB bus-master + slave; integrated link-list DMA engine with direct M-Bus
access; 802.1Q VLAN insert/delete; high-priority TX queue (QoS/CoS); independent
TX/RX FIFO; half & full duplex; flow control (full duplex) and back-pressure (half
duplex). The Faraday IP is the same block mainline Linux drives as
`faraday,ftgmac100` / `aspeed,ast2400-mac`; the AST2050 DT uses
`compatible = "aspeed,ast2050-mac", "faraday,ftgmac100"`
(`asus-kgpe-d16-firmware/RAPTOR_ENGINEERING_AST2050_ANALYSIS.md`).

---

## 2. Full MAC register map (offset 0x00–0xC8)

Reset ("Init") values and access are from the datasheet register definitions
[DS §14.3 p.125–143](#sources); the offset/name column is cross-checked against `[ftgmac100.h](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.h)`
`FTGMAC100_OFFSET_*` (which describes the identical Faraday IP). Where the Faraday
header and the AST2050 datasheet **disagree**, the datasheet governs for AST2050 and
the divergence is footnoted.

:::{list-table} FTGMAC100 register map — MAC base + offset
:header-rows: 1
:widths: 8 16 12 8 40 16

* - Offset
  - Datasheet name
  - Reset
  - Access
  - Description
  - [`ftgmac100.h`](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.h)
* - `0x00`
  - ISR
  - `0x0`
  - RW
  - Interrupt Status Register (write-1-to-clear). See §3.
  - `OFFSET_ISR`
* - `0x04`
  - IER / IME
  - `0x0`
  - RW
  - Interrupt Enable Register (per-ISR-bit enables). See §3.
  - `OFFSET_IER`
* - `0x08`
  - MAC MADR
  - `0x0`
  - RW
  - MAC Most-Significant Address Reg — top 2 bytes of MAC address in [15:0]; [31:16] reserved.
  - `OFFSET_MAC_MADR`
* - `0x0C`
  - MAC LADR
  - `0x0`
  - RW
  - MAC Least-Significant Address Reg — low 4 bytes of MAC address.
  - `OFFSET_MAC_LADR`
* - `0x10`
  - MAHT0
  - `0x0`
  - RW
  - Multicast Address Hash Table 0 (hash bits 31:0).
  - `OFFSET_MAHT0`
* - `0x14`
  - MAHT1
  - `0x0`
  - RW
  - Multicast Address Hash Table 1 (hash bits 63:32).
  - `OFFSET_MAHT1`
* - `0x18`
  - NPTXPD
  - `0x0`
  - W
  - Normal-Priority TX Poll Demand — any write makes the engine fetch the NP TX descriptor and check TXDMA OWN. Reads as 0.
  - `OFFSET_NPTXPD`
* - `0x1C`
  - RXPD
  - `0x0`
  - W
  - RX Poll Demand — any write makes the engine fetch the RX descriptor and check RXPKT RDY. Reads as 0.
  - `OFFSET_RXPD`
* - `0x20`
  - NPTXR BADR
  - `0x0`
  - RW
  - Normal-Priority TX Ring Base Address; bits [27:4] used, 16-byte aligned; [31:28],[3:0] reserved.
  - `OFFSET_NPTXR_BADR`
* - `0x24`
  - RXR BADR
  - `0x0`
  - RW
  - RX Ring Base Address; bits [27:4], 16-byte aligned; [31:28],[3:0] reserved.
  - `OFFSET_RXR_BADR`
* - `0x28`
  - HPTXPD
  - `0x0`
  - W
  - High-Priority TX Poll Demand (write-triggers; reads 0).
  - `OFFSET_HPTXPD`
* - `0x2C`
  - HPTXR BADR
  - `0x0`
  - W
  - High-Priority TX Ring Base Address; bits [27:4], 16-byte aligned.
  - `OFFSET_HPTXR_BADR`
* - `0x30`
  - ITC
  - `0x0`
  - RW
  - Interrupt Timer Control (TX/RX interrupt mitigation). Recommended `0x0000_1010`. See §4.
  - `OFFSET_ITC`
* - `0x34`
  - APTC
  - `0x0`
  - RW
  - Automatic Polling Timer Control. Recommended `0x0000_0001`. See §4.
  - `OFFSET_APTC`
* - `0x38`
  - DBLAC
  - `0x0002_2F00`
  - RW
  - DMA Burst Length & Arbitration Control (descriptor sizes, burst sizes, RX-FIFO threshold arb). Recommended `0x0002_2F72`. See §4.
  - `OFFSET_DBLAC`
* - `0x3C`
  - DMAFIFOS
  - `0x0C00_0000`
  - R
  - DMA/FIFO State (debug: DMA req/grant, FIFO empty, TX/RX DMA state machines).
  - `OFFSET_DMAFIFOS`
* - `0x40`
  - *(reserved on AST2050)*
  - —
  - —
  - Not defined in the AST2050 register list. Faraday header names it `REVR` (revision).
  - `OFFSET_REVR`
* - `0x44`
  - FEAR
  - `0x0`
  - R
  - Feature Register — real TX FIFO size [5:3], RX FIFO size [2:0] (`000` = 2K default). Read before sizing FIFOs.
  - `OFFSET_FEAR`
* - `0x48`
  - TPAFCR
  - `0x0000_00F1`
  - RW
  - TX Priority Arbitration & FIFO Control (TX/RX FIFO size, early TX/RX thresholds, HP/NP packet thresholds).
  - `OFFSET_TPAFCR`
* - `0x4C`
  - RBSR
  - `0x0000_0640`
  - RW
  - Receive Buffer Size; bits [13:3], 8-byte aligned, unit 1 byte.
  - `OFFSET_RBSR`
* - `0x50`
  - **MACCR**
  - `0x0`
  - RW
  - **MAC Control Register** — reset, speed, duplex, RX/TX MAC & DMA enables, filtering. See §5 (full bitfields).
  - `OFFSET_MACCR`
* - `0x54`
  - MACSR
  - `0x0`
  - RW
  - MAC Status Register (collision / TX-OK / RX status, write-1-to-clear). See §6.
  - `OFFSET_MACSR`
* - `0x58`
  - TM
  - `0x0`
  - RW
  - Test Mode Register (polling/interrupt-timer test, collision test, backoff).
  - `OFFSET_TM`
* - `0x60`
  - **PHYCR**
  - `0x0000_0034`
  - RW
  - **PHY Control Register** — MDIO read/write trigger, PHY/register address, MDC threshold. See §7.
  - `OFFSET_PHYCR`
* - `0x64`
  - **PHYDATA**
  - `0x0`
  - RW/R
  - **PHY Data Register** — MIIRDATA[31:16] (R), MIIWDATA[15:0] (RW). See §7.
  - `OFFSET_PHYDATA`
* - `0x68`
  - FCR
  - `0x0000_0400`
  - RW
  - Flow Control Register (pause time, thresholds, TX/RX pause). See §8.
  - `OFFSET_FCR`
* - `0x6C`
  - BPR
  - `0x0000_0200`
  - RW
  - Back Pressure Register (half-duplex jam). See §8.
  - `OFFSET_BPR`
* - `0x70`
  - PWRTC
  - `0x0`
  - RW
  - Power Control (bit 18 `SW_PDNPHY` software power-down PHY; bit 15 `PWRSAV`). **Datasheet-only — see note.**
  - *(header: `WOLCR`)*
* - `0x74`–`0x8C`
  - *(reserved on AST2050)*
  - —
  - —
  - Not defined in the AST2050 register list. Faraday header uses these for Wake-on-LAN (`WOLSR`, `WFCRC`, `WFBM1..4`). **See note.**
  - `OFFSET_WOLSR…WFBM4`
* - `0x90`
  - NPTXR PTR
  - `X`
  - R
  - Normal-Priority TX Ring Pointer (debug).
  - `OFFSET_NPTXR_PTR`
* - `0x94`
  - HPTXR PTR
  - `X`
  - R
  - High-Priority TX Ring Pointer (debug).
  - `OFFSET_HPTXR_PTR`
* - `0x98`
  - RXR PTR
  - `X`
  - R
  - RX Ring Pointer (debug).
  - `OFFSET_RXR_PTR`
* - `0xA0`
  - TPKT CNT
  - `0x0`
  - R
  - TX packets transmitted OK (debug counter).
  - `OFFSET_TX`
* - `0xA4`
  - TXMCOL/TXSCOL
  - `0x0`
  - R
  - [31:16] multi-collision TX-OK, [15:0] single-collision TX-OK (debug).
  - `OFFSET_TX_MCOL_SCOL`
* - `0xA8`
  - TXECOL/TXFAIL
  - `0x0`
  - R
  - [31:16] TXFAIL (late/≥16 col/underrun), [15:0] TXECOL (≥16 collisions) (debug).
  - `OFFSET_TX_ECOL_FAIL`
* - `0xAC`
  - TXUNDERUN/TXLCOL
  - `0x0`
  - R
  - [31:16] TX underrun fails, [15:0] late-collision fails (debug).
  - `OFFSET_TX_LCOL_UND`
* - `0xB0`
  - RPKT CNT
  - `0x0`
  - R
  - RX packets received OK (debug).
  - `OFFSET_RX`
* - `0xB4`
  - BROPKT CNT
  - `0x0`
  - R
  - RX broadcast packets (debug).
  - `OFFSET_RX_BC`
* - `0xB8`
  - MULPKT CNT
  - `0x0`
  - R
  - RX multicast packets (debug).
  - `OFFSET_RX_MC`
* - `0xBC`
  - RPF/AEP CNT
  - `0x0`
  - R
  - [31:16] RX pause frames, [15:0] alignment-error packets (debug).
  - `OFFSET_RX_PF_AEP`
* - `0xC0`
  - RUNT CNT
  - `0x0`
  - R
  - RX runt packets [15:0] (debug).
  - `OFFSET_RX_RUNT`
* - `0xC4`
  - CRCER/FTL CNT
  - `0x0`
  - R
  - [31:16] CRC-error packets, [15:0] frame-too-long packets (debug).
  - `OFFSET_RX_CRCER_FTL`
* - `0xC8`
  - RLOST/RCOL CNT
  - `0x0`
  - R
  - [31:16] RX lost (FIFO full), [15:0] RX collision (debug).
  - `OFFSET_RX_COL_LOST`
:::

Sources for the whole table: [DS §14.3 p.125–143](#sources) and `[ftgmac100.h](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.h)`.

:::{note}
**Register-map divergences between the AST2050 datasheet and the Faraday header.**

- **`0x40`** — the AST2050 register list has no `0x40` entry (jumps `0x3C` → `0x44`);
  `[ftgmac100.h](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.h)` names it `REVR`. Treat as undocumented/reserved on AST2050.
- **`0x70`** — the AST2050 datasheet defines `0x70` as **PWRTC** (Power Control:
  `SW_PDNPHY` bit 18, `PWRSAV` bit 15) [DS §14.3 p.141](#sources). The Faraday header labels
  `0x70` `WOLCR` (Wake-on-LAN Control) and `0x74`–`0x8C` as the WOL block. The
  AST2050 register list does **not** define `0x74`–`0x8C` at all. For a faithful
  AST2050 model, follow the datasheet (PWRTC at `0x70`, `0x74`–`0x8C` reserved).
:::

### 2.1 Descriptor rings (referenced by the BADR registers)

The BADR registers point to descriptor rings in system memory; each descriptor is
16 bytes. Key ownership/ring bits (needed when auditing a live ring over P2A/JTAG):

:::{list-table} Descriptor word 0 key bits
:header-rows: 1
:widths: 14 16 14 56

* - Descriptor
  - Field
  - Bit
  - Meaning
* - TXDES#0 (`0x00`)
  - TXDMA OWN
  - 31
  - 1 = owned by MAC engine; MAC clears it when TX of the frame completes.
* - TXDES#0
  - EDOTR
  - 30
  - End Descriptor Of transmit Ring (wrap marker).
* - TXDES#0
  - FTS / LTS
  - 29 / 28
  - First / Last transmit segment of a packet.
* - TXDES#0
  - TXBUF SIZE
  - 13:0
  - Transmit buffer size in bytes (non-zero).
* - TXDES#3 (`0x0C`)
  - TXBUF BADR
  - 27:1
  - Transmit buffer base address (≥ 2-byte aligned; bit 0 = 0).
* - RXDES#0 (`0x00`)
  - RXPKT RDY
  - 31
  - 0 = owned by MAC engine; MAC **sets** it when a frame is received / buffer full.
* - RXDES#0
  - EDORR
  - 30
  - End Descriptor Of Receive Ring (wrap marker).
* - RXDES#0
  - FRS / LRS
  - 29 / 28
  - First / Last receive segment.
:::

Descriptor bit definitions: [DS §14.4.1 TXDES p.144–145](#sources), [DS §14.4.2 RXDES p.146](#sources).
The `OWN`/`EDOTR` semantics were used directly in the project's on-hardware TX-ring
probe (`asus-kgpe-d16-firmware/NIC-MAC-REGISTER-COMPARISON.md`, "TX descriptor ring
probe" section — U-Boot's 1-descriptor ring with `EDOTR` set, `OWN=SW`).

---

## 3. Interrupt Status (ISR, `0x00`) & Interrupt Enable (IER, `0x04`)

ISR bits are **write-1-to-clear**. IER `0x04` holds one enable bit per ISR bit at the
same bit position (e.g. IER[10] enables ISR[10]). [DS §14.3 p.125–126](#sources)

:::{list-table} MAC00 ISR / MAC04 IER bitfields
:header-rows: 1
:widths: 10 26 64

* - Bit
  - Name (ISR / IER)
  - Meaning (ISR); IER[n] = interrupt-enable for ISR[n]
* - 31:11
  - Reserved (0)
  - —
* - 10
  - HPTXBUF UNAVA
  - High-priority transmit buffer unavailable.
* - 9
  - PHYSTS CHG
  - PHY link status change.
* - 8
  - AHB ERR
  - AHB bus error.
* - 7
  - TPKT LOST
  - TX packet lost (late/excessive collision or under-run).
* - 6
  - NPTXBUF UNAVA
  - Normal-priority transmit buffer unavailable.
* - 5
  - TPKT2F
  - TXDMA moved data into the TX FIFO.
* - 4
  - TPKT2E
  - Packet transmitted to Ethernet successfully.
* - 3
  - RPKT LOST
  - Received packet lost (RX FIFO full).
* - 2
  - RXBUF UNAVA
  - Receiving buffer unavailable.
* - 1
  - RPKT2F
  - Packet received into RX FIFO successfully.
* - 0
  - RPKT2B
  - RXDMA delivered packet(s) to RX buffer successfully.
:::

[DS §14.3 p.125–126](#sources). The Faraday driver programs the same enables in `IER`
(`FTGMAC100_INT_*` in `[ftgmac100.c](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.c)`); bit positions are identical.

---

## 4. Timer / DMA-arbitration control registers

### 4.1 ITC — Interrupt Timer Control (`0x30`, reset 0, recommended `0x0000_1010`)

Interrupt mitigation: batch TX/RX interrupts by a threshold count and a timer. [DS
§14.3 p.128–130]

:::{list-table} MAC30 ITC bitfields
:header-rows: 1
:widths: 12 24 64

* - Bit
  - Field
  - Meaning
* - 31:16
  - Reserved (0)
  - —
* - 15
  - TXINT TIME SEL
  - TX cycle-time select. Set → 81.92 µs (100M) / 819.2 µs (10M); clear → 5.12 µs (100M) / 51.2 µs (10M).
* - 14:12
  - TXINT THR
  - Max pending TX interrupts before one is generated; if `!=0`, IRQ when TX-packet count reaches it.
* - 11:8
  - TXINT CNT
  - Max wait (in TX cycle times) to issue TX IRQ after a packet; 0 = disabled.
* - 7
  - RXINT TIME SEL
  - RX cycle-time select (same values as TX).
* - 6:4
  - RXINT THR
  - Max pending RX interrupts before one is generated.
* - 3:0
  - RXINT CNT
  - Max wait (in RX cycle times) to issue RX IRQ after a packet; 0 = disabled.
:::

When both THR and CNT are 0, TX interrupting is governed by `TXIC` in TXDES#1. [DS
§14.3 p.128–130]

### 4.2 APTC — Automatic Polling Timer Control (`0x34`, reset 0, recommended `0x0000_0001`)

Lets the engine auto-poll descriptors instead of relying on poll-demand writes. [DS
§14.3 p.131]

:::{list-table} MAC34 APTC bitfields
:header-rows: 1
:widths: 12 24 64

* - Bit
  - Field
  - Meaning
* - 31:13
  - Reserved (0)
  - —
* - 12
  - TXPOLL TIME SEL
  - TX poll-time select (set → 81.92 µs/100M, 819.2 µs/10M; clear → 5.12 µs/100M, 51.2 µs/10M).
* - 11:8
  - TXPOLL CNT
  - TX auto-poll period (unit = 1 TX poll time); 0 = no auto-poll of TX descriptor.
* - 7:5
  - Reserved (0)
  - —
* - 4
  - RXPOLL TIME SEL
  - RX poll-time select (same values).
* - 3:0
  - RXPOLL CNT
  - RX auto-poll period; 0 = no auto-poll of RX descriptor.
:::

[DS §14.3 p.131](#sources)

### 4.3 DBLAC — DMA Burst Length & Arbitration (`0x38`, reset `0x0002_2F00`, recommended `0x0002_2F72`)

:::{list-table} MAC38 DBLAC bitfields
:header-rows: 1
:widths: 12 22 66

* - Bit
  - Field
  - Meaning
* - 31:24
  - Reserved (0)
  - —
* - 23
  - IFG INC
  - Inter-frame-gap increase (1) / decrease (0).
* - 22:20
  - IFG CNT
  - IFG adjust count; unit = 1 TX clock (40 ns @100M, 400 ns @10M).
* - 19:16
  - TXDES SIZE
  - Transmit descriptor size; unit 8 bytes; writing 0 illegal.
* - 15:12
  - RXDES SIZE
  - Receive descriptor size; unit 8 bytes; writing 0 illegal.
* - 11:10
  - TXBST SIZE
  - TXDMA max burst: 00=64B, 01=128B, 10=256B, 11=512B.
* - 9:8
  - RXBST SIZE
  - RXDMA max burst: 00=64B, 01=128B, 10=256B, 11=512B.
* - 7
  - Reserved (0)
  - —
* - 6
  - RX THR EN
  - Enable RX-FIFO threshold arbitration between RXDMA and TXDMA.
* - 5:3
  - RXFIFO HTHR
  - RX-FIFO high threshold (n/8 of FIFO) — RXDMA gets priority above it.
* - 2:0
  - RXFIFO LTHR
  - RX-FIFO low threshold — TXDMA regains priority at/below it (must be `< HTHR`).
:::

[DS §14.3 p.132–133](#sources). `DMAFIFOS` (`0x3C`, reset `0x0C00_0000`, read-only) exposes the
TX/RX DMA request/grant, FIFO-empty flags and DMA state machines for debug [DS §14.3
p.134].

### 4.4 TPAFCR (`0x48`, reset `0x0000_00F1`) and RBSR (`0x4C`, reset `0x0000_0640`)

`TPAFCR` sets TX/RX FIFO sizes ([29:27]/[26:24]; `000`=2K, others invalid on this
part), Early-TX-threshold [23:16] and Early-RX-threshold [15:8] (unit 64 bytes),
plus high/normal-priority packet thresholds [7:4]/[3:0]. `RBSR` sets the receive
buffer size in bits [13:3] (unit 1 byte, 8-byte aligned). [DS §14.3 p.135–136](#sources)

---

## 5. MACCR — MAC Control Register (`0x50`, reset `0x0`) — full bitfields

This is the central control register. Bits below are the AST2050 datasheet
definitions [DS §14.3 p.137–138](#sources); the last column gives the matching mainline macro
`[ftgmac100.h](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.h)`. **Two positions diverge** (bits 6 and 11) and are footnoted.

:::{list-table} MAC50 MACCR — every bit
:header-rows: 1
:widths: 8 22 8 46 16

* - Bit
  - Field (datasheet)
  - Access
  - Meaning
  - [`ftgmac100.h`](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.h)
* - 31
  - SW RST
  - RW
  - Software reset. Writing 1 asserts reset for **175 AHB clocks** (~200 system clocks) then auto-clears. Does **not** reset SPEED 100 / GMAC MODE.
  - `MACCR_SW_RST`
* - 30:20
  - Reserved (0)
  - —
  - —
  - —
* - **19**
  - **SPEED 100**
  - RW
  - **Speed mode: 1 = 100 Mbps, 0 = 10 Mbps.** With GMAC MODE (bit 9) decides 10/100/1000. Cannot be software-reset. This is the mainline **`FAST_MODE`** bit — the "RX-fix" bit in the project NIC notes.
  - `MACCR_FAST_MODE`
* - 18
  - DISCARD CRCERR
  - RW
  - Discard packets flagged with CRC error.
  - `MACCR_DISCARD_CRCERR`
* - 17
  - RX BROADPKT EN
  - RW
  - Receive broadcast packets.
  - `MACCR_RX_BROADPKT`
* - 16
  - RX MULTIPKT EN
  - RW
  - Receive **all** multicast packets.
  - `MACCR_RX_MULTIPKT`
* - 15
  - RX HT EN
  - RW
  - Store incoming multicast packet if it passes hash-table filtering.
  - `MACCR_HT_MULTI_EN`
* - 14
  - RX ALLADR
  - RW
  - Promiscuous — do not check destination address.
  - `MACCR_RX_ALL`
* - 13
  - JUMBO LF
  - RW
  - Jumbo long-frame threshold: set → 9216/9220 B; clear → 1518/1522 B (w/ VLAN).
  - `MACCR_JUMBO_LF`
* - 12
  - RX RUNT
  - RW
  - Receive packets shorter than 64 B (≥ 10 B).
  - `MACCR_RX_RUNT`
* - 11
  - Reserved (0)
  - —
  - Reserved per AST2050 datasheet. **(Faraday header names bit 11 `PHY_LINK_LEVEL`.)**
  - `MACCR_PHY_LINK_LEVEL` †
* - 10
  - CRC APD
  - RW
  - Append CRC to transmitted packets.
  - `MACCR_CRC_APD`
* - 9
  - GMAC MODE
  - RW
  - 1 = 1000 Mbps engine, 0 = 10/100. Cannot be software-reset. (Always 0 on AST2050.)
  - `MACCR_GIGA_MODE`
* - 8
  - FULLDUP
  - RW
  - 1 = full duplex, 0 = half duplex.
  - `MACCR_FULLDUP`
* - 7
  - ENRX IN HALFTX
  - RW
  - Enable packet reception while transmitting in half-duplex.
  - `MACCR_ENRX_IN_HALFTX`
* - 6
  - PHY link status detection
  - RW
  - 1 = rising/falling-edge trigger, 0 = high-level sensitive. **(Faraday header names bit 6 `LOOP_EN`.)**
  - `MACCR_LOOP_EN` †
* - 5
  - HPTXR EN
  - RW
  - Enable the high-priority transmit ring.
  - `MACCR_HPTXR_EN`
* - 4
  - REMOVE VLAN
  - RW
  - Strip VLAN tag from received tagged packets.
  - `MACCR_RM_VLAN`
* - 3
  - RXMAC EN
  - RW
  - Enable RXMAC (receive packets).
  - `MACCR_RXMAC_EN`
* - 2
  - TXMAC EN
  - RW
  - Enable TXMAC (transmit packets).
  - `MACCR_TXMAC_EN`
* - 1
  - RXDMA EN
  - RW
  - Enable RX DMA channel; clearing stops reception immediately.
  - `MACCR_RXDMA_EN`
* - 0
  - TXDMA EN
  - RW
  - Enable TX DMA channel; clearing stops transmission immediately.
  - `MACCR_TXDMA_EN`
:::

† **Bit-6 / bit-11 divergence.** The generic Faraday [`ftgmac100.h`](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.h) assigns bit 6 =
`LOOP_EN` and bit 11 = `PHY_LINK_LEVEL`. The AST2050 datasheet instead documents
bit 6 as **PHY link-status detection mode** (edge vs. level) and marks bit 11
**reserved** [DS §14.3 p.137–138](#sources). Aspeed's integration of the Faraday IP is
authoritative for AST2050 behaviour; a faithful model should follow the datasheet
and treat the mainline names as aliases at those two positions.

**Worked example (observed on real AST2050 HW).** The U-Boot `aspeednic` driver
leaves `MACCR = 0x0008_0500` = `FAST_MODE(19) | CRC_APD(10) | FULLDUP(8)` before
enabling DMA, then reaches `0x0008_050F` after also setting
`TXDMA_EN|RXDMA_EN|TXMAC_EN|RXMAC_EN` (bits 3:0). Verify: `0x80000 | 0x400 | 0x100 =
0x80500`, `+ 0xF = 0x8050F` — consistent with the bit map above. Captured over P2A in
`asus-kgpe-d16-firmware/NIC-MAC-REGISTER-COMPARISON.md`.

---

## 6. MACSR — MAC Status Register (`0x54`, reset 0)

Status/statistics, **write-1-to-clear**. [DS §14.3 p.138](#sources)

:::{list-table} MAC54 MACSR bitfields
:header-rows: 1
:widths: 10 22 68

* - Bit
  - Field
  - Meaning (write 1 to clear)
* - 31:12
  - Reserved (0)
  - —
* - 11
  - COL EXCEED
  - Collision count exceeded 16.
* - 10
  - LATE COL
  - Late collision detected by transmitter.
* - 9
  - TPKT LOST
  - TX packet lost (late/excessive collision).
* - 8
  - TPKT OK
  - Packet transmitted successfully.
* - 7
  - RUNT
  - Runt packet received.
* - 6
  - FTL
  - Frame-too-long received.
* - 5
  - CRC ERR
  - Incoming CRC invalid (unless CRC-DIS set).
* - 4
  - RPKT LOST
  - Received packet lost (RX FIFO full).
* - 3
  - RPKT SAVE
  - Packet saved to RX FIFO successfully.
* - 2
  - COL
  - Incoming packet dropped due to collision.
* - 1
  - BROADCAST
  - Incoming broadcast packet.
* - 0
  - MULTICAST
  - Incoming multicast packet.
:::

[DS §14.3 p.138](#sources). The `TM` test register (`0x58`) holds polling-/interrupt-timer test
modes (bits 20/19), transmit-collision test (bit 15), backoff value [14:5] and retry
limit [4:0] [DS §14.3 p.138–139](#sources).

### 6.1 Address filtering (uses MACCR + MADR/LADR + MAHT0/1)

Reception is filtered by the combination of MACCR bits **RX ALLADR (14)**,
**RX MULTIPKT (16)**, **RX BROADPKT (17)** and **RX HT EN (15)** against the unicast
address (MADR/LADR, `0x08`/`0x0C`) and the 64-bit multicast hash table
(MAHT0/MAHT1, `0x10`/`0x14`). [DS §14.4.5 p.149](#sources)

---

## 7. MDIO / MII management interface (PHYCR + PHYDATA)

The MAC embeds a clause-22 MII management (MDC/MDIO) controller. All PHY register
access goes through **PHYCR (`0x60`)** and **PHYDATA (`0x64`)**. [DS §14.4.6 p.150](#sources)

### 7.1 PHYCR — PHY Control Register (`0x60`, reset `0x0000_0034`)

:::{list-table} MAC60 PHYCR bitfields
:header-rows: 1
:widths: 10 18 10 46 16

* - Bit
  - Field
  - Access
  - Meaning
  - [`ftgmac100.h`](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.h)
* - 31:28
  - Reserved (0)
  - —
  - —
  - —
* - 27
  - MIIWR
  - RW
  - Write 1 to start a PHY **write**; auto-cleared when the write completes.
  - `PHYCR_MIIWR` (BIT 27)
* - 26
  - MIIRD
  - RW
  - Write 1 to start a PHY **read**; auto-cleared when the read completes.
  - `PHYCR_MIIRD` (BIT 26)
* - 25:21
  - REGAD
  - RW
  - PHY register address (clause-22 register number, 0–31).
  - `PHYCR_REGAD(x)` = `(x & 0x1f) << 21`
* - 20:16
  - PHYAD
  - RW
  - PHY (device) address on the MDIO bus, 0–31.
  - `PHYCR_PHYAD(x)` = `(x & 0x1f) << 16`
* - 15:6
  - Reserved (0)
  - —
  - —
  - —
* - 5:0
  - MDC CYCTHR
  - RW
  - MDC cycle threshold: `MDC period = MDC_CYCTHR × RX-clock period`. Use `0x34` (reset) for the first access / on PHY-link change; allowed `0x02–0x3F` (10M), `0x0B–0x3F` (100M).
  - `PHYCR_MDC_CYCTHR(x)` = `x & 0x3f`
:::

[DS §14.3 p.139](#sources) + `[ftgmac100.h](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.h)`.

### 7.2 PHYDATA — PHY Data Register (`0x64`, reset 0)

:::{list-table} MAC64 PHYDATA bitfields
:header-rows: 1
:widths: 12 18 10 44 16

* - Bit
  - Field
  - Access
  - Meaning
  - [`ftgmac100.h`](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.h)
* - 31:16
  - MIIRDATA
  - R
  - Data read back from the PHY register.
  - `PHYDATA_MIIRDATA(d)` = `(d >> 16) & 0xffff`
* - 15:0
  - MIIWDATA
  - RW
  - Data to write to the PHY register.
  - `PHYDATA_MIIWDATA(x)` = `x & 0xffff`
:::

[DS §14.3 p.139–140](#sources) + `[ftgmac100.h](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.h)`.

### 7.3 Clause-22 frame format

The MDIO bit stream is sampled on the rising edge of MDC [DS §14.4.6 p.150]:

:::{list-table} MII management frame (clause 22)
:header-rows: 1
:widths: 14 12 10 10 12 12 10 12 8

* - Operation
  - PRE
  - ST
  - OP
  - PHYAD
  - REGAD
  - TA
  - DATA
  - IDLE
* - Read
  - `1…1`
  - `01`
  - `10`
  - `AAAAA`
  - `RRRRR`
  - `Z0`
  - `D…D (16)`
  - `Z`
* - Write
  - `1…1`
  - `01`
  - `01`
  - `AAAAA`
  - `RRRRR`
  - `10`
  - `D…D (16)`
  - `Z`
:::

### 7.4 How the driver issues a read / write

Sequence used by `[ftgmac100.c](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.c)` (`ftgmac100_mdiobus_read`/`_write`), consistent with
the datasheet:

- **Read (register r on PHY p):** write `PHYCR = PHYAD(p) | REGAD(r) | MDC_CYCTHR |
  MIIRD` (set bit 26). Poll PHYCR until `MIIRD` (bit 26) auto-clears (timeout ~10 ms
  in the driver). Read the result from `PHYDATA[31:16]` (`MIIRDATA`).
- **Write (value v):** write `PHYDATA = MIIWDATA(v)` (low 16 bits) first, then write
  `PHYCR = PHYAD(p) | REGAD(r) | MDC_CYCTHR | MIIWR` (set bit 27). Poll PHYCR until
  `MIIWR` (bit 27) auto-clears.

[DS §14.3 p.139 + §14.4.6 p.150](#sources), `[ftgmac100.c](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.c)`.

:::{note}
**RMII / PHY-mode caveat observed on the KGPE-D16 rig.** With the DT set to the real
RMII PHY (`phy-mode = "rmii"`, no `fixed-link`), the modern mainline [`ftgmac100`](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.c)
driver logs `Unsupported PHY mode rmii !` and never calls `adjust_link(up)`, so
`MACCR` stays 0 and `eth0` gets no carrier. The MAC-clock rate was ruled out as the
cause (see [`0002-ftgmac100-ast2050-macclk.patch`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/kernel/patches/0002-ftgmac100-ast2050-macclk.patch), which leaves MACCLK at the U-Boot
default and, tested on real HW, does **not** fix RMII TX). Details:
`asus-kgpe-d16-firmware/NIC-MAC-REGISTER-COMPARISON.md`,
`asus-kgpe-d16-firmware/kernel/patches/0002-ftgmac100-ast2050-macclk.patch`.
:::

---

## 8. Flow control (FCR `0x68`), back pressure (BPR `0x6C`), power (PWRTC `0x70`)

:::{list-table} MAC68 FCR bitfields (reset `0x0000_0400`)
:header-rows: 1
:widths: 12 22 66

* - Bit
  - Field
  - Meaning
* - 31:16
  - PAUSE TIME
  - Pause time placed in the transmitted pause frame (unit = 1 slot time).
* - 15:9
  - FC HIGH / FC LOW
  - RX-FIFO free-space thresholds (unit 256 B; defaults high=`0x5`, low=`0x2`), selected by bit 8.
* - 8
  - FC HTHR SEL
  - Select high (1) vs. low (0) RX-FIFO free-space threshold.
* - 7:5
  - Reserved (0)
  - —
* - 4
  - RX PAUSE
  - A pause frame was received (write 1 to clear).
* - 3
  - TXPAUSED
  - Read-only: transmission is paused due to a received pause frame.
* - 2
  - FCTHR EN
  - Enable threshold-based pause-frame transmission.
* - 1
  - TX PAUSE
  - Write 1 to send a pause frame; auto-clears after transmission.
* - 0
  - FC EN
  - Flow-control mode enable.
:::

:::{list-table} MAC6C BPR bitfields (reset `0x0000_0200`)
:header-rows: 1
:widths: 12 22 66

* - Bit
  - Field
  - Meaning
* - 31:15
  - Reserved (0)
  - —
* - 14:8
  - BK LOW
  - RX-FIFO free-space low threshold; jam generated below it (unit 256 B; default `0x2`).
* - 7:4
  - BKJAM LEN
  - Back-pressure jam length (0000=4B … 1001=1518B, 1010=2048B).
* - 3:2
  - Reserved (0)
  - —
* - 1
  - BKADR MODE
  - 1 = jam only on address match; 0 = jam on any incoming packet.
* - 0
  - BK EN
  - Back-pressure mode enable (half-duplex).
:::

`PWRTC` (`0x70`, reset 0): bit 18 `SW_PDNPHY` (software power-down PHY), bit 15
`PWRSAV` (power-saving mode), rest reserved. [DS §14.3 p.140–141](#sources)

---

## 9. Bring-up / initialisation order (datasheet §14.5)

Datasheet-prescribed init sequence [DS §14.5.1 p.150–151]:

1. Set `GMAC MODE` (MACCR[9]) and `SPEED 100` (MACCR[19]) appropriately (0/1 → 100M
   on AST2050).
2. Set `SW RST` (MACCR[31]) = 1; wait ~200 system clocks for auto-clear.
3. Read `FEAR` (`0x44`) for the real TX/RX FIFO sizes.
4. Allocate + initialise the transmit descriptor ring and buffers.
5. Program `NPTXR BADR` (`0x20`) (and `HPTXR BADR` `0x2C` if used).
6. Program `IER` (`0x04`), `MADR`/`LADR` (`0x08`/`0x0C`), `MAHT0` (`0x10`).
7. Program `ITC` (`0x30`), `APTC` (`0x34`), `TPAFCR` (`0x48`), `DBLAC` (`0x38`).
8. Program `MACCR` (`0x50`) last to set the final config and enable the channels.

This matches the mainline `ftgmac100_init_all` / `ftgmac100_reset_and_config_mac`
flow. On the AST2050 rig, the modern driver was found to **hang on the first MACCR
write** inside `ndo_open` in the post-P2A-reset context (open issue — a clock/reset/
AHB-state difference from probe time), documented in
`asus-kgpe-d16-firmware/NIC-MAC-REGISTER-COMPARISON.md`.

---

## 10. External PHY — Realtek RTL8201CP (RMII 10/100)

The KGPE-D16 BMC uses a Realtek **RTL8201CP** single-port 10/100 PHY on the MAC's
RMII interface (the mainline `ftgmac100_26` driver also lists RTL8201EL / RTL8201N /
RTL8211BN as supported PHYs;
`asus-kgpe-d16-firmware/RAPTOR_ENGINEERING_AST2050_ANALYSIS.md`). The RTL8201CP
exposes the standard IEEE 802.3 clause-22 register set (registers 0–6) plus Realtek
vendor registers (16–31). [RTL8201CP DS §6 p.8–13](#sources)

### 10.1 PHY identification (registers 2 & 3)

:::{list-table} RTL8201CP PHY identifier
:header-rows: 1
:widths: 10 16 20 54

* - Reg
  - Name
  - Value
  - Note
* - 2
  - PHYID1
  - `0x0000`
  - PHY identifier word 1 (RO).
* - 3
  - PHYID2
  - `0x8201`
  - PHY identifier word 2 (RO) — the recognisable "8201" tag.
:::

[RTL8201CP DS §6.3–6.4 p.9](#sources). A driver reads REGAD=2/3 via PHYCR/PHYDATA (§7) and
matches `0x0000_8201`.

### 10.2 Register 0 — BMCR (Basic Mode Control Register)

:::{list-table} RTL8201CP Reg 0 BMCR
:header-rows: 1
:widths: 8 24 10 58

* - Bit
  - Name
  - Default
  - Meaning
* - 15
  - Reset
  - 0
  - Software reset (self-clearing); returns control/status registers to defaults.
* - 14
  - Loopback
  - 0
  - Loop TXD3:0 back to the receive path.
* - 13
  - Spd_Set
  - 0
  - Speed when auto-neg off: 1 = 100M, 0 = 10M (reflects negotiated speed after AN).
* - 12
  - Auto-Negotiation Enable
  - 1
  - 1 = enable NWay AN (bits 13 & 8 ignored); 0 = manual.
* - 11
  - Power Down
  - 0
  - Power down PHY (MDC/MDIO stay alive).
* - 10
  - Reserved
  - —
  - (Standard clause-22 "Isolate" position; reserved on RTL8201CP.)
* - 9
  - Restart Auto-Negotiation
  - 0
  - 1 = restart AN.
* - 8
  - Duplex Mode
  - 0
  - When AN off: 1 = full, 0 = half (reflects negotiated duplex after AN).
* - 7:0
  - Reserved
  - —
  - (Standard clause-22 bit 7 = Collision-Test; reserved here.)
:::

[RTL8201CP DS §6.1 p.8](#sources)

### 10.3 Register 1 — BMSR (Basic Mode Status Register)

:::{list-table} RTL8201CP Reg 1 BMSR
:header-rows: 1
:widths: 8 26 10 56

* - Bit
  - Name
  - Default
  - Meaning
* - 15
  - 100Base-T4
  - 0
  - T4 capability (not supported).
* - 14
  - 100Base-TX FD
  - 1
  - 100Base-TX full-duplex capable.
* - 13
  - 100Base-TX HD
  - 1
  - 100Base-TX half-duplex capable.
* - 12
  - 10Base-T FD
  - 1
  - 10Base-T full-duplex capable.
* - 11
  - 10Base-T HD
  - 1
  - 10Base-T half-duplex capable.
* - 10:7
  - Reserved
  - —
  - —
* - 6
  - MF Preamble Suppression
  - 1
  - Accepts management frames with suppressed preamble (≥32 preamble bits required on first access after reset).
* - 5
  - Auto-Negotiation Complete
  - 0
  - 1 = AN finished.
* - 4
  - Remote Fault
  - 0
  - Remote fault detected (clear-on-read).
* - 3
  - Auto-Negotiation Ability
  - 1
  - Link has not experienced a fail state.
* - 2
  - Link Status
  - 0
  - 1 = valid link established.
* - 1
  - Jabber Detect
  - 0
  - Jabber condition.
* - 0
  - Extended Capability
  - 1
  - Extended register set present.
:::

[RTL8201CP DS §6.2 p.9](#sources)

### 10.4 Register 4 — ANAR (Auto-Negotiation Advertisement)

:::{list-table} RTL8201CP Reg 4 ANAR
:header-rows: 1
:widths: 10 14 10 66

* - Bit
  - Name
  - Default
  - Meaning
* - 15
  - NP
  - 0
  - Next-page.
* - 14
  - ACK
  - 0
  - Acknowledge (RO).
* - 13
  - RF
  - 0
  - Advertise remote-fault.
* - 12
  - Reserved
  - —
  - —
* - 11
  - TXFC
  - 0
  - Advertise TX flow-control support.
* - 10
  - RXFC
  - 0
  - Advertise RX flow-control support. (MAC sets this via SMI to request flow control.)
* - 9
  - T4
  - 0
  - Advertise 100Base-T4 (RO, not supported).
* - 8
  - TXFD
  - 1
  - Advertise 100Base-TX full-duplex.
* - 7
  - TX
  - 1
  - Advertise 100Base-TX.
* - 6
  - 10FD
  - 1
  - Advertise 10Base-T full-duplex.
* - 5
  - 10
  - 1
  - Advertise 10Base-T.
* - 4:0
  - Selector
  - `00001`
  - Protocol selector = CSMA/CD.
:::

[RTL8201CP DS §6.5 p.10](#sources). **Register 5 ANLPAR** (link-partner ability) mirrors ANAR
but is read-only and reflects the partner's advertised abilities [RTL8201CP DS §6.6
p.10–11]. **Register 6 ANER** holds AN-expansion status: bit 4 `MLF` (multiple link
fault), bit 3 `LP_NP_ABLE`, bit 2 `NP_ABLE`, bit 1 `PAGE_RX`, bit 0 `LP_NW_ABLE`
[RTL8201CP DS §6.7 p.11](#sources).

### 10.5 Vendor registers 16–19 (incl. the RMII indicator)

:::{list-table} RTL8201CP vendor registers (selected)
:header-rows: 1
:widths: 8 16 12 64

* - Reg
  - Name
  - Bit
  - Meaning
* - 16
  - NSR
  - 11 ENNWLE / 10 Testfun / 9 NWLPBK / 2 FLAGABD / 1 FLAGPDF / 0 FLAGLSC
  - NWay setup + AN state flags.
* - 17
  - LBREMR
  - 15 RPTR / 12 LDPS / 11 AnalogOFF / 9 LB / 8 F_Link_10 / 7 F_Link_100 / **1 FXMODE** / **0 RMIIMODE**
  - Loopback/bypass/error-mask; **bit 0 `RMIIMODE` (RO) indicates RMII mode is enabled**, bit 1 `FXMODE` indicates fibre mode.
* - 18
  - REC
  - 15:0
  - RX_ER counter (invalid-packet count, RO).
* - 19
  - SNR
  - —
  - SNR display (diagnostic).
:::

[RTL8201CP DS §6.8–6.11 p.12–13](#sources). Note the RTL8201CP selects **RMII vs. MII by pin
strapping**, not by a writeable register — register 17 bit 0 (`RMIIMODE`) is a
**read-only** reflection of the strap. [RTL8201CP DS §6.9 p.12](#sources)

### 10.6 RMII specifics and the reference-clock requirement

- **RMII uses a shared 50 MHz reference clock** for both TX and RX (vs. separate
  25 MHz TXC/RXC in MII). On the AST2050 pinout the pin `RMIIRCLK` (input direction,
  pin A7 in MII mode = `MIITXCK`) is the **RMII 1 50 MHz reference clock**; the second
  RMII channel uses `RMII2RCLK` (pin B7 in MII mode = `MIIRXCK`). [DS §3 pin table
  "RMIIRCLK … RMII 1 50MHz reference clock"; DS §4.7.2 p.68]
- In RMII mode the AST2050 exposes 2-bit data buses `RMIITXD[1:0]` / `RMIIRXD[1:0]`,
  plus `RMIITXEN`, `RMIICRSDV` (carrier-sense/data-valid) and `RMIIRXER`; the MII-mode
  4-bit `MIITXD[3:0]`/`MIIRXD[3:0]` are unused. [DS §3 pin table; DS §4.7.2 p.68](#sources)
- MDC/MDIO management pins are `MIIMDC` (pin A3, output) and `MIIMDIO` (pin A2,
  bidirectional). [DS §3 pin table "MIIMDC / MIIMDIO"](#sources)
- The mainline driver treats RMII RCLK as an optional clock ("RCLK is for RMII,
  typically used for NCSI"), skipping it for the AST2400-class MAC; on AST2050 the
  50 MHz refclk path must physically exist for RMII TX/RX to clock.
  [`ftgmac100.c`, `asus-kgpe-d16-firmware/kernel/patches/0002-ftgmac100-ast2050-macclk.patch`](#sources)

RMII/MII AC timing (for board bring-up): TX/RX clock cycle 40 ns (25 MHz MII), data
output setup 30 ns / hold 2.5 ns, data input setup 5 ns / hold 0 ns. [DS §4.7.2 p.68](#sources)

---

## 11. SCU bits that gate the MAC (clock, pinmux, reset, PHY mode)

The MAC will not operate unless the System Control Unit (SCU, base `0x1E6E_2000`)
de-asserts its reset, routes its pins, and selects the interface mode. Relevant bits:

:::{list-table} SCU registers controlling the MAC
:header-rows: 1
:widths: 12 22 12 54

* - SCU reg
  - Field
  - Bits
  - Meaning
* - `SCU04` (reset `0x000FFE5C`)
  - Reset MAC#1 / MAC#2 Controller
  - 11 / 12
  - 1 = hold MAC in async reset (**default = held**); software writes 0 to release. [DS §18.2 SCU04](#sources)
* - `SCU08` (reset `0xE3F00070`)
  - Clock selection
  - —
  - General SoC clock tree; the MAC is clocked from HCLK — no dedicated MAC clock-select field. [DS §18.2 SCU08](#sources)
* - `SCU0C` (reset `0x000C3E8B`)
  - Clock-stop control
  - —
  - No dedicated MAC clock-stop bit (MAC runs on HCLK, which is not in the stop list). [DS §18.2 SCU0C](#sources)
* - `SCU40` (SOC scratch, reset 0)
  - MAC#1 PHY Mode / MAC#2 PHY Mode
  - 15:14 / 13:12
  - `00` Dedicated PHY, `01` NCSI, `10` Intel NCSI EVB, `11` reserved — the ARM firmware passes this to the kernel. [DS §18.2 SCU40](#sources)
* - `SCU70` (HW trapping, strap-loaded)
  - MAC interface mode selection
  - 8:6
  - `011` MII(MAC#1) only, `100` RMII(MAC#1) only, `110` RMII(MAC#1)+RMII(MAC#2), `111` disable MAC (000–010,101 reserved). [DS §18.2 SCU70](#sources)
* - `SCU74` (reset `0x40048000`)
  - MAC pin enables
  - 27 / 25 / 20
  - 27 = GPIOE pins shared with MAC (for SCU70[8:6]=2/4/7); 25 = MAC PHY#1 `PHYLINK`/`PHYPD#` pins; 20 = MAC#2 MDC/MDIO pins. [DS §18.2 SCU74](#sources)
:::

**Cross-check against real AST2050 hardware.** Registers dumped over P2A while U-Boot
(working NIC) and Linux ran were **byte-identical**:
`SCU04=0x000ff658`, `SCU08=0x61800070`, `SCU0C=0x000c3e89`, `SCU48=0x00000000`
(MAC clock delay), `SCU70=0x00819582`, `SCU74=0x4204d000`
(`asus-kgpe-d16-firmware/NIC-MAC-REGISTER-COMPARISON.md`). Decoding
`SCU70[8:6]` from `0x00819582` gives `0b110` = **RMII(MAC#1)+RMII(MAC#2)**, matching
the RMII wiring; and `SCU04` bit 11 = 0 (MAC#1 reset released). This confirms the
clock/pinmux/reset/PHY-mode class is correctly configured on the rig and is *not* the
cause of the modern-kernel RMII-TX issue — that lies in the driver's `ndo_open`
path (§9).

The Raptor porting notes flag the same SCU touch-points: pinmux/interface-mode
(SCU74/SCU80–9C group) and the SCU48 MAC clock-delay as the AST2050-specific items to
verify (`asus-kgpe-d16-firmware/RAPTOR-PORTING-GUIDE.md`, "Change 10: Ethernet
(FTGMAC100)").

---

## Sources

Primary hardware authority:

- **ASPEED AST2050/AST1100 A3 Datasheet, V1.05** (2010-05-25), in-repo:
  `datasheets/aspeed/AST2050_AST1100_A3_Datasheet_V1.05.pdf`. Chapters used:
  §1.3.14 / §2.6 (feature overview), §3 (pin table), §4.7.2 (MII/RMII interface,
  p.68), **§14 "10/100 Ethernet MAC Controller"** (register map p.124–143, function
  description incl. §14.4.6 MII management p.144–151), §16 (interrupt table), §18.2
  (SCU registers p.205–219).

Software view of the same Faraday FTGMAC100 IP:

- Mainline Linux `drivers/net/ethernet/faraday/ftgmac100.h` — register offsets and
  `MACCR`/`PHYCR`/`PHYDATA` bit macros
  (<https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.h>).
- Mainline Linux `drivers/net/ethernet/faraday/ftgmac100.c` — MDIO read/write
  sequence, init flow, RMII/RCLK handling.

External PHY:

- **Realtek RTL8201CP Datasheet**, Track ID JATR-1076-21 Rev. 1.24 — clause-22 MII
  register set (BMCR/BMSR/PHYID/ANAR/ANLPAR/ANER) and vendor registers 16–19,
  incl. `RMIIMODE` (<https://belchip.by/sitedocs/38346.pdf>; also
  <http://realtek.info/pdf/rtl8201cp.pdf>).

Project reverse-engineering / on-hardware evidence (private analysis repo
`ai-shenanigans-for-bmcs/`):

- `asus-kgpe-d16-firmware/NIC-MAC-REGISTER-COMPARISON.md` — U-Boot-vs-Linux MAC/SCU
  register dumps over P2A, the `MACCR=0x80500/0x8050F` worked example, TX-ring probe,
  and the `ndo_open`/MACCR-write-stall root-cause trace.
- `asus-kgpe-d16-firmware/kernel/patches/0002-ftgmac100-ast2050-macclk.patch` — the
  AST2050 MACCLK behaviour + the note that MAC-clock rate is not the RMII-TX cause.
- `asus-kgpe-d16-firmware/RAPTOR_ENGINEERING_AST2050_ANALYSIS.md` and
  `asus-kgpe-d16-firmware/RAPTOR-PORTING-GUIDE.md` — FTGMAC100 driver / PHY support,
  DT `compatible` strings, SCU touch-points, IRQ mapping.
- `asus-kgpe-d16-firmware/hwreg.h` (`AST_MAC1_BASE 0x1E660000`,
  `AST_MAC2_BASE 0x1E680000`) and `asus-kgpe-d16-firmware/ast2050.h`
  (U-Boot `CONFIG_ASPEEDNIC`, MAC#1/#2 PHY-setting scratch-register semantics).
