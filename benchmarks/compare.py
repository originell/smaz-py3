"""Run both pyperf suites and optionally enforce a per-case regression limit."""

import argparse
import json
import math
import statistics
import subprocess
import sys
from pathlib import Path

import pyperf

from benchmarks.corpus import CASES, verify_backends


def summarize(reference, rust):
    """Compare mean latency for every expected benchmark; reject partial suites."""
    expected = {
        f"{case} / {operation}"
        for case in CASES
        for operation in ("compress", "decompress")
    }
    for suite in (reference, rust):
        if set(suite.get_benchmark_names()) != expected:
            raise ValueError("Both suites must contain all 30 matching benchmarks")
    results = []
    for case, text in CASES.items():
        for operation in ("compress", "decompress"):
            name = f"{case} / {operation}"
            old = reference.get_benchmark(name)
            new = rust.get_benchmark(name)
            if old.get_unit() != "second" or new.get_unit() != "second":
                raise ValueError(f"{name}: expected latency in seconds")
            old_ns, new_ns = old.mean() * 1e9, new.mean() * 1e9
            results.append(
                {
                    "case": case,
                    "operation": operation,
                    "input_bytes": len(text.encode("utf-8")),
                    "c_ns": old_ns,
                    "rust_ns": new_ns,
                    "speedup": old_ns / new_ns,
                }
            )
    return results


def regressions(results, tolerance):
    return [r for r in results if r["rust_ns"] > r["c_ns"] * (1 + tolerance)]


def compare(args):
    forwarded = args.pyperf_args
    if forwarded[:1] == ["--"]:
        forwarded = forwarded[1:]
    # Reserve pyperf's output and worker options for the orchestrator.
    reserved = ("--backend", "--output", "--append", "--worker", "--pipe")
    if any(a.split("=", 1)[0] in reserved or a.startswith("-o") for a in forwarded):
        raise ValueError(
            "Pass tuning options only; backend and output are managed here"
        )
    paths = [args.output_dir / f"{backend}.json" for backend in ("c", "rust")]
    summary_path = args.json or args.output_dir / "summary.json"
    if summary_path.resolve() in {path.resolve() for path in paths}:
        raise ValueError("The summary path must differ from both pyperf report paths")
    for path in [*paths, summary_path]:
        if path.exists() and not args.overwrite:
            raise FileExistsError(
                f"{path} exists; choose another directory or --overwrite"
            )
    verify_backends()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for backend, path in zip(("c", "rust"), paths):
        if path.exists():
            path.unlink()
        subprocess.run(
            [
                sys.executable,
                "-m",
                "benchmarks.run",
                *forwarded,
                "--backend",
                backend,
                "--output",
                str(path),
            ],
            check=True,
        )
    subprocess.run(
        [sys.executable, "-m", "pyperf", "compare_to", *map(str, paths), "--table"],
        check=True,
    )
    results = summarize(*(pyperf.BenchmarkSuite.load(str(path)) for path in paths))
    geometric_mean = math.exp(statistics.mean(math.log(r["speedup"]) for r in results))
    print(f"Geometric mean C/Rust: {geometric_mean:.2f}x (each row weighted equally)")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(
        json.dumps(
            {
                "statistic": "mean",
                "c_report": str(paths[0]),
                "rust_report": str(paths[1]),
                "max_regression": args.max_regression,
                "geometric_mean_speedup": geometric_mean,
                "results": results,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    failures = regressions(results, args.max_regression)
    if args.check and failures:
        print(
            f"{len(failures)} rows exceed "
            f"{args.max_regression:.0%} regression tolerance:"
        )
        for row in failures:
            print(f"  {row['case']} / {row['operation']}: {row['speedup']:.2f}x C/Rust")
        return 1
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("target/benchmarks"))
    parser.add_argument("--json", type=Path, help="optional summary path")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--max-regression", type=float, default=0.10)
    parser.add_argument(
        "pyperf_args", nargs=argparse.REMAINDER, help="pyperf flags after --"
    )
    args = parser.parse_args()
    if not math.isfinite(args.max_regression) or args.max_regression < 0:
        parser.error("use a finite, nonnegative regression tolerance")
    try:
        return compare(args)
    except (ValueError, FileExistsError, RuntimeError) as error:
        parser.exit(2, f"{error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
