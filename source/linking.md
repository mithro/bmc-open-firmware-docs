# Linking policy — when and what to link

Every page on this site makes claims that are backed by *something* — a
datasheet page, a decompiled firmware file, a mainline driver, a sibling page
that documents the block being mentioned. The rule of this site is that **the
reader must never have to go searching for the thing a sentence is talking
about**: if it exists, the sentence links to it.

This page defines what must be linked, where each kind of thing links to, and
what must *not* be linked. It exists because link gaps come in three distinct
layers that fail in different ways:

1. **Artifact links** — a file, repo, branch, patch, or datasheet is *named*
   but not linked (or linked at the wrong ref/path).
2. **Citation links** — an evidence tag like `[DS §14.2 p.124]` is missing its
   target and renders as literal bracket text.
3. **Semantic cross-links** — prose discusses a *topic* (the P2A cold-boot, the
   64 MiB constraint, a peripheral) that has a dedicated page here, without
   linking to it.

## Quick decision table

```{list-table}
:header-rows: 1
:widths: 30 40 30

* - You are writing about…
  - Link to…
  - Markup
* - A topic with a page on this site
  - that page (first mention per section)
  - `` {doc}`/debug/bring-up` ``
* - A specific section of a page
  - the heading anchor (h1–h3)
  - `` [the P2A path](debug/bring-up.md#heading-slug) ``
* - A file in the program repo
  - the GitHub blob on `main`
  - `` [`hwreg.h`](https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/asus-kgpe-d16-firmware/hwreg.h) ``
* - Specific lines of that file
  - the blob with a `#LN-LM` anchor
  - `` [platform.S:363-377](…/platform.S#L363-L377) ``
* - A directory in a repo
  - the GitHub *tree* URL
  - `` [`io-tables/`](…/tree/main/dell-c410x-firmware/io-tables) ``
* - A mainline kernel/U-Boot file
  - the blob at the **correct ref** (see below)
  - `` [`ftgmac100.c`](https://github.com/torvalds/linux/blob/master/drivers/net/ethernet/faraday/ftgmac100.c) ``
* - A repo, fork, or branch
  - the repo URL / `tree/<branch>`
  - `` [`mithro/qemu`](https://github.com/mithro/qemu) ``, `` [`hpe-ipdu-port`](https://github.com/mithro/u-boot/tree/hpe-ipdu-port) ``
* - A project, daemon, or tool
  - its canonical repo or homepage
  - `` [`bmcweb`](https://github.com/openbmc/bmcweb) ``, `[culvert](https://github.com/mithro/culvert)`
* - A datasheet fact
  - a citation tag → the page's Sources
  - `` [DS §14.2 p.124](#sources) ``
* - The datasheet itself (in Sources)
  - the in-repo PDF blob
  - `` **[INA219 datasheet](…/datasheets/INA219_Datasheet.pdf)** ``
* - A standard / external doc
  - the canonical (or archived) URL
  - `` [DMTF Redfish standard](https://www.dmtf.org/standards/redfish) ``
```

## 1. Cross-references within this site

Use MyST `{doc}` roles so the Sphinx link checker validates them:
`` {doc}`/drivers/linux` `` (absolute) or `` {doc}`../debug/bring-up` ``
(relative), with custom text as `` {doc}`the G3 VIC fix </drivers/linux>` ``.
`myst_heading_anchors = 3` is enabled, so any h1–h3 heading can be deep-linked
by its slug (e.g. `` [the compact G3 VIC](hardware/soc-ast2050.md#interrupt-controller-the-compact-g3-vic) `` —
always verify the generated slug against the built page).
Explicit `{ref}` labels (like `(g3-vic)=`) are preferred for targets that are
linked from several pages, because they survive heading rewording.

**When**: the *first* mention of the topic in a page section — not every
repetition, and not when the same section already carries the link. The test is
reader benefit: *would a reader plausibly want to jump from this sentence to
that page?*

Typical topic → page mappings on this site:

- the P2A cold-boot, JTAG run-control, "blind to the VIC" → {doc}`/debug/bring-up`
- header pinouts, wiring, OpenOCD invocation → {doc}`/debug/jtag-uart`
- the 64 MiB DRAM constraint, Redfish-on-silicon, KCS host IPMI, vKVM →
  {doc}`/firmware/openbmc`
- the G3 VIC driver, the ftgmac100 `FAST_MODE` RX fix, the patch series →
  {doc}`/drivers/linux`
- the `kgpe-d16-bmc` / `ns9360` QEMU machines, the faithful G3 model →
  {doc}`/emulation/qemu`; qtest / `firmware-testbench` benches →
  {doc}`/emulation/testbench`
- any named peripheral (INA219, ADT7462, PEX8696, W83795G, …) → its page under
  {doc}`/hardware/peripherals/index`
- the C410X seven-bus fan-out / `i2cdetect` map → {doc}`/hardware/i2c-topology`
- a SoC block's registers → the right page under {doc}`/hardware/registers/index`

✗ *Bad*: "The reliable sequence disables the ARM via the SCU strap" — with no
link, on a page that isn't the SCU reference.
✓ *Good*: "…via the SCU strap ({doc}`/hardware/registers/scu-clock-reset`)".

**Wrong-target rule**: link the *most specific correct* target. A sentence
about DDR2 init corrections links {doc}`/hardware/registers/ddr2-sdram` (or the
SoC page's DDR2 section), not the generic {doc}`/drivers/linux`. A sentence
about the *host-side* `drm/ast` driver must not link the *BMC-side*
`drm/aspeed` directory, and vice versa.

## 2. Program-repository artifacts

Everything in [`mithro/ai-shenanigans-for-bmcs`](https://github.com/mithro/ai-shenanigans-for-bmcs)
links as a GitHub blob on `main`:
`https://github.com/mithro/ai-shenanigans-for-bmcs/blob/main/<path>` — use
`/tree/main/<path>` for directories. This covers analysis documents
(`ANALYSIS.md`, `RAPTOR-PORTING-GUIDE.md`, …), headers (`hwreg.h`,
`ast2050.h`), init code (`platform.S`), kernel patches
(`kernel/patches/*.patch` — note patch 0001 lives under
`qemu-firmware/kernel/patches/`), configs (`openocd/*.cfg`), scripts, the
reconstructed device tree (`aspeed-bmc-dell-c410x.dts`), IO-table decodes, the
vendored Digi U-Boot tree, and the **datasheet PDFs** (GitHub renders them).

- Line-specific citations append `#LN` / `#LN-LM`:
  `` [JTAG-USAGE-GUIDE.md:250-256](…/JTAG-USAGE-GUIDE.md#L250-L256) ``. For a
  multi-range cite like `[dts:739-743,769]`, anchor the first range.
- Things that are **gitignored/regenerated** (extracted firmware, `fullfw`,
  build outputs) are *not on GitHub* and must not be "linked" — name them and
  link the script or README that regenerates them instead.

## 3. Upstream source code — picking the ref

Link mainline files at the **correct ref**, and re-verify the path resolves —
files move:

- **Living code** → `blob/master` (torvalds/linux, u-boot/u-boot, qemu). E.g.
  the Aspeed clock driver is now
  [`drivers/clk/aspeed/clk-aspeed.c`](https://github.com/torvalds/linux/blob/master/drivers/clk/aspeed/clk-aspeed.c)
  — the old `drivers/clk/clk-aspeed.c` path 404s.
- **Removed code** → the **last tag that carried it**:
  `arch/arm/mach-ns9xxx` → torvalds/linux **v2.6.39**; the KGPE-D16 coreboot
  code (`southbridge/amd/sb700`, `drivers/i2c/w83795`) → coreboot **4.11**;
  the ns9750 U-Boot files → u-boot **v2012.10**.
- **Vendor-only code** → the in-repo vendored copy (e.g. `ns9750_eth.h`,
  `ns9750_usb_ohci.h` exist only in the Digi 1.1.4 tree under
  `hpe-ipdu-firmware/uboot-port/reference/`), never a guessed upstream path.
- **Stale forks**: check the fork's branches before linking into it —
  `mithro/qemu@master` is an ancient fork; the program's work is on the
  `d16-ast2050-machine` / `ns9360-machine` branches, so file links go there.

## 4. Repositories, branches, and PRs

Name a repo → link the repo. Name a branch → link `tree/<branch>`.
Name a tag → link `tree/<tag>` (or the blob at that tag).

**Planned things stay unlinked.** A topic branch that does not exist yet
(u-boot `ast2050-port`; zephyr `arch-arm926ejs` / `soc-ast2050` /
`soc-ns9360`) is written as plain code text, ideally marked *(planned)* —
a link that 404s is worse than no link. When the branch lands, link it.

## 5. Projects, daemons, and tools

First mention (per section) of a named software component links its canonical
home: OpenBMC daemons to their `github.com/openbmc/<name>` repos (`bmcweb`,
`entity-manager`, `dbus-sensors`, `obmc-console`, `obmc-ikvm`,
`phosphor-state-manager`, `phosphor-host-ipmid`, `phosphor-net-ipmid`,
`phosphor-pid-control`, `phosphor-gpio-monitor`, `phosphor-bmc-code-mgmt`);
tools to their repos ([culvert](https://github.com/mithro/culvert) — the G3
fork; [upstream](https://github.com/amboar/culvert) where the contrast
matters — [spispy](https://github.com/osresearch/spispy),
[ipmitool](https://github.com/ipmitool/ipmitool)) or homepages
([OpenOCD](https://openocd.org/)). If no canonical URL can be verified
(`plxtools`), leave the name unlinked rather than guessing.

## 6. Standards and external references

Specifications and external docs link their canonical page (DMTF Redfish,
kernel.org docs, Zephyr/U-Boot/QEMU manuals, ARM TRMs). For vendor pages and
datasheets with link-rot risk, prefer the in-repo PDF first and add the vendor
URL (or a web.archive.org snapshot) as the secondary link. Paywalled or
registration-gated sources (JEDEC) are named with an explanation instead of a
dead link.

## 7. Citations and the Sources section

Every register page carries a `## Sources` section; evidence tags in the body
jump to it:

- **Datasheet cites**: `` [DS §14.2 p.124](#sources) ``,
  `` [HWRef p.36](#sources) ``, `` [W83795G DS p.28](#sources) `` — the tag
  *always* carries the `(#sources)` target. A bare `[DS §14.2 p.124]` renders
  as literal bracket text — this is the single most common historical defect
  on this site.
- **File cites**: `` [platform.S:363-377](…#L363-L377) ``,
  `` [ANALYSIS.md:499](…#L499) ``, `` [dts:596-663](…#L596-L663) `` — link the
  blob with line anchors directly (not `#sources`).
- **Sources entries themselves** link the artifact: the in-repo PDF, the
  analysis file, the driver source. A Sources entry must never link
  `(#sources)` — that is a self-link to the section it sits in. Write the tag
  as plain bold (`**DS**`) and put the link on the file name.
- Never leave tool-generated placeholders like `[WebSearch: …]` in prose —
  replace them with the real citation or remove them.

## 8. What NOT to link

- Register/bit names (`SCU70[1:0]`, `MACCR`), DT compatibles
  (`aspeed,ast2050-vic`), config symbols, shell commands, code identifiers.
- Bit-notation prose like `[MSB, LSB]` or `[2n+1:2n]` — brackets are fine
  here; they are not citations.
- Part numbers used as nouns where the sentence is *about the page's own
  subject* (the INA219 page doesn't link "INA219" to itself).
- Planned/nonexistent artifacts (see §4) and unverifiable URLs (see §5).
- Repeated mentions in the same section after a linked first mention.
- Don't link inside a link: `[a [b](url)][ref]` is invalid CommonMark and
  renders broken.

## 9. Verify before you link

A link added without verification is a future 404. Before committing:

- **In-repo paths**: check against GitHub `main` (`git ls-tree` on a fresh
  fetch, or the contents API) — not against a possibly-dirty local checkout.
- **Upstream paths**: HTTP 200 on `raw.githubusercontent.com` (or the contents
  API) at the exact ref used.
- **Branches/repos**: the API returns them by name.
- **Heading anchors**: the target heading exists in the target file.
- **External URLs**: resolve (a bot-blocking 403 from a known-good site is
  acceptable; a 404 is not).

CI runs `sphinx-build -b linkcheck` as a gate; `{doc}`/`{ref}` roles are
validated at build time with warnings-as-errors, which is why internal
cross-references should use roles rather than raw relative URLs where possible.

## 10. Markup conventions

- Inline links `[text](url)`; file names in code style inside the label:
  `` [`ftgmac100.c`](…) ``.
- Reference-style `[text][label]` is fine *only* with a matching
  `[label]: url` definition in the same file — an undefined label renders as
  literal text.
- Keep a citation tag and its `(#sources)` target on the same line; a tag
  wrapped across a line break loses its target silently.
- Bold-linked Sources entries: `**[name](url)** — description (in-repo PDF).`
