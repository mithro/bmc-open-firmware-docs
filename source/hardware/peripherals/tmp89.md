# TMP89FM42LUG — display / bezel sub-MCU

The TMP89FM42LUG is a Toshiba **TLCS-870/C1** single-chip 8-bit CMOS
microcontroller. On the iPDU it is the front-panel "Display Module" controller
(7-segment display, LEDs, buzzer) and talks to the NS9360 over a UART (through a
MAX3243EI RS-232 shifter). Its 3.6864 MHz crystal (Y6) is a UART baud-rate
crystal that divides evenly to 115200/57600/…/9600 baud. `[ANALYSIS.md](#sources)`

## Device overview `[TMP89 DS p.1-2](#sources)`

```{list-table} TMP89FM42LUG summary
:header-rows: 0
:widths: 34 66

* - Family / core
  - TLCS-870/C1, 8-bit CISC
* - Flash (program)
  - 32768 bytes
* - RAM
  - 2048 bytes
* - Package
  - LQFP44-P-1010-0.80B (44-pin)
* - Instruction time
  - 238 ns at 4.2 MHz (122 µs at 32.768 kHz)
* - I/O ports
  - 40 pins (2 reserved for HF oscillator); 8 high-current (≈6 mA)
* - Serial
  - UART ×1, UART/SIO ×1, I2C/SIO ×1
* - Analog
  - 10-bit SAR ADC, 8 channels
* - Timers
  - 16-bit TCA ×2, 8-bit TC0 ×4, RTC, watchdog, time-base
* - Other
  - Key-on wake-up ×8, power-on reset, voltage detect, on-chip debug
* - Supply
  - 2.7–3.6 V at 4.2 MHz (2.2–3.6 V at 2 MHz)
```

## Interface to the NS9360 (serial / pin mapping)

The relevant serial pins on the TMP89 (from the pin assignment)
`[TMP89 DS p.3](#sources)`:

```{list-table} TMP89 serial/interface pins
:header-rows: 1
:widths: 18 30 52

* - Port pin
  - Alternate function
  - Role
* - P20
  - TXD0 / RXD0 / SO0 / OCDCK
  - UART0 TX (bezel link candidate) / on-chip-debug clk
* - P21
  - RXD0 / TXD0 / SI0 / OCDIO
  - UART0 RX / on-chip-debug data
* - P90 / P91
  - TXD1 / RXD1
  - UART1 (second serial channel)
* - PB4 / PB5 / PB6
  - SO0/SI0/SCLK0 (RXD0/TXD0 mux)
  - Synchronous SIO
* - P23 / P24
  - SDA0 / SCL0
  - I2C bus
* - P10
  - RESET
  - Reset input
* - P00 / P01
  - XIN / XOUT
  - 3.6864 MHz crystal (Y6)
```

The NS9360 side of this link is one of its UART/SIO serial ports through a
MAX3243EI; `ANALYSIS.md` identifies the display path as NS9360 **Serial Port B**
(primary comms, DMA channel 7). On-chip debug (OCD) shares P20/P21 with UART0,
which is consistent with the J10 "PIC JTAG" sub-MCU programming header.
`[ANALYSIS.md](#sources)` `[HEADERS-J1-J6.md](#sources)`

## UART0 register set `[TMP89 DS p.222-224](#sources)`

```{list-table} UART0 SFR addresses
:header-rows: 1
:widths: 22 16 62

* - Register
  - Address
  - Purpose
* - UART0CR1
  - 0x001A
  - Control 1 (enable, framing, parity, base clock)
* - UART0CR2
  - 0x001B
  - Control 2 (RT-clock, RX noise reject, RX stop bits)
* - UART0DR
  - 0x001C
  - Baud-rate divisor
* - UART0SR
  - 0x001D
  - Status (error / busy / buffer flags)
* - TD0BUF / RD0BUF
  - (data buffers)
  - Transmit / receive data buffers
```

**UART0CR1 (0x001A)** `[TMP89 DS p.222](#sources)`

```{list-table} UART0CR1 bit fields
:header-rows: 1
:widths: 14 16 12 58

* - Bit
  - Symbol
  - R/W
  - Function
* - 7
  - TXE
  - R/W
  - Transmit enable (1 = enable)
* - 6
  - RXE
  - R/W
  - Receive enable (1 = enable)
* - 5
  - STOPBT
  - R/W
  - Transmit stop-bit length (0 = 1 bit, 1 = 2 bits)
* - 4
  - EVEN
  - R/W
  - Parity: 0 = odd, 1 = even
* - 3
  - PE
  - R/W
  - Parity add/check enable
* - 2
  - IRDASEL
  - R/W
  - TXD pin: 0 = UART, 1 = IrDA
* - 1
  - BRG
  - R/W
  - Transfer base clock: 0 = fcgck/fs, 1 = TCA0 output
* - 0
  - —
  - R
  - Reserved
```

**UART0CR2 (0x001B)** `[TMP89 DS p.223](#sources)`: bits 5:3 RTSEL (RT-clock count per
frame bit), bits 2:1 RXDNC (RX noise-rejection width), bit 0 STOPBR (receive
stop-bit length). **UART0DR (0x001C)** `[TMP89 DS p.223](#sources)`: 8-bit baud-rate
divisor (set TXE/RXE = 0 before changing).

**UART0SR (0x001D)** `[TMP89 DS p.224](#sources)`

```{list-table} UART0SR status bits
:header-rows: 1
:widths: 14 16 70

* - Bit
  - Symbol
  - Meaning when 1
* - 7
  - PERR
  - Parity error
* - 6
  - FERR
  - Framing error
* - 5
  - OERR
  - Overrun error
* - 4
  - —
  - Reads 0
* - 3
  - RBSY
  - Receive busy (receiving)
* - 2
  - RBFL
  - Receive buffer full
* - 1
  - TBSY
  - Transmit busy (transmitting)
* - 0
  - TBFL
  - Transmit buffer full (write complete)
```

## Bezel serial protocol ("Dialog" / HpBlSeR09)

The firmware's display link is implemented in a source module `Dialog.c`, over a
port defined by `APP_DIALOG_PORT`; the protocol handshake string is `HpBlSeR09`
("HP Bezel Serial, rev 09"). The link runs at a configurable baud rate ("error
when change baud rate in Dialog.c"). Capabilities the MCU exposes to the NS9360:
`[ANALYSIS.md](#sources)`

- 7-segment display (`7seg` CLI test), error LED, per-outlet blue UID LEDs,
  buzzer with "LED Beep Codes".
- Health monitoring: `Display Connected` / `Display Disconnected` events and a
  toggleable "Display Communications Alarm".
- Front-bezel test entry: `fbt_init`, `fbt_init2`.
- The same daisy-chain path can flash "HP Intelligent Modular PDU Display
  Module" firmware to the bezel and extension bars.

---

## Sources

- **TMP89FM42LUG datasheet** (Toshiba TLCS-870/C1) — device overview + the
  UART0 register set.
- **`hpe-ipdu-firmware/ANALYSIS.md`** + `HEADERS-J1-J6.md` — the sub-MCU role
  (display/bezel controller) and the reverse-engineered "Dialog" protocol.
