# Changelog

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## 2.0.0 (unreleased)

Upgrade to Python 3.11 or newer before installing 2.0.0. Existing `compress()` and
`decompress()` calls and stored SMAZ data remain compatible with 1.x.
Building from source now requires Rust 1.83 or newer; prebuilt wheels do not
require a Rust compiler.

### Added

- Add compatibility tests and a repeatable benchmark against the original C extension.

### Changed

- Port the codec and Python extension to Rust with PyO3 and maturin, preserving
  the SMAZ wire format and API.
- Improve Python API performance: a local pyperf run on CPython 3.12 and Apple
  Silicon measured a **2.15× geometric mean speedup** over the C extension across
  30 compression/decompression cases. See the
  [benchmark results](benchmarks/README.md#local-pyperf-result-2026-10-11).
- Switch project management to uv with a shared `pyproject.toml` and `uv.lock`.
- Document uv-based development workflow and default tooling.
- Require Python 3.11 or newer and test Python 3.11–3.15, following the upstream
  support lifecycle.
- Consolidate code formatting and linting on Ruff.

### Removed

- Drop Python 3.10 support; it reached end of life on 2026-10-01.

### Fixed

- Reject truncated compressed data with `ValueError`.
- Preserve embedded NUL bytes when decoding externally produced SMAZ data.

## 1.1.3 - 2023-10-24

### Fixed

- Fix a bug preventing installation on Windows
  ([#3](https://github.com/originell/smaz-py3/issues/3)).

Thanks to everyone who reported!

## 1.1.2 - 2023-01-19

### Added

- Python 3.11 support.

## 1.1.1 - 2022-03-23

### Added

- Python 3.10 support.

## 1.1.0 - 2021-08-24

This release does not introduce any new features. Only the way we package smaz-py3 is
updated. The changes should make installation faster and easier for almost everyone.

### Changed

- Switch to building wheels for all popular platforms, including Apple Silicon Macs.

## 1.0.2 - 2021-07-29

### Added

- Python 3.9 support.

## 1.0.1 - 2019-12-25

### Added

- First public release.
