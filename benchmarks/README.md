# C versus Rust benchmarks

After [development setup](../CONTRIBUTING.md#development-setup), run:

```sh
uv run maturin develop --release
uv run python -m benchmarks.compare --check
```

Reports go to `target/benchmarks/c.json`, `rust.json`, and `summary.json`.
Use `--output-dir` to keep another run or `--overwrite` to replace existing
reports. Pass pyperf options after `--`, for example `-- --rigorous`.

`--check` fails if any case's mean latency exceeds C by more than 10%;
`--max-regression 0` removes the tolerance. This check applies independently of
pyperf's statistical significance result. `C/Rust` above 1 means Rust is faster;
the geometric mean weights all cases equally.

## Measurement details

The 30 cases measure Python API latency, including argument and result
conversion. Both backends use identical inputs and must produce identical bytes.
Each runs in separate pyperf workers with calibration and warm-up. Compilation,
imports, and precompression happen outside the timed region; `Runner.timeit()`
avoids an extra Python wrapper call.

The C baseline is unchanged from
[commit 0ec8b64](https://github.com/originell/smaz-py3/commit/0ec8b64c1e062529f178b48d4dc6b02a626fa45c),
compiled with Python's optimized extension flags; only the module initialization
symbol is renamed. The Rust runner requires a release build. Repeated decoder
timings stay below 4096 decoded bytes because the original C wrapper leaks when
growing its buffer. Compatibility tests cover larger inputs separately.

Run on an idle machine, inspect pyperf's stability warnings, and repeat borderline
results. Run benchmarks locally because shared CI runners produce noisy timings.
The JSON reports retain samples and environment/compiler metadata.

## Local pyperf result: 2026-10-11

pyperf 2.10.0, CPython 3.12.11, macOS 27.0.1 (arm64),
Rust 1.98.1 release build, C compiled with `-O3`. Means of 60 values per
case: 20 workers × 3 values, one warm-up per worker, automatic loop calibration
with a 100 ms minimum. All 30 mean latencies were lower than C; geometric mean
speedup: 2.15×. The 10% regression check passed.

pyperf reported instability warnings. Treat these ratios as measurements of this
run, especially the small gains.

| Input | Compression speedup | Decompression speedup |
| --- | ---: | ---: |
| empty | 1.56× | 2.11× |
| one character | 1.45× | 1.51× |
| short word | 1.67× | 1.40× |
| English sentence | 2.13× | 1.33× |
| English paragraph | 1.60× | 1.50× |
| URL | 2.02× | 1.42× |
| numbers | 2.78× | 1.31× |
| Italian | 2.33× | 1.40× |
| Unicode | 4.34× | 1.23× |
| literal run 255 | 8.85× | 1.17× |
| literal run 256 | 9.20× | 1.17× |
| literal run 257 | 9.18× | 1.20× |
| alternating literals | 2.24× | 1.31× |
| English 4 KiB | 2.29× | 1.35× |
| Unicode 4 KiB | 40.19× | 1.04× |
