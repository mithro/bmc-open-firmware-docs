# Contributing

## Building the docs locally

```sh
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
sphinx-build -b html source _build/html      # build
sphinx-build -b linkcheck source _build/link  # link check (CI gate)
```

The Read the Docs build treats warnings as errors (`fail_on_warning`), so keep
the tree warning-clean: every page must be reachable from a `toctree`, and every
cross-reference must resolve.

## Authoring conventions

- **Markdown (MyST)** for prose; use `{doc}` / `{ref}` for cross-references so
  the link checker can validate them.
- **Link everything that is linkable** — files, repos, datasheets, citations,
  and topics documented on other pages. The full policy, with target
  conventions per artifact type and examples, is {doc}`linking`.
- **Dates** are ISO 8601 (`YYYY-MM-DD`).
- Each hardware page follows the shared layout (bus/address → register map →
  reset values → behaviour → datasheet source) so a reader can build both a
  model and a driver from it.
- Pages marked *(planned)* must carry a concrete, CI-verifiable acceptance
  criterion.

## Relationship to the program repository

This public site is authored content plus curated material synced from the
[program repository](https://github.com/mithro/ai-shenanigans-for-bmcs). Reverse-engineering detail derived from proprietary
firmware is only published once cleared; interface contracts and public-datasheet
register maps are published freely so the models and drivers can be built openly.
