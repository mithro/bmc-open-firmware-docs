# NS9360 — GPIO, DMA & secondary blocks

Continuation of {doc}`soc-ns9360`: the BBus utility/GPIO block, the AHB and BBus DMA, and the secondary controllers (LCD, IEEE 1284, USB) plus the GPIO pin-mux and the open-source driver cross-reference.

## BBus Utility (GPIO)


**Base address: 0x9060_0000** [HWRef p.463](#sources), [mach-ns9xxx regs-bbu.h](https://github.com/torvalds/linux/blob/v2.6.39/arch/arm/mach-ns9xxx/include/mach/regs-bbu.h)
[u-boot ns9750_bbus.h](https://github.com/u-boot/u-boot/blob/v2012.10/include/ns9750_bbus.h). This block owns the 73 GPIO pins, the master reset that
holds the other BBus peripherals in reset out of power-up, the endian
configuration for the bus masters, and USB configuration.

```{list-table} BBus utility registers (offset from 0x9060_0000)
:header-rows: 1
:widths: 16 26 58

* - Offset
  - Register
  - Description
* - 0x000
  - Master Reset
  - Per-peripheral reset (all held reset out of power-up)
* - 0x004
  - BBus Utility Interrupt Status
  - Module interrupt flag (write 1 to clear)
* - 0x010-0x028
  - GPIO Config #1-#7
  - Pin config (gpio0-gpio55), 8 pins per register
* - 0x030 / 0x034
  - GPIO Control #1 / #2
  - Output data, gpio0-31 / gpio32-63
* - 0x040 / 0x044
  - GPIO Status #1 / #2
  - Input data, gpio0-31 / gpio32-63
* - 0x050
  - BBus Timeout
  - Bus-activity monitor
* - 0x060 / 0x064
  - BBus DMA Interrupt Status / Enable
  - Per-DMA-channel (16) interrupt
* - 0x070
  - USB Configuration
  - USB PHY type, host/device select, speed
* - 0x080
  - Endian Configuration
  - Per-bus-master endianness
* - 0x090
  - ARM Wake-up
  - Serial-channel wake-up match word
* - 0x100-0x108
  - GPIO Config #8-#10
  - Pin config (gpio56-gpio72)
* - 0x120
  - GPIO Control #3
  - Output data, gpio64-gpio72
* - 0x130
  - GPIO Status #3
  - Input data, gpio64-gpio72
```

Note the split layout: GPIO config #1-#7 at 0x010-0x028, then #8-#10 at
0x100-0x108; control #1-#2 at 0x030/0x034, then #3 at 0x120; status #1-#2 at
0x040/0x044, then #3 at 0x130 [HWRef p.463](#sources). Bases and offsets match
[mach-ns9xxx regs-bbu.h](https://github.com/torvalds/linux/blob/v2.6.39/arch/arm/mach-ns9xxx/include/mach/regs-bbu.h) (`BBU_GCONFb1`=0x…010, `BBU_GCONFb2`=0x…100,
`BBU_GCTRL1`=0x…030, `BBU_GSTAT1`=0x…040) and [u-boot ns9750_bbus.h](https://github.com/u-boot/u-boot/blob/v2012.10/include/ns9750_bbus.h)
(`MASTER_RESET`=0x00, `GPIO_CFG_BASE`=0x10, `GPIO_CTRL_BASE`=0x30,
`GPIO_STAT_BASE`=0x40, `ENDIAN_CFG`=0x80).

### GPIO configuration field

Each pin is configured by a **4-bit field**; eight pins pack into each 32-bit
config register, lowest-numbered pin in the least-significant nibble [HWRef p.466-473](#sources).

```{list-table} Per-pin GPIO config nibble [HWRef p.473, Table 344](#sources)
:header-rows: 1
:widths: 12 14 12 62

* - Bit
  - Field
  - Access
  - Meaning
* - 3
  - DIR
  - R/W
  - Direction (only in GPIO/function-3 mode): 0 = input, 1 = output
* - 2
  - INV
  - R/W
  - Invert (applies in all modes): 0 = normal, 1 = inverted
* - 1:0
  - FUNC
  - R/W
  - Function select: 00/01/10 = peripheral function 0/1/2, 11 = GPIO
```

**Reset default per nibble = 0x3** → every pin comes up as **GPIO, input, no
inversion** [HWRef p.473](#sources). This matches [mach-ns9xxx regs-bbu.h](https://github.com/torvalds/linux/blob/v2.6.39/arch/arm/mach-ns9xxx/include/mach/regs-bbu.h) (`BBU_GCONFx_DIR`
= nibble bit 3, `_INV` = bit 2, `_FUNC` = bits 1:0) and [u-boot ns9750_bbus.h](https://github.com/u-boot/u-boot/blob/v2012.10/include/ns9750_bbus.h)
(`GPIO_CFG_OUTPUT`=0x08, `GPIO_CFG_FUNC_GPIO`=0x03). Because eight pins share one
register, a driver must read-modify-write [PLAN-INCREMENTAL-PORT.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/PLAN-INCREMENTAL-PORT.md).

```{list-table} GPIO config register coverage [HWRef p.466-472](#sources)
:header-rows: 1
:widths: 22 18 60

* - Register
  - Offset
  - Pins (nibble low → high)
* - GPIO Config #1
  - 0x010
  - gpio0 … gpio7
* - GPIO Config #2
  - 0x014
  - gpio8 … gpio15
* - GPIO Config #3
  - 0x018
  - gpio16 … gpio23
* - GPIO Config #4
  - 0x01C
  - gpio24 … gpio31
* - GPIO Config #5
  - 0x020
  - gpio32 … gpio39
* - GPIO Config #6
  - 0x024
  - gpio40 … gpio47
* - GPIO Config #7
  - 0x028
  - gpio48 … gpio55
* - GPIO Config #8
  - 0x100
  - gpio56 … gpio63
* - GPIO Config #9
  - 0x104
  - gpio64 … gpio71
* - GPIO Config #10
  - 0x108
  - gpio72 (nibble 0; upper 28 bits write 0x3333333)
```

Output values are written to GPIO Control #1/#2/#3 (0x030 / 0x034 / 0x120; one bit
per pin, reset 0) and inputs are read from GPIO Status #1/#2/#3 (0x040 / 0x044 /
0x130; read-only, reset undefined). Control/Status #3 hold gpio64-gpio72 in bits
8:0 [HWRef p.473-482](#sources).

### Master Reset register

```{list-table} Master Reset (0x000) — all bits R/W, active high [HWRef p.464](#sources)
:header-rows: 1
:widths: 12 16 12 60

* - Bits
  - Field
  - Reset
  - Meaning
* - 12
  - USBDEV
  - 1
  - USB device controller reset
* - 11
  - USBHST
  - 1
  - USB host controller reset
* - 10 / 9
  - RTC2 / RTC1
  - 1
  - RTC calendar / configuration reset
* - 7
  - I2C
  - 1
  - I2C controller reset
* - 6
  - 1284
  - 1
  - IEEE 1284 controller reset
* - 5 / 4
  - SerD / SerC
  - 1
  - Serial channel D / C reset
* - 3 / 2
  - SerA / SerB
  - 1
  - Serial channel A / B reset
* - 1
  - reserved
  - 0
  - write 1
* - 0
  - DMA
  - 1
  - BBus DMA reset
```

All BBus peripherals except the bridge are held in reset after power-up; software
must clear these bits (write 0) before touching a peripheral's registers
[HWRef p.464](#sources), [PLAN-INCREMENTAL-PORT.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/PLAN-INCREMENTAL-PORT.md). Bit assignments match
[u-boot ns9750_bbus.h](https://github.com/u-boot/u-boot/blob/v2012.10/include/ns9750_bbus.h) (`MASTER_RESET_I2C`=0x80, `_SER1..4`, `_DMA`=0x01).

### Endian and USB configuration

```{list-table} Endian Configuration (0x080) — 0 = little, 1 = big [HWRef p.486-487](#sources)
:header-rows: 1
:widths: 12 16 14 58

* - Bits
  - Field
  - Reset
  - Meaning
* - 12
  - AHBM
  - gpio[44]
  - AHB bus master endianness (must match AHB)
* - 9
  - USBHST
  - gpio[44]
  - USB host controller endianness
* - 5 / 4
  - SerD / SerC
  - 0
  - Serial channel D / C endianness
* - 3 / 2
  - SerA / SerB
  - 0
  - Serial channel A / B endianness
* - 1
  - reserved
  - 0
  - write 0
* - 0
  - DMA
  - gpio[44]
  - BBus + USB DMA endianness
```

gpio[44] is the endian strap: AHBM, USBHST, and DMA reset to its value; the serial
ports reset little-endian [HWRef p.486](#sources). This is the third register the BE→LE boot
stub clears (bits 0x1201) [PLAN-INCREMENTAL-PORT.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/uboot-port/PLAN-INCREMENTAL-PORT.md). `USB Configuration` (0x070):
bit 5 `EXT_PHY`, bit 4 `INT_PHY` (host/device), bit 2 `SPEED`; write only while the
USB module is in reset [HWRef p.485-486](#sources). `BBus Timeout` (0x050): bit 31 `EN`,
bits 15:0 `COUNT` (max BBus cycle length, keep ≥ 255) [HWRef p.482](#sources). `BBus DMA
Interrupt Status`/`Enable` (0x060/0x064) carry per-channel (1-16) flags for the
BBus DMA controller [HWRef p.482-485](#sources). `ARM Wake-up` (0x090) is the 32-bit
serial-match wake word [HWRef p.488](#sources).

## BBus Bridge and AHB DMA


**Base address: 0xA0400000** [HWRef p.415, p.428](#sources). The bridge connects the AHB and
the BBus (BBus runs at half the AHB clock), arbitrates BBus mastership, hosts a
two-channel AHB DMA controller (the only one that supports memory-to-memory), and
contains the SPI-EEPROM boot engine [HWRef p.409-416](#sources).

```{list-table} BBus bridge control/status registers (offset from 0xA0400000) [HWRef p.429](#sources)
:header-rows: 1
:widths: 18 30 52

* - Offset
  - Register
  - Description
* - 0x0000 / 0x0020
  - DMA Ch1 / Ch2 Buffer Descriptor Pointer
  - First descriptor pointer
* - 0x0004 / 0x0024
  - DMA Ch1 / Ch2 Control
  - Channel enable/abort/go, widths, bursts, mode
* - 0x0008 / 0x0028
  - DMA Ch1 / Ch2 Status and Interrupt Enable
  - Completion/error/abort interrupts
* - 0x000C / 0x002C
  - DMA Ch1 / Ch2 Peripheral Chip Select
  - External chip-select assignment + polarity
* - 0x1000
  - BBus Bridge Interrupt Status
  - Aggregated per-module interrupt sources
* - 0x1004
  - BBus Bridge Interrupt Enable
  - Enable/mask into bbus_int
* - 0x1008
  - BBus Bridge Prefetch Buffer Enable
  - Per-master octal-word prefetch enable
```

```{list-table} AHB DMA Channel Control (0x0004 / 0x0024) — key fields [HWRef p.431-434](#sources)
:header-rows: 1
:widths: 12 14 12 62

* - Bits
  - Field
  - Access
  - Meaning
* - 31
  - CE
  - R/W
  - Channel enable
* - 30
  - CA
  - R/W
  - Channel abort (finish current, close buffer)
* - 29
  - CG
  - R/W
  - Channel go (start transfer; +CE for memory-to-memory)
* - 28:27 / 26:25
  - SW / DW
  - R/W
  - Source / destination width (00/01/10 = 8/16/32-bit)
* - 24:23 / 22:21
  - SB / DB
  - R/W
  - Source / destination burst (1/2/4/8)
* - 20 / 19
  - SINC_N / DINC_N
  - R/W
  - Suppress source / destination address increment
* - 18
  - POL
  - R/W
  - dma_req/dma_done polarity
* - 17
  - MODE
  - R/W
  - Fly-by: 0 = peripheral→memory, 1 = memory→peripheral
* - 16
  - RST
  - R/W
  - Reset the register (except INDEX)
* - 15:10
  - STATE
  - R
  - DMA state machine value
* - 9:0
  - INDEX
  - R
  - Current byte offset in the descriptor
```

The Status/Interrupt-Enable register (0x0008/0x0028) has the pending flags
(bit 31 `NCIP` normal complete, 30 `ECIP` error, 29 `NRIP` buffer-not-ready, 28
`CAIP` abort, 27 `PCIP` premature complete, all RW1TC) and matching enables
(24-20), plus debug fields [HWRef p.435-437](#sources). Buffer descriptors are 16 bytes
(source, length, destination, {W/I/L/F flags + status}); up to 64 per channel in a
1 KB circular list [HWRef p.417-419](#sources). The Bridge Interrupt Status/Enable (0x1000/
0x1004) aggregate every BBus peripheral plus the two AHB DMA channels into the
single `bbus_int` (interrupt source ID 2) [HWRef p.438-441](#sources).

### SPI-EEPROM boot logic

When strapped for SPI-EEPROM boot (`boot_cfg` = 11), the on-chip boot engine
drives Serial channel B as an SPI master (SPI mode 0, ~1.5 MHz), reads a
128-130-byte configuration header from EEPROM address 0 (SDRAM mode value plus the
memory-controller timing registers), programs the memory controller, copies the
image into SDRAM, and releases the CPU [HWRef p.425-427](#sources). During this the hardware
loads channel B's Control A/B and Bit-rate registers automatically (CE=1, WLS=8,
SPI master, MSB-first, BCLK reference, N=0x00F) [HWRef p.426](#sources). This is the
alternative to flash boot and is documented here because it fully drives the
serial and memory-controller blocks.

## BBus DMA Controllers


**Base addresses: 0x9000_0000 (DMA1, BBus peripherals) and 0x9091_0000 (DMA2, USB
device).** Two controllers, 16 channels each, moving data between external memory
and internal peripherals in fly-by mode only — no memory-to-memory and no
external-peripheral DMA (those use the AHB DMA in the bridge) [HWRef p.443-445](#sources).
Each channel is hard-wired to a peripheral [HWRef p.450-452](#sources).

```{list-table} BBus DMA1 channel assignments [HWRef p.451](#sources)
:header-rows: 1
:widths: 14 40 46

* - Channel
  - Peripheral
  - Direction
* - 1 / 2
  - Serial B receiver / transmitter
  - RX / TX
* - 3 / 4
  - Serial A receiver / transmitter
  - RX / TX
* - 5 / 6
  - Serial C receiver / transmitter
  - RX / TX
* - 7 / 8
  - Serial D receiver / transmitter
  - RX / TX
* - 9 / 10
  - IEEE 1284 command receiver / transmitter
  - RX / TX
* - 11 / 12
  - IEEE 1284 data receiver / transmitter
  - RX / TX
* - 13-16
  - unused
  - —
```

DMA2 channels 1-12 map to the USB device control endpoints and endpoints 1-10
[HWRef p.452](#sources). Each channel exposes, at a 0x20 stride from its controller base,
a Buffer Descriptor Pointer (+0x00), a Control register (+0x10, fields CE/CA/MODE
fly-by/BTE burst/BDR refetch/RST/STATE/INDEX), and a Status/Interrupt-Enable
register (+0x14, NCIP/ECIP/NRIP/CAIP/PCIP pending + enables) [HWRef p.453-460](#sources). The
firmware's heaviest users are the serial channels feeding the display link and the
metering SPI [ANALYSIS.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/ANALYSIS.md).

## LCD, IEEE 1284, USB host & USB device (secondary blocks)

These four secondary blocks — all unused on the HPE iPDU — are documented at
full per-bit register depth on a dedicated page: {doc}`soc-ns9360-secondary`
(LCD controller, IEEE 1284 parallel port, USB host/OHCI, and USB device).

## GPIO pin multiplexing (board-relevant subset)


Every GPIO pin has up to four functions; function 3 is always plain GPIO, and
functions 0/1/2 are peripheral roles selected by the config nibble above. The
full 73-pin table is in the datasheet [HWRef p.50-59, Table 9](#sources); the rows a port
must set for this board are [ANALYSIS.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/ANALYSIS.md), [HWRef p.50-63](#sources):

```{list-table} Key GPIO peripheral functions
:header-rows: 1
:widths: 20 20 60

* - GPIO
  - Function 0
  - Role on this board
* - gpio8 / gpio9
  - Serial A TXD / RXD
  - Debug UART console (J25), 115200 8N1
* - gpio0-gpio7
  - Serial B (UART/SPI)
  - Display-unit link (SPI B disabled; pins reused as GPIO input in firmware)
* - gpio40 / gpio41
  - Serial C TXD / RXD
  - Secondary serial / candidate metering SPI
* - gpio44 / gpio45
  - Serial D TXD / RXD
  - Serial D (gpio44 also = endian strap)
* - gpio34 / gpio35
  - iic_scl / iic_sda
  - I2C bus (function 0)
* - gpio50
  - MII mdio
  - Ethernet management data
* - gpio51-gpio65
  - MII rx/tx/control
  - Ethernet MII to the ICS1893 PHY
* - gpio16 / gpio17
  - USB_OVR / USB_PWR
  - USB host sideband (unused); gpio17 also = PLL ND strap
```

The I2C pins default to GPIO and the I2C module is held in reset until its pins are
configured to function 0 [HWRef p.50, p.63](#sources). Full firmware-observed GPIO config
values (e.g. GPIO Config #1 = 0x33333333, all of Serial B as GPIO inputs) are in
[ANALYSIS.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/hpe-ipdu-firmware/ANALYSIS.md).

## Open-source cross-reference


The archived Linux and U-Boot support describe this exact SoC (Linux calls it
NS9360; U-Boot's NS9750 register set is the same NET+ARM map), and the two agree
on every base address and register offset — the useful, independent
cross-reference for this document [mach-ns9xxx](https://github.com/torvalds/linux/tree/v2.6.39/arch/arm/mach-ns9xxx), [u-boot ns9750](https://github.com/u-boot/u-boot/tree/v2012.10).

```{list-table} Base-address agreement
:header-rows: 1
:widths: 26 24 24 26

* - Module
  - This doc / HWRef
  - Linux mach-ns9xxx
  - U-Boot ns9750
* - System Control
  - 0xA0900000
  - 0xa0900000
  - 0xA0900000
* - Memory Controller
  - 0xA0700000
  - 0xa0700000
  - 0xA0700000
* - Ethernet MAC
  - 0xA0600000
  - (not in Linux mach)
  - 0xA0600000
* - BBus / GPIO
  - 0x90600000
  - 0x90600000
  - 0x90600000
* - Serial (channel B)
  - 0x90200000
  - BBus window
  - 0x90200000
```

Confirmed offset agreements include SCM `PLL`=0x188, `CLOCK`=0x17C, `RESET`=0x180,
`ISRADDR`=0x164, interrupt-status-active=0x168, chip-select base/mask
(0x1D0/0x1F0), the timer set (reload 0x044, read 0x084, control 0x190, status
0x170); the memory-controller CTRL/STATUS/CFG (0x00/0x04/0x08), dynamic timing
block (0x20-0x58), and static config (0x200); the BBus GPIO config/ctrl/status
(0x10/0x30/0x40) with the output-direction bit at nibble bit 3; and the four
serial channel bases (0x90200000/40, 0x90300000/40). The PLL field split (FS bits
24:23, ND bits 20:16) and the clock derivation $\text{systemclock} = \text{crystal} \times (ND+1) \gg FS$,
$\text{cpuclock} = \text{systemclock}/2$ are identical across both code bases and the
datasheet [mach-ns9xxx processor-ns9360.c](https://github.com/torvalds/linux/blob/v2.6.39/arch/arm/mach-ns9xxx/processor-ns9360.c), [u-boot ns9750dev.h](https://github.com/u-boot/u-boot/blob/v2012.10/include/configs/ns9750dev.h), [HWRef p.153](#sources).

## See also

**Related pages**

- {doc}`/hardware/soc-ns9360` — the NS9360 SoC overview and SCM register map
- {doc}`/hardware/soc-ns9360-memory-serial` — memory controller, Ethernet and serial
- {doc}`/hardware/soc-ns9360-secondary` — LCD, IEEE 1284 and USB secondary blocks
- {doc}`/systems/hpe-ipdu` — the board whose GPIO/BBus wiring this drives
- {doc}`/drivers/uboot` — the open NS9360 U-Boot port

**External references**

- [Linux `arch/arm/mach-ns9xxx` (v2.6.39)](https://github.com/torvalds/linux/tree/v2.6.39/arch/arm/mach-ns9xxx) — `gpio-ns9360.c` / `regs-bbu.h` in the historical mainline tree
- [U-Boot documentation](https://docs.u-boot.org/en/latest/) — the open-firmware path chosen for this SoC
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
