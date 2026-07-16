# AST2050 engines & bridges: HACE, MIC, MDMA, A2P, 2D graphics, HW cursor

Complete, register-by-register reference for six AST2050 / AST1100 (G3) on-chip
blocks that had no register map in the open-firmware docs. Every register in each
block is documented — including reserved offsets and blocks that neither target
board (ASUS KGPE-D16, Dell C410X) actually programs — because the project
requires a complete map.

All content is derived from the in-repo ASPEED AST2050/AST1100 A3 datasheet
V1.05 [DS](#sources), cross-checked against Raptor Engineering's U-Boot headers
[ast2050.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/ast2050.h) / [hwreg.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h). Citations are inline as [DS §N p.P](#sources) (datasheet
chapter / printed page, which equals the PDF page number), [`ast2050.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/ast2050.h),
[`hwreg.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h); full link definitions are collected in the Sources section at the
end.

Conventions used in the register tables below:

- **Access**: `RW` read/write, `R` read-only, `W1C` write-1-to-clear (the
  datasheet spells these "cleared by writing 1"), `—` reserved / not writable.
- **Reset (Init)**: `X` = undefined at reset (datasheet "Init = X"); `0` = clears
  to zero; a hex literal is the exact reset value.
- Reserved bit ranges are listed explicitly and read as 0 unless noted.

## Address map and interrupt assignments

The six blocks sit at these bases in the ch. 9 address map, and four of them own
a dedicated interrupt line in the ch. 10 Interrupt Source Table
[DS §10 p.99](#sources):

:::{list-table} Block bases and VIC interrupt lines
:header-rows: 1
:widths: 22 20 12 46

* - Block
  - Base address
  - VIC INT#
  - Notes
* - Memory Integrity Check (MIC)
  - `0x1E64_0000`
  - 1
  - `MIC interrupt`, sensitive high-level [DS §13 p.116](#sources) [DS §10 p.99](#sources)
* - Hash & Crypto Engine (HACE)
  - `0x1E6E_3000`
  - 4
  - `Crypto interrupt`, sensitive high-level [DS §19 p.221](#sources) [DS §10 p.99](#sources)
* - MDMA Engine
  - `0x1E74_0000`
  - 6
  - `MDMA interrupt`, sensitive high-level [DS §22 p.257](#sources) [DS §10 p.99](#sources)
* - AHB-to-P-Bus / AHB→PCI (A2P) bridge
  - `0x1E72_0000`
  - —
  - No own interrupt; window bridge only [DS §21 p.256](#sources)
* - 2D Graphics Engine (GER)
  - `PCIS14 (BAR1) + 0x8000`
  - —
  - No dedicated interrupt line; completion is polled via `GER4C` (§35 assigns
    no VIC source, and there is no 2D entry in Table 36) [DS §35 p.393](#sources)
* - Graphics Hardware Cursor
  - `0x1E6E_2050` / `0x1E70_0008`
  - 21 (SCU)
  - No dedicated line; the cursor-change IRQ enable/status is in `SCU18`, so it is
    delivered as the SCU interrupt (VIC #21) [DS §37 p.401](#sources)
:::

None of these six blocks is defined in the Raptor U-Boot register headers: the
SDRAM, SCU, timer, VIC, WDT, UART, MAC, GPIO and AHB controllers appear in
[hwreg.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h) but the DMA / crypto / MIC sections are left as empty stub comments
[hwreg.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h). The only firmware-side evidence that these engines exist and were
exercised is the (disabled) SLT self-test command set in the KGPE-D16 U-Boot
config, which lists `CFG_CMD_HACTEST` and `CFG_CMD_MICTEST` [ast2050.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/ast2050.h).

---

## Hash & Crypto Engine (HACE) — `0x1E6E_3000`

**Used on target boards?** No. Neither the KGPE-D16 open-firmware stack
(OpenBMC / u-bmc) nor the C410X path programs HACE; the block is present on the
SoC but idle. The only reference in the KGPE-D16 firmware is the disabled SLT
`CFG_CMD_HACTEST` self-test [ast2050.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/ast2050.h). No mainline Linux driver targets the
G3 HACE — the mainline [`drivers/crypto/aspeed/`](https://github.com/torvalds/linux/tree/master/drivers/crypto/aspeed) (aspeed-hace) driver supports
only the later AST2500/AST2600 HACE, which has a different, scatter-gather
register interface.

HACE accelerates hash digest, encryption and decryption. It splits into an
independent **Hash Engine** and **Crypto Engine** that can also run cascaded
(hash-first or crypto-first). It fetches data directly over the memory bus (not
AHB) and is fired by writing its command register [DS §19 p.221](#sources). Ciphers:
AES-128/192/256 in ECB/CBC/CFB/OFB/CTR and RC4; digests MD5 / SHA-1 / SHA-224 /
SHA-256 with optional HMAC, over lengths up to 256 MB [DS §19 p.221](#sources).

HACE implements 11 32-bit registers. Offsets `0x14` and `0x18` are **not
assigned** (reserved gap between HACE10 and HACE1C) [DS §19 p.222](#sources).

:::{list-table} HACE register summary
:header-rows: 1
:widths: 8 34 10 10 38

* - Offset
  - Register
  - Access
  - Init
  - Description
* - `00h`
  - HACE00 — Crypto Data Source base
  - RW
  - X
  - Base address of crypto source data (8-byte aligned) [DS §19 p.222](#sources)
* - `04h`
  - HACE04 — Crypto Data Destination base
  - RW
  - X
  - Base address of crypto destination data (8-byte aligned) [DS §19 p.222](#sources)
* - `08h`
  - HACE08 — Crypto Context Buffer base
  - RW
  - X
  - Base address of crypto context buffer (8-byte aligned) [DS §19 p.223](#sources)
* - `0Ch`
  - HACE0C — Crypto Data Length
  - RW
  - X
  - Byte length to encrypt/decrypt [DS §19 p.223](#sources)
* - `10h`
  - HACE10 — Crypto Engine Command
  - RW
  - X
  - Fires and configures the crypto engine [DS §19 p.223](#sources)
* - `14h`
  - *(reserved gap)*
  - —
  - —
  - Not assigned [DS §19 p.222](#sources)
* - `18h`
  - *(reserved gap)*
  - —
  - —
  - Not assigned [DS §19 p.222](#sources)
* - `1Ch`
  - HACE1C — Engine Status
  - RW/R
  - 0
  - Interrupt flags and busy/idle status for both engines [DS §19 p.224](#sources)
* - `20h`
  - HACE20 — Hash Data Source base
  - RW
  - X
  - Base address of hash source data (8-byte aligned) [DS §19 p.225](#sources)
* - `24h`
  - HACE24 — Hash Digest Write Buffer base
  - RW
  - X
  - Base address of hash digest output (8-byte aligned) [DS §19 p.225](#sources)
* - `28h`
  - HACE28 — HMAC Key Buffer base
  - RW
  - X
  - Base address of HMAC key buffer (64-byte aligned) [DS §19 p.225](#sources)
* - `2Ch`
  - HACE2C — Hash Data Length
  - RW
  - X
  - Byte length to hash [DS §19 p.225](#sources)
* - `30h`
  - HACE30 — Hash Engine Command
  - RW
  - X
  - Fires and configures the hash engine [DS §19 p.226](#sources)
:::

### HACE00/04/08 — Crypto source / destination / context base

:::{list-table} HACE00, HACE04, HACE08 (identical layout)
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:28
  - —
  - Reserved (0)
* - 27:3
  - RW
  - Base address [27:3] of the crypto data source (HACE00), destination (HACE04) or context buffer (HACE08). Must be 8-byte aligned. [DS §19 p.222](#sources) [DS §19 p.223](#sources)
* - 2:0
  - —
  - Reserved (0) — implied by the 8-byte alignment
:::

### HACE0C — Crypto Data Length

:::{list-table} HACE0C — Crypto Data Length Register
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:28
  - —
  - Reserved (0)
* - 27:0
  - RW
  - Crypto data length in bytes (`0` invalid, `1`=1 byte, …). RC4 length is byte-aligned; AES length is 16-byte-aligned. Max `256MB-1`; min 1 byte (RC4) or 16 bytes (AES). In cascaded mode HACE0C[27:0] MUST equal HACE2C[27:0]. [DS §19 p.223](#sources)
:::

### HACE10 — Crypto Engine Command

:::{list-table} HACE10 — Crypto Engine Command Register
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:13
  - —
  - Reserved (0)
* - 12
  - RW
  - Enable crypto interrupt. `0` disable; `1` interrupt when the crypto command finishes. [DS §19 p.223](#sources)
* - 11
  - RW
  - Disable crypto engine read-in & write-out data. `0` enable data movement; `1` disable. [DS §19 p.223](#sources)
* - 10
  - RW
  - Disable loading context from the context buffer before running. `0` load context; `1` skip. [DS §19 p.223](#sources)
* - 9
  - RW
  - Disable saving context into the context buffer on completion. `0` save; `1` skip. [DS §19 p.223](#sources)
* - 8
  - RW
  - Crypto algorithm select. `0` AES; `1` RC4. [DS §19 p.223](#sources)
* - 7
  - RW
  - Crypto mode. `0` decryption (ciphertext→plaintext); `1` encryption (plaintext→ciphertext). [DS §19 p.223](#sources)
* - 6:4
  - RW
  - AES operation mode: `000` ECB (no IV); `001` CBC; `010` CFB; `011` OFB; `100` CTR; `101`/`110`/`111` invalid. IV comes from the context buffer. Ignored for RC4. [DS §19 p.224](#sources)
* - 3:2
  - RW
  - AES key length: `00` 128-bit; `01` 192-bit; `10` 256-bit; `11` invalid. Ignored for RC4. [DS §19 p.224](#sources)
* - 1:0
  - RW
  - Crypto engine operation mode: `00`/`01` independent; `10` cascaded (crypto first, hash second); `11` cascaded (hash first, crypto second). Must match HACE30[1:0] or the engine can dead-lock. [DS §19 p.224](#sources)
:::

### HACE1C — Engine Status

:::{list-table} HACE1C — Engine Status Register (Init = 0)
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:13
  - —
  - Reserved (0)
* - 12
  - W1C
  - Crypto interrupt flag. `0` none; `1` pending. Set when a crypto command finishes (if enabled); write `1` to clear. [DS §19 p.224](#sources)
* - 11:10
  - —
  - Reserved (0)
* - 9
  - W1C
  - Hash interrupt flag. `0` none; `1` pending. Set when a hash command finishes (if enabled); write `1` to clear. [DS §19 p.224](#sources)
* - 8:2
  - —
  - Reserved (0)
* - 1
  - R
  - Crypto engine status. `0` idle; `1` busy. [DS §19 p.224](#sources)
* - 0
  - R
  - Hash engine status. `0` idle; `1` busy. [DS §19 p.224](#sources)
:::

### HACE20/24 — Hash data source / digest write buffer base

:::{list-table} HACE20, HACE24
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:28
  - —
  - Reserved (0)
* - 27:3
  - RW
  - Base address [27:3] of the hash source data (HACE20) or the hash digest write buffer (HACE24). Must be 8-byte aligned. Digest/buffer sizes: MD5 16/16 B, SHA-1 20/20 B, SHA-224 28/32 B, SHA-256 32/32 B. [DS §19 p.225](#sources)
* - 2:0
  - —
  - Reserved (0)
:::

### HACE28 — HMAC Key Buffer base

:::{list-table} HACE28 — HMAC Key Buffer base
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:28
  - —
  - Reserved (0)
* - 27:6
  - RW
  - Base address [27:6] of the HMAC key buffer; must be 64-byte aligned. Holds the result of the "calculate HMAC key" command (HACE30[8]=1). [DS §19 p.225](#sources)
* - 5:0
  - —
  - Reserved (0)
:::

### HACE2C — Hash Data Length

:::{list-table} HACE2C — Hash Data Length Register
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:28
  - —
  - Reserved (0)
* - 27:0
  - RW
  - Hash data length in bytes (`0`=0, `1`=1 byte, …). When HACE30[8:7]=2 (accumulative) the length is 64-byte aligned, min 64 B; otherwise byte-aligned, min 0 B. Max `256MB-1`. In cascaded mode HACE2C[27:0] MUST equal HACE0C[27:0]. [DS §19 p.225](#sources)
:::

### HACE30 — Hash Engine Command

:::{list-table} HACE30 — Hash Engine Command Register
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:10
  - —
  - Reserved (0)
* - 9
  - RW
  - Enable hash interrupt. `0` disable; `1` interrupt when hash command finishes. [DS §19 p.226](#sources)
* - 8:7
  - RW
  - HMAC command mode: `00` digest without HMAC; `01` digest with HMAC; `10` digest in accumulative mode; `11` calculate HMAC key (hash engine must be in independent mode). [DS §19 p.226](#sources)
* - 6:4
  - RW
  - Hash algorithm: `000` MD5; `010` SHA-1; `100` SHA-224; `101` SHA-256; `001`/`011`/`110`/`111` invalid. [DS §19 p.226](#sources)
* - 3:2
  - RW
  - Byte-swap control: `01` little-endian (all MD5 commands); `10` big-endian (SHA-1/224/256 commands); `00`/`11` invalid. [DS §19 p.226](#sources)
* - 1:0
  - RW
  - Hash engine operation mode: `00`/`01` independent; `10` cascaded (crypto first, hash second); `11` cascaded (hash first, crypto second). Must match HACE10[1:0] or the engine can dead-lock. [DS §19 p.226](#sources)
:::

### Crypto context buffer layout

The context buffer pointed to by HACE08 has an algorithm-specific layout
[DS §19 p.227](#sources):

:::{list-table} Crypto context buffer formats
:header-rows: 1
:widths: 20 14 66

* - Algorithm
  - Size
  - Byte layout
* - RC4
  - 272 B
  - `000–007` reserved; `008` index I (init 1); `009` index J (init 0); `00A–00F` reserved; `010–10F` RC4 key byte 0–255 [DS §19 p.227](#sources)
* - AES-128
  - 192 B
  - `000–00F` IV byte 0–15 (not needed in ECB); `010–0BF` SW-expanded key byte 0–175 [DS §19 p.227](#sources)
* - AES-192
  - 224 B
  - `000–00F` IV byte 0–15; `010–0DF` SW-expanded key byte 0–207 [DS §19 p.227](#sources)
* - AES-256
  - 256 B
  - `000–00F` IV byte 0–15; `010–0FF` SW-expanded key byte 0–239 [DS §19 p.227](#sources)
:::

---

## Memory Integrity Check (MIC) — `0x1E64_0000`

**Used on target boards?** No. MIC is a background DRAM-scrubbing / checksum
engine; neither board's open firmware enables it (both rely on the standard DDR2
controller init). It is present on the SoC and appears only in the disabled
KGPE-D16 SLT `CFG_CMD_MICTEST` self-test [ast2050.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/ast2050.h). No mainline driver
exists for it.

MICE (Memory Integrity Check Engine) connects directly to the AHB bus and reads
SDRAM over the M-bus, scanning memory in 4 KB units and maintaining a Fletcher's
checksum per unit; it raises VIC INT#1 on a checksum mismatch [DS §13 p.116](#sources).
It implements 8 32-bit registers backed by two software-supplied DRAM buffers: a
**control buffer** (2 page-control bits per 4 KB page) and a **checksum buffer**
(4 checksum bytes per page) [DS §13 p.120](#sources).

:::{list-table} MIC register summary
:header-rows: 1
:widths: 8 36 10 12 34

* - Offset
  - Register
  - Access
  - Init
  - Description
* - `00h`
  - MIC00 — Control Buffer base
  - RW
  - X
  - Base address of page-control buffer (8-byte aligned) [DS §13 p.116](#sources)
* - `04h`
  - MIC04 — Checksum Buffer base
  - RW
  - X
  - Base address of checksum buffer (8-byte aligned) [DS §13 p.116](#sources)
* - `08h`
  - MIC08 — Rate Control
  - RW
  - X
  - Scan rate; higher value = slower [DS §13 p.117](#sources)
* - `0Ch`
  - MIC0C — Control
  - RW
  - `0xxx_xxxx`
  - Enable + page count to scan [DS §13 p.117](#sources)
* - `10h`
  - MIC10 — Stop-Page
  - RW
  - X
  - Stop/skip page + checksum write-back [DS §13 p.117](#sources)
* - `14h`
  - MIC14 — Error Status & Interrupt Mask
  - RW/R
  - 0
  - Error flags, IRQ mask, current page [DS §13 p.118](#sources)
* - `18h`
  - MIC18 — First Page Error Status
  - RW/R
  - `0000_xxxx`
  - First-page error flag + page number [DS §13 p.118](#sources)
* - `1Ch`
  - MIC1C — Secondary Page Error Status
  - RW/R
  - `0000_xxxx`
  - Secondary-page error flag + page number [DS §13 p.118](#sources)
:::

### MIC00 / MIC04 — Control / Checksum buffer base

:::{list-table} MIC00, MIC04 (identical layout)
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:28
  - —
  - Reserved (0)
* - 27:3
  - RW
  - Base address [27:3] of the control buffer (MIC00) / checksum buffer (MIC04). Must be 8-byte aligned, so bits [2:0] are always 0. [DS §13 p.116](#sources)
* - 2:0
  - —
  - Reserved (0)
:::

### MIC08 — Rate Control

:::{list-table} MIC08 — Rate Control Register
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:16
  - —
  - Reserved (0)
* - 15:0
  - RW
  - Rate control setting. A higher value slows the scan and reduces the extra DRAM bandwidth used; the datasheet gives only this qualitative relation, not an exact formula. [DS §13 p.117](#sources)
:::

### MIC0C — Control

:::{list-table} MIC0C — Control Register (Init = 0xxx_xxxx)
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:29
  - —
  - Reserved (0)
* - 28
  - RW
  - Enable MICE. `0` reset (default); `1` enable. Control and checksum buffers must be prepared before enabling. [DS §13 p.117](#sources)
* - 27:12
  - RW
  - Number of pages to check (16-bit → up to 64K pages = 256 MB, since each page is 4 KB). Scanning always starts at page #0 (address `0x0000_0000`). The value must be 16-aligned (#15, #31, #47, …). [DS §13 p.117](#sources)
* - 11:0
  - —
  - Reserved (0)
:::

### MIC10 — Stop-Page

:::{list-table} MIC10 — Stop-Page Register
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:16
  - RW
  - Write-back value for the checksum buffer. If non-zero, MICE writes `{[31:16], 0x0000}` into the checksum buffer of page #N where N = MIC10[15:0]. [DS §13 p.117](#sources)
* - 15:0
  - RW
  - Page number of the stop-page. Writing this register makes MICE stop and skip the integrity check at that page when the current process page equals it. Must not exceed MIC0C[27:12]. [DS §13 p.117](#sources)
:::

### MIC14 — Error Status & Interrupt Mask

:::{list-table} MIC14 — Error Status and Interrupt Mask Register (Init = 0)
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31
  - —
  - Reserved (0)
* - 30
  - R
  - Lost-page error flag. `0` not detected; `1` detected. [DS §13 p.118](#sources)
* - 29
  - R
  - Secondary-page error flag (mirrors MIC1C[29]). `0`/`1` = not/​detected. [DS §13 p.118](#sources)
* - 28
  - R
  - First-page error flag (mirrors MIC18[28]). `0`/`1` = not/​detected. [DS §13 p.118](#sources)
* - 27:18
  - —
  - Reserved (0)
* - 17:16
  - RW
  - Interrupt mask (`1` = enable) [DS §13 p.118](#sources):
    - bit 17 enables the CPU interrupt on the secondary-page error flag
    - bit 16 enables it on the first-page error flag
* - 15:0
  - R
  - Current process page number of the engine. [DS §13 p.118](#sources)
:::

### MIC18 — First Page Error Status

:::{list-table} MIC18 — First Page Error Status Register (Init = 0000_xxxx)
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31
  - —
  - Reserved (0)
* - 30
  - R
  - Lost-page error flag (mirrors MIC14[30]). [DS §13 p.118](#sources)
* - 29
  - —
  - Reserved (0)
* - 28
  - W1C
  - First-page error flag. `0` not detected; `1` detected. Cleared by writing 1. [DS §13 p.118](#sources)
* - 27:16
  - —
  - Reserved (0)
* - 15:0
  - R
  - Page number of the first-page error. [DS §13 p.118](#sources)
:::

### MIC1C — Secondary Page Error Status

:::{list-table} MIC1C — Secondary Page Error Status Register (Init = 0000_xxxx)
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31
  - —
  - Reserved (0)
* - 30
  - R
  - Lost-page error flag (mirrors MIC14[30]). [DS §13 p.118](#sources)
* - 29
  - W1C
  - Secondary-page error flag. `0` not detected; `1` detected. Cleared by writing 1. [DS §13 p.118](#sources)
* - 28:16
  - —
  - Reserved (0)
* - 15:0
  - R
  - Page number of the secondary-page error. [DS §13 p.119](#sources)
:::

### Page control bits & buffer formats

Each 4 KB page carries 2 control bits in the control buffer that decide MICE's
behaviour on that page [DS §13 p.119](#sources):

:::{list-table} MIC page-control-bit modes
:header-rows: 1
:widths: 22 20 24 34

* - Bits
  - Read DRAM
  - Update checksum
  - Update error status
* - `00` Skip
  - No
  - No
  - No
* - `01` ECC mode
  - Yes
  - No
  - No
* - `10` Debug mode
  - Yes
  - Always
  - No
* - `11` MIC mode
  - Yes
  - When checksum buffer is at its initial value
  - Yes
:::

Buffer layout (M = MIC0C[27:12]) [DS §13 p.120](#sources):

- **Control buffer**: 2 bits per page — page #0 occupies bits `000–001`, page #1
  bits `002–003`, … page #M bits `2*M – 2*M+1`. Total size
  `2 × MaxPageNumber_16Aligned` bits.
- **Checksum buffer**: 4 bytes per page — page #0 at bytes `000–003`, page #1 at
  `004–007`, … page #M at `4*M – 4*M+3`. Software must initialise it to 0. Total
  size `4 × MaxPageNumber_16Aligned` bytes.

---

## MDMA Engine — `0x1E74_0000`

**Used on target boards?** No. MDMA is a memory-to-memory copy / fill
accelerator; neither board's open firmware uses it. It is present on the SoC. No
mainline driver exists.

MDMA speeds up memory copy and memory fill (4×–8× over CPU loops) and buffers up
to 16 double-words of commands so a burst of commands can be queued without
waiting for idle; it can raise VIC INT#6 [DS §22 p.257](#sources). It implements 6
32-bit registers. Offsets `00h`–`0Ch` push a command into the queue on write;
offsets `10h`/`14h` are ordinary registers [DS §22 p.257](#sources). Buffer-fill mode
issues only writes and is intended for ECC-DRAM initialisation [DS §22 p.258](#sources).

Before writing `00h`/`04h`/`08h`/`0Ch`, software must ensure the available queue
length (MDMA14[8:4]) is non-zero, or an overflow occurs; when the clock ratio
MCLK/H-PLL > 2 (either direction) those writes are only legal while MDMA is idle
(MDMA14[3]=1) [DS §22 p.257](#sources).

:::{list-table} MDMA register summary
:header-rows: 1
:widths: 8 34 10 12 36

* - Offset
  - Register
  - Access
  - Init
  - Description
* - `00h`
  - MDMA00 — Source Data base (→queue)
  - RW
  - X
  - Source base address [27:0] [DS §22 p.257](#sources)
* - `04h`
  - MDMA04 — Destination Data base (→queue)
  - RW
  - X
  - Destination base address [27:0] [DS §22 p.258](#sources)
* - `08h`
  - MDMA08 — Buffer Filling Data (→queue)
  - RW
  - X
  - 32-bit fill pattern [DS §22 p.258](#sources)
* - `0Ch`
  - MDMA0C — Command (→queue)
  - RW
  - `0xxx_xxxx`
  - Fires a command; ID, type, length [DS §22 p.258](#sources)
* - `10h`
  - MDMA10 — Interrupt Control
  - RW
  - 0
  - Per-ID + idle + overflow IRQ masks [DS §22 p.259](#sources)
* - `14h`
  - MDMA14 — Interrupt Status
  - RW/R
  - `0000_0100`
  - Per-ID status, queue length, idle/overflow [DS §22 p.260](#sources)
:::

### MDMA00 / MDMA04 — Source / Destination base

:::{list-table} MDMA00, MDMA04
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:28
  - —
  - Reserved (0)
* - 27:0
  - RW
  - Base address [27:0] of source (MDMA00) / destination (MDMA04). Byte-aligned, up to 256 MB. Writing pushes into the command queue. [DS §22 p.257](#sources) [DS §22 p.258](#sources)
:::

### MDMA08 — Buffer Filling Data

:::{list-table} MDMA08 — Buffer Filling Data Register
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:0
  - RW
  - The double-word value written into the target buffer during a buffer-fill command. Fill ranges must be double-word aligned. [DS §22 p.258](#sources)
:::

### MDMA0C — Command

:::{list-table} MDMA0C — MDMA Command Register (Init = 0xxx_xxxx)
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31
  - RW
  - Update status of the MDMA command ID. `0` disable; `1` — on completion, set the status bit of the ID given in [30:28]. [DS §22 p.258](#sources)
* - 30:28
  - RW
  - MDMA command ID (#0–#7), assigned by software; used to steer the completion interrupt. [DS §22 p.258](#sources)
* - 27:26
  - —
  - Reserved (0)
* - 25:24
  - RW
  - Command type: `00` MDMA copy; `10` buffer-fill (write-only, for ECC init); `01`/`11` reserved. [DS §22 p.258](#sources)
* - 23:0
  - RW
  - Data length in bytes (`0` invalid, `1`=1 byte, …), up to `16M-1` per command. Writing this register fires the command. [DS §22 p.258](#sources)
:::

### MDMA10 — Interrupt Control

:::{list-table} MDMA10 — Interrupt Control Register (Init = 0)
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:24
  - —
  - Reserved (0)
* - 23:16
  - RW
  - Per-ID interrupt mask, one bit per command ID: bit 23 = ID #7 … bit 16 = ID #0. `1` = generate interrupt when a command with that ID finishes. [DS §22 p.259](#sources)
* - 15:4
  - —
  - Reserved (0)
* - 3
  - RW
  - Enable interrupt when the MDMA controller becomes IDLE. `0` disable; `1` enable. [DS §22 p.259](#sources)
* - 2
  - —
  - Reserved (0)
* - 1
  - RW
  - Enable interrupt on command-queue overflow (`1` recommended). [DS §22 p.259](#sources)
* - 0
  - —
  - Reserved (0)
:::

### MDMA14 — Interrupt Status

:::{list-table} MDMA14 — Interrupt Status Register (Init = 0000_0100)
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:24
  - —
  - Reserved (0)
* - 23:16
  - W1C
  - Per-ID completion status, bit 23 = ID #7 … bit 16 = ID #0. `1` = that command finished; write 1 to clear. [DS §22 p.260](#sources)
* - 15:9
  - —
  - Reserved (0)
* - 8:4
  - R
  - Available command-queue length: `00000` full (no free space) … `10000` 16 free double-words; others reserved. The FIFO holds 16 double-words. [DS §22 p.260](#sources)
* - 3
  - W1C
  - MDMA idle status. `1` = idle and queue empty; write 1 to clear. Bit 3 is **0** at reset — the Init value `0x00000100` sets bit 8 (the [8:4] free-dword-count field = 16), not this bit. [DS §22 p.261](#sources)
* - 2
  - —
  - Reserved (0)
* - 1
  - W1C
  - Command-queue overflow: `1` = the CPU kept writing commands with available length 0. Write 1 to clear. [DS §22 p.261](#sources)
* - 0
  - R
  - MDMA controller status. `0` idle and queue empty; `1` busy or queue not empty. [DS §22 p.261](#sources)
:::

---

## AHB-to-P-Bus / AHB→PCI (A2P) Bridge — `0x1E72_0000`

**Used on target boards?** No (outbound direction). A2P is the **outbound**
BMC→host bridge: it lets the ARM core issue transactions onto the internal
P-Bus (the bus that carries the PCI slave controller's commands), i.e. it is
only meaningful when the AST2050 is the PCI **master**. On both target boards the
AST2050 is a PCI **endpoint** (VGA / BMC device), not a bus master, so the
outbound A2P path is not exercised. The *inbound* counterpart — the P-to-AHB
(P2A) back door in ch. 36 — is the one the project actually uses ([culvert](https://github.com/mithro/culvert)'s
`p2a` access). No mainline driver programs A2P.

A2P is a **one-way** bridge providing a path for the ARM to reach IP modules on
the P-Bus [DS §21 p.256](#sources). It is **auto-enabled** when the SoC is put into PCI
master mode via `SCU70[4]` [DS §21 p.256](#sources). It exposes no conventional
bitfield registers; instead its `0x1E72_0000` window is an address map onto the
P-Bus:

:::{list-table} A2P address windows (base 0x1E72_0000 + OFFSET)
:header-rows: 1
:widths: 26 22 52

* - OFFSET range
  - P-Bus space
  - Description
* - `0x00000 – 0x0007F`
  - Relocated I/O
  - ARM accesses map to relocated I/O on the P-Bus [DS §21 p.256](#sources)
* - `0x00080 – 0x0FFFF`
  - *(reserved)*
  - Reserved [DS §21 p.256](#sources)
* - `0x10000 – 0x1FFFF`
  - MMIO
  - ARM accesses map to MMIO space on the P-Bus [DS §21 p.256](#sources)
:::

**Operation note:** because A2P is one-way (AHB→P-Bus), the ARM cannot generate
arbitrary PCI *bus* commands through it — it simply forwards AHB reads/writes in
its window to the P-Bus I/O or MMIO regions [DS §21 p.256](#sources). This is the mirror
image of the ch. 36 P2A bridge, which forwards host PCI accesses inbound to the
AHB and is normally locked [DS §36 p.400](#sources).

---

## 2D Graphics Engine (GER) — `PCIS14 (BAR1) + 0x8000`

**Used on target boards?** Not by the open firmware. The AST2050's VGA is wired
on the KGPE-D16 (onboard display) and the C410X, but the open-firmware stacks use
the plain framebuffer (mainline [`drivers/gpu/drm/ast`](https://github.com/torvalds/linux/tree/master/drivers/gpu/drm/ast) on later parts does no G3
2D acceleration); the 2D engine here is programmed only by the proprietary VGA
BIOS / driver. Documented for completeness; the block is present on the SoC.

The 2D Graphics Engine renders BitBLT, font-expansion and line-drawing commands
at up to 266 MHz / 64-bit-per-clock throughput and accesses data directly over
the M-Bus [DS §35 p.393](#sources). It implements **83** 32-bit registers, reached
through PCI memory-mapped I/O at `(PCIS14 BAR1) + 0x8000 + offset`
[DS §35 p.393](#sources). Many registers carry a **second meaning in line-drawing mode**;
both meanings are given below. The block owns a 16-stage HW command queue and
integrated 8×8 pattern/mask registers [DS §35 p.393](#sources).

Register offsets `00h`–`3Ch` are the drawing-parameter and command block, `40h`
is a **reserved gap**, `44h`–`4Ch` are the command-queue control/status, and
`100h`–`1FCh` are the 64 pattern / monochrome-bitmap registers. Offsets
`50h`–`FCh` are a reserved gap [DS §35 p.394](#sources) [DS §35 p.399](#sources).

:::{list-table} 2D engine (GER) register summary
:header-rows: 1
:widths: 8 34 10 10 38

* - Offset
  - Register (BitBLT / font meaning)
  - Access
  - Init
  - Line-drawing alternate meaning
* - `00h`
  - GER00 — Source Buffer base (or Font Buffer base, enhanced font)
  - RW
  - X
  - — [DS §35 p.394](#sources)
* - `04h`
  - GER04 — Row pitch of Source Buffer (or Font Buffer)
  - RW
  - X
  - — [DS §35 p.394](#sources)
* - `08h`
  - GER08 — Destination Buffer base
  - RW
  - X
  - — [DS §35 p.394](#sources)
* - `0Ch`
  - GER0C — Row pitch + height of Destination Buffer
  - RW
  - X
  - — [DS §35 p.394](#sources)
* - `10h`
  - GER10 — Coordinate of destination bitmap (top-left X/Y)
  - RW
  - X
  - Start point of line drawing (X/Y) [DS §35 p.395](#sources)
* - `14h`
  - GER14 — Coordinate of source bitmap (top-left X/Y)
  - RW
  - X
  - Major-axis select + error term [DS §35 p.395](#sources)
* - `18h`
  - GER18 — Drawing width + height
  - RW
  - X
  - Width of the major axis [DS §35 p.395](#sources)
* - `1Ch`
  - GER1C — Foreground colour of pattern
  - RW
  - X
  - — [DS §35 p.396](#sources)
* - `20h`
  - GER20 — Background colour of pattern
  - RW
  - X
  - — [DS §35 p.396](#sources)
* - `24h`
  - GER24 — Foreground colour of source
  - RW
  - X
  - K1 term of line drawing [DS §35 p.396](#sources)
* - `28h`
  - GER28 — Background colour of source
  - RW
  - X
  - K2 term of line drawing [DS §35 p.396](#sources)
* - `2Ch`
  - GER2C — Monochrome mask of pattern #0
  - RW
  - X
  - Line-style pattern #0 [DS §35 p.396](#sources)
* - `30h`
  - GER30 — Monochrome mask of pattern #1
  - RW
  - X
  - Line-style pattern #1 [DS §35 p.396](#sources)
* - `34h`
  - GER34 — Top-left clipping corner (X/Y)
  - RW
  - X
  - — [DS §35 p.396](#sources)
* - `38h`
  - GER38 — Bottom-right clipping corner (X/Y)
  - RW
  - X
  - — [DS §35 p.396](#sources)
* - `3Ch`
  - GER3C — 2D Engine Command
  - RW
  - 0
  - Command word (both modes) [DS §35 p.397](#sources)
* - `40h`
  - *(reserved gap)*
  - —
  - —
  - Not assigned [DS §35 p.398](#sources)
* - `44h`
  - GER44 — Command Queue Setting
  - RW
  - 0
  - — [DS §35 p.398](#sources)
* - `48h`
  - GER48 — Command Queue Write-Pointer
  - RW
  - 0
  - — [DS §35 p.399](#sources)
* - `4Ch`
  - GER4C — 2D Engine Status
  - R
  - 0
  - — [DS §35 p.399](#sources)
* - `50h–FCh`
  - *(reserved gap)*
  - —
  - —
  - Not assigned [DS §35 p.399](#sources)
* - `100h–1FCh`
  - PTR00–PTRFC — Pattern regs #1–#64 (or monochrome bitmap regs, font)
  - RW
  - X
  - — [DS §35 p.399](#sources)
:::

### GER00 / GER08 — Source / Destination buffer base

:::{list-table} GER00, GER08 (and GER00 font-buffer variant)
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:28
  - —
  - Reserved (0)
* - 27:3
  - RW
  - Base address [27:3] of the source buffer (GER00) or destination buffer (GER08); 8-byte aligned. In enhanced font-expansion, GER00 is instead the font-buffer base. [DS §35 p.394](#sources)
* - 2:0
  - —
  - Reserved (0)
:::

### GER04 — Row pitch of source / font buffer

:::{list-table} GER04 — Row Pitch of Source (or Font) Buffer
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:29
  - —
  - Reserved (0)
* - 28:16
  - RW
  - Row pitch [12:0] = bitmap width × bytes/pixel. Limits: 256-color `0000–07FF`, high-color `0000–0FFF`, true-color `0000–1FFF`. Font variant: GER04[28:16] = (GER18[26:16]+7)>>3, with `0 < GER04[28:16]×GER18[10:0] ≤ 0xFFF`. [DS §35 p.394](#sources)
* - 15:0
  - —
  - Reserved (0)
:::

### GER0C — Row pitch + height of destination buffer

:::{list-table} GER0C — Row Pitch and Height of Destination Buffer
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:29
  - —
  - Reserved (0)
* - 28:19
  - RW
  - Row pitch [12:3] of the destination buffer = width × bytes/pixel. Limits: 256-color `0000–07F8`, high-color `0000–0FF8`, true-color `0000–1FF8`. [DS §35 p.394](#sources)
* - 18:11
  - —
  - Reserved (0)
* - 10:0
  - RW
  - Height [10:0] of the destination buffer, range `0000–07FF`. [DS §35 p.394](#sources)
:::

### GER10 — Destination coordinate / line start point

:::{list-table} GER10 — Destination bitmap coordinate (line: start point)
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:28
  - —
  - Reserved (0)
* - 27:16
  - RW
  - X coordinate [11:0] of the destination top-left corner (line mode: start point), format S11.0. [DS §35 p.395](#sources)
* - 15:12
  - —
  - Reserved (0)
* - 11:0
  - RW
  - Y coordinate [11:0] of the destination top-left corner (line mode: start point), format S11.0. [DS §35 p.395](#sources)
:::

### GER14 — Source coordinate / line major+error term

:::{list-table} GER14 — Source bitmap coordinate (line: major axis + error term)
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:28
  - —
  - Reserved (0) — BitBLT mode
* - 27:16
  - RW
  - **BitBLT:** X coordinate [11:0] of the source top-left corner (S11.0). Must be 0 when GER3C[2:0]=2 or 3. [DS §35 p.395](#sources)
* - 15:12
  - —
  - Reserved (0) — BitBLT mode
* - 11:0
  - RW
  - **BitBLT:** Y coordinate [11:0] of the source top-left corner (S11.0). Must be 0 when GER3C[2:0]=2 or 3. [DS §35 p.395](#sources)
* - 24
  - RW
  - **Line:** major-axis select — `0` Y-axis, `1` X-axis (bits 31:25 and 23:22 reserved). [DS §35 p.395](#sources)
* - 21:0
  - RW
  - **Line:** error term [21:0] of the line-drawing algorithm. [DS §35 p.395](#sources)
:::

### GER18 — Drawing width+height / line major-axis width

:::{list-table} GER18 — Drawing width & height (line: major-axis width)
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:27
  - —
  - Reserved (0)
* - 26:16
  - RW
  - Width [10:0] of the destination bitmap. Range: 256-color `1–2040`, high-color `1–2044`, true-color `1–2046`. Line mode: width [10:0] of the major axis. [DS §35 p.395](#sources)
* - 15:11
  - —
  - Reserved (0)
* - 10:0
  - RW
  - Height [10:0] of the destination bitmap (BitBLT). Reserved in line mode (bits 15:0 = 0). [DS §35 p.395](#sources)
:::

### GER1C / GER20 — Pattern foreground / background colour

:::{list-table} GER1C, GER20
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:0
  - RW
  - Full 32-bit foreground colour of pattern (GER1C) / background colour of pattern (GER20). [DS §35 p.396](#sources)
:::

### GER24 / GER28 — Source colour / line K1,K2 terms

:::{list-table} GER24, GER28
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:0
  - RW
  - **BitBLT:** foreground colour of source (GER24) / background colour of source (GER28), 32-bit. [DS §35 p.396](#sources)
* - 21:0
  - RW
  - **Line:** K1 term (GER24) / K2 term (GER28) of the line-drawing algorithm (bits 31:22 reserved). [DS §35 p.396](#sources)
:::

### GER2C / GER30 — Pattern mask / line-style pattern

:::{list-table} GER2C, GER30
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:0
  - RW
  - **BitBLT:** monochrome mask of pattern bits [31:0] (GER2C) / [63:32] (GER30). **Line:** line-style pattern bits [31:0] (GER2C) / [63:32] (GER30). [DS §35 p.396](#sources)
:::

### GER34 / GER38 — Clipping rectangle corners

:::{list-table} GER34 (top-left), GER38 (bottom-right)
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:28
  - —
  - Reserved (0)
* - 27:16
  - RW
  - X coordinate [11:0] of the clipping-rectangle corner — top-left for GER34, bottom-right for GER38. [DS §35 p.396](#sources)
* - 15:12
  - —
  - Reserved (0)
* - 11:0
  - RW
  - Y coordinate [11:0] of the clipping-rectangle corner. [DS §35 p.396](#sources)
:::

### GER3C — 2D Engine Command

:::{list-table} GER3C — 2D Engine Command Register (Init = 0)
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31
  - RW
  - Reset line-style counter on a new line-drawing command. `0` no-op; `1` reset. [DS §35 p.397](#sources)
* - 30
  - RW
  - Enable line drawing with a style pattern. `0` no style; `1` styled. [DS §35 p.397](#sources)
* - 29:24
  - RW
  - Line-style period [5:0] — up to 64 points. [DS §35 p.397](#sources)
* - 23
  - RW
  - End-point rendering for line drawing. `0` disable; `1` enable. [DS §35 p.397](#sources)
* - 22
  - —
  - Reserved (0)
* - 21
  - RW
  - X-axis rendering direction. `0` +X; `1` −X. [DS §35 p.398](#sources)
* - 20
  - RW
  - Y-axis rendering direction. `0` +Y; `1` −Y. [DS §35 p.398](#sources)
* - 19
  - —
  - Reserved (0)
* - 18
  - RW
  - Font expansion mode. `0` opaque; `1` transparent. [DS §35 p.398](#sources)
* - 17:16
  - RW
  - Pattern source: `00` foreground-colour register; `01` monochrome mask register; `10` pattern register; `11` invalid. [DS §35 p.398](#sources)
* - 15:8
  - RW
  - Raster-operation (ROP) code [7:0] — one of 256 raster ops. [DS §35 p.398](#sources)
* - 7
  - RW
  - Monochrome-mask transparency. `0` opaque; `1` transparent. [DS §35 p.398](#sources)
* - 6
  - RW
  - Source bitmap origin. `0` video frame buffer; `1` command queue (not supported for line drawing). [DS §35 p.398](#sources)
* - 5:4
  - RW
  - Colour mode: `00` 256-color (8-bpp); `01` high-color (16-bpp); `10` true-color (24-bpp); `11` invalid. [DS §35 p.398](#sources)
* - 3
  - RW
  - Rectangular clipping. `0` disable; `1` enable. [DS §35 p.398](#sources)
* - 2:0
  - RW
  - Command type: `000` BitBLT; `001` line drawing; `010` font expansion (patterns from registers); `011` enhanced font expansion (patterns from frame buffer); `1xx` invalid. [DS §35 p.398](#sources)
:::

### GER44 — Command Queue Setting

:::{list-table} GER44 — Command Queue Setting Register (Init = 0)
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:28
  - RW
  - Available size of the HW command queue [3:0]: `0000` 0 B, `0001` 8 B, `0010` 16 B, … `1111` 120 B (8 B per step). [DS §35 p.398](#sources)
* - 27:26
  - RW
  - Command-queue buffer size: `00` 256 KB; `01` 512 KB; `10` 1 MB; `11` 2 MB. [DS §35 p.398](#sources)
* - 25
  - RW
  - Command-queue operation mode: `0` command data from video frame buffer; `1` from memory-mapped I/O command. [DS §35 p.398](#sources)
* - 24:0
  - RW
  - Base address [27:3] of the command-queue buffer. [DS §35 p.398](#sources)
:::

### GER48 — Command Queue Write-Pointer

:::{list-table} GER48 — Write-Pointer of Command Queue (Init = 0)
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:18
  - —
  - Reserved (0)
* - 17:0
  - RW
  - Write-pointer of the command queue [20:3]. [DS §35 p.399](#sources)
:::

### GER4C — 2D Engine Status

:::{list-table} GER4C — 2D Engine Status Register (Init = 0)
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31
  - R
  - 2D engine status. `0` idle; `1` busy. [DS §35 p.399](#sources)
* - 30:18
  - R
  - Debug port (debug use only). [DS §35 p.399](#sources)
* - 17:0
  - R
  - Read-pointer of the command queue [20:3]. [DS §35 p.399](#sources)
:::

### PTR00–PTRFC — Pattern / monochrome-bitmap registers (`100h`–`1FCh`)

:::{list-table} PTR00–PTRFC — Pattern registers #1–#64
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:0
  - RW
  - 64 consecutive 32-bit registers at `100h`–`1FCh`. In BitBLT these are the ROP pattern registers #1–#64; in font-expansion they are the monochrome bitmap registers #1–#64. [DS §35 p.399](#sources)
:::

---

## Graphics Hardware Cursor — `0x1E6E_2050` / `0x1E70_0008`

**Used on target boards?** Not by the open firmware. The 64×64 hardware cursor
overlay belongs to the internal VGA/CRT path and is driven by the proprietary
VGA BIOS / graphics driver; the open-firmware stacks do not program it.
Documented for completeness; present on the SoC.

The hardware cursor supports a 64×64 monochrome cursor (AND-XOR-RGB444 pixel
format) or a 64×64 colour cursor (ARGB4444), with X/Y offset, its shape read
from a designated area in the VGA frame buffer, and its parameters read back from
VGA scratch registers. It can auto-generate a **cursor-change interrupt**
[DS §37 p.401](#sources). Unlike the other blocks, the cursor has no dedicated register
page; its control/status registers are spread across the Video Engine control
space (`0x1E70_0000`) and the SCU / VGA-scratch space (`0x1E6E_2000`)
[DS §37 p.401](#sources).

:::{list-table} Hardware-cursor register summary
:header-rows: 1
:widths: 20 26 10 10 34

* - Address
  - Register
  - Access
  - Init
  - Description
* - `0x1E70_0008`
  - VR008 — Video Engine Control
  - RW
  - 0
  - Bit 8 disables the VGA HW-cursor overlay [DS §37 p.401](#sources)
* - `0x1E6E_2018`
  - SCU18 — Interrupt Control & Status
  - RW
  - 0
  - Cursor / scratch-change IRQ enables + status [DS §37 p.401](#sources)
* - `0x1E6E_2050`
  - VGA Scratch #1
  - R
  - 0
  - Cursor X/Y offset, type, enable [DS §37 p.401](#sources)
* - `0x1E6E_2054`
  - VGA Scratch #2
  - R
  - 0
  - Cursor Y position, X position offset [DS §37 p.402](#sources)
* - `0x1E6E_2058`
  - VGA Scratch #3
  - R
  - 0
  - Cursor pattern memory address [DS §37 p.402](#sources)
:::

### VR008 — Video Engine Control (cursor bit)

:::{list-table} VR008 — Video Engine Control Register (Init = 0)
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 8
  - RW
  - Disable HW-cursor overlay for the internal VGA. `0` VGA output includes the HW-cursor overlay image; `1` VGA output without the overlay (clients must overlay via the Quick Cursor algorithm). The DAC output still carries the overlay when required even if this bit is 1. [DS §37 p.401](#sources)
:::

*(Only bit 8 of VR008 is defined for the hardware cursor; the remaining VR008
bits belong to the Video Engine and are outside this block [DS §37 p.401](#sources).)*

### SCU18 — Interrupt Control & Status (cursor IRQs)

:::{list-table} SCU18 — Interrupt Control and Status Register (Init = 0)
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:18
  - —
  - Reserved (0)
* - 17
  - W1C
  - VGA scratch-register change interrupt + status. `1` = interrupt occurred; write 1 to clear. [DS §37 p.401](#sources)
* - 16
  - W1C
  - VGA cursor-change interrupt + status. `1` = interrupt occurred; write 1 to clear. [DS §37 p.401](#sources)
* - 15:2
  - —
  - Reserved (0)
* - 1
  - RW
  - Enable VGA scratch-register change interrupt. `0` disable; `1` enable. [DS §37 p.401](#sources)
* - 0
  - RW
  - Enable VGA cursor-change interrupt. `0` disable; `1` enable. [DS §37 p.401](#sources)
:::

### VGA Scratch Register #1 (`0x1E6E_2050`)

:::{list-table} VGA Scratch #1 (Init = 0)
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:30
  - R
  - Reserved
* - 29:24
  - R
  - Hardware cursor X position offset [5:0]. [DS §37 p.401](#sources)
* - 23:22
  - R
  - Reserved
* - 21:16
  - R
  - Hardware cursor Y position offset [5:0]. [DS §37 p.401](#sources)
* - 15:10
  - R
  - Reserved
* - 9
  - R
  - Cursor type. `0` monochrome; `1` colour. [DS §37 p.401](#sources)
* - 8
  - R
  - Hardware cursor enabled. `0` disabled; `1` enabled. [DS §37 p.401](#sources)
* - 7:0
  - R
  - Reserved
:::

### VGA Scratch Register #2 (`0x1E6E_2054`)

:::{list-table} VGA Scratch #2 (Init = 0)
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:27
  - R
  - Reserved
* - 26:16
  - R
  - Hardware cursor Y position [10:0]. [DS §37 p.402](#sources)
* - 15:12
  - R
  - Reserved
* - 11:0
  - R
  - Hardware cursor X position offset [11:0]. [DS §37 p.402](#sources)
:::

### VGA Scratch Register #3 (`0x1E6E_2058`)

:::{list-table} VGA Scratch #3 (Init = 0)
:header-rows: 1
:widths: 10 10 80

* - Bits
  - Access
  - Description
* - 31:28
  - R
  - Reserved
* - 27:0
  - R
  - Hardware cursor pattern memory address [27:0]. [DS §37 p.402](#sources)
:::

### Cursor shape structure

Each cursor pixel is a 16-bit word in the frame-buffer shape area
[DS §37 p.403](#sources):

- **Monochrome (AND-XOR-RGB444):** [DS §37 p.403](#sources)

  - bit[15] AND-mask
  - bit[14] XOR-mask
  - bit[13:12] reserved
  - bit[11:8] R
  - bit[7:4] G
  - bit[3:0] B

  The AND/XOR pair selects:

  - `0,0` background (cursor R/G/B)
  - `0,1` foreground (cursor R/G/B)
  - `1,0` transparent (graphics R/G/B)
  - `1,1` inverse (NOT graphics R/G/B)

- **Colour (ARGB4444):** [DS §37 p.403](#sources)

  - bit[15:12] alpha
  - bit[11:8] R
  - bit[7:4] G
  - bit[3:0] B

  Output = alpha × graphics + (1−alpha) × cursor, normalised to the display
  format. When X/Y-offset is enabled only a partial bitmap is displayed.

---

## Cross-reference: firmware headers & mainline drivers

- **[hwreg.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h) / [ast2050.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/ast2050.h)** (Raptor Engineering AST2050 U-Boot): none of these
  six blocks is defined. The DMA, SSP, I2C and RTC register sections in
  [hwreg.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h) are empty stub comments; only SDRAM, SCU, timer, VIC, WDT, UART, MAC,
  GPIO and AHB controllers are populated [hwreg.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h). The KGPE-D16 U-Boot config
  references HACE and MIC only through the disabled SLT self-test macros
  `CFG_CMD_HACTEST` / `CFG_CMD_MICTEST` [ast2050.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/ast2050.h).
- **Mainline Linux:** the AST2050 (G3) predates mainline ASPEED support
  (earliest is the AST2400 / G4), so no mainline driver targets these G3 block
  instances. The related later-generation drivers — [`drivers/crypto/aspeed`](https://github.com/torvalds/linux/tree/master/drivers/crypto/aspeed)
  (HACE, AST2500/AST2600 only) and [`drivers/gpu/drm/ast`](https://github.com/torvalds/linux/tree/master/drivers/gpu/drm/ast) (desktop AST VGA) — do
  not program the register interfaces documented here.

## Gaps and caveats

- **A2P has no bitfield registers** in the datasheet — only the three address
  windows above and the "auto-enable in PCI-master mode (SCU70[4])" rule
  [DS §21 p.256](#sources). There is no per-register reset/access table to reproduce.
- **HACE `0x14` / `0x18`** are undocumented gaps between HACE10 and HACE1C; the
  datasheet lists exactly 11 registers and skips these offsets [DS §19 p.222](#sources).
- **2D engine `0x40` and `0x50`–`0xFC`** are reserved gaps; the datasheet's "83
  registers" count = 19 named registers (`00`–`4C`, minus the `40` gap) + 64
  pattern registers (`100`–`1FC`) [DS §35 p.393](#sources) [DS §35 p.399](#sources).
- **Reset values** are quoted verbatim from the datasheet "Init" fields; several
  are `X` (undefined) because they are software-loaded pointers with no defined
  power-on value.
- The extracted-text working copy (`AST2050_V1.05.txt`) carries interleaved
  "ASPEED Confidential" watermark fragments; all values here were read back
  against the source PDF pages (e.g. PDF p.222 confirmed identical to the text).

## See also

**Related pages**

- {doc}`/hardware/registers/ddr2-sdram` — the DRAM that the MIC scrubs and the MDMA fills (ECC init)
- {doc}`/hardware/registers/pcie-vga-usb-bridges` — the inbound P2A bridge, counterpart to the outbound A2P here, and the PCI endpoint
- {doc}`/hardware/registers/display-usb` — the VGA/Video path the 2D engine and hardware cursor belong to
- {doc}`/hardware/registers/scu-clock-reset` — YCLK/GCLK gating and the SCU04 resets for HACE and the 2D engine

**External references**

- [Linux crypto API](https://docs.kernel.org/crypto/index.html) — the framework a HACE hash/cipher driver registers with
- [Linux DMA engine subsystem](https://docs.kernel.org/driver-api/dmaengine/index.html) — the dmaengine model for a memory-to-memory copier like MDMA
- [aspeed HACE device-tree binding](https://github.com/torvalds/linux/blob/master/Documentation/devicetree/bindings/crypto/aspeed,ast2500-hace.yaml) — the later-gen Aspeed hash/crypto binding
- [Linux GPU/DRM documentation](https://docs.kernel.org/gpu/index.html) — the display/2D-acceleration subsystem context for the 2D engine and cursor

## Sources

- **DS** ASPEED, *AST2050 / AST1100 A3 Datasheet, V1.05* (25 May 2010), in-repo at
  [`datasheets/aspeed/AST2050_AST1100_A3_Datasheet_V1.05.pdf`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/datasheets/aspeed/AST2050_AST1100_A3_Datasheet_V1.05.pdf). Chapters used:
  §10 Interrupt Source Table (p.99); §13 Memory Integrity Check Controller
  (p.116–120); §19 Hash & Crypto Engine / HACE (p.221–227); §21 AHB-to-P-Bus
  Bridge (p.256); §22 MDMA Engine (p.257–261); §35 2D Graphics Engine
  (p.393–399); §36 P-Bus-to-AHB Bridge (p.400); §37 Graphics Hardware Cursor
  (p.401–403). Doc page = PDF page (offset 0).
- [ast2050.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/ast2050.h) Raptor Engineering AST2050 U-Boot board config, in-repo at
  [`asus-kgpe-d16-firmware/ast2050.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/ast2050.h).
- [hwreg.h](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h) Raptor Engineering AST2100/AST2050 SoC register locations, in-repo at
  [`asus-kgpe-d16-firmware/hwreg.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h).
- **aspeed-crypto** Mainline Linux ASPEED HACE driver (AST2500/AST2600):
  <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/drivers/crypto/aspeed>
- **aspeed-drm** Mainline Linux ASPEED VGA (`ast`) DRM driver:
  <https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/tree/drivers/gpu/drm/ast>
