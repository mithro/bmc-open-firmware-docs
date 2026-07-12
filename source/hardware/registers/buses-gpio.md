# AST2050 buses (I2C/SMBus, SPI/SMC, LPC) & GPIO

Register-by-register reference for the on-chip serial buses and general-purpose
I/O of the Aspeed **AST2050 / AST1100 (G3)** BMC SoC: the I2C/SMBus controller,
the Static Memory Controller (SMC, which carries the SPI flash interface), the
LPC bridge (including the iLPC-to-AHB backdoor), and the GPIO controller.

The AST2050 is a third-generation Aspeed part (ARM926EJ-S / ARMv5TE) that
predates mainline Linux Aspeed support (which begins at the AST2400 / "G4"). The
peripherals documented here are register-compatible enough with the G4 that the
mainline G4 drivers bind with `aspeed,ast2050-*` compatibles, so the mainline
drivers are used below as an independent cross-check of the datasheet.

```{admonition} Sources and citation shorthand
:class: note

Every register fact is cross-referenced against at least two sources. Inline
citations use these tags (full list under [Sources](#sources)):

- **[DS §N p.M](#sources)** — *ASPEED AST2050/AST1100 A3 Datasheet, V1.05* (2010-05-25),
  the primary datasheet. Page numbers are the printed page numbers.
- **[hwreg.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h)**, **[ast2050.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/ast2050.h)** — Raptor Engineering AST2050 U-Boot headers
  vendored in the repo.
- **[i2c-aspeed.c](https://github.com/torvalds/linux/blob/master/drivers/i2c/busses/i2c-aspeed.c)**, **[gpio-aspeed.c](https://github.com/torvalds/linux/blob/master/drivers/gpio/gpio-aspeed.c)** — mainline Linux drivers (register
  offsets are identical to the AST2050 datasheet).
- **[RAPTOR-ANALYSIS](#sources)**, **[drivers-analysis](#sources)**, **[gpio-pin-mapping](#sources)**,
  **[culvert](#sources)** — reverse-engineering notes in the repo.

Values are register **offsets** unless a full physical address is given. All
registers are 32-bit and accessed on the APB bus (little-endian).
```

## SoC address map (relevant bases)

