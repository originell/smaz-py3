# Contributing to smaz-py3

This guide covers building from source, making changes, and running the tests.
For installation and usage examples, see [README.md](README.md).

## Development setup

Install [Rust](https://rustup.rs/) 1.83 or newer and
[uv](https://docs.astral.sh/uv/) 0.13.0 or newer. `uv sync` installs Python if a
compatible version isn't available. This project supports Python 3.11–3.15.

The compatibility tests also need a C compiler:

- **macOS:** install Xcode Command Line Tools with `xcode-select --install`.
- **Linux:** install GCC or Clang, plus Python development headers if your
  distribution packages them separately.
- **Windows:** install [Microsoft C++ Build Tools](https://learn.microsoft.com/en-us/cpp/overview/acquire-msvc)
  with the **Desktop development with C++** workload.

Clone the repository and create the development environment:

```sh
git clone https://github.com/originell/smaz-py3.git
cd smaz-py3
uv sync
```

`uv sync` builds the Rust extension in release mode and installs the development
tools.

Enable the project's commit and push checks with the locked
[prek](https://prek.j178.dev/) installation:

```sh
uv run --no-sync prek install
```

## Finding the source

- `src/codec.rs` contains the compression and decompression algorithms.
- `src/codebook.rs` contains the SMAZ dictionary.
- `src/lib.rs` exposes the Python API through PyO3.
- `tests/` contains Python API and compatibility tests. Rust unit tests live
  alongside the codec.

Keep `benchmarks/reference/` unchanged: the tests use that original C
implementation to check compatibility.

## Making and checking changes

After editing Rust source, rebuild the extension so Python uses your changes,
then run the Python and Rust tests:

```sh
uv run maturin develop --release
uv run pytest
cargo test --locked
```

Format your changes with:

```sh
uv run ruff format .
cargo fmt
```

Run the checks before submitting a change:

```sh
uv run --no-sync prek run --all-files
uv run --no-sync prek run --all-files --stage pre-push
```

## Benchmarks

See [benchmarks/README.md](benchmarks/README.md) for running benchmarks and
interpreting the results.

## Building distributions

Build distributable wheels and a source archive with:

```sh
uv run maturin build --release --locked
uv run maturin sdist
```

For the account settings and approval steps used to publish a release, see
[RELEASING.md](https://github.com/originell/smaz-py3/blob/main/RELEASING.md).

## Changing Rust dependencies

After changing Rust dependencies, refresh their license notices:

```sh
cargo fetch --locked
uv run python scripts/update_licenses.py
```
