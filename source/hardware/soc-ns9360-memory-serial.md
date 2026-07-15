# NS9360 — memory, Ethernet & serial

Continuation of {doc}`soc-ns9360`: the external-memory controller, the Ethernet Communication Module, the serial (UART/SPI) channels, the I2C interface, and the RTC.

## Memory Controller


**Base address: 0xA0700000** [HWRef p.281](#sources), [mach-ns9xxx regs-mem.h](https://github.com/torvalds/linux/blob/v2.6.39/arch/arm/mach-ns9xxx/include/mach/regs-mem.h), [u-boot ns9750_mem.h](https://github.com/u-boot/u-boot/blob/v2012.10/include/ns9750_mem.h).

An AMBA-AHB MultiPort Memory Controller (ARM PL172/PL175 lineage) with a dynamic
(SDRAM / low-power SDRAM) controller and a static (ROM / Flash / SRAM) controller.
It supports 8/16/32-bit static width, 16/32-bit dynamic width, little/big endian,
async page-mode static reads, and up to 256 MB per chip select; synchronous burst
static memory is *not* supported [HWRef p.196-197](#sources).

### Memory controller register map

```{list-table} Memory controller registers (offset from 0xA0700000)
:header-rows: 1
:widths: 20 24 56

* - Offset
  - Register
  - Description
* - 0x000
  - Control
  - Enable, address-mirror, low-power mode
* - 0x004
  - Status
  - Busy / write-buffer / self-refresh status
* - 0x008
  - Config
  - Endian mode (END)
* - 0x020
  - DynamicControl
  - SDRAM command mode, clock enable, self-refresh
* - 0x024
  - DynamicRefresh
  - Refresh timer (×16 HCLK)
* - 0x028
  - DynamicReadConfig
  - Read data capture strategy
* - 0x030-0x058
  - Dynamic tRP … tMRD
  - SDRAM timing parameters (see below)
* - 0x080
  - StaticExtendedWait
  - Shared long-transfer wait timeout
* - 0x100-0x164
  - DynamicConfig0-3 / RasCas0-3
  - Per-CS SDRAM organisation and RAS/CAS latency
* - 0x200-0x278
  - StaticConfig0-3 + delays
  - Per-CS static memory width/timing
```

Offsets confirmed by [mach-ns9xxx regs-mem.h](https://github.com/torvalds/linux/blob/v2.6.39/arch/arm/mach-ns9xxx/include/mach/regs-mem.h) (`MEM_CTRL`=0xa0700000,
`MEM_DMCONF`=0x100+8x, `MEM_SMC`=0x200+8x) and [u-boot ns9750_mem.h](https://github.com/u-boot/u-boot/blob/v2012.10/include/ns9750_mem.h).

### Control, Status, Config

```{list-table} Control register (0x000) [HWRef p.284-285](#sources)
:header-rows: 1
:widths: 12 14 12 62

* - Bits
  - Field
  - Access
  - Meaning
* - 31:3
  - reserved
  - —
  - reserved
* - 2
  - LPM
  - R/W
  - Low-power mode (SDRAM still refreshed)
* - 1
  - ADDM
  - R/W
  - Address mirror: 1 = reset map (CS1 mirrored to CS0/CS4), 0 = normal
* - 0
  - MCEN
  - R/W
  - Memory controller enable
```

`Status` (0x004): bit 2 `SA` self-refresh acknowledge, bit 1 `WBS` write-buffer
status, bit 0 `BUSY` [HWRef p.286](#sources). `Config` (0x008): bit 0 `END` endian
(0 = little, 1 = big; reset from gpio[44], software-overridable) — this is the
memory-controller half of the endian switch [HWRef p.286-287](#sources), [mach-ns9xxx](https://github.com/torvalds/linux/tree/v2.6.39/arch/arm/mach-ns9xxx).

### Dynamic (SDRAM) controller

```{list-table} DynamicControl register (0x020) [HWRef p.287-289](#sources)
:header-rows: 1
:widths: 12 14 12 62

* - Bits
  - Field
  - Access
  - Meaning
* - 31:15
  - reserved
  - —
  - reserved
* - 14
  - nRP
  - R/W
  - dy_pwr_n level (SDRAM reset/power-down signal)
* - 13
  - reserved
  - R/W
  - write 0
* - 12:9
  - reserved
  - —
  - reserved
* - 8:7
  - SDRAMInit
  - R/W
  - Command: 00 = NORMAL, 01 = MODE, 10 = PALL (precharge all), 11 = NOP
* - 6:3
  - reserved
  - —
  - reserved
* - 2
  - SR
  - R/W
  - Self-refresh request
* - 1
  - reserved
  - R/W
  - write 1
* - 0
  - CE
  - R/W
  - Dynamic memory clock enable (must be 1 during SDRAM init)
```

`DynamicRefresh` (0x024) bits 10:0 `REFRESH`: 0 = disabled, else the value ×16 =
HCLK ticks between refreshes [HWRef p.289](#sources). `DynamicReadConfig` (0x028) bits 1:0
`RD`: command-delayed capture strategy (01/10/11 = +0/+1/+2 clock) [HWRef p.291](#sources).

The SDRAM timing registers each hold one field (value n encodes n+1 clocks):

```{list-table} Dynamic timing registers (value = n+1 clocks) [HWRef p.292-302](#sources)
:header-rows: 1
:widths: 20 14 12 54

* - Register
  - Offset
  - Field width
  - Parameter
* - tRP (Precharge period)
  - 0x030
  - 4-bit
  - Precharge command period
* - tRAS (Active to precharge)
  - 0x034
  - 4-bit
  - Active to precharge
* - tSREX (Self-refresh exit)
  - 0x038
  - 4-bit
  - Self-refresh exit time
* - tAPR (Last data to active)
  - 0x03C
  - 4-bit
  - Last data out to active
* - tDAL (Data-in to active)
  - 0x040
  - 4-bit
  - Data-in to active
* - tWR (Write recovery)
  - 0x044
  - 4-bit
  - Write recovery time
* - tRC (Active to active)
  - 0x048
  - 5-bit
  - Active to active command period
* - tRFC (Auto refresh)
  - 0x04C
  - 5-bit
  - Auto refresh period
* - tXSR (Exit self-refresh)
  - 0x050
  - 5-bit
  - Exit self-refresh to active
* - tRRD (Bank A to bank B)
  - 0x054
  - 4-bit
  - Active bank A to active bank B
* - tMRD (Mode to active)
  - 0x058
  - 4-bit
  - Load-mode to active command time
```

Per-chip-select SDRAM organisation is set in `DynamicConfig0-3` (0x100 + n*0x20):

```{list-table} DynamicConfig register (0x100 + n*0x20) [HWRef p.304-307](#sources)
:header-rows: 1
:widths: 12 14 12 62

* - Bits
  - Field
  - Access
  - Meaning
* - 31:21
  - reserved
  - —
  - reserved
* - 20
  - Protect
  - R/W
  - Write protect
* - 19
  - BDMC
  - R/W
  - Buffer enable (disable during SDRAM init, enable for normal use)
* - 18:15
  - reserved
  - —
  - reserved
* - 14
  - AM
  - R/W
  - Address mapping high bit: 0 = 16-bit bus, 1 = 32-bit bus
* - 13
  - reserved
  - —
  - reserved
* - 12:7
  - AM1
  - R/W
  - Address mapping: SDRAM density/width/row/col/bank (Table 191)
* - 6:5
  - reserved
  - —
  - reserved
* - 4:3
  - MD
  - R/W
  - Memory device: 00 = SDRAM, 01 = low-power SDRAM, 10/11 reserved
* - 2:0
  - reserved
  - —
  - reserved
```

The AM/AM1 encoding (Table 191) maps to a device organisation: AM (bit 14)
= external bus width (0 = 16-bit, 1 = 32-bit); AM1 bit 12 = mapping style
(0 = high-performance row/bank/col, 1 = low-power bank/row/col); AM1 bits 11:9 =
density/row; AM1 bits 8:7 = device width (00 = ×8, 01 = ×16, 10 = ×32). Example:
a 4M×16 (64 Mb, 4-bank, 12-row, 8-col) device on a 16-bit bus = AM 0, bits 11:9
= 001, bits 8:7 = 01 [HWRef p.305-307](#sources).

`DynamicRasCas0-3` (0x104 + n*0x20): bits 9:8 `CAS` (01/10/11 = 1/2/3 clocks),
bits 1:0 `RAS` (01/10/11 = 1/2/3 clocks); must match the SDRAM mode register
[HWRef p.308](#sources). For the board's IS42S32800D at the operating AHB clock the
port draft uses CAS = 2, RAS = 3 [PLAN-INCREMENTAL-PORT.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/PLAN-INCREMENTAL-PORT.md).

### Static (flash / SRAM) controller

```{list-table} StaticConfig register (0x200 + n*0x20) [HWRef p.309-312](#sources)
:header-rows: 1
:widths: 12 14 12 62

* - Bits
  - Field
  - Access
  - Meaning
* - 31:21
  - reserved
  - —
  - reserved
* - 20
  - PSMC
  - R/W
  - Write protect
* - 19
  - BSMC
  - R/W
  - Write-buffer enable (must be 0 for non-SRAM peripherals)
* - 18:9
  - reserved
  - —
  - reserved
* - 8
  - EW
  - R/W
  - Extended wait (use the shared StaticExtendedWait timer; not with page mode)
* - 7
  - PB
  - R/W
  - Byte-lane state / write-enable strapping (CS1 from strap)
* - 6
  - PC
  - R/W
  - Chip-select polarity: 0 = active low, 1 = active high (CS1 from gpio[49])
* - 5:4
  - reserved
  - —
  - reserved
* - 3
  - PM
  - R/W
  - Async page mode enable (page length 4)
* - 1:0
  - MW
  - R/W
  - Memory width: 00 = 8-bit, 01 = 16-bit, 10 = 32-bit (CS1 from strap)
```

Field bits match [mach-ns9xxx regs-mem.h](https://github.com/torvalds/linux/blob/v2.6.39/arch/arm/mach-ns9xxx/include/mach/regs-mem.h) (`MEM_SMC_EW`=8, `MEM_SMC_PB`=7,
`MEM_SMC_PC`=6, `MEM_SMC_PM`=3, `MEM_SMC_MW`=1:0) and [u-boot ns9750_mem.h](https://github.com/u-boot/u-boot/blob/v2012.10/include/ns9750_mem.h).
Per-CS timing (all n = wait states, value ≈ n+1 HCLK):
`StaticWaitWen` (0x204, WE delay), `StaticWaitOen` (0x208, OE delay),
`StaticWaitRd` (0x20C, read), `StaticWaitPage` (0x210, page-mode read),
`StaticWaitWr` (0x214, write), `StaticWaitTurn` (0x218, bus turnaround)
[HWRef p.313-318](#sources). The shared `StaticExtendedWait` (0x080) times CS whose `EW`
bit is set: bits 9:0 encode (n+1)×16 HCLK cycles [HWRef p.303](#sources). On this board the
two 16-bit NOR chips use MW = 16-bit with page-burst, and the boot flash on CS0
is auto-configured by the reset straps [ANALYSIS.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/ANALYSIS.md), [PLAN-INCREMENTAL-PORT.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/PLAN-INCREMENTAL-PORT.md).

## Ethernet Communication Module


**Base address: 0xA0600000** [HWRef p.341](#sources), [u-boot ns9750_eth.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/reference/digi-cc9p9360-uboot/u-boot-1.1.4-digi/U-Boot/include/ns9750_eth.h). The module is an
Ethernet MAC plus a front-end (EFE). The MAC talks to an **external PHY** over a
software-selected **MII or RMII** interface (the board uses MII to an ICS1893 PHY)
[HWRef p.319-324](#sources), [ANALYSIS.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/ANALYSIS.md). Frames move by buffer-descriptor DMA: four
receive descriptor rings (A/B/C/D) plus one transmit ring [HWRef p.328-334](#sources).

### Ethernet register map

```{list-table} Ethernet registers (offset from 0xA0600000)
:header-rows: 1
:widths: 16 20 64

* - Offset
  - Register
  - Description
* - 0x000
  - EGCR1
  - General control 1 (RX/TX enable, DMA, MAC reset, RX init, PHY mode)
* - 0x004
  - EGCR2
  - General control 2 (TX error clear, statistics control)
* - 0x008
  - EGSR
  - General status (RX init complete)
* - 0x018 / 0x01C
  - ETSR / ERSR
  - Last transmit / receive frame status
* - 0x400 / 0x404
  - MAC1 / MAC2
  - MAC config (resets, RX enable / duplex, CRC, pad)
* - 0x408 / 0x40C
  - IPGT / IPGR
  - Back-to-back / non-back-to-back inter-packet gap
* - 0x410 / 0x414
  - CLRT / MAXF
  - Collision window/retry, max frame length
* - 0x418
  - SUPP
  - PHY support (RMII reset, RMII speed)
* - 0x420-0x434
  - MCFG..MIND
  - MII management (config, command, address, write/read data, indicators)
* - 0x440-0x448
  - SA1 / SA2 / SA3
  - Station (MAC) address octets
* - 0x500-0x508
  - SAFR / HT1 / HT2
  - Address filter, multicast hash tables
* - 0x680
  - STAT base
  - 39 statistics counters + carry/mask registers
* - 0xA00-0xA0C
  - RXAPTR..RXDPTR
  - RX descriptor ring pointers (pools A-D)
* - 0xA10 / 0xA14
  - EINTR / EINTREN
  - Interrupt status / enable
* - 0xA18-0xA20
  - TXPTR / TXRPTR / TXERBD
  - TX descriptor pointer, recover pointer, error pointer
* - 0xA28-0xA38
  - RX*OFF / TXOFF
  - Descriptor progress offsets
* - 0xA3C
  - RXFREE
  - Free-buffer notification (per pool)
* - 0x1000
  - TXBD
  - On-chip TX buffer descriptor RAM (64 descriptors)
```

Offsets and mnemonics confirmed by [u-boot ns9750_eth.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/reference/digi-cc9p9360-uboot/u-boot-1.1.4-digi/U-Boot/include/ns9750_eth.h) (`EGCR1`=0x000,
`MAC1`=0x400, `MCFG`=0x420, `SA1`=0x440, `RXAPTR`=0xA00, `TXBD`=0x1000, etc.).

### General control / status

```{list-table} EGCR1 — General Control 1 (0x000) [HWRef p.343-346](#sources)
:header-rows: 1
:widths: 12 14 12 62

* - Bits
  - Field
  - Access
  - Meaning
* - 31
  - ERX
  - R/W
  - Enable RX packet processing (0 = soft-reset RX)
* - 30
  - ERXDMA
  - R/W
  - Enable receive DMA
* - 29
  - reserved
  - —
  - reserved
* - 28
  - ERXSHT
  - R/W
  - Accept short (<64 byte) frames (debug)
* - 27:24
  - reserved
  - —
  - write 0
* - 23
  - ETX
  - R/W
  - Enable TX packet processing (0 = soft-reset TX)
* - 22
  - ETXDMA
  - R/W
  - Enable transmit DMA
* - 21
  - reserved
  - —
  - write 1
* - 20
  - reserved
  - —
  - write 0
* - 19
  - ERXINIT
  - R/W
  - Initialise RX descriptor registers from RXAPTR..RXDPTR
* - 18:16
  - reserved
  - —
  - reserved
* - 15:14
  - PHY_MODE
  - R/W
  - Interface: 00 = MII, 01 = RMII (change only while MAC reset)
* - 13:11
  - reserved
  - —
  - reserved / write 0
* - 10
  - RXALIGN
  - R/W
  - Insert 2-byte pad to long-word-align RX payload
* - 9
  - MAC_HRST
  - R/W
  - MAC host soft reset (hold >=5 us; reset 1)
* - 8
  - ITXA
  - R/W
  - Insert MAC station address into TX frames
* - 7:0
  - reserved
  - —
  - reserved
```

`EGCR2` (0x004): bit 3 `TCLER` (0→1 clears a TX error and restarts the TX
processor from TXRPTR), bit 2 `AUTOZ` (clear statistics on read), bit 1 `CLRCNT`
(clear statistics), bit 0 `STEN` (enable statistics) [HWRef p.346-347](#sources). `EGSR`
(0x008): bit 20 `RXINIT` = RX descriptor init complete [HWRef p.348](#sources). `ETSR`
(0x018) and `ERSR` (0x01C) hold the last TX / RX frame status (TXOK, collision
count, aborts; RXSIZE, RXOK, broadcast/multicast, short) and their low 16 bits are
copied into the closing buffer descriptor [HWRef p.348-353](#sources).

### MAC configuration

```{list-table} MAC1 (0x400) [HWRef p.354-355](#sources)
:header-rows: 1
:widths: 12 14 12 62

* - Bits
  - Field
  - Access
  - Meaning
* - 31:16
  - reserved
  - —
  - reserved
* - 15
  - SRST
  - R/W
  - Soft reset MAC/SAL/RMII/RX_WR/TX_RD (reset 1)
* - 14:11
  - reserved
  - —
  - reserved / write 0
* - 10
  - RPERFUN
  - R/W
  - Reset MAC receive logic
* - 9
  - RPEMCST
  - R/W
  - Reset MAC control-sublayer / transmit domain
* - 8
  - RPETFUN
  - R/W
  - Reset MAC transmit logic
* - 7:5
  - reserved
  - —
  - reserved
* - 4
  - LOOPBK
  - R/W
  - Internal loopback
* - 3:1
  - reserved
  - —
  - write 0
* - 0
  - RXEN
  - R/W
  - MAC receive enable
```

```{list-table} MAC2 (0x404) — key fields [HWRef p.355-357](#sources)
:header-rows: 1
:widths: 12 14 12 62

* - Bits
  - Field
  - Access
  - Meaning
* - 14
  - EDEFER
  - R/W
  - Defer to carrier indefinitely (802.3u)
* - 12
  - NOBO
  - R/W
  - No backoff (retransmit immediately)
* - 9
  - LONGP
  - R/W
  - Long-preamble enforcement
* - 8
  - PUREP
  - R/W
  - Pure-preamble enforcement
* - 7
  - AUTOP
  - R/W
  - Auto VLAN pad detect
* - 6
  - VLANP
  - R/W
  - VLAN pad to 64 bytes
* - 5
  - PADEN
  - R/W
  - Pad short frames (requires CRCEN)
* - 4
  - CRCEN
  - R/W
  - Append CRC to every TX frame
* - 2
  - HUGE
  - R/W
  - Allow frames longer than MAXF
* - 0
  - FULLD
  - R/W
  - Full-duplex
```

Inter-packet gap and collision: `IPGT` (0x408, back-to-back, recommend 0x15 full
/ 0x12 half duplex), `IPGR` (0x40C, IPGR1 window + IPGR2), `CLRT` (0x410, CWIN =
collision window bits 13:8, RETX = retry limit bits 3:0, reset 0x370F), `MAXF`
(0x414, max frame length, reset 0x0600 = 1536) [HWRef p.358-361](#sources). `SUPP` (0x418):
bit 15 `RPERMII` (reset RMII), bit 8 `SPEED` (RMII 10/100) [HWRef p.362](#sources). MAC1/MAC2
field bits match [u-boot ns9750_eth.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/reference/digi-cc9p9360-uboot/u-boot-1.1.4-digi/U-Boot/include/ns9750_eth.h) (`MAC1_SRST`=0x8000, `MAC1_RXEN`=0x0001,
`MAC2_FULLD`=0x0001, `MAC2_CRCEN`=0x0010, `MAC2_PADEN`=0x0020).

### MII management (PHY access)

```{list-table} MII management registers [HWRef p.363-369](#sources)
:header-rows: 1
:widths: 14 12 74

* - Register
  - Offset
  - Fields
* - MCFG
  - 0x420
  - - bit 15 RMIIM (reset)
    - bits 4:2 CLKS (MDC clock divide of AHB)
    - bit 1 SPRE (suppress preamble)
* - MCMD
  - 0x424
  - 0→1 to start:
    - bit 1 SCAN (continuous read)
    - bit 0 READ (single read)
* - MADR
  - 0x428
  - - bits 12:8 DADR (PHY device address)
    - bits 4:0 RADR (PHY register)
* - MWTD
  - 0x42C
  - bits 15:0 write data (writing triggers an MII write cycle)
* - MRDD
  - 0x430
  - bits 15:0 read data (valid after MIND.BUSY clears)
* - MIND
  - 0x434
  - - bit 3 MIILF (link fail)
    - bit 2 NVALID (read not valid)
    - bit 1 SCAN
    - bit 0 BUSY
```

An MII read: write `MADR` (PHY + register), set `MCMD.READ` (0→1), poll
`MIND.BUSY`/`MIND.NVALID`, read `MRDD`. MDC must be ≤ 2.5 MHz — set `CLKS` to
divide the AHB clock accordingly (e.g. ÷40) [HWRef p.363-366](#sources). The board's PHY is
at MDIO address 1 [REFERENCE-MATERIAL.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/REFERENCE-MATERIAL.md).

### Station address, filtering, descriptors

`SA1`/`SA2`/`SA3` (0x440/0x444/0x448) hold the 48-bit station address, two octets
per register; note octet 6 is the first byte on the wire [HWRef p.369-371](#sources).
`SAFR` (0x500): bit 3 `PRO` (promiscuous), bit 2 `PRM` (all multicast), bit 1
`PRA` (hash-filtered multicast), bit 0 `BROAD` (broadcast) [HWRef p.371](#sources). `HT1`/
`HT2` (0x504/0x508) are the 64-bit multicast hash table indexed by the top 6 bits
of the destination-address CRC [HWRef p.372-373](#sources).

Receive descriptor rings start at `RXAPTR`/`RXBPTR`/`RXCPTR`/`RXDPTR`
(0xA00-0xA0C); the transmit ring starts at `TXPTR` (0xA18, an 8-bit RAM index).
Each buffer descriptor is 16 bytes: word 0 = source address, word 1 =
buffer/frame length (11 bits), word 2 = unused, word 3 = control bits
{W = wrap, I = interrupt, E/L = enable/last, F = full} plus the 16-bit status
[HWRef p.329-332, p.403](#sources). `EINTR` (0xA10) reports RX events (bits 25:16:
FIFO overflow, buffer closed, done-per-pool, no-buffer, buffer-full, ready) and TX
events (bits 6:0: statistics overflow, buffer closed, buffer-not-ready, done, err,
idle); each bit is cleared by writing 1. `EINTREN` (0xA14) is the matching enable
mask [HWRef p.391-395](#sources). `RXFREE` (0xA3C, write-only, per-pool) tells the receiver
a buffer was freed; `TXERBD` (0xA20) points at a failed TX descriptor for recovery
via `TXRPTR` + `EGCR2.TCLER` [HWRef p.396-402](#sources).

### Statistics

39 counters based at 0x680 plus 4 carry/mask registers (`CAR1`/`CAR2` at
0x730/0x734, `CAM1`/`CAM2` at 0x738/0x73C). Counters cover combined RX+TX frame
size buckets (`TR64`…`TRMGV`, 0x680-0x698), receive counters (`RBYT`, `RPKT`,
`RFCS`, `RMCA`, `RBCA`, alignment/code/carrier/undersize/oversize/fragment/jabber),
and transmit counters (`TBYT`, `TPKT`, collisions, deferral, FCS, oversize/
undersize/fragment) [HWRef p.374-388](#sources). Enable via `EGCR2.STEN`; carry bits set
`EINTR.STOVFL` unless masked in CAM1/CAM2.

## Serial Control Module (UART / SPI)


**Base addresses:** channel B = 0x9020_0000, channel A = 0x9020_0040,
channel C = 0x9030_0000, channel D = 0x9030_0040 [HWRef p.571-572](#sources)
[u-boot ns9750_ser.h](https://github.com/u-boot/u-boot/blob/v2012.10/include/ns9750_ser.h). Each channel is a 0x40-byte block with identical layout,
independently configurable as UART, SPI master, or SPI slave (via `MODE` in
Control Register B). On the board, channel A (0x9020_0040) is the debug console at
115200 8N1 (J25 "Digi UART"), channel B carries the display unit link, and one
channel drives the MAXQ3180 metering AFE by SPI [ANALYSIS.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/ANALYSIS.md), [REFERENCE-MATERIAL.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/REFERENCE-MATERIAL.md).

### Channel register map

```{list-table} Serial channel registers (offset within the 0x40 block)
:header-rows: 1
:widths: 14 22 64

* - Offset
  - Register
  - Description
* - 0x00
  - Control Register A
  - Enable, word length, parity, stop, DMA, interrupt enables
* - 0x04
  - Control Register B
  - Mode (UART/SPI), bit order, gap-timer enables, CS polarity (SPI)
* - 0x08
  - Status Register A
  - TX/RX ready, FIFO levels, errors, modem-status change
* - 0x0C
  - Bit-rate register
  - Clock source, oversampling, divisor
* - 0x10
  - FIFO Data register
  - TX/RX data (32-byte FIFOs)
* - 0x14
  - Receive Buffer Gap Timer
  - Close RX buffer after a buffer-level idle gap
* - 0x18
  - Receive Character Gap Timer
  - Close RX buffer after a character-level idle gap
* - 0x1C / 0x20
  - Receive Match / Match Mask
  - Up to 4 byte comparators for RX matching
* - 0x34 / 0x38
  - Flow Control / Flow Control Force
  - Software/hardware XON/XOFF, forced character
```

Offsets confirmed by [u-boot ns9750_ser.h](https://github.com/u-boot/u-boot/blob/v2012.10/include/ns9750_ser.h) (`CTRL_A`=0x00, `CTRL_B`=0x04,
`STAT_A`=0x08, `BITRATE`=0x0C, `FIFO`=0x10, `RX_MATCH`=0x1C, `FLOW_CTRL`=0x34).
Each channel has a 32-byte TX FIFO and 32-byte RX FIFO; data formats are
5-8 data bits, odd/even/no parity, 1 or 2 stop bits; async up to 1.8432 Mbps
[HWRef p.564-570](#sources).

### UART Control Register A (0x00)

```{list-table} UART Control Register A [HWRef p.574-577](#sources)
:header-rows: 1
:widths: 12 14 12 62

* - Bits
  - Field
  - Access
  - Meaning
* - 31
  - CE
  - R/W
  - Channel enable (set only after all control/bit-rate fields are set)
* - 30
  - BRK
  - R/W
  - Send break
* - 29
  - STICKP
  - R/W
  - Stick parity
* - 28
  - EPS
  - R/W
  - Even parity select
* - 27
  - PE
  - R/W
  - Parity enable
* - 26
  - STOP
  - R/W
  - Stop bits: 0 = 1 stop, 1 = 2 stop
* - 25:24
  - WLS
  - R/W
  - Word length: 00 = 5, 01 = 6, 10 = 7, 11 = 8 bits
* - 23
  - CTSTX
  - R/W
  - Gate TX on external CTS
* - 22
  - RTSRX
  - R/W
  - RTS reflects RX-FIFO-almost-full
* - 21
  - RL
  - R/W
  - Remote loopback
* - 20
  - LL
  - R/W
  - Local loopback
* - 19:18
  - reserved
  - —
  - write 0
* - 17
  - DTR
  - R/W
  - DTR output
* - 16
  - RTS
  - R/W
  - RTS output
* - 15:12
  - reserved
  - —
  - write 0
* - 11:9
  - RIE
  - R/W
  - RX interrupt enables (register-ready, FIFO-half, buffer-closed)
* - 8
  - ERXDMA
  - R/W
  - Enable receive DMA
* - 7:5
  - RIC
  - R/W
  - Modem-change interrupt enables (DCD, RI, DSR)
* - 4:1
  - TIC
  - R/W
  - TX interrupt enables (CTS-change, register-empty, FIFO-half; bit 1 = 0)
* - 0
  - ETXDMA
  - R/W
  - Enable transmit DMA
```

Control Register B (0x04): bits 31:28 `RDM` (RX match-byte enables), bit 27
`RBGT` / bit 26 `RCGT` (gap-timer enables), **bits 21:20 `MODE`** (00 = UART,
10 = SPI master, 11 = SPI slave — set before CE), bit 19 `BITORDR` (0 = LSB
first), bit 15 `RTSTX` (RTS active only while transmitting, for multidrop)
[HWRef p.577-580](#sources).

### UART Status Register A (0x08)

```{list-table} UART Status Register A — selected bits [HWRef p.580-586](#sources)
:header-rows: 1
:widths: 12 14 12 62

* - Bits
  - Field
  - Access
  - Meaning
* - 31:28
  - MATCH1-4
  - R
  - RX match-byte hits
* - 27 / 26
  - BGAP / CGAP
  - R
  - Buffer / character gap-timer expiry
* - 21:20
  - RXFDB
  - R
  - RX FIFO valid-byte count (00 = word, 01 = 1, 10 = 2, 11 = 3)
* - 19:16
  - DCD/RI/DSR/CTS
  - R
  - Modem input states
* - 15:12
  - RBRK/RFE/RPE/ROVER
  - R
  - RX break / framing / parity / overrun errors
* - 11
  - RRDY
  - R
  - RX register ready (data available)
* - 10
  - RHALF
  - R
  - RX FIFO half full
* - 9
  - RBC
  - RW1TC
  - RX buffer closed (write 1 to release RRDY)
* - 8
  - RFS
  - R
  - RX FIFO has room for two more lines
* - 7:4
  - DCDI/RII/DSRI/CTSI
  - RW1TC
  - Modem-status change flags
* - 3
  - TRDY
  - R
  - TX register empty (may write FIFO)
* - 2
  - THALF
  - R
  - TX FIFO half empty
* - 0
  - TEMPTY
  - R
  - TX FIFO empty
```

### Bit-rate register (0x0C)

```{list-table} Bit-rate register [HWRef p.587-591](#sources)
:header-rows: 1
:widths: 12 14 12 62

* - Bits
  - Field
  - Access
  - Meaning
* - 31
  - EBIT
  - R/W
  - Bit-rate generator enable
* - 30
  - TMODE
  - R/W
  - Timing mode (set 1; uses TDCR/RDCR oversampling)
* - 29 / 28
  - RXSRC / TXSRC
  - R/W
  - RX/TX clock source: 0 = internal, 1 = external GPIO
* - 27 / 26
  - RXEXT / TXEXT
  - R/W
  - Drive RX/TX clock out on GPIO
* - 25:24
  - CLKMUX
  - R/W
  - Clock source: 00 = x1_sys_osc/2, 01 = BCLK, 10/11 = external RX/TX clock
* - 23 / 22
  - TXCINV / RXCINV
  - R/W
  - TX/RX clock invert (also select SPI mode phase)
* - 21
  - reserved / SPCPOL
  - R/W
  - reserved in UART; SPI clock idle polarity in SPI mode
* - 20:19
  - TDCR
  - R/W
  - TX oversampling: 01 = 8x, 10 = 16x, 11 = 32x (00 invalid for UART)
* - 18:17
  - RDCR
  - R/W
  - RX oversampling: 01 = 8x, 10 = 16x, 11 = 32x
* - 16 / 15
  - reserved / TICS,RICS
  - R/W
  - reserved in UART; SPI internal-clock source in SPI mode
* - 14:0
  - N
  - R/W
  - Divisor: $N = \dfrac{F_\text{CLK}}{\text{oversample} \times \text{baud}} - 1$
```

Field bits match [u-boot ns9750_ser.h](https://github.com/u-boot/u-boot/blob/v2012.10/include/ns9750_ser.h) (`EBIT`=0x80000000, `TMODE`=0x40000000,
`CLKMUX_MA`=0x03000000, `TCDR_MA`=bits 20:19, `RCDR_MA`=bits 18:16, `N_MA`=14:0).
`CLKMUX` = 00 selects x1_sys_osc/2 ($= 29.4912/2 = 14.7456\,\text{MHz}$); `CLKMUX` = 01
selects BCLK (the BBus clock) $= \text{AHB}/2 = f_\text{vco}/8 \approx 44.24\,\text{MHz}$ [HWRef p.566 Table 400](#sources).
Example N values for x1_sys_osc/2 at 16× oversampling: 115200 baud → N = 7,
9600 baud → N = 95, 38400 baud → N = 23 [HWRef p.591, Table 407](#sources).

```{admonition} Baud divisor convention
:class: note

Digi's U-Boot serial driver computes $N = \dfrac{\text{CONFIG_SYS_CLK_FREQ}/8}{\text{baud} \times 16} - 1$,
i.e. BBus clock = system(PLL)/8, using `CLKMUX = BCLK`
[u-boot ns9750_serial.c](https://github.com/u-boot/u-boot/blob/v2012.10/drivers/serial/ns9750_serial.c). With the correct PLL/system clock (≈354 MHz), that
BBus clock is ≈44.2 MHz, so 115200 8N1 (16×) gives N = 23. The clean
datasheet-grounded alternative is `CLKMUX = x1_sys_osc/2` (14.7456 MHz), for which
Table 407 gives N = 7 at 16× for 115200. Verify N against the actual selected
`CLKMUX` source; do not reuse an N derived from a differently-labelled "system
clock" [HWRef p.591](#sources), [PLAN-INCREMENTAL-PORT.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/PLAN-INCREMENTAL-PORT.md).
```

`FIFO Data` (0x10) is the single 32-bit TX/RX data port; the gap timers
(0x14/0x18), match/mask (0x1C/0x20), and flow-control (0x34/0x38) registers close
RX buffers on idle/pattern and implement XON/XOFF [HWRef p.592-600](#sources).

### SPI mode

Setting Control Register B `MODE` to 10 (master) or 11 (slave) reuses the same
five registers (A, B, Status A, Bit-rate, FIFO at 0x00-0x10); the other offsets
are unused [HWRef p.601-609](#sources). In SPI: word length is forced to 8 bits;
Control Register B bit 25 becomes `CSPOL` (chip-select polarity); the Bit-rate
register bits 21/16/15 become `SPCPOL`/`TICS`/`RICS`, and the SPI mode 0-3 is set
by the `SPCPOL`+`TXCINV`+`RXCINV` combination [HWRef p.605, p.610-623](#sources). SPI master
rate = BCLK/4 (max 11.07 Mbps); slave clock comes from the external master. The
recommended SPI clock source is BCLK (`CLKMUX` = 01) [HWRef p.603, p.608](#sources). The
SPI-EEPROM boot engine uses channel B in SPI mode 0 at CPU-clock/128
[HWRef p.425-426](#sources).

## I2C Master/Slave Interface


**Base address: 0x9050_0000** [HWRef p.512](#sources). A combined master/slave controller
(master and slave are mutually exclusive), two open-drain lines SDA/SCL, 7- and
10-bit addressing, multi-master arbitration, and standard (100 kHz) / fast
(400 kHz) timing [HWRef p.507-509](#sources). The board wires SDA/SCL to gpio[35]/gpio[34]
[ANALYSIS.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/ANALYSIS.md). The firmware uses this bus actively [ANALYSIS.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/ANALYSIS.md).

```{list-table} I2C registers (offset from 0x9050_0000) [HWRef p.512](#sources)
:header-rows: 1
:widths: 14 30 56

* - Offset
  - Register
  - Description
* - 0x00 (write)
  - Command Transmit Data
  - Command + transmit byte (CMD_TX_DATA_REG)
* - 0x00 (read)
  - Status Receive Data
  - Status + received byte (STATUS_RX_DATA_REG)
* - 0x04
  - Master Address
  - Master device address + 7/10-bit mode
* - 0x08
  - Slave Address
  - Slave device address + general-call enable + mode
* - 0x0C
  - Configuration
  - Timing (standard/fast), spike filter, clock divider
```

```{list-table} Command Transmit Data (write, 0x00) [HWRef p.513](#sources)
:header-rows: 1
:widths: 12 14 12 62

* - Bits
  - Field
  - Access
  - Meaning
* - 31:16
  - reserved
  - —
  - reserved
* - 15
  - PIPE
  - W
  - Pipeline mode — must be 0
* - 14
  - DLEN
  - W
  - iic_dlen — must be 0
* - 13
  - TXVAL
  - W
  - New transmit data valid
* - 12:8
  - CMD
  - W
  - Command (see below)
* - 7:0
  - TXDATA
  - W
  - Transmit byte
```

```{list-table} Status Receive Data (read, 0x00) [HWRef p.514](#sources)
:header-rows: 1
:widths: 12 14 12 62

* - Bits
  - Field
  - Access
  - Meaning
* - 31:16
  - reserved
  - —
  - reserved
* - 15
  - BSTS
  - R
  - Bus status (master): 0 = free, 1 = occupied
* - 14
  - RDE
  - R
  - Receive data enable
* - 13
  - SCMDL
  - R
  - Slave command locked
* - 12
  - MCMDL
  - R
  - Master command locked
* - 11:8
  - IRQCD
  - R
  - Interrupt code (cleared by reading this register)
* - 7:0
  - RXDATA
  - R
  - Received byte
```

Master commands (CMD field): 0x00 `M_NOP`, 0x04 `M_READ`, 0x05 `M_WRITE`,
0x06 `M_STOP`; slave commands 0x10 `S_NOP`, 0x16 `S_STOP` [HWRef p.510-511](#sources).
`Master Address` (0x04): bits 10:1 device address, bit 0 `MAM` (0 = 7-bit,
1 = 10-bit) [HWRef p.515](#sources). `Slave Address` (0x08): bit 11 `GCA` (general-call
enable, default 1), bits 10:1 `SDA` (default 0x7F), bit 0 `SAM` [HWRef p.516](#sources).
`Configuration` (0x0C): bit 15 `IRQD` (mask CPU interrupt — keep 0), bit 14 `TMDE`
(0 = standard, 1 = fast), bit 13 `VSCD` (keep 0), bits 12:9 `SFW` (spike-filter
width), bits 8:0 `CLREF` (clk_ref[9:1], must be > 3; $\text{bus clock} = \dfrac{\text{clk}}{(\text{CLREF} \times 2) + 4 + \text{scl_delay}}$,
$\text{clk} = \text{cpu_clk}/4$) [HWRef p.517-518](#sources). Interrupt codes reported in
`IRQCD` include `M_ARBIT_LOST` (1), `M_NO_ACK` (2), `M_TX_DATA` (3), `M_RX_DATA`
(4), `M_CMD_ACK` (5), and slave codes 8-F [HWRef p.518-519](#sources).

## Real Time Clock


**Base address: 0x9070_0000** [HWRef p.491](#sources). Tracks time-of-day to 10 ms with a
full calendar (year 1900-2999), an alarm, and rollover-event interrupts
[HWRef p.489-490](#sources). Time and calendar values are BCD. The board adds a coin-cell
backup [ANALYSIS.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/ANALYSIS.md).

```{list-table} RTC registers (offset from 0x9070_0000) [HWRef p.491](#sources)
:header-rows: 1
:widths: 14 26 60

* - Offset
  - Register
  - Description
* - 0x00
  - General Control
  - Enable time / calendar counters
* - 0x04
  - 12/24 Hour
  - 0 = 24-hour, 1 = 12-hour mode
* - 0x08
  - Time
  - Hours/minutes/seconds/hundredths (BCD, + PM flag)
* - 0x0C
  - Calendar
  - Century/year/date/month/day-of-week (BCD)
* - 0x10 / 0x14
  - Time Alarm / Calendar Alarm
  - Alarm match values (BCD)
* - 0x18
  - Alarm Enable
  - Per-unit alarm triggers (month/date/hour/min/sec/hsec)
* - 0x1C
  - Event Flags
  - Rollover/alarm events (clear on read)
* - 0x20
  - Interrupt Enable
  - Per-event interrupt enable
* - 0x24
  - Interrupt Disable
  - Per-event interrupt disable
* - 0x28
  - Interrupt Enable Status
  - Which events are enabled/disabled
* - 0x2C
  - General Status
  - Valid time/calendar/alarm configuration
```

`General Control` (0x00): bit 1 `Cal`, bit 0 `Time` — each 0 = enabled,
1 = disabled (both reset disabled) [HWRef p.492](#sources). `Alarm Enable` (0x18) bits 5:0
= month/date/hour/minute/second/hundredth triggers; `Event Flags` (0x1C, clear on
read) reports which fired plus a combined `Alarm` bit; `Interrupt Enable` /
`Interrupt Disable` (0x20/0x24) gate the RTC interrupt; `General Status` (0x2C)
bits 3:0 report valid configuration (`VCAC`/`VTAC`/`VCC`/`VTC`) and the counters
will not run on an invalid configuration [HWRef p.498-506](#sources). The RTC clock divider
that produces the 100 Hz tick lives in the SCM at 0xA0900224 [HWRef p.193](#sources).

## See also

**Related pages**

- {doc}`/hardware/soc-ns9360` — the NS9360 SoC overview and SCM register map
- {doc}`/hardware/soc-ns9360-io` — GPIO, BBus utility and DMA register maps
- {doc}`/hardware/peripherals/ics1893` — the Ethernet PHY on the MAC's MII bus
- {doc}`/hardware/peripherals/maxq3180` — the metering AFE on a serial-SPI channel
- {doc}`/systems/hpe-ipdu` — the board this memory/serial map describes

**External references**

- [Linux `arch/arm/mach-ns9xxx` (v2.6.39)](https://github.com/torvalds/linux/tree/v2.6.39/arch/arm/mach-ns9xxx) — `regs-mem.h` and the serial driver in the historical mainline tree
- [U-Boot documentation](https://docs.u-boot.org/en/latest/) — the open-firmware path chosen for this SoC (CFI NOR, serial, MAC)
- [Zephyr architecture-porting guide](https://docs.zephyrproject.org/latest/hardware/porting/arch.html) — the ARMv5 / ARM926EJ-S port this core needs

## Sources

Primary datasheets (in-repo, the authority for the register map):

- **NS9360 Hardware Reference**, Digi 90000675 rev J — [HWRef p.N](#sources)
  (`hpe-ipdu-firmware/datasheets/NS9360_HW_Reference_90000675_J.pdf`);
  online: <https://ftp1.digi.com/support/documentation/90000675_J.pdf>.
- **NS9360 Datasheet**, Digi 91001326 rev D — [Datasheet](#sources)
  (`hpe-ipdu-firmware/datasheets/NS9360_datasheet_91001326_D.pdf`);
  online: <https://ftp1.digi.com/support/documentation/91001326_D.pdf>.

In-repo analysis and port planning (board specifics, firmware evidence):

- [`ANALYSIS.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/ANALYSIS.md) — `hpe-ipdu-firmware/ANALYSIS.md` (board inventory, NS9360 I/O
  map, firmware register usage).
- [`REFERENCE-MATERIAL.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/REFERENCE-MATERIAL.md) — `hpe-ipdu-firmware/uboot-port/REFERENCE-MATERIAL.md`.
- [`PLAN-INCREMENTAL-PORT.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/PLAN-INCREMENTAL-PORT.md) — `hpe-ipdu-firmware/uboot-port/PLAN-INCREMENTAL-PORT.md`
  (register quick reference and clock/baud derivation).

Independent open-source cross-reference (register names, bases, bitfields):

- [mach-ns9xxx](https://github.com/torvalds/linux/tree/v2.6.39/arch/arm/mach-ns9xxx) — Linux kernel `arch/arm/mach-ns9xxx` at tag v2.6.39:
  `include/mach/regs-sys-ns9360.h`, `regs-sys-common.h`, `regs-bbu.h`,
  `regs-mem.h`, `hardware.h`, `processor-ns9360.c`, `time-ns9360.c`,
  `gpio-ns9360.c`. Raw source, e.g.
  <https://raw.githubusercontent.com/torvalds/linux/v2.6.39/arch/arm/mach-ns9xxx/include/mach/regs-sys-ns9360.h>.
- [u-boot ns9750](https://github.com/u-boot/u-boot/tree/v2012.10) — U-Boot at tag v2012.10: `include/ns9750_sys.h`,
  [`ns9750_mem.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/reference/digi-cc9p9360-uboot/u-boot-1.1.4-digi/U-Boot/include/ns9750_mem.h), [`ns9750_bbus.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/reference/digi-cc9p9360-uboot/u-boot-1.1.4-digi/U-Boot/include/ns9750_bbus.h), [`ns9750_ser.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/reference/digi-cc9p9360-uboot/u-boot-1.1.4-digi/U-Boot/include/ns9750_ser.h), `include/configs/ns9750dev.h`,
  `drivers/serial/ns9750_serial.c`. Raw source, e.g.
  <https://raw.githubusercontent.com/u-boot/u-boot/v2012.10/include/ns9750_sys.h>.
- [u-boot ns9750_eth.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/reference/digi-cc9p9360-uboot/u-boot-1.1.4-digi/U-Boot/include/ns9750_eth.h) — the Ethernet register header is not in mainline
  U-Boot; the Digi-derived version is preserved in a mirror at
  <https://raw.githubusercontent.com/true-systems/om5p-ac-v2-unlocker/master/u-boot_mr1750/include/ns9750_eth.h>.
