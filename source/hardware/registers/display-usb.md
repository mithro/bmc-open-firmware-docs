# AST2050 USB 2.0, Video Engine & VGA (full register maps)

Complete register-by-register reference for the three large **display / USB**
blocks of the Aspeed **AST2050 (SoC generation 3, "G3"; also sold as AST1100)**
that are only summarised elsewhere in these docs:

1. the **USB 2.0 Virtual Hub Controller** (§15, base `0x1E6A0000`, VIC #5) — and
   its companion **USB 1.1 UHCI host controller** (base `0x1E6B0000`, §1b),
2. the **Video (Capture/Compression) Engine** (§20, base `0x1E700000`, VIC #7),
3. the **VGA Display Controller** (§34, legacy VGA I/O space + MMIO alias).

Every table is transcribed from the in-repo *AST2050/AST1100 A3 Datasheet V1.05*
(25 May 2010). Each register is listed with its offset/index, reset value,
per-field access, and a bit-field breakdown; reserved bits and reserved
registers are marked explicitly, and register gaps in an address window are
called out rather than silently dropped. Where a mainline Linux driver exists
for the equivalent block it is cross-checked and cited.

Citations use these short forms:

- `[DS §N p.P](#sources)` — the A3 datasheet, chapter N, printed page P (= PDF page).
- Named URLs — mainline Linux drivers and specs (see [Sources](#sources)).

```{admonition} G3 vs G4+ — offsets differ, but these three blocks mostly match
:class: important

The AST2050 is *not* mainline-Linux-supported (the earliest Aspeed in mainline
is the AST2400 / "G4"). Some G3 blocks sit at different offsets from their G4+
equivalents. For the three blocks documented here the register *offsets* are
in fact largely stable across generations, which is what makes the mainline
drivers usable as a cross-check:

- **USB vhub** — `HUB00…HUB3C` / device / endpoint offsets match the mainline
  [`aspeed-vhub`](https://github.com/torvalds/linux/tree/master/drivers/usb/gadget/udc/aspeed-vhub) gadget driver register file 1:1. `[vhubh]`
- **Video Engine** — `VR000…VR308` offsets match the `VE_*` offsets in the
  mainline [`aspeed-video`](https://github.com/torvalds/linux/blob/master/drivers/media/platform/aspeed/aspeed-video.c) V4L2 driver 1:1. `[aspeedvideo]`
- **VGA** — the legacy VGA + Aspeed extended-CRT index space (`CR80…CRD7`) is
  the same one the mainline **[`drm/ast`](https://github.com/torvalds/linux/tree/master/drivers/gpu/drm/ast)** PCI-VGA driver drives (that driver
  historically enumerates *AST1100* among its chips). This is **not** the
  same block as [`drm/aspeed`](https://github.com/torvalds/linux/tree/master/drivers/gpu/drm/aspeed), which is the separate SoC "GFX/CRT" controller at
  `0x1E6E6000`. `[astdrv]`, `[aspeeddrm]`
```

Access-attribute abbreviations used below: **R** read-only, **W** write-only,
**RW** read/write. "W1C" in a description means write-1-to-clear. Reset value
`X` means undefined at reset.

---

## 1. USB 2.0 Virtual Hub Controller (§15, base `0x1E6A0000`)

One hub controller plus **7 downstream device controllers** and a pool of **21
programmable endpoints** that can be assigned to any device. USB 2.0 HS/FS,
integrated DMA (M-bus, bypasses AHB), 32-stage descriptor rings per endpoint,
2 KB of SRAM split into 16×128-byte IN-transmit pages, RC-independent remote
wake-up. `[DS §15.1–15.2 p.154](#sources)`

### 1.1 Address map (offset from `0x1E6A0000`)

```{list-table} §15.3.1 Address definition
:header-rows: 1
:widths: 26 12 62

* - Offset
  - Size
  - Contents
* - `0x000–0x03F`
  - 64 B
  - Root/Global (hub) register file — 16 registers `HUB00…HUB3C`
* - `0x040–0x07F`
  - 64 B
  - Reserved
* - `0x080–0x087`
  - 8 B
  - Root device SETUP data buffer
* - `0x088–0x0BF`
  - 7×8 B
  - Device #1…#7 SETUP data buffers (8 B each, contiguous)
* - `0x0C0–0x0FF`
  - 64 B
  - Reserved
* - `0x100–0x16F`
  - 7×16 B
  - Device #1…#7 register files (16 B each: `DEV00…DEV0C`); device *N* base = `0x100 + (N−1)·0x10`
* - `0x170–0x1FF`
  - 144 B
  - Reserved
* - `0x200–0x34F`
  - 21×16 B
  - Programmable endpoint #0…#20 register files (16 B each: `EPP00…EPP0C`); endpoint *N* base = `0x200 + N·0x10`
```

The **SETUP data buffers** are 8-byte scratch areas holding the raw 8-byte USB
`SETUP` packet (`bmRequestType`, `bRequest`, `wValue`, `wIndex`, `wLength`) of
the most recent CONTROL transfer for the root device and for each downstream
device; they have no bit-field structure. `[DS §15.3.1 p.155](#sources)`

### 1.2 Root/Global (hub) register file `HUB00…HUB3C`

```{list-table} Root/Global register summary (offset from base)
:header-rows: 1
:widths: 12 10 44 34

* - Offset
  - Reset
  - Register
  - Access
* - `0x00`
  - `0`
  - HUB00 — Root Function Control & Status
  - mixed
* - `0x04`
  - `0`
  - HUB04 — Root Configuration Setting
  - mixed
* - `0x08`
  - `0`
  - HUB08 — Interrupt Control
  - RW
* - `0x0C`
  - `0`
  - HUB0C — Interrupt Status
  - mixed (W1C)
* - `0x10`
  - `0`
  - HUB10 — Programmable EP Pool ACK Interrupt Enable
  - RW
* - `0x14`
  - `0`
  - HUB14 — Programmable EP Pool NAK Interrupt Enable
  - RW
* - `0x18`
  - `0`
  - HUB18 — Programmable EP Pool ACK Interrupt Status
  - RW (W1C)
* - `0x1C`
  - `0`
  - HUB1C — Programmable EP Pool NAK Interrupt Status
  - RW (W1C)
* - `0x20`
  - `0x3FF`
  - HUB20 — Device Controller Soft Reset Enable
  - RW
* - `0x24`
  - `X`
  - HUB24 — USB Status (debug)
  - R
* - `0x28`
  - `X`
  - HUB28 — Programmable EP Pool Data Toggle Value Set
  - W
* - `0x2C`
  - `0`
  - HUB2C — Isochronous Transaction Fail Accumulator (debug)
  - RW
* - `0x30`
  - `0`
  - HUB30 — Endpoint 0 (hub default control EP) Control/Status
  - mixed
* - `0x34`
  - `X`
  - HUB34 — Endpoint 0 IN/OUT Data Buffer Base Address
  - RW
* - `0x38`
  - `0`
  - HUB38 — Endpoint 1 (hub status-change IN EP) Control/Status
  - mixed
* - `0x3C`
  - `0`
  - HUB3C — Endpoint 1 Status Change Bitmap Data
  - RW
```

`[DS §15.3.2 p.156–164](#sources)`

```{list-table} HUB00 (0x00) — Root Function Control & Status; reset 0
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31
  - R
  - USB PHY clock enable status: 0 = disabled by SCU0C[14], 1 = enabled. Enable sequence: SCU0C[14]=1 (wait 10 ms), SCU04[14]=0, HUB00[11]=1
* - 30:18
  - RW
  - Reserved (0)
* - 17
  - RW
  - Isochronous IN null-data response control: 0 = no response (host timeout), 1 = return 0-byte DATA0
* - 16
  - RW
  - Complete a "SPLIT IN transaction" after SOF received: 0 = disable, 1 = enable. **Must be 1 during Set_Address** or the status-phase IN cannot finish
* - 15
  - R
  - Loop-back test result: 0 = fail, 1 = pass (cleared when leaving USB Test Mode)
* - 14
  - R
  - Loop-back test finished: 0 = not yet, 1 = finished
* - 13
  - R
  - USB PHY BIST result: 0 = pass, 1 = fail (cleared by HUB00[12]=0)
* - 12
  - RW
  - USB PHY BIST control: 0 = off, 1 = on
* - 11
  - RW
  - Disable USB PHY reset: 0 = assert PHY reset, 1 = release PHY reset
* - 10:8
  - RW
  - USB Test Mode: 000 disable, 001 Test J, 010 Test K, 011 Test SE0_NAK, 100 Test Packet, 101/110 reserved, 111 Test Loop Back (debug)
* - 7
  - RW
  - Force USB bus-state timer to test mode (×32 faster) — debug
* - 6
  - RW
  - Force bus state to High Speed — debug
* - 5
  - RW
  - Remote-wakeup signalling pulse width: 0 = 8 ms, 1 = 12 ms
* - 4
  - RW
  - Enable manual remote wakeup (settable only in Suspend; H/W-cleared after wakeup)
* - 3
  - RW
  - Enable automatic remote wakeup (issued on any FW write while suspended)
* - 2
  - RW
  - Enable clock stopping in Suspend (must be 1 to use remote wakeup)
* - 1
  - RW
  - Upstream-port connection speed: 0 = HS + FS, 1 = FS only
* - 0
  - RW
  - Enable upstream-port connection
```

```{list-table} HUB04 (0x04) — Root Configuration Setting; reset 0
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:16
  - R
  - Status of DMA page buffer (debug): bit *k* = page #(k−16); 0 = free, 1 = allocated. The 2 KB IN SRAM is 16×128 B pages; pages 0–2 form a per-active-EP ring (their status bits reserved)
* - 15:7
  - —
  - Reserved
* - 6:0
  - RW
  - Root-function device address (apply after the Set_Address status phase)
```

```{list-table} HUB08 (0x08) — Interrupt Control (0 = disable, 1 = enable); reset 0
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:18
  - RW
  - Reserved (0)
* - 17
  - RW
  - Enable Programmable EP Pool NAK interrupt (first-level enable for all pooled EPs)
* - 16
  - RW
  - Enable Programmable EP Pool ACK/STALL interrupt
* - 15:9
  - RW
  - Enable Device #7…#1 controller interrupt (bit 15 = dev #7 … bit 9 = dev #1; first-level enable per downstream device)
* - 8
  - RW
  - Enable USB Suspend-Resume interrupt
* - 7
  - RW
  - Enable USB Suspend-Entry interrupt
* - 6
  - RW
  - Enable USB Bus-Reset interrupt
* - 5
  - RW
  - Enable Hub EP1 IN data-packet ACK interrupt
* - 4
  - RW
  - Enable Hub EP0 IN data-packet NAK interrupt
* - 3
  - RW
  - Enable Hub EP0 IN data-packet ACK/STALL interrupt
* - 2
  - RW
  - Enable Hub EP0 OUT data-packet NAK interrupt
* - 1
  - RW
  - Enable Hub EP0 OUT data-packet ACK/STALL interrupt
* - 0
  - RW
  - Enable Hub EP0 SETUP data-packet ACK interrupt
```

```{list-table} HUB0C (0x0C) — Interrupt Status; reset 0 (RW bits are W1C)
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:19
  - —
  - Reserved (0)
* - 18
  - R
  - USB command bus dead-locked (FATAL): a CPU bus command could not finish a USB transaction — USB clock stopped, PHY failed, or still suspended. Cannot be masked; cleared by returning to normal or by reset
* - 17
  - R
  - Programmable EP Pool NAK interrupt occurred
* - 16
  - R
  - Programmable EP Pool ACK/STALL interrupt occurred
* - 15:9
  - R
  - Device #7…#1 controller interrupt occurred (bit 15 = dev #7 … bit 9 = dev #1)
* - 8
  - RW
  - USB Suspend-Resume event occurred (upstream port resumed)
* - 7
  - RW
  - USB Suspend-Entry event occurred
* - 6
  - RW
  - USB Bus-Reset occurred
* - 5
  - RW
  - Hub EP1 IN data packet ACK/STALL returned
* - 4
  - RW
  - Hub EP0 IN data packet NAK returned
* - 3
  - RW
  - Hub EP0 IN data packet ACK/STALL returned
* - 2
  - RW
  - Hub EP0 OUT data packet NAK returned
* - 1
  - RW
  - Hub EP0 OUT data packet ACK/STALL returned (or PING responded with STALL)
* - 0
  - RW
  - Hub EP0 SETUP data arrives
```

```{list-table} HUB10 / HUB14 / HUB18 / HUB1C — Programmable-EP-pool interrupt enable/status; reset 0
:header-rows: 1
:widths: 12 12 22 54

* - Offset
  - Bits
  - Access
  - Function
* - `0x10`
  - 31:21
  - —
  - Reserved (0)
* - `0x10`
  - 20:0
  - RW
  - HUB10: per-endpoint ACK interrupt **enable**, bit *N* = programmable EP #*N* (0 = disable, 1 = enable)
* - `0x14`
  - 31:21
  - —
  - Reserved (0)
* - `0x14`
  - 20:0
  - RW
  - HUB14: per-endpoint NAK interrupt **enable**, bit *N* = EP #*N*
* - `0x18`
  - 31:21
  - —
  - Reserved (0)
* - `0x18`
  - 20:0
  - RW
  - HUB18: per-endpoint ACK interrupt **status** (W1C). Set on STALL, short OUT packet, descriptor interrupt-gen/single-mode, or descriptor list emptied
* - `0x1C`
  - 31:21
  - —
  - Reserved (0)
* - `0x1C`
  - 20:0
  - RW
  - HUB1C: per-endpoint NAK interrupt **status** (W1C), set when the EP responds NAK
```

```{list-table} HUB20 (0x20) — Device Controller Soft Reset Enable; reset 0x3FF (0 = normal, 1 = reset)
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:10
  - —
  - Reserved (0)
* - 9
  - RW
  - Enable Programmable EP Pool software reset
* - 8
  - RW
  - Enable DMA controller software reset
* - 7:1
  - RW
  - Enable Device #7…#1 controller software reset (bit 7 = dev #7 … bit 1 = dev #1)
* - 0
  - RW
  - Enable Root Hub controller software reset
```

Soft reset clears controller status only (not all registers); for a full reset
use SCU04. Set the bit to 1 to start, 0 to stop; no delay needed between.
`[DS §15.3.2 p.162](#sources)`

```{list-table} HUB24 (0x24) — USB Status (debug, read-only); reset X
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31
  - R
  - USB Suspend state
* - 30
  - R
  - USB Bus-Reset state
* - 29
  - R
  - USB bus line state DN (D−)
* - 28
  - R
  - USB bus line state DP (D+)
* - 27
  - R
  - USB bus speed: 0 = Full Speed, 1 = High Speed (valid after first post-bus-reset packet)
* - 26:16
  - R
  - Last USB frame-number record
* - 15
  - R
  - UTMI XcvrSelect: 0 = HS, 1 = FS
* - 14
  - R
  - UTMI TermSelect: 0 = HS, 1 = FS
* - 13:12
  - R
  - UTMI OPMode: 0 normal, 1 non-driving, 2 disable bit-stuff/NRZI, 3 reserved
* - 11:8
  - R
  - Endpoint number of last USB transaction
* - 7
  - —
  - Reserved (0)
* - 6:0
  - R
  - Device address of last USB transaction
```

```{list-table} HUB28 (0x28) — Programmable EP Pool Data Toggle Value Set (write-only); reset X
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:9
  - —
  - Reserved (0)
* - 8
  - W
  - Endpoint data-toggle initial value: 0 = DATA0, 1 = DATA1. Only one toggle initialised per write (indexed by bits[4:0]); reads return 0
* - 7:5
  - —
  - Reserved (0)
* - 4:0
  - W
  - Programmable endpoint index (0–20 valid, 21–31 invalid). Control/Bulk/Interrupt only; Iso EPs reset automatically on SOF
```

```{list-table} HUB2C (0x2C) — Isochronous Transaction Fail Accumulator (debug); reset 0
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:26
  - —
  - Reserved (0)
* - 25:16
  - RW
  - Isochronous OUT failure counter
* - 15:10
  - —
  - Reserved
* - 9:0
  - RW
  - Isochronous IN failure counter. Any write clears both counters
```

```{list-table} HUB30 (0x30) — Endpoint 0 (hub default control EP) Control/Status; reset 0
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:23
  - —
  - Reserved (0)
* - 22:16
  - R
  - EP0 OUT received data byte count
* - 15
  - —
  - Reserved (0)
* - 14:8
  - RW
  - EP0 IN data byte count for transfer
* - 7:3
  - —
  - Reserved (0)
* - 2
  - RW
  - EP0 OUT buffer ready to receive (H/W clears when data received)
* - 1
  - RW
  - EP0 IN buffer ready to transfer (H/W clears when sent). Bits 1 and 2 are mutually exclusive
* - 0
  - RW
  - EP0 STALL control (auto-cleared on next SETUP)
```

```{list-table} HUB34 (0x34) — Endpoint 0 IN/OUT Data Buffer Base Address; reset X
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:28
  - —
  - Reserved (0)
* - 27:3
  - RW
  - Base address of the 64-byte EP0 control data buffer (64-bit boundary); direction set by S/W per control-transfer mode
* - 2:0
  - —
  - Reserved (0)
```

```{list-table} HUB38 (0x38) — Endpoint 1 (hub status-change IN EP) Control/Status; reset 0
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:3
  - —
  - Reserved (0)
* - 2
  - W
  - Reset EP1 data-toggle bit to DATA0 (1 = reset)
* - 1
  - RW
  - EP1 STALL control
* - 0
  - RW
  - Enable Endpoint 1
```

```{list-table} HUB3C (0x3C) — Endpoint 1 Status Change Bitmap Data; reset 0
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:8
  - —
  - Reserved
* - 7:1
  - RW
  - Port #7…#1 status-change bit (device #7…#1)
* - 0
  - RW
  - Hub-port status-change bit
```

When any HUB3C bit is non-zero the hub returns this byte on an EP1 IN poll;
otherwise it NAKs. `[DS §15.3.2 p.164](#sources)`

### 1.3 Downstream Device #1–#7 register file `DEV00…DEV0C`

Identical layout for each of the 7 devices; device *N* base = `0x100 + (N−1)·0x10`.
`[DS §15.3.3 p.165–166](#sources)`

```{list-table} DEV00 (+0x00) — Downstream Device Function Enable Control; reset 0
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:15
  - —
  - Reserved (0)
* - 14:8
  - RW
  - Downstream device address (apply after Set_Address status phase)
* - 7
  - —
  - Reserved (0)
* - 6
  - RW
  - Enable EP0 IN data-packet NAK interrupt
* - 5
  - RW
  - Enable EP0 IN data-packet ACK/STALL interrupt
* - 4
  - RW
  - Enable EP0 OUT data-packet NAK interrupt
* - 3
  - RW
  - Enable EP0 OUT data-packet ACK/STALL interrupt
* - 2
  - RW
  - Enable EP0 SETUP data-packet ACK interrupt
* - 1
  - RW
  - Device-port speed: 0 = FS/LS, 1 = HS
* - 0
  - RW
  - Enable device port (cleared automatically on upstream-port bus reset)
```

```{list-table} DEV04 (+0x04) — Interrupt Status; reset 0 (W1C)
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:5
  - —
  - Reserved (0)
* - 4
  - RW
  - EP0 IN data-packet NAK returned
* - 3
  - RW
  - EP0 IN data-packet ACK received or STALL returned
* - 2
  - RW
  - EP0 OUT data-packet NAK returned
* - 1
  - RW
  - EP0 OUT data-packet ACK/STALL returned (or PING → STALL)
* - 0
  - RW
  - EP0 SETUP data-packet received
```

```{list-table} DEV08 (+0x08) — Endpoint 0 Control/Status; reset 0
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:29
  - —
  - Reserved (0)
* - 28
  - R
  - CSPLIT IN wait (debug)
* - 27
  - R
  - Normal IN wait (debug)
* - 26
  - R
  - Start SPLIT cycle (debug)
* - 25:24
  - R
  - Transmit DMA state machine (debug): 00 idle, 01 DMA request, 10 DMA done & data ready, 11 reserved
* - 23
  - —
  - Reserved (0)
* - 22:16
  - R
  - EP0 OUT received data byte count
* - 15
  - —
  - Reserved (0)
* - 14:8
  - RW
  - EP0 IN data byte count for transfer
* - 7:3
  - —
  - Reserved (0)
* - 2
  - RW
  - EP0 OUT buffer ready to receive
* - 1
  - RW
  - EP0 IN buffer ready to transfer
* - 0
  - RW
  - EP0 STALL control
```

```{list-table} DEV0C (+0x0C) — Endpoint 0 IN/OUT Data Buffer Base Address; reset X
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:28
  - —
  - Reserved (0)
* - 27:3
  - RW
  - Base address of the 64-byte control data buffer (64-bit boundary)
* - 2:0
  - —
  - Reserved (0)
```

### 1.4 Programmable Endpoint #0–#20 register file `EPP00…EPP0C`

Identical layout for each of the 21 pooled endpoints; endpoint *N* base =
`0x200 + N·0x10`. `[DS §15.3.4 p.167–171](#sources)`

```{list-table} EPP00 (+0x00) — Endpoint Configuration; reset 0
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:16
  - —
  - Reserved (0)
* - 15:14
  - RW
  - Isochronous data stages (auto-toggle Iso only): 00 = 1 stage, 01 = 2 stages, 1x = 3 stages
* - 13
  - RW
  - Endpoint auto-data-toggle disable: 0 = enable, 1 = disable (OUT: ignore sequence errors; IN: PID from descriptor list)
* - 12
  - RW
  - Endpoint STALL control (Bulk/Interrupt only); 1 = always STALL until cleared
* - 11:8
  - RW
  - Endpoint number
* - 7
  - —
  - Reserved (0)
* - 6:4
  - RW
  - Endpoint type: 00x disable, 010 Bulk In, 011 Bulk Out, 100 Interrupt In, 101 Interrupt Out, 110 Iso In, 111 Iso Out
* - 3:1
  - RW
  - Allocated device port: 000 root, 001–111 downstream device 1–7
* - 0
  - RW
  - Enable endpoint (0 = disabled/reset, 1 = enabled)
```

```{list-table} EPP04 (+0x04) — DMA Descriptor List Control/Status; reset 0
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:21
  - —
  - Reserved (0)
* - 20
  - R
  - Occupied transmit-IN buffer status (debug)
* - 19:16
  - R
  - Occupied transmit-IN buffer index (debug)
* - 15:13
  - —
  - Reserved (0)
* - 12
  - R
  - Current interrupt-generation flag from active descriptor (debug)
* - 11
  - R
  - CSPLIT IN wait (debug)
* - 10:9
  - R
  - Auto data-toggle count (debug)
* - 8
  - R
  - Start SPLIT cycle (debug)
* - 7:4
  - R
  - Current descriptor processing status (debug): 16 RX/TX states, 00 = RX idle … 15 = TX IN transaction done
* - 3
  - —
  - Reserved (0)
* - 2
  - RW
  - Descriptor-list operation reset (1 = reset descriptor engine & flush buffers)
* - 1
  - RW
  - Single-stage descriptor mode: 0 = 32-stage ring, 1 = 1-stage (write pointer at EPP0C auto-cleared when transaction done)
* - 0
  - RW
  - Descriptor-list operation enable: 0 = disabled / single-stage, 1 = 32-stage ring. Mutually exclusive with bit 1 (single mode wins)
```

```{list-table} EPP08 (+0x08) — DMA Descriptor/Buffer Base Address; reset X
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:28
  - —
  - Reserved (0)
* - 27:3
  - RW
  - Base address — descriptor-list base (when descriptors enabled) or DMA data-buffer base (when disabled); 8-byte (64-bit) boundary
* - 2:0
  - —
  - Reserved (0)
```

```{list-table} EPP0C (+0x0C) — DMA Descriptor List Read(DMA)/Write(CPU) Pointer and Status; reset 0
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31
  - R
  - Descriptor-list empty flag: 0 = not empty, 1 = empty
* - 30
  - —
  - Reserved (0)
* - 29:28
  - RW
  - Endpoint current data-toggle sequence value (next-transaction PID): 00 DATA0, 01 DATA2, 10 DATA1, 11 MDATA (write valid only in single mode, IN type, auto-toggle disabled)
* - 27
  - —
  - Reserved (0)
* - 26:16
  - RW
  - Packet size (bytes). Meaning: IN+single = Tx data length; IN+32-stage = Tx length; OUT+single = Rx length (by RXDMA); OUT+32-stage = EP max packet size (short-packet trigger)
* - 15:13
  - —
  - Reserved (0)
* - 12:8
  - RW
  - Descriptor-list DMA read pointer (H/W position; init only while disabled & not single mode)
* - 7:5
  - —
  - Reserved (0)
* - 4:0
  - RW
  - Descriptor-list CPU write pointer (leading pointer; WPTR = RPTR means empty, WPTR = RPTR−1 means full)
```

### 1.5 Programmable-endpoint DMA descriptor (in DRAM; 8 bytes/stage)

Each descriptor-ring stage is an 8-byte entry in memory (pointed to by EPP08),
not a register in the `0x1E6A0000` window. Bits are numbered by absolute
descriptor bit (`DES_0` = word at byte offset 0, bits 31:0; `DES_1` = word at
byte offset 4, bits 63:32). `[DS §15.3.5 p.172–173](#sources)`

```{list-table} DES_0 (bits 31:0) — Data Buffer Base Address; reset X
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:28
  - —
  - Reserved
* - 27:3
  - RW
  - DMA data-buffer base address (8-byte / 64-bit boundary)
* - 2:0
  - —
  - Reserved
```

```{list-table} DES_1 (bits 63:32) — Descriptor Control/Status; reset X
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 63
  - RW
  - Enable interrupt generation on this descriptor: interrupt raised when transaction done + this bit set, on last descriptor of an empty list, on STALL, or on NAK with empty list & NAK-int enabled
* - 62:60
  - R
  - Device port number (RX only): 000 root hub, 001–111 port 1–7
* - 59:56
  - R
  - Endpoint number (RX only)
* - 55
  - —
  - Reserved
* - 54:48
  - R
  - Device address (RX only)
* - 47:46
  - RW
  - Data packet PID: 00 DATA0, 01 DATA2, 10 DATA1, 11 MDATA. RX = received PID; TX = PID used when H/W auto-toggle (EPP00[13]) disabled
* - 45
  - R
  - End of packet (E) (RX only; Iso OUT to a FS device)
* - 44
  - R
  - Start of a packet (S) (RX only). With bit 45 encodes HS→FS Iso-OUT data relation (S:E) 00 middle, 01 end, 10 beginning, 11 all of the FS payload
* - 43
  - RW
  - OUT packet valid flag (written 1 by H/W when OUT-transaction DMA done)
* - 42:32
  - RW
  - Packet length in bytes. RX: written by DMA (received length, excl. CRC); TX: CPU sets the transmit length
```

### 1.6 Register reset table (§15.3.6)

Which reset source clears which register/field (Y = cleared). Registers not
listed have no reset control. `[DS §15.3.6 p.173](#sources)`

```{list-table} Reset sources per register
:header-rows: 1
:widths: 16 16 14 14 14 14 12

* - Register (bits)
  - SCU[14] global
  - Bus reset
  - HUB20[0]
  - HUB20[7:1]
  - HUB20[9]
  - EPP00[0]
* - HUB00[30:16], HUB00[15:14]*, HUB00[13:0]
  - Y
  - —
  - —
  - —
  - —
  - —
* - HUB04[6:0]
  - Y
  - Y
  - —
  - —
  - —
  - —
* - HUB08[17:0]
  - Y
  - —
  - —
  - —
  - —
  - —
* - HUB0C[17:16], HUB0C[15:9] (device-specific), HUB0C[8:0]
  - Y
  - Y
  - Y (port)
  - Y (dev)
  - —
  - —
* - HUB10 / HUB14 [20:0]
  - Y
  - —
  - —
  - —
  - —
  - —
* - HUB18 / HUB1C [20:0]
  - Y
  - Y
  - EPP[3:1]-specific
  - —
  - Y (EP)
  - Y (EP)
* - HUB20[9:0]
  - Y (all → 1)
  - —
  - —
  - —
  - —
  - —
* - HUB2C[25:16], [9:0]
  - Y
  - Y
  - Y
  - —
  - —
  - —
* - HUB30 / HUB38 / HUB3C
  - Y
  - —
  - —
  - —
  - —
  - —
* - DEV00[14:8], [6:1], [0]
  - Y
  - Y (bit0)
  - —
  - —
  - —
  - —
* - DEV04[4:0], DEV08[28:24]
  - Y
  - Y
  - device-specific
  - —
  - —
  - —
* - DEV08[2:0]
  - Y
  - —
  - —
  - —
  - —
  - —
* - EPP00[15:0]
  - Y
  - —
  - —
  - —
  - —
  - —
* - EPP04[12:8], [7:4], [2:0]
  - Y
  - Y
  - EPP[3:1]-specific
  - —
  - Y
  - Y
* - EPP0C[12:8], [4:0]
  - Y
  - Y
  - EPP[3:1]-specific
  - —
  - Y
  - Y
```

*HUB00[10:8] retains its value unless it equals 111 (test loop-back), per the
datasheet's "Others" column. `[DS §15.3.6 p.173](#sources)`

### 1.7 Mainline cross-check

The mainline [`aspeed-vhub`](https://github.com/torvalds/linux/tree/master/drivers/usb/gadget/udc/aspeed-vhub) USB-gadget driver register file matches this block
1:1: `AST_VHUB_CTRL` 0x00, `AST_VHUB_CONF` 0x04, `AST_VHUB_IER` 0x08,
`AST_VHUB_ISR` 0x0C, `AST_VHUB_EP_ACK_IER` 0x10, `AST_VHUB_EP_NACK_IER` 0x14,
`AST_VHUB_EP_ACK_ISR` 0x18, `AST_VHUB_EP_NACK_ISR` 0x1C, `AST_VHUB_SW_RESET`
0x20, `AST_VHUB_USBSTS` 0x24, `AST_VHUB_EP_TOGGLE` 0x28, `AST_VHUB_ISO_FAIL_ACC`
0x2C, `AST_VHUB_EP0_CTRL` 0x30, `AST_VHUB_EP0_DATA` 0x34, `AST_VHUB_EP1_CTRL`
0x38, `AST_VHUB_EP1_STS_CHG` 0x3C — the same `HUB00…HUB3C` offsets, with the
generic-endpoint window at base + 0x200 + N·0x10 as here. `[vhubh]` The driver
targets AST2400/2500/2600; the AST2050's 7 downstream devices + 21 pooled
endpoints are the ancestor of that design.

---

## 1b. USB 1.1 Host Controller (UHCI, base `0x1E6B0000`)

Distinct from the USB 2.0 *device-mode* virtual hub at `0x1E6A0000` (§1), the
AST2050 also has a **USB 1.1 host controller at base `0x1E6B0000`** (a `0x100`
window). It is a **standard Intel UHCI** (Universal Host Controller Interface)
block — *not* an Aspeed-proprietary register file — so its registers follow the
UHCI 1.1 specification rather than the datasheet: `USBCMD`/`USBSTS`/`USBINTR` at
offset `0x00`/`0x02`/`0x04`, `FRNUM` `0x06`, `FRBASEADD` `0x08`, `SOFMOD` `0x0C`,
and `PORTSC1`/`PORTSC2` at `0x10`/`0x12`. It is therefore documented here by
reference to that standard, which the mainline driver already implements. This
host controller carries the BMC's USB **virtual media** and **virtual
keyboard/mouse**.

- **Clock gate** — `SCU0C[7]` "Stop UCLK (USB 1.1)", the only SCU trace of the
  block. [DS §18 p.209](#sources) [`hwreg.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h)
- **Interrupt** — VIC source #4 ("USB1.1" in the Raptor IRQ map).
  [RAPTOR_ENGINEERING_AST2050_ANALYSIS.md](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/RAPTOR_ENGINEERING_AST2050_ANALYSIS.md)
- **Reset** — held by the `SCU04` USB1.1-host reset bit until released by init.

**Software.** The standard mainline [`uhci-hcd`](https://github.com/torvalds/linux/blob/master/drivers/usb/host/uhci-hcd.c) /
`generic-uhci` driver binds — the project's real-hardware device tree declares
`usb@1e6b0000` with `compatible = "aspeed,ast2400-uhci", "generic-uhci"`. Raptor's
2.6.28 port shipped a custom `astuhci` driver, but the generic UHCI driver is
expected to work against Aspeed's standards-compliant implementation. In QEMU the
stock UHCI host model (e.g. `piix3-usb-uhci`) presents the identical interface.

```{admonition} No EHCI (USB 2.0 host) on the AST2050
:class: important

The AST2050 has **no EHCI / USB 2.0 host controller**. This is stated explicitly
in the hardware-verified Raptor analysis — *"the AST2050 has UHCI only (no
EHCI/USB 2.0) … Do NOT add EHCI — AST2050 doesn't have it."* A `usb@1e6a1000`
EHCI node does appear in the G4-template real-hardware DTS, but that base address
is carried over from the AST2400 (G4) binding and does **not** correspond to G3
silicon. On the AST2050 the USB 2.0 capability is the *device-mode* virtual hub
at `0x1E6A0000` (§1 above), not an EHCI host. Model and port accordingly: a UHCI
**host** plus a USB 2.0 **device** hub, with no EHCI host block.
```

---

## 2. Video (Capture/Compression) Engine (§20, base `0x1E700000`)

Captures the internal VGA output (or an external DVO/ADC source) into DRAM and
compresses it with a mixed JPEG + Vector-Quantisation codec. Two YUV formats
(420/444), block-change detection, CRC scene-change detection, arbitrary down-
scaling with a 4×2 spatial filter, 12 JPEG quality levels, optional RC4
encryption of the output stream, and a video-mode-change watchdog. Up to
1920×1200×32bpp @ 60 Hz; ~30 fps at 1280×1024 YUV420. `[DS §20.1–20.2 p.232–233](#sources)`

All registers are protected by the **VR000 key** (write `0x1A03_8AA8` to unlock;
any other value locks — registers stay readable when locked). `[DS §20.3 p.234](#sources)`

### 2.1 Register file overview

```{list-table} Video Engine register map (offset from base 0x1E700000)
:header-rows: 1
:widths: 12 10 12 66

* - Offset
  - Reset
  - Access
  - Register
* - `0x000`
  - `0`
  - RW
  - VR000 — Protection Key
* - `0x004`
  - `0`
  - RW
  - VR004 — Video Engine Sequence Control (capture/compress triggers, status)
* - `0x008`
  - `0`
  - RW
  - VR008 — Video Control (source select, frame rate, DVO/ADC input)
* - `0x00C`
  - `X`
  - RW
  - VR00C — Video Timing Generation (VR008[5]=0) / Direct-Frame-Buffer base (VR008[5]=1)
* - `0x010`
  - `X`
  - RW
  - VR010 — Video Timing Generation (VR008[5]=0) / Direct-FB fetch timing + line offset (VR008[5]=1)
* - `0x014`
  - `X`
  - RW
  - VR014 — Video Scaling Factor (H/V down-scale)
* - `0x018`
  - `X`
  - RW
  - VR018 — Scaling Filter Parameter #0 (F00–F03)
* - `0x01C`
  - `X`
  - RW
  - VR01C — Scaling Filter Parameter #1 (F10–F13)
* - `0x020`
  - `X`
  - RW
  - VR020 — Scaling Filter Parameter #2 (F20–F23)
* - `0x024`
  - `X`
  - RW
  - VR024 — Scaling Filter Parameter #3 (F30–F33)
* - `0x028`
  - —
  - —
  - *(gap — not defined; reserved)*
* - `0x02C`
  - `0`
  - RW
  - VR02C — Video BCD (block-change detection) Control
* - `0x030`
  - `X`
  - RW
  - VR030 — Capturing Window Setting
* - `0x034`
  - `X`
  - RW
  - VR034 — Compression Window Setting
* - `0x038`
  - `X`
  - RW
  - VR038 — Compression Stream-Buffer Processing Offset
* - `0x03C`
  - `X`
  - RW/R
  - VR03C — Compression Stream-Buffer Read Offset
* - `0x040`
  - `X`
  - RW
  - VR040 — CRC Buffer Base Address
* - `0x044`
  - `X`
  - RW
  - VR044 — Video Source Buffer #1 Base Address
* - `0x048`
  - `X`
  - RW
  - VR048 — Video Source Buffer Scan-Line Offset
* - `0x04C`
  - `X`
  - RW
  - VR04C — Video Source Buffer #2 Base Address
* - `0x050`
  - `X`
  - RW
  - VR050 — BCD Flag Buffer Base Address
* - `0x054`
  - `X`
  - RW
  - VR054 — Compressed Video Stream Buffer Base Address
* - `0x058`
  - `X`
  - RW
  - VR058 — Video Stream Buffer Size (packet count/size)
* - `0x05C`
  - `X`
  - R
  - VR05C — Compression Stream-Buffer Write Offset (read-back)
* - `0x060`
  - `0`
  - RW
  - VR060 — Video Compression Control (JPEG/VQ/RC4, quant tables)
* - `0x064`
  - `X`
  - —
  - VR064 — reserved
* - `0x06C`
  - `X`
  - —
  - VR06C — reserved
* - `0x070`
  - `X`
  - R
  - VR070 — Total Size of Compressed Video Stream (read-back)
* - `0x074`
  - `X`
  - R
  - VR074 — Total Number of Compressed Video Blocks (read-back)
* - `0x078`
  - `X`
  - R
  - VR078 — Frame-End Offset of Compressed Stream Buffer (read-back)
* - `0x07C`
  - `X`
  - R
  - VR07C — Compressed Frame Counter (read-back)
* - `0x090`
  - `X`
  - R
  - VR090 — Video Source Left/Right Edge Detection (read-back)
* - `0x094`
  - `X`
  - R
  - VR094 — Video Source Top/Bottom Edge Detection (read-back)
* - `0x098`
  - `X`
  - R
  - VR098 — Video Mode Detection Status (read-back)
* - `0x300`
  - `0`
  - RW
  - VR300 — Video Control (RC4/scaling line buffer/VSYNC delay)
* - `0x304`
  - `0`
  - RW
  - VR304 — Video Interrupt Control (enables)
* - `0x308`
  - `X`
  - RW
  - VR308 — Video Interrupt Status (W1C)
* - `0x30C`
  - `X`
  - RW
  - VR30C — Mode-Detection Parameter
* - `0x310`
  - `0x0000_0000`
  - RW/R
  - VR310 — Video Memory Restriction Area Start Address
* - `0x314`
  - `0x0FFF_0000`
  - RW/R
  - VR314 — Video Memory Restriction Area End Address
* - `0x320`
  - `X`
  - RW
  - VR320 — Primary CRC Parameter (source buffer #1)
* - `0x324`
  - `X`
  - RW/R
  - VR324 — Secondary CRC Parameter (source buffer #2)
* - `0x328`
  - `X`
  - RW
  - VR328 — Video Data Truncation (R/G/B bit reduction)
* - `0x340`
  - `X`
  - R
  - VR340 — VGA Scratch Remap read-back (cursor pos/type/enable, remap CR80)
* - `0x344`
  - `X`
  - R
  - VR344 — VGA Scratch Remap read-back (H/W cursor X/Y position)
* - `0x348`
  - `X`
  - R
  - VR348 — VGA Scratch Remap read-back (cursor pattern address)
* - `0x34C`
  - `X`
  - R
  - VR34C — VGA Scratch Remap read-back (VGA CR8C–CR8F)
* - `0x350`
  - `X`
  - R
  - VR350 — VGA Scratch Remap read-back (VGA CR90–CR93)
* - `0x354`
  - `X`
  - R
  - VR354 — VGA Scratch Remap read-back (VGA CR94–CR97)
* - `0x358`
  - `X`
  - R
  - VR358 — VGA Scratch Remap read-back (VGA CR98–CR9B)
* - `0x35C`
  - `X`
  - R
  - VR35C — VGA Scratch Remap read-back (VGA power/status + CR9C–CR9E)
* - `0x400–0x4FC`
  - `X`
  - RW
  - VR400–VR4FC — RC4 encryption key SRAM #0–#63 (64 words / 256 B)
```

Undefined offsets between the rows above (e.g. `0x068`, `0x080–0x08C`,
`0x09C–0x2FC`, `0x318–0x31C`, `0x32C–0x33C`, `0x360–0x3FC`) are not documented
and read as reserved. `[DS §20.3 p.234–255](#sources)`

### 2.2 Key bit-field registers

```{list-table} VR000 (0x000) — Protection Key; reset 0
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:0
  - RW
  - Protection key. Write `0x1A03_8AA8` to unlock (read-back `0x0000_0001`); any other value locks (read-back `0x0000_0000`). Reset by power-on, watchdog and SCU S/W reset; wait ≥1 µs after reset before unlocking
```

```{list-table} VR004 (0x004) — Video Engine Sequence Control; reset 0
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:19
  - R
  - Reserved (0)
* - 18
  - R
  - Video compression-engine status: 0 = busy, 1 = idle
* - 17
  - R
  - Reserved (0)
* - 16
  - R
  - Video capture-engine status: 0 = busy, 1 = idle
* - 15:12
  - R
  - Reserved (0)
* - 11:10
  - RW
  - Video data-format conversion for compression: 00 YUV444, 01 YUV420, 10/11 reserved
* - 9
  - RW
  - Reserved (must be 0)
* - 8
  - RW
  - Reserved (must be 0)
* - 7
  - RW
  - Enable watchdog for input-video mode-change detection (works only when VR004[0]=1)
* - 6
  - RW
  - Trigger insert of one full-frame compression into a stream (write 1; read 1 = not complete)
* - 5
  - RW
  - Enable automatic video compression: 0 = single frame per trigger, 1 = multiple frames (needs double buffering)
* - 4
  - RW
  - Enable/trigger video compression (0→1 triggers single-frame; ensure VR004[18]=1 first)
* - 3
  - RW
  - Enable capturing multiple frames (double-buffer); set before VR004[1]
* - 2
  - RW
  - Force compression engine idle (only when capture idle and compression hung)
* - 1
  - RW
  - Enable/trigger video capture (0→1 triggers; ensure VR004[16]=1 first)
* - 0
  - RW
  - Trigger video mode-detection hardware (0→1 triggers; 1 = enable detection HW)
```

Auto/trigger modes (VR004[3],[5]): 0,0 = single-frame S/W trigger, frame-buffer;
0,1 = single-frame H/W auto-trigger, frame-buffer; 1,1 = multi-frame H/W
auto-trigger, stream-buffer (1,0 = N/A). `[DS §20.3 p.235](#sources)`

```{list-table} VR008 (0x008) — Video Control; reset 0
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:24
  - R
  - Reserved (0)
* - 23:16
  - RW
  - Max frame-rate control: 0x00 = capture all frames; else max rate = VR008[23:16]·(source rate)/60
* - 15:14
  - RW
  - Reserved (must be 0)
* - 13
  - RW
  - Digital-video-input clock mode: 0 = single-edge, 1 = dual-edge
* - 12
  - RW
  - Video-input port bit number: 0 = 24-bit, 1 = 18-bit (single-edge only, VR008[13]=0)
* - 11:10
  - RW
  - Digital-video-input clock delay: 00 none, 01 ~1 ns, 10 inverted, 11 inverted + ~1 ns
* - 9
  - RW
  - Reserved (must be 0)
* - 8
  - RW
  - (VR008[5]=0) Disable H/W cursor overlay for internal VGA: 0 = with overlay, 1 = without. (VR008[5]=1) Auto mode for direct-fetch VGA frame buffer: 1 = video HW auto-references VGA settings (VR008[3],[4], VR00C, VR010)
* - 7:6
  - RW
  - Data format for capture: 00 CCIR601-2 YUV, 01 full-range YUV, 10 RGB (debug), 11 invalid
* - 5
  - RW
  - Fetch video directly from VGA frame buffer (internal VGA only): 0 = VGA/DVO input, 1 = direct-fetch (hi-color/true-color modes; cursor overlay done by client)
* - 4
  - RW
  - (VR008[5]=0) DE-signal source: 0 = external DE (DVI), 1 = internal timing generator. (VR008[5]=1) VGA frame-buffer bpp: 0 = 32 bpp, 1 = 16 bpp
* - 3
  - RW
  - (VR008[5]=0) External-source attribute: 0 = pure digital, 1 = from external ADC (forces internal timing gen). (VR008[5]=1) 16-bpp color mode: 0 = RGB565, 1 = RGB555
* - 2
  - RW
  - Video-source selection: 0 = integrated VGA controller, 1 = external video source
* - 1
  - RW
  - Source VSYNC polarity: 0 = same, 1 = inverted (reset to 0 before mode-detect trigger)
* - 0
  - RW
  - Source HSYNC polarity: 0 = same, 1 = inverted (reset to 0 before mode-detect trigger)
```

```{list-table} VR00C / VR010 — dual-purpose timing / direct-fetch registers
:header-rows: 1
:widths: 12 12 20 56

* - Offset
  - Bits
  - Access
  - Function
* - `0x00C`
  - 31:29
  - R
  - VR00C (VR008[5]=0, timing-gen): reserved (0)
* - `0x00C`
  - 28:16
  - RW
  - Number of pixels from HSYNC rising edge to first active pixel
* - `0x00C`
  - 15:13
  - RW
  - Reserved (0)
* - `0x00C`
  - 12:0
  - RW
  - Number of pixels from HSYNC rising edge to last active pixel
* - `0x00C`
  - 31:28 / 27:3 / 2:0
  - RW
  - VR00C (VR008[5]=1, direct-FB): reserved / direct-fetch base address bit[27:3] / reserved
* - `0x010`
  - 31:28
  - RW
  - VR010 (VR008[5]=0, timing-gen): reserved (0)
* - `0x010`
  - 27:16
  - RW
  - Scan lines from VSYNC rising edge to first active scan line
* - `0x010`
  - 15:12
  - RW
  - Reserved (0)
* - `0x010`
  - 11:0
  - RW
  - Scan lines from VSYNC rising edge to last active scan line
* - `0x010`
  - 31:16
  - RW
  - VR010 (VR008[5]=1, direct-FB): direct-fetch timing control bit[15:0]; 64-pixel min fetch time = VR010[31:15]·MCLK
* - `0x010`
  - 13:3 / 2:0
  - RW
  - direct-fetch line offset bit[27:3] / reserved (0)
```

```{list-table} VR014 (0x014) — Video Scaling Factor; reset X
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:16
  - RW
  - Vertical down-scaling factor (≥ 4096; output V size = input V size · 4096 / factor)
* - 15:0
  - RW
  - Horizontal down-scaling factor (≥ 4096; output H size = input H size · 4096 / factor)
```

```{list-table} VR018 / VR01C / VR020 / VR024 — Scaling Filter Parameters; reset X
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:0
  - RW
  - VR018: coefficients F03[31:24], F02[23:16], F01[15:8], F00[7:0] (2's-complement S2.5). VR01C = F13…F10, VR020 = F23…F20, VR024 = F33…F30. Typical presets: factor = 1.0 → `0x0020_0000`; 0.5 ≤ factor < 1.0 → `0x0010_1000`; factor < 0.5 → `0x0808_0808`
```

```{list-table} VR02C (0x02C) — Video BCD (block-change detection) Control; reset 0
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:24
  - R
  - Reserved (0)
* - 23:16
  - RW
  - BCD tolerance value (blocks changing by ≤ this are treated as unchanged)
* - 15:2
  - R
  - Reserved (0)
* - 1
  - RW
  - Delay block-change update by one frame: 0 = disable, 1 = enable
* - 0
  - RW
  - Enable block-change detection: 0 = compress all frames, 1 = compress changed blocks only
```

```{list-table} VR030 / VR034 — Capture / Compression window; reset X
:header-rows: 1
:widths: 12 12 20 56

* - Offset
  - Bits
  - Access
  - Function
* - `0x030`
  - 31:27 / 15:11
  - RW
  - VR030 reserved (0)
* - `0x030`
  - 27:16
  - RW
  - Horizontal total pixels to be captured
* - `0x030`
  - 10:0
  - RW
  - Vertical total scan lines to be captured
* - `0x034`
  - 31:27 / 15:11
  - RW
  - VR034 reserved (0)
* - `0x034`
  - 27:16
  - RW
  - Horizontal total pixels to be compressed
* - `0x034`
  - 10:0
  - RW
  - Vertical total scan lines to be compressed
```

```{list-table} VR038 / VR03C — Compression stream-buffer processing / read offset; reset X
:header-rows: 1
:widths: 12 12 20 56

* - Offset
  - Bits
  - Access
  - Function
* - `0x038`
  - 31:22 / 6:0
  - RW
  - VR038 reserved (0)
* - `0x038`
  - 21:7
  - RW
  - Stream-buffer process offset (address the ISR has accepted but still occupies)
* - `0x03C`
  - 31:22 / 6:0
  - R
  - VR03C reserved (0)
* - `0x03C`
  - 21:7
  - RW
  - Stream-buffer read offset (current S/W read pointer)
```

```{list-table} VR040–VR058 — DRAM buffer base addresses and stream size; reset X
:header-rows: 1
:widths: 12 12 18 58

* - Offset
  - Bits
  - Access
  - Function
* - `0x040`
  - 27:3
  - RW
  - CRC buffer base address bit[27:3] (bit[2:0] = 0); reserved 31:28 & 2:0
* - `0x044`
  - 27:8
  - RW
  - Video source buffer #1 base address bit[27:8] (bit[7:0] = 0); reserved 31:28 & 7:0
* - `0x048`
  - 13:8
  - RW
  - Scan-line offset (line-to-line address distance) of source buffers, bit[13:8] (bit[2:0]=0); reserved 31:14 & 2:0
* - `0x04C`
  - 27:8
  - RW
  - Video source buffer #2 base address bit[27:8] (bit[7:0] = 0); reserved 31:14 & 7:0
* - `0x050`
  - 27:3
  - RW
  - BCD flag-buffer base address bit[27:3] (4 bits/block; bit[2:0]=0); reserved 31:28 & 2:0
* - `0x054`
  - 27:7
  - RW
  - Compressed video stream-buffer base address bit[27:7] (bit[6:0]=0); reserved 31:28 & 6:0
* - `0x058`
  - 4:3
  - RW
  - Stream-buffer packet number: 00 = 4, 01 = 8, 10 = 16, 11 = 32 packets; reserved 31:5
* - `0x058`
  - 2:0
  - RW
  - Stream-buffer packet size: 000 1 KB, 001 2 KB, 010 4 KB, 011 8 KB, 100 16 KB, 101 32 KB, 110 64 KB, 111 128 KB
```

```{list-table} VR05C (0x05C) — Compression Stream-Buffer Write Offset (read-back); reset X
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:22
  - R
  - Reserved (0)
* - 21:7
  - R
  - Current write offset for compressed data in the stream buffer
* - 6:0
  - R
  - Reserved (0)
```

```{list-table} VR060 (0x060) — Video Compression Control; reset 0
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:22
  - RW
  - Reserved (0)
* - 21:20
  - RW
  - JPEG Huffman encoding table select: 00 = Y and UV tables, 01 = Y only, 1x = UV only (00 recommended)
* - 19
  - RW
  - Reserved (must be 1)
* - 18:17
  - RW
  - JPEG engine hardware test control (write 0 normally)
* - 16
  - RW
  - Reserved (must be 0)
* - 15:11
  - RW
  - DCT luminance quant-table select: bit[15] chooses luminance(0)/chrominance(1) table set; bit[14:11] = table #0–#11
* - 10:6
  - RW
  - DCT chrominance quant-table select: bit[10] chooses set; bit[9:6] = table #0–#11
* - 5
  - RW
  - Enable RC4 encryption of the compressed stream
* - 4:2
  - RW
  - Reserved (must be 0)
* - 1
  - RW
  - Enable 4-color VQ encoding: 0 = 2-color VQ, 1 = 4-color VQ
* - 0
  - RW
  - JPEG-only encoding: 0 = JPEG/VQ mixed mode, 1 = JPEG only
```

```{list-table} VR064 / VR06C — reserved
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - —
  - —
  - VR064 (0x064) and VR06C (0x06C) are documented as reserved (no fields)
```

```{list-table} VR070 / VR074 / VR078 / VR07C — compression read-back counters; reset X
:header-rows: 1
:widths: 12 12 16 60

* - Offset
  - Bits
  - Access
  - Function
* - `0x070`
  - 19:0
  - R
  - Total size of compressed video stream stored for a frame (unit = 1 dword); reserved 31:20
* - `0x074`
  - 29:16
  - R
  - Compressed block counter (blocks compressed into stream this frame)
* - `0x074`
  - 13:0
  - R
  - Processed total block counter (blocks processed by engine; YUV420 only); reserved 31:30 & 15:14
* - `0x078`
  - 21:3
  - R
  - Frame-end offset of stream buffer bit[21:3] (add to VR054 for last-data address; bit[2:0]=0); reserved 31:22 & 2:0
* - `0x07C`
  - 31:0
  - R
  - Compressed frame counter (frames compressed so far)
```

```{list-table} VR090 (0x090) — Video Source Left/Right Edge Detection (read-back); reset X
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:28
  - R
  - Reserved (0)
* - 27:16
  - R
  - Right-edge location from HSYNC rising edge (unit = 1 pixel)
* - 15
  - R
  - No display clock detected: 0 = none, 1 = clock detected
* - 14
  - R
  - No active display detected: 0 = none, 1 = active display detected
* - 13
  - R
  - No HSYNC detected: 0 = none, 1 = HSYNC detected
* - 12
  - R
  - No VSYNC detected: 0 = none, 1 = VSYNC detected
* - 11:0
  - R
  - Left-edge location from HSYNC rising edge (unit = 1 pixel)
```

```{list-table} VR094 (0x094) — Video Source Top/Bottom Edge Detection (read-back); reset X
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:29
  - R
  - Reserved (0)
* - 27:16
  - R
  - Bottom-edge location from VSYNC rising edge (unit = 1 scan line)
* - 15:12
  - R
  - Reserved (0)
* - 11:0
  - R
  - Top-edge location from VSYNC rising edge (unit = 1 scan line)
```

```{list-table} VR098 (0x098) — Video Mode Detection Status (read-back); reset X
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31
  - R
  - Mode-detection HSYNC ready: 0 = not ready, 1 = HSYNC signal detected
* - 30
  - R
  - Mode-detection VSYNC ready: 0 = not ready, 1 = VSYNC detected
* - 29
  - R
  - Mode-detection HSYNC polarity: 0 = positive, 1 = negative
* - 28
  - R
  - Mode-detection VSYNC polarity: 0 = positive, 1 = negative
* - 27:16
  - R
  - Vertical scan lines detected between two VSYNCs (all-1 if no VSYNC)
* - 15
  - R
  - Video source out of sync: 0 = stable, 1 = out of sync (valid only when watchdog VR004[7]=1)
* - 14
  - R
  - Mode-detection vertical signal stable
* - 13
  - R
  - Mode-detection horizontal signal stable
* - 12
  - R
  - Auto-detect external digital source: 0 = DVI receiver (with DE), 1 = ADC output (no DE)
* - 11:0
  - R
  - Horizontal period of detected HSYNC (valid when VR098[13]=1; all-1 if none; 24 MHz measure clock)
```

```{list-table} VR300 (0x300) — Video Control; reset 0
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:16
  - R
  - Reserved (0)
* - 15
  - RW
  - RC4 non-auto reset mode (recommend 1)
* - 14
  - RW
  - RC4 save mode (recommend 1)
* - 13:10
  - RW
  - Reserved (must be 0)
* - 9
  - RW
  - RC4 test mode (must be 0)
* - 8
  - RW
  - RC4 initial reset (only when engine idle: 1 resets RC4 state, then 0)
* - 7:6
  - RW
  - Reserved (must be 0)
* - 5:4
  - RW
  - Enable vertical down-scaling line buffer: 00 disable, 01 enable, 10/11 invalid (must enable for scaling filter, else line-drop is used)
* - 3
  - RW
  - Reserved (0)
* - 2
  - RW
  - Delay internal VSYNC: 1 = delay by 12 HSYNC periods (capture auto mode + anti-flicker)
* - 1
  - RW
  - Video stream-buffer controller save mode: 1 = recommended (0 = internal test)
* - 0
  - RW
  - Reserved (must be 0)
```

```{list-table} VR304 / VR308 — Video interrupt control / status
:header-rows: 1
:widths: 10 12 16 62

* - Bit
  - VR304 (en, reset 0)
  - VR308 (status, reset X, W1C)
  - Meaning
* - 5
  - Enable video frame-complete int
  - Video frame-complete int status
  - Whole frame captured + compressed
* - 4
  - Enable video mode-detection-ready int
  - Mode-detection-ready int status
  - Mode detection finished
* - 3
  - Enable video compression-complete int
  - Compression-complete int status
  - Compression of a frame complete
* - 2
  - Enable compression packet-ready int
  - Compression packet-ready int status
  - A stream packet is ready
* - 1
  - Enable video frame-capture-complete int
  - Capture-complete int status
  - A frame captured
* - 0
  - Enable mode-detect watchdog out-of-lock int
  - Mode-detect watchdog out-of-lock status
  - Source mode changed (watchdog)
* - 31:6
  - Reserved (VR304[7],[6] reserved 0)
  - Reserved (VR308[31:8] X, [7:6] 0)
  - —
```

```{list-table} VR30C (0x30C) — Mode-Detection Parameter; reset X
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:28
  - RW
  - Horizontal stable-detection tolerance bit[3:0] (unit = 24 MHz clock period)
* - 27:24
  - RW
  - Vertical stable-detection tolerance bit[3:0] (unit = one scan-line period)
* - 23:20
  - RW
  - Horizontal stable minimum bit[3:0] (min stable HSYNC count; min acceptable 3)
* - 19:16
  - RW
  - Vertical stable minimum bit[3:0] (min stable VSYNC count; min acceptable 3)
* - 15:8
  - RW
  - Mode-detection edge-pixel threshold bit[7:0] (min RGB value of active pixels for edge detect; ADC-noise screening)
* - 7:0
  - RW
  - Reserved (0)
```

```{list-table} VR310 / VR314 — Video Memory Restriction Area (write access outside is discarded)
:header-rows: 1
:widths: 12 12 20 56

* - Offset
  - Bits
  - Access
  - Function
* - `0x310`
  - 27:16
  - RW
  - Start address (64 KB aligned); reset `0x0000_0000`; reserved 31:28 (R) & 15:0 (R)
* - `0x314`
  - 27:16
  - RW
  - End address (64 KB aligned); reset `0x0FFF_0000`; reserved 31:28 (R) & 15:0 (R)
```

```{list-table} VR320 / VR324 — Primary / Secondary CRC parameter (24-bit CRC)
:header-rows: 1
:widths: 12 12 18 58

* - Offset
  - Bits
  - Access
  - Function
* - `0x320`
  - 31:16
  - RW
  - Primary CRC upper 16-bit polynomial (source buffer #1)
* - `0x320`
  - 15:8
  - RW
  - Primary CRC lower 8-bit polynomial
* - `0x320`
  - 7:2
  - RW
  - Max frame-skip count for CRC comparison (effective when VR320[0]=1)
* - `0x320`
  - 1
  - RW
  - Reserved (must be 0)
* - `0x320`
  - 0
  - RW
  - Scene-change detection scheme: 0 = pixel-by-pixel, 1 = CRC comparison (recommended; lower bandwidth)
* - `0x324`
  - 31:16
  - RW
  - Secondary CRC upper 16-bit polynomial (source buffer #2)
* - `0x324`
  - 15:8
  - RW
  - Secondary CRC lower 8-bit polynomial
* - `0x324`
  - 7:0
  - R
  - Reserved (0)
```

```{list-table} VR328 (0x328) — Video Data Truncation; reset X
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:16
  - R
  - Reserved (0)
* - 15:9
  - R
  - Reserved (0)
* - 8:6
  - RW
  - R-channel reduction: 000 none … 111 reduce 7 bits
* - 5:3
  - RW
  - G-channel reduction: 000 none … 111 reduce 7 bits
* - 2:0
  - RW
  - B-channel reduction: 000 none … 111 reduce 7 bits
```

```{list-table} VR340 / VR344 / VR348 — VGA scratch remap read-back (H/W cursor); reset X, read-only
:header-rows: 1
:widths: 12 12 16 60

* - Offset
  - Bits
  - Access
  - Function
* - `0x340`
  - 29:24
  - R
  - VGA H/W cursor X position offset bit[5:0]; reserved 31:30
* - `0x340`
  - 21:16
  - R
  - VGA H/W cursor Y position offset bit[5:0]; reserved 23:22 & 15:10
* - `0x340`
  - 9
  - R
  - VGA H/W cursor type: 0 = monochrome, 1 = color
* - `0x340`
  - 8
  - R
  - VGA H/W cursor enabled
* - `0x340`
  - 7:0
  - R
  - Remap of VGA CR80 register
* - `0x344`
  - 26:16
  - R
  - H/W cursor Y position bit[10:0]; reserved 31:27 & 15:12
* - `0x344`
  - 11:0
  - R
  - H/W cursor X position bit[11:0]
* - `0x348`
  - 25:3
  - R
  - H/W cursor pattern memory address bit[25:3]; reserved 31:26 & 2:0
```

```{list-table} VR34C–VR35C — VGA scratch remap read-back (CR8C–CR9E + status); reset X, read-only
:header-rows: 1
:widths: 12 12 16 60

* - Offset
  - Bits
  - Access
  - Function
* - `0x34C`
  - 31:24 / 23:16 / 15:8 / 7:0
  - R
  - Remap of VGA CR8F / CR8E / CR8D / CR8C
* - `0x350`
  - 31:24 / 23:16 / 15:8 / 7:0
  - R
  - Remap of VGA CR93 / CR92 / CR91 / CR90
* - `0x354`
  - 31:24 / 23:16 / 15:8 / 7:0
  - R
  - Remap of VGA CR97 / CR96 / CR95 / CR94
* - `0x358`
  - 31:24 / 23:16 / 15:8 / 7:0
  - R
  - Remap of VGA CR9B / CR9A / CR99 / CR98
* - `0x35C`
  - 31:30
  - R
  - VGA power state
* - `0x35C`
  - 29 / 28 / 27 / 26 / 25 / 24
  - R
  - VGA attribute-index-register bit 5 / mask-register-not-zero / CRT reset / screen off / reset / enable
* - `0x35C`
  - 23:16 / 15:8 / 7:0
  - R
  - Remap of VGA CR9E / CR9D / CR9C
```

```{list-table} VR400–VR4FC (0x400–0x4FC) — RC4 Encryption Key SRAM; reset X
:header-rows: 1
:widths: 14 10 76

* - Bits
  - Access
  - Function
* - 31:0
  - RW
  - RC4 key data SRAM. 64 dwords (registers #0–#63, 256 B total) holding the RC4 expanded keys; must be initialised before enabling RC4 (VR060[5]=1). Key expansion done by firmware
```

### 2.3 Mainline cross-check

The mainline [`aspeed-video`](https://github.com/torvalds/linux/blob/master/drivers/media/platform/aspeed/aspeed-video.c) V4L2 driver drives the same offsets under `VE_*`
names: `VE_PROTECTION_KEY` 0x000, `VE_SEQ_CTRL` 0x004, `VE_CTRL` 0x008,
`VE_TGS_0/1` 0x00C/0x010, `VE_SCALING_FACTOR` 0x014, `VE_SCALING_FILTER0..3`
0x018–0x024, `VE_BCD_CTRL` 0x02C, `VE_CAP_WINDOW` 0x030, `VE_COMP_WINDOW` 0x034,
`VE_COMP_PROC_OFFSET` 0x038, `VE_COMP_OFFSET` 0x03C, `VE_JPEG_ADDR` 0x040,
`VE_SRC0_ADDR` 0x044, `VE_SRC_SCANLINE_OFFSET` 0x048, `VE_SRC1_ADDR` 0x04C,
`VE_COMP_ADDR` 0x054, `VE_STREAM_BUF_SIZE` 0x058, `VE_COMP_CTRL` 0x060,
`VE_MODE_DETECT_STATUS` 0x098, `VE_INTERRUPT_CTRL` 0x304, `VE_INTERRUPT_STATUS`
0x308 — matching `VR000…VR308` here. The same `VE_CTRL` capture/compress
trigger and mode-detect bits map to VR004. The unlock key `0x1A03_8AA8` is the
driver's `VE_PROTECTION_KEY_UNLOCK`. `[aspeedvideo]`

---

## 3. VGA Display Controller (§34)

An in-band, IBM-VGA-compliant PCI display device (32-bit PCI, 33 MHz). Claims
the *VGA Device* PCI class when enabled and *Video Device* when disabled; shares
the top of SDRAM for its frame buffer (size set by external trapping resistors).
Max 1920×1200 @ 60 Hz (200 MHz video clock), 200 MHz triple RAMDAC, VESA DDC,
64×64 hardware cursor, 24-bit DVO output. Reset only by PCI-bus reset or
power-on. `[DS §34.1–34.2 p.368–369](#sources)`

Registers are accessed via **legacy VGA I/O ports** (with the 3B*/3D* mono/color
alias and 3C4/3CE/3C0 index+data pairs) and, for the extended set, also via an
**MMIO alias** at `Base + index`. Standard VGA groups (Sequencer, CRTC,
Graphics, Attribute, RAMDAC) are transcribed in full below because the datasheet
specifies Aspeed-specific bits within them; the Aspeed **Extended CRT** set
(§34.9) — frame-buffer base, scan pitch, mode/PLL controls, hardware cursor — is
the board-porting-critical part.

### 3.1 General / external registers

```{list-table} General VGA registers (legacy I/O port)
:header-rows: 1
:widths: 14 18 10 58

* - Register
  - I/O port
  - Reset
  - Fields
* - VGAER — VGA Enable
  - R/W 3C3
  - 00h
  - [0] RW VGA enable (0 disable, 1 enable); [7:1] reserved
* - VGAMR — Miscellaneous Output
  - W 3C2 / R 3CC
  - 00h
  - [7] vertical-sync polarity (0 +, 1 −); [6] horizontal-sync polarity; [5] page bit for odd/even; [4] reserved; [3:2] clock select (00 25.175 MHz, 01 28.322 MHz, 1x D-PLL programmed); [1] enable video memory at VGA aperture; [0] I/O address select (0 = 3Bx, 1 = 3Dx). All RW
* - VGAFCR — Feature Control
  - W 3BA/3DA / R 3CA
  - 00h
  - [3] feature control bit[2]; [1:0] feature control bit[1:0]; [7:4],[2] reserved. All RW
* - VGAIR0 — Input Status #0
  - R 3C2
  - 00h
  - [7] vertical-retrace interrupt flag; [4] video DAC comparator read-back; [6:5],[3:0] reserved
* - VGAIR1 — Input Status #1
  - R 3BA/3DA
  - X1h
  - [5:4] diagnostic (00 P2/P0, 01 P5/P4, 10 P3/P1, 11 P7/P6 — pre-RAMDAC DVO bits); [3] vertical-retrace signal; [0] inversion of display-enable (0 during DE, 1 out of DE); [7:6],[2:1] reserved
* - VGAFBR0 — Frame Buffer Segment Address #0
  - R/W 3CD
  - 00h
  - [7:4] segment read address bit[3:0]; [3:0] segment write address bit[3:0]
* - VGAFBR1 — Frame Buffer Segment Address #1
  - R/W 3CB
  - 00h
  - [7:4] segment read address bit[7:4]; [3:0] segment write address bit[7:4]
```

`[DS §34.3 p.369–371](#sources)`

### 3.2 Sequencer registers (index port 3C4, data port 3C5)

```{list-table} Sequencer (VGASR*) — data at 3C5, indexed by 3C4
:header-rows: 1
:widths: 10 44 10 36

* - Index
  - Register
  - Reset
  - Fields
* - —
  - VGASRI — Sequencer Index (port 3C4)
  - 00h
  - [5:0] index bit[5:0]; [7:6] reserved
* - 00
  - VGASR0 — Reset
  - 00h
  - [1] async reset (active-low: 0 reset, 1 run); [0] sync reset (active-low); [7:2] reserved
* - 01
  - VGASR1 — Clocking Mode
  - 00h
  - [5] screen off (1 = off); [4] shift-load by 4; [3] divide video clock by 2; [2] shift-load by 2; [0] dot-clock (0 = 9-dot, 1 = 8-dot char); [7:6],[1] reserved
* - 02
  - VGASR2 — Map Mask
  - 00h
  - [3:0] enable memory write map[3:0]; [7:4] reserved
* - 03
  - VGASR3 — Character Map Select
  - 00h
  - [5] CG map A select bit[2]; [4] CG map B select bit[2]; [3:2] CG map A select bit[1:0]; [1:0] CG map B select bit[1:0]; [7:6] reserved
* - 04
  - VGASR4 — Memory Mode
  - 00h
  - [3] enable Chain-4 mode; [2] odd/even (0 = odd/even, 1 = sequential); [1] extended memory (0 = 64 KB, 1 = 256 KB); [7:4],[0] reserved
```

`[DS §34.4 p.371–372](#sources)`

### 3.3 CRT Controller registers (index port 3B4/3D4, data 3B5/3D5)

```{list-table} CRTC (VGACR*) — data at 3B5/3D5, indexed by 3B4/3D4; reset XXh unless noted
:header-rows: 1
:widths: 8 40 8 44

* - Index
  - Register
  - Reset
  - Fields (all RW unless noted)
* - —
  - VGACRI — CRTC Index (port 3B4/3D4)
  - 00h
  - [7:0] index bit[7:0]
* - 00
  - VGACR0 — Horizontal Total
  - XX
  - [7:0] horizontal total bit[7:0] (value −5)
* - 01
  - VGACR1 — Horizontal Display Enable End
  - XX
  - [7:0] horizontal display-enable bit[7:0] (value −1)
* - 02
  - VGACR2 — Horizontal Blank Start
  - XX
  - [7:0] horizontal blank start bit[7:0]
* - 03
  - VGACR3 — Horizontal Blank End
  - XX
  - [7] enable register read-back for indices 10–11; [6:5] horizontal display-enable skew bit[1:0]; [4:0] horizontal blank end bit[4:0]
* - 04
  - VGACR4 — Horizontal Retrace Start
  - XX
  - [7:0] horizontal retrace start bit[7:0]
* - 05
  - VGACR5 — Horizontal Retrace End
  - XX
  - [7] horizontal blank end bit[5]; [6:5] horizontal retrace delay bit[1:0]; [4:0] horizontal retrace end bit[4:0]
* - 06
  - VGACR6 — Vertical Total
  - XX
  - [7:0] vertical total bit[7:0]
* - 07
  - VGACR7 — Overflow
  - XX
  - [7] V retrace start[9]; [6] V display-enable end[9]; [5] V total[9]; [4] line compare[8] (not covered by CR11[7] protection); [3] V blank start[8]; [2] V retrace start[8]; [1] V display-enable end[8]; [0] V total[8]
* - 08
  - VGACR8 — Preset Row Scan
  - XX
  - [6:5] byte panning bit[1:0]; [4:0] preset row scan bit[4:0]; [7] reserved
* - 09
  - VGACR9 — Maximum Scan Line
  - XX
  - [7] enable double scan (200→400 lines); [6] line compare[9]; [5] vertical blank[9]; [4:0] max row scan bit[4:0]
* - 0A
  - VGACRA — Cursor Start
  - XX
  - [5] cursor off; [4:0] cursor start bit[4:0]; [7:6] reserved
* - 0B
  - VGACRB — Cursor End
  - XX
  - [6:5] cursor skew bit[1:0]; [4:0] cursor end bit[4:0]; [7] reserved
* - 0C
  - VGACRC — Starting Address High
  - XX
  - [7:0] starting address bit[15:8]
* - 0D
  - VGACRD — Starting Address Low
  - XX
  - [7:0] starting address bit[7:0]
* - 0E
  - VGACRE — Cursor Location High
  - XX
  - [7:0] cursor location bit[15:8]
* - 0F
  - VGACRF — Cursor Location Low
  - XX
  - [7:0] cursor location bit[7:0]
* - 10
  - VGACR10 — Vertical Retrace Start
  - XX
  - [7:0] vertical retrace start bit[7:0]
* - 11
  - VGACR11 — Vertical Retrace End
  - 00h
  - [7] protect CRT indices 00–07 (except CR07[4]); [6] reserved (R/W only); [5] disable vertical interrupt; [4] clear vertical interrupt flag (0 = clear, 1 = no-op); [3:0] vertical retrace end bit[3:0]
* - 12
  - VGACR12 — Vertical Display Enable End
  - XX
  - [7:0] vertical display-enable end bit[7:0]
* - 13
  - VGACR13 — Offset
  - 00h
  - [7:0] offset bit[7:0]
* - 14
  - VGACR14 — Underline Location
  - XX
  - [6] select double-word mode; [5] select count-by-4 (not implemented); [4:0] underline location bit[4:0]; [7] reserved
* - 15
  - VGACR15 — Vertical Blank Start
  - XX
  - [7:0] vertical blank start bit[7:0]
* - 16
  - VGACR16 — Vertical Blank End
  - XX
  - [7:0] vertical blank end bit[7:0]
* - 17
  - VGACR17 — Mode Control
  - 00h
  - [7] hardware reset (active-low); [6] select byte mode; [5] address wrap enable (not implemented); [3] count-by-2 (not implemented); [2] horizontal retrace select (not implemented); [1] replace MA14 by RA1 (active-low); [0] replace MA13 by RA0 (active-low); [4] reserved
* - 18
  - VGACR18 — Line Compare
  - XX
  - [7:0] line compare bit[7:0]
* - 1E
  - VGACR1E — Graphics Latched Data 0 (R)
  - XX
  - [1] attribute-controller register index toggle bit; [7:2],[0] reserved
* - 1F
  - VGACR1F — Graphics Latched Data 1 (R)
  - 00h
  - [5:0] attribute-controller register index bit[5:0]; [7:6] reserved
* - 22
  - VGACR22 — Graphics Latched Data 2 (R)
  - XX
  - [7:0] graphics latched data bit[7:0]
```

Indices 19–1D, 20–21, and 23–7F are not defined by §34.5 (reserved / used for
the extended set from index 80). `[DS §34.5 p.373–377](#sources)`

### 3.4 Graphics Controller registers (index port 3CE, data 3CF)

```{list-table} Graphics Controller (VGAGR*) — data at 3CF, indexed by 3CE; reset 00h
:header-rows: 1
:widths: 8 34 46 12

* - Index
  - Register
  - Fields (all RW)
  - —
* - —
  - VGAGRI — Graphics Index (3CE)
  - [3:0] index bit[3:0]; [7:4] reserved
  - —
* - 00
  - VGAGR0 — Set/Reset Map
  - [3:0] set/reset map bit[3:0]; [7:4] reserved
  - —
* - 01
  - VGAGR1 — Enable Set/Reset Map
  - [3:0] enable set/reset map bit[3:0]; [7:4] reserved
  - —
* - 02
  - VGAGR2 — Color Compare
  - [3:0] color compare map bit[3:0]; [7:4] reserved
  - —
* - 03
  - VGAGR3 — Data Rotate
  - [4:3] function select bit[1:0]; [2:0] data rotate bit[3:0]; [7:5] reserved
  - —
* - 04
  - VGAGR4 — Read Map Selection
  - [1:0] read map select bit[1:0]; [7:2] reserved
  - —
* - 05
  - VGAGR5 — Mode
  - [6] shift mode for graphics mode 13; [5] shift mode for modes 4/5; [4] odd/even mode; [3] read-mode select (0 normal, 1 color-compare); [1:0] write-mode select bit[1:0]; [7],[2] reserved
  - —
* - 06
  - VGAGR6 — Miscellaneous
  - [3:2] memory address space (00 A000h/128 KB, 01 A000h/64 KB, 10 B000h/32 KB, 11 B800h/32 KB); [1] chain odd/even plane enable; [0] graphics mode (0 text, 1 graphics); [7:4] reserved
  - —
* - 07
  - VGAGR7 — Color Don't Care
  - [3:0] color don't care bit[3:0]; [7:4] reserved
  - —
* - 08
  - VGAGR8 — Bit Mask
  - [7:0] bit mask bit[7:0]
  - —
```

`[DS §34.6 p.377–379](#sources)`

### 3.5 Attribute Controller registers (index+data port 3C0, read 3C1)

```{list-table} Attribute Controller (VGAAR*) — W 3C0 / R 3C1; reset 00h unless noted
:header-rows: 1
:widths: 8 34 50 8

* - Index
  - Register
  - Fields (all RW)
  - —
* - —
  - VGAARI — Attribute Index (3C0 W / 3C1 R)
  - [5] pallet address source (0 = CPU R/W address, 1 = graphics streaming data); [4:0] index bit[4:0]; [7:6] reserved
  - —
* - 00–0F
  - VGAAR0–VGAARF — Pallet Register 00–0F (reset XX)
  - [5:0] pallet data bit[5:0] (16×5-bit registers); [7:6] reserved
  - —
* - 10
  - VGAAR10 — Mode Control
  - [7] internal palette size (0 = 6 bpp, 1 = 4 bpp, cascaded with index 14[1:0]); [6] pixel width (mode 13 only); [5] pixel-panning compatibility; [3] enable blink; [2] line-graphics extension (ASCII C0h–DFh); [1] monochrome display mode; [0] graphics mode (0 text, 1 graphics); [4] reserved
  - —
* - 11
  - VGAAR11 — Border Color (reset XX)
  - [7:0] border color bit[7:0]
  - —
* - 12
  - VGAAR12 — Color Plane Enable (reset XX)
  - [5:4] video status multiplexing bit[1:0]; [3:0] color-plane enable bit[3:0]; [7:6] reserved
  - —
* - 13
  - VGAAR13 — Horizontal Pixel Panning (reset 0X)
  - [3:0] horizontal pixel panning bit[3:0]; [7:4] reserved
  - —
* - 14
  - VGAAR14 — Color Select (reset 0X)
  - [3:0] color selection bit[3:0]; [7:4] reserved
  - —
```

`[DS §34.7 p.377–380](#sources)`

### 3.6 RAMDAC registers (fixed I/O ports 3C6–3C9)

```{list-table} RAMDAC (VGA*) — fixed legacy ports; reset 00h unless noted
:header-rows: 1
:widths: 16 12 12 60

* - Register
  - I/O port
  - Reset
  - Fields
* - VGAPMR — Pixel Mask
  - R/W 3C6
  - FFh
  - [7:0] W pixel mask bit[7:0]
* - VGADSR — RAMDAC Status
  - R 3C7
  - 00h
  - [1:0] R status bit[1:0]; [7:2] reserved
* - VGADRR — Read Mode Address
  - W 3C7
  - 00h
  - [7:0] W read-mode address bit[7:0]
* - VGADWR — Write Mode Address
  - R/W 3C8
  - 00h
  - [7:0] RW write-mode address bit[7:0]
* - VGAPDR — Pallet Data
  - R/W 3C9
  - 00h
  - [7:0] RW pallet data bit[7:0]
```

`[DS §34.8 p.380–381](#sources)`

### 3.7 Aspeed Extended CRT registers (§34.9)

Accessed at CRTC index 80h–D7h (data 3B5/3D5) and, per the datasheet, also at
`MMIO Base + index`. This is the Aspeed-specific set that carries the
frame-buffer base, scan pitch, extended overflow, mode/PLL controls and the
hardware-cursor pointer. `[DS §34.9 p.382](#sources)`

```{list-table} Extended CRT index map (§34.9 overview)
:header-rows: 1
:widths: 20 80

* - Index range
  - Contents (byte 3 : byte 2 : byte 1 : byte 0 of the dword-aligned view)
* - 80–83
  - VGA Scratch Register : Password (index 80)
* - 84–9F
  - VGA Scratch Registers (index 9F also holds live VGA status bits)
* - A0–A3
  - Color Mode : PCI Bus Control (PCI Control #1/#2/#3)
* - A4–A7
  - CRT Threshold : Segment Address : Misc Control
* - A8–AB
  - Power-On Trapping status : RAMDAC Control
* - AC–AF
  - Starting-Address Overflow : Vertical Overflow : Horizontal Overflow
* - B0–B3
  - CRT Counter Read Back : Offset Overflow
* - B4–B7
  - DDC Control : Power Control : (B4/B5 reserved)
* - B8–BB
  - PLL Overflow : RGB CRC Signature Read Back
* - BC–BF
  - 28 MHz PLL : 25 MHz PLL setting
* - C0–C3
  - Hardware Cursor Offset : Video PLL setting
* - C4–C7
  - H/W Cursor Y Position : H/W Cursor X Position
* - C8–CB
  - Cursor Mode/Control : H/W Cursor Pattern Address
* - CC–D7
  - Scratch registers #32–#43 (mapped over the CC–CF reserved / D0–D7 SOC-scratch-read-back slots)
```

```{list-table} Extended CRT registers CR80–CR9F
:header-rows: 1
:widths: 8 34 10 48

* - Index
  - Register (MMIO Base + index)
  - Reset
  - Fields
* - 80
  - VGACR80 — Password
  - 00h
  - [7:0] RW password bit[7:0]; unlock password = A8h
* - 81–9E
  - VGACR81–9E — Scratch Register #1–#30
  - XX
  - [7:0] RW scratch (VGA BIOS / display driver use only)
* - 9F
  - VGACR9F — Scratch Register #31 / status
  - XX
  - [7:6] R PCI power state D0–D3 (= PCIS44[1:0]); [5] R pallet-address source (= VGAARI[5]); [4] R pixel-mask status (= OR of VGAPMR[7:0]); [3] R VGA reset status (= VGACR17[7]); [2] R screen-display status (= VGASR1[5]); [1] R VGA-controller reset status (= AND of VGASR0[1:0]); [0] R VGA enable (= VGAER[0])
```

```{list-table} Extended CRT registers CRA0–CRA5 (PCI / color-mode / misc)
:header-rows: 1
:widths: 8 34 10 48

* - Index
  - Register
  - Reset
  - Fields (all RW)
* - A0
  - VGACRA0 — PCI Control #1
  - 00h
  - [6] enable video-memory access by 32-bit chain-4 (graphics mode); [5] enable linear extended memory (>256 KB); [4] enable extended segmented memory (>256 KB); [3] enable burst memory read; [2] enable burst memory write; [1] enable read-ahead cache; [0] enable post-write buffer; [7] reserved
* - A1
  - VGACRA1 — PCI Control #2
  - 00h
  - [3] disable re-locatable I/O-mapped VGA I/O decoding; [2] disable re-locatable memory-mapped VGA I/O decoding; [1] disable standard VGA I/O decoding; [0] disable standard VGA memory (A000h–BFFFh) decoding; [7:4] reserved
* - A2
  - VGACRA2 — PCI Control #3
  - 00h
  - [7] enable big-endian mode; [6] enable 16-bit big-endian (0 = 32-bit, 1 = 16-bit); [4] PCI retry for I/O while post-write buffer not empty; [3] PCI retry for memory write; [2] PCI retry for memory read; [5],[1:0] reserved
* - A3
  - VGACRA3 — Enhanced Color Mode
  - 00h
  - [7] enable DVO interface; [6] enable dual-edge DVO; [3] enable 32-bpp true color (ARGB8888); [2] enable 16-bpp high color (RGB565); [1] enable 15-bpp high color (RGB555); [0] enable enhanced 256-color mode; [5:4] reserved
* - A4
  - VGACRA4 — Misc. Control
  - 00h
  - [7] software reset 2D engine; [6] trigger VGA interrupt to BMC; [5] enable Sub-System/Sub-Vendor ID write; [4] enable VGA BIOS flash write; [3:2] 2D-engine clock source (00 MCLK, 01 ~MCLK, 10/11 reserved); [1] enable 2D-engine clock throttling (idle → 1/16); [0] enable 2D-engine clock (0 stop, 1 enable)
* - A5
  - VGACRA5 — Segmented Memory Address Overflow
  - 00h
  - [5:4] segmented memory read address bit[9:8]; [1:0] segmented memory write address bit[9:8]; [7:6],[3:2] reserved
```

```{list-table} Extended CRT registers CRA6–CRAB (threshold / RAMDAC / power-on trapping)
:header-rows: 1
:widths: 8 32 10 50

* - Index
  - Register
  - Reset
  - Fields
* - A6
  - VGACRA6 — CRT Request Threshold Low
  - 00h
  - [5:0] RW CRT request threshold low bit[5:0]; [7:6] reserved
* - A7
  - VGACRA7 — CRT Request Threshold High
  - 00h
  - [5:0] RW CRT request threshold high bit[5:0]; [7:6] reserved
* - A8
  - VGACRA8 — RAMDAC Control
  - 00h
  - [6] enable RAMDAC test mode (monitor sense); [4] disable RAMDAC mask function; [2] protect palette/gamma RAM from writes; [1] enable 24-bit gamma-correction RAM; [7],[5],[3],[0] reserved. All RW
* - A9
  - VGACRA9 — RAMDAC Test Pattern
  - 00h
  - [7:0] RW RAMDAC test pattern bit[7:0]
* - AA
  - VGACRAA — Power-On Trapping Status #1 (R)
  - X
  - [7] CPU clock frequency select bit[0]; [6] bypass clock mode (1 = test clock); [5:4] ARM boot select (00 ROMCS0#/NOR, 01 ROMCS1#/NAND, 10 ROMCS2#/SPI, 11 disable ARM); [3] enable VGA BIOS ROM; [2] PCI interface (0 = PCI slave, 1 = PCI host); [1:0] total VGA memory size (00 8 MB, 01 16 MB, 10 32 MB, 11 64 MB)
* - AB
  - VGACRAB — Power-On Trapping Status #2 (R)
  - 00h
  - [7:6] Chip ID (11 AST2100, 10 AST2050/AST1100); [5] bypass all PLL modules; [4] PCI class-code (0 video device, 1 VGA device); [3] PCI VGA config prefetch status; [2] PCI AD bus order swap (0 disable, 1 enable); [1:0] CPU clock select bit[2:1] (with CRAA[7]: 000 266, 001 233, 010 200, 011 166, 100 133, 101 100, 110 300, 111 24 MHz H-PLL bypass)
```

```{list-table} Extended CRT registers CRAC–CRB3 (extended overflow / counter read-back); reset 00h
:header-rows: 1
:widths: 8 34 58

* - Index
  - Register
  - Fields (all RW)
* - AC
  - VGACRAC — Extended Horizontal Overflow #1
  - [6] H retrace start[8]; [4] H blank start[8]; [2] H display-enable end[8]; [0] H total[8]; [7],[5],[3],[1] reserved
* - AD
  - VGACRAD — Extended Horizontal Overflow #2
  - [6:4] H retrace skew bit[2:0]; [2] H retrace end[5]; [0] H blank end[6]; [7],[3],[1] reserved
* - AE
  - VGACRAE — Extended Vertical Overflow
  - [7] disable line compare; [6:5] V retrace end[5:4]; [4] V blank end[8]; [3] V retrace start[10]; [2] V blank start[10]; [1] V display-enable end[10]; [0] V total[10]
* - AF
  - VGACRAF — Extended CRT Starting Address
  - [7:0] CRT starting address bit[23:16]
* - B0
  - VGACRB0 — Extended CRT Offset
  - [5:0] offset bit[13:8]; [7:6] reserved
* - B1
  - VGACRB1 — Horizontal Counter Read Back
  - [7:0] horizontal counter read-back bit[7:0] (R)
* - B2
  - VGACRB2 — Vertical Counter Read Back
  - [7:0] vertical counter read-back bit[7:0] (R)
* - B3
  - VGACRB3 — CRT Counter Read Back Overflow
  - [4] H counter read-back[8]; [2:0] V counter read-back[10:8]; [7:5],[3] reserved
```

Indices B4 and B5 are reserved (no register defined). `[DS §34.9 p.387](#sources)`

```{list-table} Extended CRT registers CRB6–CRBA (power / DDC / CRC read-back); reset noted
:header-rows: 1
:widths: 8 34 10 48

* - Index
  - Register
  - Reset
  - Fields
* - B6
  - VGACRB6 — Power Management
  - 00h
  - [4] enable bypass mode for video PLL; [3] power-down video PLL; [2] power-on RAMDAC (0 down, 1 on); [1] enable VSYNC off; [0] enable HSYNC off; [7:5] reserved. All RW
* - B7
  - VGACRB7 — DDC Control
  - 00h
  - [7] R CRC-signature-generation status (0 in-progress/never, 1 valid); [6] trig CRC-signature generation (≥1 frame; poll [7] before reading RGB CRC); [5] DDC data input; [4] DDC clock input; [3] DDC data output; [2] enable DDC data output buffer; [1] DDC clock output; [0] enable DDC clock output buffer
* - B8
  - VGACRB8 — Blue CRC Signature Read Back
  - FCh
  - [7:0] RW blue CRC signature read-back bit[7:0]
* - B9
  - VGACRB9 — Green CRC Signature Read Back
  - FCh
  - [7:0] RW green CRC signature read-back bit[7:0]
* - BA
  - VGACRBA — Red CRC Signature Read Back
  - FCh
  - [7:0] RW red CRC signature read-back bit[7:0]
```

```{list-table} Extended CRT registers CRBB–CRC1 (D-PLL / video-PLL settings)
:header-rows: 1
:widths: 8 34 10 48

* - Index
  - Register
  - Reset
  - Fields (all RW)
* - BB
  - VGACRBB — PLL Overflow
  - 1Fh
  - [5:4] video PLL extended post-divider (00 1/1, 01 1/2, 10 1/2, 11 1/4); [3:2] 28.322 MHz PLL extended post-divider bit[1:0]; [1:0] 25.175 MHz PLL extended post-divider bit[1:0]; [7:6] reserved
* - BC
  - VGACRBC — 25.175 MHz PLL Setting
  - E9h
  - [7:0] video PLL numerator bit[7:0]
* - BD
  - VGACRBD — 25.175 MHz PLL Setting
  - 65h
  - [6:5] video PLL post-divider bit[1:0] (00 1/1, 01 1/2, 10 1/2, 11 1/4; effective when 25.175 MHz selected by legacy register); [4:0] video PLL de-numerator bit[4:0]; [7] reserved
* - BE
  - VGACRBE — 28.322 MHz PLL Setting
  - 95h
  - [7:0] video PLL numerator bit[7:0]
* - BF
  - VGACRBF — 28.322 MHz PLL Setting
  - 62h
  - [6:5] video PLL post-divider bit[1:0] (effective when 28.322 MHz selected by legacy register); [4:0] video PLL de-numerator bit[4:0]; [7] reserved
* - C0
  - VGACRC0 — Video PLL Setting
  - 4Eh
  - [7:0] video PLL numerator bit[7:0]
* - C1
  - VGACRC1 — Video PLL Setting
  - 61h
  - [6:5] video PLL post-divider bit[1:0]; [4:0] video PLL de-numerator bit[4:0]; [7] reserved
```

```{list-table} Extended CRT registers CRC2–CRD7 (hardware cursor + scratch); reset 00h unless noted
:header-rows: 1
:widths: 8 34 58

* - Index
  - Register
  - Fields (all RW)
* - C2
  - VGACRC2 — H/W Cursor X Position Offset
  - [5:0] cursor X position offset bit[5:0]; [7:6] reserved
* - C3
  - VGACRC3 — H/W Cursor Y Position Offset
  - [5:0] cursor Y position offset bit[5:0]; [7:6] reserved
* - C4
  - VGACRC4 — H/W Cursor X Position #1
  - [7:0] cursor X position bit[7:0]
* - C5
  - VGACRC5 — H/W Cursor X Position #2
  - [3:0] cursor X position bit[11:8]; [7:4] reserved
* - C6
  - VGACRC6 — H/W Cursor Y Position #1
  - [7:0] cursor Y position bit[7:0]
* - C7
  - VGACRC7 — H/W Cursor Y Position #2
  - [2:0] cursor Y position bit[10:8]; [7:3] reserved
* - C8
  - VGACRC8 — H/W Cursor Pattern Address #1
  - [7:0] cursor pattern memory address bit[11:4] (16-byte aligned; bit[3:0]=0)
* - C9
  - VGACRC9 — H/W Cursor Pattern Address #2
  - [7:0] cursor pattern memory address bit[19:12]
* - CA
  - VGACRCA — H/W Cursor Pattern Address #3
  - [7:0] cursor pattern memory address bit[27:20]
* - CB
  - VGACRCB — H/W Cursor Control
  - [1] enable H/W cursor display; [0] cursor type (0 = 2-bpp, 1 = 16-bpp ARGB1555); [7:2] reserved
* - CC–D7
  - VGACRCC–D7 — Scratch Register #32–#43 (reset XX)
  - [7:0] scratch register bit[7:0] (also serving the CC–CF reserved and D0–D7 SOC-scratch read-back slots of the overview map)
```

`[DS §34.9 p.383–392](#sources)`

### 3.8 Mainline cross-check

The legacy VGA + Aspeed extended-CRT index space here is exactly what the
mainline **[`drm/ast`](https://github.com/torvalds/linux/tree/master/drivers/gpu/drm/ast)** PCI-VGA driver programs — that driver historically
enumerates **AST1100** among its supported chips, matching the CRAB[7:6]=10
"AST2050/AST1100" chip ID above. It drives the same index registers: password
CR80/unlock, CRAA/CRAB power-on-trapping straps for VRAM-size and chip
detection, CRA3 color-mode, CRAC–CRAF/CRB0 extended H/V overflow + CRT start
address + offset, CRB6 power management, CRBB–CRC1 D-PLL, and CRC2–CRCB for the
64×64 hardware cursor. `[astdrv]`

Note the distinction: **[`drm/ast`](https://github.com/torvalds/linux/tree/master/drivers/gpu/drm/ast)** is the host-side driver for this legacy PCI
VGA device, whereas **[`drm/aspeed`](https://github.com/torvalds/linux/tree/master/drivers/gpu/drm/aspeed)** is a *different* block — the SoC's separate
"GFX/CRT" display controller (base `0x1E6E6000`) that does not exist as a PCI
VGA device. A BMC-side OpenBMC/u-bmc port that wants this VGA controller would
drive these same index registers via the MMIO alias (`Base + index`) rather than
through PCI I/O ports. `[aspeeddrm]`

---

## See also

**Related pages**

- {doc}`/hardware/registers/pcie-vga-usb-bridges` — the PCI/VGA/USB endpoint summary that points to these full register maps
- {doc}`/hardware/registers/engines-blocks` — the 2D graphics engine and hardware cursor that share this VGA/Video path
- {doc}`/hardware/registers/scu-clock-reset` — the DCLK/ECLK/USB2.0 clock enables and SCU04 resets these blocks need
- {doc}`/hardware/registers/index` — register reference landing

**External references**

- [Linux USB gadget API](https://docs.kernel.org/driver-api/usb/gadget.html) — the gadget/virtual-hub model behind the USB block (`aspeed-vhub`)
- [Linux V4L2 core](https://docs.kernel.org/driver-api/media/v4l2-core.html) — the video-capture framework the Video Engine driver targets
- [Linux DRM/KMS](https://docs.kernel.org/gpu/drm-kms.html) — the display/mode-setting framework for the VGA controller
- [aspeed video-engine device-tree binding](https://github.com/torvalds/linux/blob/master/Documentation/devicetree/bindings/media/aspeed,video-engine.yaml) — the upstream binding for the Aspeed Video Engine

## Sources

- **AST2050/AST1100 A3 Datasheet, V1.05** (25 May 2010), in-repo PDF
  `datasheets/aspeed/AST2050_AST1100_A3_Datasheet_V1.05.pdf`. Chapters
  transcribed here: **§15 USB 2.0 Virtual Hub Controller** (p.154–178; register
  file §15.3 p.155–173), **§20 Video Engine** (p.232–255; register file §20.3
  p.234–255), **§34 VGA Display Controller** (p.368–392; standard sets §34.3–34.8
  p.369–381, Aspeed extended CRT §34.9 p.382–392). Doc (printed) page = PDF page.
- Mainline Linux drivers used as cross-checks:
  - [`aspeed-vhub` register header ([`vhub.h`](https://github.com/torvalds/linux/blob/master/drivers/usb/gadget/udc/aspeed-vhub/vhub.h))][vhubh] — USB gadget virtual-hub
    register offsets `HUB00…HUB3C` and per-device / per-endpoint windows.
  - [`aspeed-video.c` V4L2 driver][aspeedvideo] — Video Engine `VE_*` register
    offsets matching `VR000…VR308` and the `0x1A03_8AA8` protection key.
  - [`drm/ast` PCI-VGA driver][astdrv] — the legacy VGA + extended-CRT index
    registers (CR80–CRD7), including AST1100/AST2050 chip support.
  - [`drm/aspeed` SoC GFX/CRT driver][aspeeddrm] — the *separate* SoC display
    block at `0x1E6E6000` (contrast, not the VGA controller documented here).

[vhubh]: https://github.com/torvalds/linux/blob/master/drivers/usb/gadget/udc/aspeed-vhub/vhub.h
[aspeedvideo]: https://github.com/torvalds/linux/blob/master/drivers/media/platform/aspeed/aspeed-video.c
[astdrv]: https://github.com/torvalds/linux/tree/master/drivers/gpu/drm/ast
[aspeeddrm]: https://github.com/torvalds/linux/tree/master/drivers/gpu/drm/aspeed