From the ARM Address Space Mapping table [DS §9 p.97](#sources), cross-checked against the
Raptor U-Boot headers [hwreg.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h), [ast2050.h]:

```{list-table}
:header-rows: 1
:widths: 34 26 40

* - Block
  - Physical range
  - Notes
* - Static memory (boot-up default)
  - `0x00000000`–`0x01FFFFFF`
  - 32 MiB; the boot chip-select is aliased here so the CPU fetches reset code
    from `0x00000000` [DS §9 p.97](#sources), [DS §11.3 p.105](#sources)
* - SDRAM (after re-map)
  - `0x00000000`–`0x0FFFFFFF`
  - DRAM is re-mapped over low memory after init [DS §9 p.97](#sources)
* - Static memory (flash data window)
  - `0x10000000`–`0x15FFFFFF`
  - 96 MiB; CE0/CE1/CE2 flash **data/execute** windows. Architectural CE0 base
    `0x10000000` [DS §11.1 p.100](#sources). The Raptor/ASUS boot SPI flash is accessed
    at `0x14000000` (`PHYS_FLASH_1`) with an alias base `0x10000000`
    (`PHYS_FLASH_2_BASE`) [ast2050.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/ast2050.h)
* - **Static Memory Controller (SMC) registers**
  - `0x16000000`–`0x17FFFFFF`
  - Control window; `AST_SMC_BASE` [hwreg.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h), "Base address of SMC = 0x1600_0000"
    [DS §11.1 p.100](#sources)
* - AHB Bus Controller (AHBC)
  - `0x1E600000`
  - Holds the address-remap register `AHB_ADDR_REMAP_REG` (`+0x8C`) [hwreg.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h)
* - Interrupt controller (VIC)
  - `0x1E6C0000`
  - Compact G3 layout [hwreg.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h)
* - SDRAM controller / SCU
  - `0x1E6E0000` / `0x1E6E2000`
  - lock-key protected [hwreg.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h)
* - **GPIO controller**
  - `0x1E780000`
  - `AST_GPIO_BASE` [hwreg.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h); [DS §9 p.97](#sources), [DS §23.3 p.262](#sources)
* - **LPC controller**
  - `0x1E789000`
  - [DS §9 p.97](#sources), [DS §30.3 p.311](#sources)
* - **I2C/SMBus controller**
  - `0x1E78A000`
  - [DS §9 p.97](#sources), [DS §31.4 p.334](#sources); `0x40` stride per engine [RAPTOR-ANALYSIS](#sources)
```

---

## I2C / SMBus controller

Base `0x1E78A000` [DS §31.1 p.327](#sources). The block is **one global register set plus
seven identical 64-byte device (channel) register sets**, followed by a 256-byte
shared buffer pool [DS §31.1 p.327](#sources), [DS §31.4.1 p.334](#sources). Each device is an
independent I2C/SMBus master **and/or** slave engine. Devices #1 and #2 are the
only ones that additionally support FML mode, SMBus alert pins, and DMA buffers
[DS §31.2 p.327-328](#sources).

```{admonition} How many I2C buses does the AST2050 really have? — 7, not 14
:class: warning

The datasheet is explicit: *"I2C/SMBus Controller implements one set of global
registers and **7 sets of device registers**"* and *"Support totally **7**
I2C/SMBus devices"* [DS §31.1 p.327](#sources), [DS §31.2.5 p.328](#sources). The address table only
allocates Device 1–7 [DS §31.4.1 p.334](#sources).

The reconstructed KGPE-D16 device tree lists **14** buses (`i2c0`…`i2c13` at
`i2c-bus@40 … @480`) and the Aspeed vendor SDK `i2c-ast.c` registers 14 platform
devices [RAPTOR-ANALYSIS](#sources), because both are templated from the **AST2400 (G4)**,
which has 14 engines. On the AST2050 only the first 7 (offsets `0x40`–`0x1FF`)
are physically present; the `@300`–`@480` nodes have no backing hardware.
```

### Address / channel layout

Global registers occupy `0x000`–`0x03F`; each device occupies a 64-byte
(`0x40`) window [DS §31.4.1 p.334]:

```{list-table}
:header-rows: 1
:widths: 30 24 46

* - Region
  - Offset range
  - Size / notes
* - Global Register
  - `0x000`–`0x03F`
  - 64 B — interrupt-status summary + pin mux
* - Device 1
  - `0x040`–`0x07F`
  - 64 B — FML / SMBus-alert / DMA capable
* - Device 2
  - `0x080`–`0x0BF`
  - 64 B — FML / SMBus-alert / DMA capable
* - Device 3
  - `0x0C0`–`0x0FF`
  - 64 B
* - Device 4
  - `0x100`–`0x13F`
  - 64 B
* - Device 5
  - `0x140`–`0x17F`
  - 64 B
* - Device 6
  - `0x180`–`0x1BF`
  - 64 B
* - Device 7
  - `0x1C0`–`0x1FF`
  - 64 B
* - Buffer Pool
  - `0x200`–`0x2FF`
  - 256 B shared internal SRAM (Pool-buffer mode) [DS §31.2.5 p.328](#sources)
```

### Global registers (`0x000`–`0x03F`)

```{list-table}
:header-rows: 1
:widths: 12 20 12 56

* - Offset
  - Name
  - R/W
  - Description
* - `0x00`
  - I2CG00 Device Interrupt Status
  - R
  - Summary of interrupt events from all 7 devices. Bit 0 = Dev #1 …
    Bit 6 = Dev #7 (1 = interrupt occurs). Bits 31:7 reserved. Read-only
    summary — cleared by clearing the source device's status [DS §31.4.2 p.334](#sources)
* - `0x04`
  - I2CG04 I2C6/I2C7 Pin Multiplexing
  - RW
  - Bits 1:0 select the pin mux for I2C1/I2C2/I2C6/I2C7: `00` = 7-set I2C;
    `01` = 6-set I2C + 2 Alert (I2C1/2); `10` = 6-set I2C + 1 FML (I2C1);
    `11` = 5-set I2C + 2 FML (I2C1/2). Bits 31:2 reserved [DS §31.4.2 p.335](#sources)
```

### Per-device register map (offsets within each `0x40` window)

Confirmed identical to mainline [i2c-aspeed.c](https://github.com/torvalds/linux/blob/master/drivers/i2c/busses/i2c-aspeed.c) offsets (`FUN_CTRL 0x00`,
`AC_TIMING_REG1 0x04`, `AC_TIMING_REG2 0x08`, `INTR_CTRL 0x0c`, `INTR_STS 0x10`,
`CMD 0x14`, `DEV_ADDR 0x18`, `BYTE_BUF 0x20`).

```{list-table}
:header-rows: 1
:widths: 12 24 10 12 42

* - Offset
  - Register
  - R/W
  - Reset
  - Purpose
* - `0x00`
  - I2CD00 Function Control
  - RW
  - `0`
  - Master/slave enable, address-response enables, drive modes [DS §31.4.3 p.335](#sources)
* - `0x04`
  - I2CD04 Clock & AC Timing #1
  - RW
  - `X`
  - Base-clock divisors + tBUF/tHDSTA/tACST/tCKHigh/tCKLow/tHDDAT [DS §31.4.3 p.337](#sources)
* - `0x08`
  - I2CD08 Clock & AC Timing #2
  - RW
  - `X`
  - SCL clock-low timeout cycles [DS §31.4.3 p.338](#sources)
* - `0x0C`
  - I2CD0C Interrupt Control
  - RW
  - `0`
  - Per-event interrupt enables [DS §31.4.3 p.338](#sources)
* - `0x10`
  - I2CD10 Interrupt Status
  - RW (W1C)
  - `0`
  - Per-event interrupt status; write-1-to-clear [DS §31.4.3 p.339](#sources)
* - `0x14`
  - I2CD14 Command / Status
  - RW / R
  - `0`
  - Master/slave commands + line/bus state + debug state machine [DS §31.4.3 p.340](#sources)
* - `0x18`
  - I2CD18 Slave Device Address
  - RW
  - `X`
  - Bits 6:0 = 7-bit slave address; 31:7 reserved [DS §31.4.3 p.342](#sources)
* - `0x1C`
  - I2CD1C Pool Buffer Control
  - RW / R
  - `X`
  - Tx/Rx pool-buffer base/end pointers + received-count pointer [DS §31.4.3 p.343](#sources)
* - `0x20`
  - I2CD20 Tx/Rx Byte Buffer
  - RW / R
  - `X`
  - Byte-buffer mode: 7:0 Tx (RW), 15:8 Rx (R); 31:16 reserved [DS §31.4.3 p.343](#sources)
* - `0x24`
  - I2CD24 DMA Mode Control *(Dev #1/#2 only)*
  - RW
  - `X`
  - 27:12 DMA buffer base (4 KiB aligned), 11:0 DMA size; 31:28 reserved [DS §31.4.3 p.343](#sources)
* - `0x28`
  - I2CD28 DMA Mode Status *(Dev #1/#2 only)*
  - R
  - `X`
  - 11:0 last-accessed DMA address / byte count; 31:12 reserved [DS §31.4.3 p.344](#sources)
* - `0x2C`–`0x3F`
  - *(reserved)*
  - —
  - —
  - Not defined; do not access
```

#### I2CD00 — Function Control Register (`+0x00`) [DS §31.4.3 p.335-336](#sources)

```{list-table}
:header-rows: 1
:widths: 12 10 78

* - Bit
  - R/W
  - Description
* - 31:16
  - —
  - Reserved (0)
* - 15
  - RW
  - Disable multi-master capability (master only): 1 = single-master, skip
    arbitration-lost check
* - 14
  - RW
  - Enable SCL direct-drive mode (master only): 1 = always drive (no
    open-drain tri-state). Extension of bit 7
* - 13:12
  - RW
  - Clock-cycle selection for slowing down FML master clock (Dev #1/#2; reserved
    otherwise): `00`=+2 … `11`=+5 APB cycles
* - 11
  - RW
  - Enable slow-down FML master clock (Dev #1/#2; reserved otherwise)
* - 10
  - RW
  - Receiving data-mode selection: 0 = filter SCL/SDA (drop <1 APB-cycle
    glitches); 1 = sample (synchronize)
* - 9
  - RW
  - Data sequence: 0 = MSB-first, 1 = LSB-first
* - 8
  - RW
  - Enable SDA actively driven high for 1T (before tri-state) — higher transfer rate
* - 7
  - RW
  - Enable SCL actively driven high for 1T (master only)
* - 6
  - RW
  - Enable FML function mode (Dev #1/#2 only; reserved otherwise)
* - 5
  - RW
  - Enable SMBus **Device Default Address** (`1100_001`) response
* - 4
  - RW
  - Enable SMBus **Device Alert Response Address** (`0001_100`) response
* - 3
  - RW
  - Enable SMBus **ARP Host Address** (`0001_000`) response
* - 2
  - RW
  - Enable I2C **General Call Address** (`0000_000`) response
* - 1
  - RW
  - Enable slave function
* - 0
  - RW
  - Enable master function
```

```{note}
When both master and slave functions are disabled simultaneously, the device's
interrupt-control (`I2CD0C`), interrupt-status (`I2CD10`) and command
(`I2CD14`) registers are reset [DS §31.4.3 p.336](#sources). In that state
`I2CD14[15:12]` become direct GPIO drives of SCL/SDA for manual bus-lock
recovery.
```

#### I2CD04 — Clock & AC Timing Control #1 (`+0x04`) [DS §31.4.3 p.337-338](#sources)

```{list-table}
:header-rows: 1
:widths: 12 66 22

* - Bit
  - Field
  - Encoding
* - 31:28
  - tBUF — bus-free time (Stop→Start)
  - `0nnn` = 1–8 × Base-Clock #1; `1nnn` = 1–8 × Base-Clock #2
* - 27:24
  - tHDSTA — master Start hold time
  - as tBUF (Base-Clock #1 / #2)
* - 23:20
  - tACST — master Start/Stop setup/hold (max of tSUSTA, tHDSTAr, tSUSTO)
  - as tBUF (Base-Clock #1 / #2)
* - 19
  - Reserved
  - —
* - 18:16
  - tCKHigh — SCL high pulse width
  - `000`–`111`; value depends on FML-enable and Base-Clock #1 divisor [DS §31.4.3 p.337](#sources)
* - 15
  - Reserved
  - —
* - 14:12
  - tCKLow — SCL low pulse width
  - `000`=1 … `111`=8 cycles of Base-Clock #1
* - 11:10
  - tHDDAT — master/slave data hold
  - master `00`=1…`11`=4; slave `00`=0…`11`=3 (Base-Clock #1)
* - 9:8
  - Timeout base-clock divisor (from APB clock)
  - `00`÷16 K, `01`÷64 K, `10`÷256 K, `11`÷1024 K
* - 7:4
  - Base-Clock #2 divisor (from APB clock)
  - `0000`÷2, `0001`÷4 … `1111`÷65536
* - 3:0
  - Base-Clock #1 divisor (from APB clock)
  - `0000`÷1, `0001`÷2 … `1111`÷32768
```

`Freq(SCL) = Freq(CoreClock) / (tBaseCyc × (tCKLow + tCKHigh))`, with
`tBaseCyc ∈ {1,2,4,…,32768}` and `tCKLow, tCKHigh ∈ {1..8}` [DS §31.3 p.329](#sources).
A full divisor→(Base clock, tCKHigh, tCKLow) lookup is tabulated at [DS §31.3.1
p.333]. Corroborated by [i2c-aspeed.c](https://github.com/torvalds/linux/blob/master/drivers/i2c/busses/i2c-aspeed.c)'s `aspeed_i2c_24xx_get_clk_reg_val`.

#### I2CD08 — Clock & AC Timing Control #2 (`+0x08`) [DS §31.4.3 p.338](#sources)

Bits 31:3 reserved. Bits **2:0** = cycles of clock-low timeout (`tTimeOut`):
`000` = no timeout control, `001` = 1–2 … `111` = 7–8 cycles of the Timeout
Base Clock (one cycle of uncertainty because the timeout counter free-runs).

#### I2CD0C / I2CD10 — Interrupt Control / Status (`+0x0C` / `+0x10`)

`I2CD0C` (enable, RW, reset 0) and `I2CD10` (status, W1C, reset 0) share the same
bit layout [DS §31.4.3 p.338-340](#sources). Bits 31:14 reserved.

```{list-table}
:header-rows: 1
:widths: 10 90

* - Bit
  - Event
* - 13
  - Bus Recover Done
* - 12
  - SMBus Device Alert
* - 11
  - SMBus ARP Host Address Detection
* - 10
  - SMBus Device Alert Response Address Detection
* - 9
  - SMBus Device Default Address Detection
* - 8
  - General Call Address Detection
* - 7
  - Slave Address Received Match
* - 6
  - SCL clock-low timeout
* - 5
  - Abnormal Start/Stop condition detected (illegal transfer state)
* - 4
  - Normal Stop condition detected (master: Stop issued; slave: Stop seen)
* - 3
  - Master arbitration loss
* - 2
  - Receive Done (all expected bytes received / buffer full / terminated)
* - 1
  - Transmit with NACK returned
* - 0
  - Transmit Done with ACK returned
```

`I2CD10` bits are cleared by writing `1` ("WC"). Software must clear the Receive
Done status (bit 2) to allow the next byte reception [DS §31.4.3 p.340](#sources).

#### I2CD14 — Command / Status Register (`+0x14`) [DS §31.4.3 p.340-342](#sources)

The command half (RW) fires transfers; the status half (R) exposes line/bus
state and the transfer state machine. Command bit positions match mainline
[i2c-aspeed.c](https://github.com/torvalds/linux/blob/master/drivers/i2c/busses/i2c-aspeed.c) (`M_START_CMD BIT(0)`, `M_TX_CMD BIT(1)`, `M_RX_CMD BIT(3)`,
`M_S_RX_CMD_LAST BIT(4)`, `M_STOP_CMD BIT(5)`).

```{list-table}
:header-rows: 1
:widths: 12 10 78

* - Bit
  - R/W
  - Description
* - 31:29
  - —
  - Reserved (0)
* - 28
  - R
  - SDA_OE (debug only) — SDA output-enable state
* - 27
  - R
  - SDA_O (debug only) — SDA output value
* - 26
  - R
  - SCL_OE (debug only)
* - 25
  - R
  - SCL_O (debug only)
* - 24:23
  - R
  - Transfer-mode timing stage (debug): `00`=T0 … `11`=T3
* - 22:19
  - R
  - Transfer-mode state machine (debug): `0000`=IDLE, `1000`=MACTIVE,
    `1001`=MSTART, `1010`=MSTARTR, `1011`=MSTOP, `1100`=MTXD, `1101`=MRXACK,
    `1110`=MRXD, `1111`=MTXACK, `0001`=SWAIT, `0100`=SRXD, `0101`=STXACK,
    `0110`=STXD, `0111`=SRXACK, `0011`=RECOVER
* - 18
  - R
  - Sampled SCL line state
* - 17
  - R
  - Sampled SDA line state
* - 16
  - R
  - Bus Busy status (0 = idle, 1 = busy / idle-timing not met)
* - 15
  - RW
  - SDA_OE direct control (GPIO; active only when master **and** slave disabled) — bus-lock recovery
* - 14
  - RW
  - SDA_O direct control
* - 13
  - RW
  - SCL_OE direct control
* - 12
  - RW
  - SCL_O direct control
* - 11
  - RW
  - Enable Bus Recover command (valid only when SCL high; issues 1–8 SCL clocks
    to free a slave-locked SDA; state machine must be IDLE)
* - 10
  - RW
  - Issue I2C/SMBus Slave Alert signal (Dev #1/#2 only; auto-cleared on address match)
* - 9
  - RW
  - Enable Master/Slave Receive **from DMA** buffer (Dev #1/#2)
* - 8
  - RW
  - Enable Master/Slave Transmit **from DMA** buffer (Dev #1/#2)
* - 7
  - RW
  - Enable Master/Slave Receive into **Pool** buffer
* - 6
  - RW
  - Enable Master/Slave Transmit from **Pool** buffer
* - 5
  - RW
  - **Master Stop** command (4th priority; auto-cleared)
* - 4
  - RW
  - Master/Slave Receive Command Last (0 = respond ACK/continue, 1 = respond NACK/end)
* - 3
  - RW
  - **Master Receive** command (3rd priority; auto-cleared)
* - 2
  - RW
  - **Slave Transmit** command
* - 1
  - RW
  - **Master Transmit** command (2nd priority; auto-cleared)
* - 0
  - RW
  - **Master Start** / Repeated-Start command (1st priority; only when master
    enabled and bus idle; auto-cleared)
```

When several commands are written together they execute in priority order:
(1) Master Start, (2) Master Transmit, (3) Slave Transmit **or** Master Receive,
(4) Master Stop. Hardware clears each on completion, and clears **all** on
arbitration loss or an invalid Start/Stop. Master and Slave commands must not be
active at the same time [DS §31.4.3 p.342](#sources).

#### I2CD1C — Pool Buffer Control (`+0x1C`) [DS §31.4.3 p.343](#sources)

```{list-table}
:header-rows: 1
:widths: 12 10 78

* - Bit
  - R/W
  - Description
* - 31:24
  - R
  - Actual received pool-buffer address pointer (received byte count = pointer − base×4 + 1; 0 ⇒ 256 bytes)
* - 23:16
  - RW
  - Receive pool-buffer end address (buffer size = end − base×4 + 1)
* - 15:8
  - RW
  - Transmit data-buffer end address (Tx byte count = end − base×4 + 1)
* - 7:6
  - —
  - Reserved
* - 5:0
  - RW
  - Buffer base-address pointer (unit = one dword; shared by Tx and Rx)
```

### SMBus / FML / general notes

- **I2C master**: Philips I2C-BUS v2.1 compatible; multi-master; 0.5 Kbps–8 Mbps
  at 50 MHz core clock; clock stretching; arbitration-lost interrupt with
  automatic transfer cancel; bus-lock recovery [DS §31.2.1 p.327](#sources).
- **I2C slave**: 7-bit addressing only; controllable General-Call response;
  clock stretching; automatic ACK/NACK [DS §31.2.2 p.327](#sources).
- **SMBus**: SBS SMBus 2.0 compatible; controllable ARP Host Address
  (`0001_000`), ARP Device Default Address (`1100_001`), Alert Response Address
  (`0001_100`); **two alert pins** for the two SMBus/I2C controllers (Devices #1
  and #2) supporting master-alert interrupt and slave-alert [DS §31.2.3 p.328](#sources).
- **FML**: Devices #1/#2 can be programmed as FML controllers, up to 8 Mbps
  [DS §31.2.4 p.328](#sources).
- **Buffer modes**: Byte buffer (dedicated register `I2CD20`), Pool buffer
  (256 B shared SRAM at `0x200`), DMA buffer (up to 4 KiB from SDRAM, Devices
  #1/#2 only) [DS §31.2.5 p.328](#sources). Initialization order: write `I2CD00` enable,
  `I2CD04`, `I2CD08`, `I2CD10=0xFFFFFFFF`, `I2CD0C` enables [DS §31.5.1 p.344](#sources).
- Board usage: on the Dell C410X, I2C engine 3 (bus `0xF3`) drives the PEX PCIe
  switches; expander/sensor buses `0xF0`–`0xF6` hang off the other engines
  [gpio-pin-mapping](#sources). Corroborated by mainline [i2c-aspeed.c](https://github.com/torvalds/linux/blob/master/drivers/i2c/busses/i2c-aspeed.c)
  (`aspeed,ast2400-i2c-bus`), whose register map matches the above.

---

## SPI / SMC flash controller

The AST2050 uses the **legacy Static Memory Controller (SMC)** — *not* the newer
FMC/SPI controllers of the AST2400+. Register (control) window base
`0x16000000` [DS §11.1 p.100](#sources), [hwreg.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h); flash **data/execute** windows live in
the `0x10000000`–`0x15FFFFFF` static-memory region [DS §9 p.97](#sources).

The SMC implements **8 × 32-bit registers** and can drive up to three chip
selects (CE0/CE1/CE2), each independently programmable as **NOR / NAND / SPI**
flash. **On the AST2050/AST1100, only the SPI-flash interface is supported** —
the NOR/NAND register views are documented as a superset and are inert on this
part [DS §11.1 p.100](#sources).

```{admonition} Flash address windows
:class: note

- Architectural CE0 base = `0x10000000`; CE1 = `0x10000000 + SegSize`;
  CE2 = `0x10000000 + 2×SegSize`, where SegSize is set by `SMC00[1:0]`
  (32/16/8/4 MiB) [DS §11.1 p.100](#sources), [DS §11.3 p.105](#sources).
- Only one CE can be the CPU-boot chip select (mapped to `0x00000000`); default
  types are CE0=NOR, CE1=NAND, CE2=SPI [DS §11.1 p.100](#sources).
- The Raptor/ASUS single-SPI board maps its boot flash at `0x14000000`
  (`PHYS_FLASH_1`) with alias `0x10000000` (`PHYS_FLASH_2_BASE`) [ast2050.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/ast2050.h).
- The SMC **register** window (this block) is at `0x16000000` [hwreg.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h).
```

### Register map (base `0x16000000`) [DS §11.3 p.105-112](#sources)

```{list-table}
:header-rows: 1
:widths: 12 30 10 14 34

* - Offset
  - Register
  - R/W
  - Reset
  - Purpose
* - `0x00`
  - SMC00 CE0 Segment / AC Timing
  - RW
  - `0x00000240`
  - Per-CE flash-type + segment-size + segment write-enable
* - `0x04`
  - SMC04 CE0 Control
  - RW
  - `0`
  - CE0 command/timing (view depends on `SMC00[5:4]` type)
* - `0x08`
  - SMC08 CE1 Control
  - RW
  - `0`
  - CE1 command/timing (view depends on `SMC00[7:6]`)
* - `0x0C`
  - SMC0C CE2 Control
  - RW
  - `0`
  - CE2 command/timing (view depends on `SMC00[9:8]`)
* - `0x10`
  - SMC10 Misc. Control
  - RW
  - `0`
  - NOR/NAND timers, NAND ECC mode, WP#/RB# pin control
* - `0x14`
  - SMC14 NAND ECC Generation Control/Status
  - RW / R
  - `0`
  - NAND SECDED ECC generation (inert on AST2050)
* - `0x18`
  - SMC18 NAND ECC check value
  - RW
  - `0`
  - Stored ECC to compare against
* - `0x1C`
  - SMC1C NAND ECC check result
  - R
  - `0`
  - ECC pass/fail + error position
```

#### SMC00 — CE Segment / AC Timing (`+0x00`) [DS §11.3 p.105](#sources)

```{list-table}
:header-rows: 1
:widths: 12 10 78

* - Bit
  - R/W
  - Description
* - 31:13
  - —
  - Reserved (0)
* - 12
  - RW
  - Enable CE2 segment write (0 = read-only, 1 = writable)
* - 11
  - RW
  - Enable CE1 segment write
* - 10
  - RW
  - Enable CE0 segment write
* - 9:8
  - RW
  - CE2 flash type: `00` NOR, `01` NAND, `1x` **SPI NOR (default)**
* - 7:6
  - RW
  - CE1 flash type: `00` NOR, `01` **NAND (default)**, `1x` SPI NOR
* - 5:4
  - RW
  - CE0 flash type: `00` **NOR (default)**, `01` NAND, `1x` SPI NOR
* - 3:2
  - RW
  - Reserved
* - 1:0
  - RW
  - Segment size: `00` **32 MB (default)**, `01` 16 MB, `10` 8 MB, `11` 4 MB
```

#### SMC04/08/0C — CE Control, **SPI-flash view** (`+0x04/08/0C`) [DS §11.3 p.107-108](#sources)

This is the operative view on the AST2050. The register meaning switches on the
CE's type field in `SMC00`.

```{list-table}
:header-rows: 1
:widths: 12 10 78

* - Bit
  - R/W
  - Description
* - 31:28
  - RW
  - Reserved
* - 27:24
  - RW
  - CE# inactive pulse width: `0000`=16T … `1111`=1T (T = 1 HCLK)
* - 23:16
  - RW
  - Command data — byte used for Fast-Read command or Byte-Write CMD phase
* - 15:13
  - RW
  - Reserved
* - 12
  - RW
  - Disable SPI-flash **read-command merge**: 0 = enable (default; merges
    continuous-address reads within 16 clocks), 1 = disable (perf penalty)
* - 11
  - RW
  - Reserved
* - 10:8
  - RW
  - SPI clock frequency (t-CK): `000` HCLK/16 (default), `001` /14, `010` /12,
    `011` /10, `100` /8, `101` /6, `110` /4, `111` /2
* - 7:6
  - RW
  - Dummy cycles before data for Fast-Read: `00` 0 B (default) … `11` 3 B
* - 5
  - RW
  - MSB/LSB-first: 0 = MSB-first (default for boot code), 1 = LSB-first
* - 4
  - RW
  - Clock Mode_0 / Mode_3 select (initial SPI clock 0 vs 1)
* - 3
  - RW
  - Enable dual-data input mode (2 bits/clock, doubles read rate)
* - 2
  - RW
  - User-Mode CE# active control (1 = deassert CE# after op / on CE change)
* - 1:0
  - RW
  - Command Mode: `00` Normal Read (`03h`+addr+data), `01` Fast Read (CMD+addr+data),
    `10` Normal Write, `11` User Mode (raw read/write, 1–4 bytes)
```

```{admonition} SMC read-path behavior
:class: note

By default the SMC **merges continuous-address reads** so that reads within 16
clocks issue a single SPI read command, reducing per-access command overhead;
setting `SMC04[12]=1` disables this (with a performance penalty) [DS §11.3
p.107]. Except in User Mode the address space supports up to 16 MiB [DS §11.3
p.108]. Boot/execute reads use Normal Read (`03h`) at HCLK/16, MSB-first, no
dummy cycles by reset default. The AST2050 SMC read path binds unchanged in the
QEMU/kernel G3 model [drivers-analysis](#sources).
```

For completeness the same register has a **NOR-flash view** (bits: 31:30 timer
unit, 29:28 operation mode {normal / t-WEL·t-OEL-long / ACK-control}, 27:24
t-CEH, 23:20 t-ACT2CE, 19:16 t-WEH, 15:12 t-WEL, 11:8 t-OEH, 7:4 t-OEL, 3:0
t-CE2ACT) and a **NAND-flash view** (31:28 t-WEH, 27:24 t-WEL, 23:20 t-REH,
19:16 t-REL, 15:12 t-CESH, 11:10 t-WTR, 9:4 boot-read busy wait time, 3 user-mode
row-address cycles, 2 user-mode CE# active, 1 random-read, 0 boot/user mode)
[DS §11.3 p.105-108](#sources). Both views are inert on the AST2050.

#### SMC10 — Misc. Control (`+0x10`) [DS §11.3 p.109-111](#sources)

```{list-table}
:header-rows: 1
:widths: 12 10 78

* - Bit
  - R/W
  - Description
* - 31:24
  - RW
  - NOR timer value setting (unit from `SMC04/08/0C[31:30]`)
* - 23
  - RW
  - NOR ACK# control timeout interrupt status (write 1 to clear)
* - 22
  - RW
  - NOR ACK# control timeout interrupt enable
* - 21
  - RW
  - NAND timer interrupt status (write 1 to clear)
* - 20
  - RW
  - NAND timer interrupt enable
* - 19
  - RW
  - NAND timer enable (0 resets timer)
* - 18:8
  - RW
  - NAND timer value setting (0 = disabled; else value × 4 µs)
* - 7:6
  - RW
  - NAND ECC mode: `00` 256 B, `01` 512 B, `10` 1024 B, `11` 2048 B
* - 5
  - RW
  - WP# output value (write enable when WP# supported)
* - 4
  - RW
  - WP# pin supported (must be pulled low externally)
* - 3
  - R
  - R/B# pin input value (0 busy, 1 normal)
* - 2
  - RW
  - R/B# rising-edge detect status (write 1 to clear)
* - 1
  - RW
  - Enable R/B# status interrupt
* - 0
  - RW
  - R/B# pin supported
```

#### SMC14 / SMC18 / SMC1C — NAND ECC (inert on AST2050) [DS §11.3 p.111-112](#sources)

- **SMC14** (`+0x14`): 31:30 reserved(0), 29 ECC reset enable, 28 ECC generation
  enable (max 2048-byte SECDED), 27:0 ECC value (R).
- **SMC18** (`+0x18`): 31:28 reserved(0), 27:0 ECC check value (RW) — SW writes
  the stored ECC for the hardware compare.
- **SMC1C** (`+0x1C`, R): 31 ECC unrecoverable error, 30 ECC field error (1-bit,
  no correct needed), 29 recoverable error (needs correct), 28 ECC check pass,
  27:16 ECC accumulate counter, 15:14 reserved(0), 13:3 recoverable error byte
  position, 2:0 recoverable error bit position.

```{admonition} Mainline cross-reference caveat
:class: warning

Mainline's [`spi-aspeed-smc.c`](https://github.com/torvalds/linux/blob/master/drivers/spi/spi-aspeed-smc.c) targets the **AST2400+ FMC/SPI** controllers
(`aspeed,ast2400-fmc`/`-spi` …) whose register layout differs from the legacy
AST2050 SMC documented here; the older `drivers/mtd/maps/ast-nor.c` was removed
upstream [drivers-analysis](#sources). So for this block the datasheet is the sole primary;
the repo headers [hwreg.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h), [ast2050.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/ast2050.h) and RE notes corroborate the base
addresses and SPI-only usage.
```

---

## LPC controller

Base `0x1E789000` [DS §30.3 p.312](#sources), [DS §9 p.97](#sources). The block integrates **both**
an LPC **Host** controller and an LPC **Slave** controller (only one enabled at a
time), plus an IPMI 2.0/1.1 BMC KCS/BT interface, port-80h/81h snooping, two
Virtual UARTs, and — most relevant to security posture — the **LPC-to-AHB
bridge** ("iLPC2AHB"). There are **49 registers** [DS §30.1 p.311](#sources). Register
offsets 0x00–0x7C are H8S/2168-compatible.

### Register map (base `0x1E789000`) [DS §30.3 p.311-326](#sources)

```{list-table}
:header-rows: 1
:widths: 12 26 62

* - Offset
  - Register
  - Purpose
* - `0x00`
  - HICR0
  - Host Interface Control 0 — LPC channel #1/#2/#3 enables, SW shutdown, PME
* - `0x04`
  - HICR1
  - Host Interface Control 1 — LPC/SERIRQ busy flags, SW reset/shutdown, PME bit
* - `0x08`
  - HICR2
  - Host Interface Control 2 — LPC reset/shutdown/abort IRQ status + IBF/error IRQ enables
* - `0x0C`
  - HICR3
  - Host Interface Control 3 — LFRAME/CLKRUN/SERIRQ/LRESET/LPCPD/PME pin monitoring
* - `0x10`
  - HICR4
  - Host Interface Control 4 — LADR12 select, KCS/BT enable for channel #3
* - `0x14`
  - LADR3H
  - LPC channel #3 address, bits [15:8]
* - `0x18`
  - LADR3L
  - LPC channel #3 address, bits [7:0]
* - `0x1C`
  - LADR12H
  - LPC channel #1/#2 address, bits [15:8]
* - `0x20`
  - LADR12L
  - LPC channel #1/#2 address, bits [7:0] (reset `60h`/`62h`)
* - `0x24`
  - IDR1
  - Channel #1 input data register
* - `0x28`
  - IDR2
  - Channel #2 input data register
* - `0x2C`
  - IDR3
  - Channel #3 input data register
* - `0x30`
  - ODR1
  - Channel #1 output data register
* - `0x34`
  - ODR2
  - Channel #2 output data register
* - `0x38`
  - ODR3
  - Channel #3 output data register
* - `0x3C`
  - STR1
  - Channel #1 status (C/D1, IBF1, OBF1, user bits)
* - `0x40`
  - STR2
  - Channel #2 status
* - `0x44`
  - STR3
  - Channel #3 status
* - `0x48`
  - BTR0
  - BT status register 0 (FIFO read/host read/write/BTDTR IRQs)
* - `0x4C`
  - BTR1
  - BT status register 1 (reset / event / read-end / write-end / pointer-clear IRQs)
* - `0x50`
  - BTCSR0
  - BT control/status 0 — FIFO select + BT IRQ enables
* - `0x54`
  - BTCSR1
  - BT control/status 1 — slave-reset-read + BT IRQ enables
* - `0x58`
  - BTCR
  - BT control register — busy flags, event ATN, pointer clears
* - `0x5C`
  - BTDTR
  - BT data buffer (read/write)
* - `0x60`
  - BTIMSR
  - BT interrupt mask register — BMC HW reset, OEM user bits
* - `0x64`
  - BTFVSR0
  - BT FIFO valid size (host write transfer)
* - `0x68`
  - BTFVSR1
  - BT FIFO valid size (host read transfer)
* - `0x6C`
  - *(reserved)*
  - Not defined
* - `0x70`
  - SIRQCR0
  - SERIRQ control 0 — quiet/continuous flag, direct mode, SMI/IRQ enables
* - `0x74`
  - SIRQCR1
  - SERIRQ control 1 — host IRQ6/9/10/11 enables (sets 2 & 3)
* - `0x78`
  - SIRQCR2
  - SERIRQ control 2 — direct mode 3
* - `0x7C`
  - SIRQCR3
  - SERIRQ control 3 — SERIRQ output select (IRQ1/6/9/10/11/12/SMI)
* - `0x80`
  - **HICR5**
  - Host Interface Control 5 — **LPC-to-AHB bridge enable/base**, IRQX, FWH,
    PME/snoop enables
* - `0x84`
  - **HICR6**
  - Host Interface Control 6 — LPC-to-AHB decode range (`HWNCARE`), PME/snoop status
* - `0x88`
  - **HICR7**
  - Host Interface Control 7 — LPC-to-AHB remap base [31:16] (`ADRBASE`)
* - `0x8C`
  - **HICR8**
  - Host Interface Control 8 — LPC-to-AHB remap mask [31:16] (`ADRMASK`)
* - `0x90`
  - SNPWADR
  - LPC snoop address (snoop #1 [31:16], snoop #0 [15:0]) — e.g. port 80h/81h
* - `0x94`
  - SNPWDR
  - LPC snoop data (snoop #1 [15:8], snoop #0 [7:0])
* - `0x98`–`0x9C`
  - *(reserved)*
  - Not defined
* - `0xA0`
  - LHCR0
  - LPC Host Control 0 — host-controller enable, APB↔LPC bridge, SIRQ options
* - `0xA4`
  - LHCR1
  - LPC Host Control 1 — host time-out limit + force-abort + fire cycle
* - `0xA8`
  - LHCR2
  - LPC Host Control 2 — host SIRQ interrupt enables + error/done IRQ enables
* - `0xAC`
  - LHCR3
  - LPC Host Control 3 — host busy/wait status + SIRQ/timeout/sync/done status
* - `0xB0`
  - LHCR4
  - LPC Host Control 4 — APB-to-LPC remap base [31:28] (`P2LBASE`) + host cmd/header
* - `0xB4`
  - LHCR5
  - LPC Host Control 5 — host cycle address [31:0]
* - `0xB8`
  - LHCR6
  - LPC Host Control 6 — host write data [31:0]
* - `0xBC`
  - LHCR7
  - LPC Host Control 7 — host read data [31:0] (latched)
* - `0xC0`
  - LHCR8
  - LPC Host Control 8 — reserved
* - `0xC4`
  - LHCR9
  - LPC Host Control 9 — reserved
* - `0xC8`
  - LHCRA
  - LPC Host Control A — host SIRQ edge/level trigger mode [20:0]
* - `0xCC`
  - LHCRB
  - LPC Host Control B — host SIRQ high/rising trigger mode [20:0]
```

### iLPC-to-AHB bridge (the "backdoor") — HICR5/6/7/8

This is the mechanism the `culvert` posture tool inspects: an LPC master (the
host) can be given arbitrary AHB read/write access into the BMC's internal
memory map. It is **off by default** and confirmed **disabled** on the studied
KGPE-D16 / C410X boards [culvert](#sources), [RAPTOR-ANALYSIS](#sources).

```{list-table}
:header-rows: 1
:widths: 14 14 12 60

* - Register
  - Field / bit
  - Reset
  - Meaning
* - HICR5 `0x80`
  - HWMBASE [31:24]
  - 0
  - LPC-to-AHB bridge address-decoding base bit [31:24] [DS §30.3 p.319](#sources)
* - HICR5 `0x80`
  - ENFWH [10]
  - 0
  - Enable LPC FWH cycles
* - HICR5 `0x80`
  - **ENL2H [8]**
  - **0**
  - **Enable LPC-to-AHB bridge** — the master posture bit; `culvert` reads this
    to report `ilpc: Disabled`/`Permissive` [DS §30.3 p.319](#sources), [culvert](#sources)
* - HICR5 `0x80`
  - IRQX/PME/snoop [23:12, 9, 5:0]
  - 0
  - KCS-channel IRQX select/enable, PME IRQ, SIRQ start-frame, LCLK req, snoop #0/#1 enable+IRQ
* - HICR6 `0x84`
  - HWNCARE [27:24]
  - 0
  - LPC-to-AHB **address-decoding "don't-care" range** control bit [27:24] [DS §30.3 p.320](#sources)
* - HICR6 `0x84`
  - STR_PME/STR_SNP1W/STR_SNP0W [2:0]
  - 0
  - PME / snoop #1 / snoop #0 interrupt status (W1C)
* - HICR7 `0x88`
  - ADRBASE [31:16]
  - 0
  - LPC-to-AHB **remapping address base** [31:16] [DS §30.3 p.320](#sources)
* - HICR8 `0x8C`
  - ADRMASK [31:16]
  - 0
  - LPC-to-AHB **remapping address mask** [31:16] [DS §30.3 p.321](#sources)
```

An LPC I/O or memory cycle whose address matches `HWMBASE`/`HWNCARE` is
translated through `ADRBASE`/`ADRMASK` into an AHB address, giving the host
full internal-bus access when `ENL2H=1`. On the AST2050 the datasheet documents
this as the same backdoor family (`p2a`, `ilpc`/`lpc2ahb`) that culvert uses on
newer parts; only the UART debug console is absent from the G3 [RAPTOR-ANALYSIS](#sources).
The KGPE-D16 has host PCI+LPC wiring so an attacker/host could enable it; the
C410X has no host CPU so nothing drives the LPC bridge [RAPTOR-ANALYSIS](#sources),
[culvert](#sources).

### HICR0 / HICR4 — channel + KCS/BT enables (representative slave-side bits)

```{list-table}
:header-rows: 1
:widths: 14 12 12 62

* - Register
  - Bit
  - Reset
  - Meaning
* - HICR0 `0x00`
  - 7 LPC3E / 6 LPC2E / 5 LPC1E
  - 0
  - Enable LPC channel #3 / #2 / #1 [DS §30.3 p.313](#sources)
* - HICR0 `0x00`
  - 3 SDWNE / 2 PMEE
  - 0
  - Enable LPC software shutdown / PME output
* - HICR2 `0x08`
  - 6 LRST / 5 SDWN / 4 ABRT
  - 0
  - LPC reset / shutdown / abort interrupt status (W0C) [DS §30.3 p.313](#sources)
* - HICR2 `0x08`
  - 3 IBFIF3 / 2 IBFIF2 / 1 IBFIE1 / 0 ERRIE
  - 0
  - IBF (channel 3/2/1) and error interrupt enables
* - HICR4 `0x10`
  - 7 LADR12AS
  - U
  - Channel #1/#2 address select (LADR12H vs LADR12L) [DS §30.3 p.314](#sources)
* - HICR4 `0x10`
  - 2 KCSENBL / 0 BTENBL
  - U / 0
  - Enable KCS (channel #3) / enable BT (channel #3)
```

### LHCR0 — LPC Host Controller enable [DS §30.3 p.321-322](#sources)

```{list-table}
:header-rows: 1
:widths: 12 10 12 66

* - Bit
  - R/W
  - Reset
  - Meaning
* - 23
  - RW
  - 0
  - LRSTNO — LPC reset pin output level (0 low / 1 high)
* - 15
  - RW
  - 1
  - LRSTNOEN — LPC reset pin output control (0 output, 1 input)
* - 12
  - RW
  - 1
  - Disable VIC output connected to host serial IRQ (default disabled; lets the
    **host use GPIO when ARM is disabled**)
* - 9 / 8
  - RW
  - 1 / 1
  - Enable PUART / VUART serial-IRQ low stretcher
* - 4
  - RW
  - 0
  - ENP2L — enable APB-to-LPC bridge
* - 2
  - RW
  - 0
  - ENLHSIRQ — enable LPC host SIRQ receive
* - 1
  - RW
  - 0
  - ENLHTM-OUT — enable LPC host time-out
* - 0
  - RW
  - 0
  - **ENLPC-HOST** — enable LPC Host Controller (for BMC to update host BIOS over
    LPC; only valid when the host is fully shut down, else LPC bus conflict)
```

The LPC **Host** side (`LHCR0`–`LHCRB`) lets the BMC master the LPC bus to
reprogram the host's SPI/FWH BIOS: `LHCR4` supplies command/header, `LHCR5` the
address, `LHCR6` write data, `LHCR7` latches read data, and writing `LHCR1[0]
LHFIRE` issues one bus cycle [DS §30.3 p.323-326](#sources). Mainline [`aspeed-lpc-ctrl.c`](https://github.com/torvalds/linux/blob/master/drivers/soc/aspeed/aspeed-lpc-ctrl.c) /
[`aspeed-lpc-snoop.c`](https://github.com/torvalds/linux/blob/master/drivers/soc/aspeed/aspeed-lpc-snoop.c) cover the equivalent G4 blocks (`aspeed,ast2400-lpc-*`)
[drivers-analysis](#sources).

---

## GPIO controller

Base `0x1E780000` [DS §23.3 p.262](#sources), [hwreg.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h). Up to **64 GPIO pins in 8 port
groups GPIOA…GPIOH** (8 pins each) [DS §23.1 p.262](#sources). The register file is split
into a base bank covering **GPIOA–GPIOD** (`0x00`–`0x1C`) and an *extended* bank
covering **GPIOE–GPIOH** (`0x20`–`0x3C`), then shared debounce settings/timers
(`0x40`–`0x58`).

```{admonition} A–H, not A–P
:class: note

Later Aspeed SoCs (AST2400+) extend the same register pattern to more port
letters (I…P and beyond), and mainline [`gpio-aspeed.c`](https://github.com/torvalds/linux/blob/master/drivers/gpio/gpio-aspeed.c) / the reconstructed
KGPE-D16 DTS describe those extra banks. **The AST2050 register file only defines
GPIOA–GPIOH** [DS §23.3 p.262-269](#sources); higher banks are not present. Only the pins
enumerated in the pin-summary below are actually bonded out.
```

Each pin supports: input/output; interrupt enable; interrupt sensitivity
(level-high/low, rising/falling edge, or dual-edge); WDT-reset tolerance; and
0/1 µs/1 ms/5 ms/10 ms debounce [DS §23.1 p.262](#sources), [DS §23.2 p.263](#sources).
Register offsets and bank byte-lane layout are identical to mainline
[gpio-aspeed.c](https://github.com/torvalds/linux/blob/master/drivers/gpio/gpio-aspeed.c) (`data 0x00, dir 0x04, irq 0x08/0x0c/0x10/0x14/0x18, tolerance
0x1c, debounce sel 0x40/0x44, debounce timers 0x50/0x54/0x58, extended data
0x20`; 8 banks).

### Register map (base `0x1E780000`) [DS §23.3 p.263-269](#sources)

```{list-table}
:header-rows: 1
:widths: 12 34 10 12 32

* - Offset
  - Register
  - R/W
  - Reset
  - Ports covered
* - `0x00`
  - GPIO00 Data Value
  - RW
  - 0
  - A(7:0) / B(15:8) / C(23:16) / D(31:24)
* - `0x04`
  - GPIO04 Direction (0=in, 1=out)
  - RW
  - 0
  - A / B / C / D
* - `0x08`
  - GPIO08 Interrupt Enable
  - RW
  - 0
  - A / B / C / D
* - `0x0C`
  - GPIO0C Interrupt Sensitivity Type 0
  - RW
  - 0
  - A / B / C / D
* - `0x10`
  - GPIO10 Interrupt Sensitivity Type 1
  - RW
  - 0
  - A / B / C / D
* - `0x14`
  - GPIO14 Interrupt Sensitivity Type 2
  - RW
  - 0
  - A / B / C / D
* - `0x18`
  - GPIO18 Interrupt Status (W1C)
  - RW
  - 0
  - A / B / C / D
* - `0x1C`
  - GPIO1C Reset Tolerant (1 = keep across WDT reset)
  - RW
  - 0
  - A / B / C / D
* - `0x20`
  - GPIO20 Extended Data Value
  - RW
  - 0
  - E(7:0) / F(15:8) / G(23:16) / H(31:24)
* - `0x24`
  - GPIO24 Extended Direction
  - RW
  - 0
  - E / F / G / H
* - `0x28`
  - GPIO28 Extended Interrupt Enable
  - RW
  - 0
  - E / F / G / H
* - `0x2C`
  - GPIO2C Extended Int Sensitivity Type 0
  - RW
  - 0
  - E / F / G / H
* - `0x30`
  - GPIO30 Extended Int Sensitivity Type 1
  - RW
  - 0
  - E / F / G / H
* - `0x34`
  - GPIO34 Extended Int Sensitivity Type 2
  - RW
  - 0
  - E / F / G / H
* - `0x38`
  - GPIO38 Extended Interrupt Status (W1C)
  - RW
  - 0
  - E / F / G / H
* - `0x3C`
  - GPIO3C Extended Reset Tolerant
  - RW
  - 0
  - E / F / G / H
* - `0x40`
  - GPIO40 Debounce Setting #1
  - RW
  - 0
  - A / B / C / D
* - `0x44`
  - GPIO44 Debounce Setting #2
  - RW
  - 0
  - A / B / C / D
* - `0x48`
  - GPIO48 Extended Debounce Setting #1
  - RW
  - 0
  - E / F / G / H
* - `0x4C`
  - GPIO4C Extended Debounce Setting #2
  - RW
  - 0
  - E / F / G / H
* - `0x50`
  - GPIO50 Debounce Time Setting #1
  - RW
  - 0
  - timer (bits 23:0), 31:24 reserved
* - `0x54`
  - GPIO54 Debounce Time Setting #2
  - RW
  - 0
  - timer (bits 23:0)
* - `0x58`
  - GPIO58 Debounce Time Setting #3
  - RW
  - 0
  - timer (bits 23:0)
```

### Bank byte-lane layout

Every A–D register packs four ports into one word; the E–H (extended) registers
mirror it [DS §23.3 p.263-265]:

```{list-table}
:header-rows: 1
:widths: 16 20 20 22 22

* - Byte lane
  - Base bank (`0x00`–`0x1C`)
  - Data reg
  - Extended bank (`0x20`–`0x3C`)
  - Ext data reg
* - bits 7:0
  - GPIOA[7:0]
  - `GPIO00`
  - GPIOE[7:0]
  - `GPIO20`
* - bits 15:8
  - GPIOB[7:0]
  - `GPIO00`
  - GPIOF[7:0]
  - `GPIO20`
* - bits 23:16
  - GPIOC[7:0]
  - `GPIO00`
  - GPIOG[7:0]
  - `GPIO20`
* - bits 31:24
  - GPIOD[7:0]
  - `GPIO00`
  - GPIOH[7:0]
  - `GPIO20`
```

### Interrupt trigger-mode encoding

The three sensitivity registers (`GPIO0C/10/14` and `GPIO2C/30/34`) jointly
encode the trigger mode per pin [DS §23.3 p.269]:

```{list-table}
:header-rows: 1
:widths: 18 18 18 46

* - Type 2 (`14`/`34`)
  - Type 1 (`10`/`30`)
  - Type 0 (`0C`/`2C`)
  - Trigger mode
* - 0
  - 0
  - 0
  - Falling-edge
* - 0
  - 0
  - 1
  - Rising-edge
* - 0
  - 1
  - 0
  - Level-low
* - 0
  - 1
  - 1
  - Level-high
* - 1
  - x
  - x
  - Dual-edge
```

### Debounce configuration

The two debounce-setting registers select which of three debounce timers applies
to a pin [DS §23.3 p.269]:

```{list-table}
:header-rows: 1
:widths: 24 24 52

* - Setting #2 (`44`/`4C`)
  - Setting #1 (`40`/`48`)
  - Function
* - 0
  - 0
  - No debounce
* - 0
  - 1
  - Use GPIO50 timer
* - 1
  - 0
  - Use GPIO54 timer
* - 1
  - 1
  - Use GPIO58 timer
```

`Debounce time = PCLK cycle × Debounce timer value` where the timer value is
`GPIO50/54/58` bits [23:0] [DS §23.3 p.269](#sources). The minimum input pulse for
edge-triggered interrupts must exceed 2 PCLK cycles [DS §3.5 p.58](#sources).

### Electrical / feature notes [DS §23.2 p.263](#sources)

- 8 dedicated + 56 shared GPIO pins; interrupts supported on all 64.
- Default **internal pull-down** on each pin; external pull-ups required.
- 8 of 64 pins have 16 mA drive; the rest 8 mA (per-pin table at [DS §3.5 p.58](#sources)).
- Reset tolerance (`GPIO1C`/`GPIO3C`): setting a bit keeps that pin's
  `GPIO00/04` (or `GPIO20/24`) state across a WDT reset [DS §23.3 p.264](#sources).

### Bonded pins (GPIO Summary) [DS §3.5 p.58-59](#sources)

Only the following GPIO signals are pinned out on the AST2050; each shares its
ball with a multi-function alternate (chosen via SCU multi-function control):

```{list-table}
:header-rows: 1
:widths: 14 22 20 44

* - Group
  - Pins present
  - Drive / buffer
  - Multiplexed alternates (examples)
* - GPIOA
  - A4, A5
  - 16 mA / TTL
  - PHYLINK, PHYPD#
* - GPIOB
  - B0–B7
  - 8–16 mA / Schmitt
  - INTA#, FLBUSY#, FLWP#, VBCS/LRST#, VBCK, VBDO/WDTRST, VBDI/EXTRST#
* - GPIOC
  - C0–C7
  - 8–12 mA / TTL·Schmitt
  - PECII/PECIO, PWM1–PWM4, **SDA5 (C6)**, **SCL5 (C7)**
* - GPIOD
  - D6, D7
  - 8 mA / TTL, pull-up
  - DDCADAT, DDCACLK
* - GPIOE
  - E0–E7 (two mux groups; SCU74[27] selects)
  - 8 mA / TTL, pull-down
  - group 1: VP0–7 / TACH0–7; group 2: MII/RMII2 TXD/RXD/… [DS §3.5 p.58 note](#sources)
* - GPIOF
  - F0–F7
  - 8 mA / TTL, pull-down
  - VP8–15 / TACH8–15
* - GPIOG
  - G0, G1
  - 8 mA / TTL, pull-down
  - VP16, VP17
* - GPIOH
  - H0–H7
  - 8–16 mA / TTL·Schmitt, pull-down
  - **SDA6 (H0)**, **SCL6 (H1)**, **SDA7/SALT2 (H2)**, **SCL7/SALT1 (H3)**,
    VPAHSYNC/HSYNC, VPAVSYNC/VSYNC, VPADE, VPACLK
```

On the Dell C410X, firmware drives 38 of these on-chip GPIOs through the AESS
kernel driver — e.g. GPIOA4/A5 as I2C-expander interrupt inputs, GPIOB0–B7 as
thermal/PSU/PCIe-switch alerts, GPIOE0–E5 as power-sequencing controls, GPIOF6
as the PEX8696 reset — alongside 80 off-chip PCA9555 expander lines
[gpio-pin-mapping](#sources).

---

## Sources

**Primary datasheet**

- **[DS](#sources)** *ASPEED AST2050/AST1100 A3 Datasheet, V1.05* (2010-05-25), in-repo at
  `datasheets/aspeed/AST2050_AST1100_A3_Datasheet_V1.05.pdf`. Sections used:
  - §9 ARM Address Space Mapping (p.97)
  - §11 Static Memory Controller — overview p.100-101, registers p.105-112
  - §23 GPIO Controller — overview p.262, registers p.263-269
  - §3.5 GPIO Summary (pin table) p.58-59
  - §30 LPC Controller — overview p.311-312, registers p.313-326
  - §31 I2C/SMBus Controller — features p.327-328, timing p.329-333,
    registers p.334-344

**In-repo reverse-engineering sources**

- **[hwreg.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h)** `asus-kgpe-d16-firmware/hwreg.h` — Raptor AST2100/AST2050 SoC
  register base addresses (SMC `0x16000000`, GPIO `0x1E780000`, SCU/SDRAM/AHBC).
- **[ast2050.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/ast2050.h)** `asus-kgpe-d16-firmware/ast2050.h` — Raptor U-Boot board config
  (flash windows `0x14000000`/`0x10000000`, single-SPI boot, `CONFIG_HARD_I2C`).
- **[RAPTOR-ANALYSIS](#sources)** `asus-kgpe-d16-firmware/RAPTOR_ENGINEERING_AST2050_ANALYSIS.md`
  — I2C engine base `0x1E78A000`, 14-bus SDK templating, AHB backdoor confirmation.
- **[culvert](#sources)** `asus-kgpe-d16-firmware/CULVERT-UART-JTAG-DEBUG.md` and
  [`CULVERT-G3-HARDWARE-RESULTS.md`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/CULVERT-G3-HARDWARE-RESULTS.md) — iLPC2AHB / LPC2AHB posture via
  `HICR5[8] ENL2H` + `HICR7 ADRBASE` / `HICR8 ADRMASK`; confirmed disabled on hardware.
- **[drivers-analysis](#sources)** `dell-c410x-firmware/aspeed-mainline-drivers-analysis.md`
  — mainline driver ↔ AST2050 mapping (i2c-aspeed, gpio-aspeed, spi-aspeed-smc,
  aspeed-lpc-ctrl/snoop).
- **[gpio-pin-mapping](#sources)** `dell-c410x-firmware/io-tables/gpio-pin-mapping.md`
  — C410X on-chip GPIO A/B/E/F usage and per-bit function.

**Secondary (mainline Linux, register cross-check)**

- **[i2c-aspeed.c](https://github.com/torvalds/linux/blob/master/drivers/i2c/busses/i2c-aspeed.c)** `drivers/i2c/busses/i2c-aspeed.c` (torvalds/linux) — register
  offsets `0x00/04/08/0c/10/14/18/20` and command bits (START=BIT0, TX=BIT1,
  RX=BIT3, RX_CMD_LAST=BIT4, STOP=BIT5) match §31.4.3; compatibles
  `aspeed,ast2400/2500/2600-i2c-bus`.
- **[gpio-aspeed.c](https://github.com/torvalds/linux/blob/master/drivers/gpio/gpio-aspeed.c)** `drivers/gpio/gpio-aspeed.c` (torvalds/linux) — bank layout
  `data 0x00 / dir 0x04 / irq 0x08,0x0c,0x10,0x14,0x18 / tolerance 0x1c /
  debounce 0x40,0x44 / timers 0x50,0x54,0x58 / ext data 0x20`, 8 banks; matches §23.3.
- **spi-aspeed-smc.c** (torvalds/linux) — targets the AST2400+ FMC/SPI, whose
  layout differs from the legacy AST2050 SMC; noted as a weak cross-reference for §11.
