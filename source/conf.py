# Configuration file for the Sphinx documentation builder.
#
# Documentation for the open BMC / firmware program covering the Aspeed AST2050
# boards (ASUS KGPE-D16, Dell C410X) and the Digi NS9360 board (HPE iPDU).
# Full options: https://www.sphinx-doc.org/en/master/usage/configuration.html

project = "Open BMC & Firmware"
copyright = "2026, Tim 'mithro' Ansell and contributors"
author = "Tim 'mithro' Ansell and contributors"

# -- General configuration ---------------------------------------------------

extensions = [
    "myst_parser",
    "sphinx_design",
    "sphinx_copybutton",
]

# MyST (Markdown) extensions used across the docs.
myst_enable_extensions = [
    "colon_fence",   # ::: fenced directives
    "deflist",       # definition lists
    "fieldlist",
    "substitution",
    "tasklist",
]
# NOTE: the MyST `linkify` extension is intentionally NOT enabled. It turns any
# bare token that looks like a domain into a link, which mis-links the
# reverse-engineering citation shorthand used throughout these pages
# (`ANALYSIS.md`, `RAPTOR-PORTING-GUIDE.md:40`, phase labels like `A.PF`, …) into
# broken `http://…` URLs. Real links use explicit `<url>` autolinks or
# `[text](url)` / reference-style markup.
myst_heading_anchors = 3

templates_path = ["_templates"]
exclude_patterns = []

# Treat every warning as an error is enforced by .readthedocs.yaml
# (fail_on_warning). Keep the tree warning-clean.
nitpicky = False

# Source files may be either reStructuredText or Markdown.
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# -- Options for HTML output -------------------------------------------------

html_theme = "furo"
html_static_path = ["_static"]
html_title = "Open BMC & Firmware"
html_theme_options = {
    "source_repository": "https://github.com/mithro/bmc-open-firmware-docs",
    "source_branch": "main",
    "source_directory": "source/",
}

# -- Link checking -----------------------------------------------------------
# `make linkcheck` / the CI link-check job uses these.
linkcheck_ignore = [
    # Private repository; not reachable from public CI.
    r"https://github\.com/mithro/ai-shenanigans-for-bmcs.*",
    # Google Docs internal references.
    r"https://docs\.google\.com/.*",
    # Valid pages that anti-bot / rate-limit the CI link checker (HTTP 403).
    r"https://developer\.arm\.com/.*",
]
linkcheck_timeout = 15
linkcheck_retries = 2
