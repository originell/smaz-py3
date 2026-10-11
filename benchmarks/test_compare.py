import argparse
import json
from pathlib import Path

import pyperf
import pytest

from benchmarks import compare
from benchmarks.corpus import CASES


def suite(latency=1e-6, *, omit=None, extra=False, unit="second", reverse=False):
    names = [
        f"{case} / {operation}"
        for case in CASES
        for operation in ("compress", "decompress")
    ]
    if extra:
        names.append("unexpected / compress")
    if reverse:
        names.reverse()
    return pyperf.BenchmarkSuite(
        [
            pyperf.Benchmark(
                [
                    pyperf.Run(
                        [latency * 0.9, latency * 1.1],
                        metadata={"name": name, "unit": unit},
                        collect_metadata=False,
                    )
                ]
            )
            for name in names
            if name != omit
        ]
    )


def test_summary_matches_names_and_uses_mean():
    results = compare.summarize(suite(2e-6), suite(reverse=True))
    assert len(results) == 30
    assert all(row["c_ns"] == pytest.approx(2000) for row in results)
    assert all(row["speedup"] == pytest.approx(2) for row in results)


@pytest.mark.parametrize("options", [{"omit": "empty / compress"}, {"extra": True}])
def test_incomplete_or_mismatched_suites_fail(options):
    with pytest.raises(ValueError, match="matching benchmarks"):
        compare.summarize(suite(), suite(**options))


def test_memory_measurements_are_rejected():
    with pytest.raises(ValueError, match="latency in seconds"):
        compare.summarize(suite(), suite(unit="byte"))


def test_gate_checks_every_row_even_with_overall_speedup():
    rows = [{"c_ns": 100, "rust_ns": 50} for _ in range(29)]
    boundary = {"c_ns": 100, "rust_ns": 110}
    slower = {"c_ns": 100, "rust_ns": 111}
    assert compare.regressions([*rows, boundary], 0.10) == []
    assert compare.regressions([*rows, slower], 0.10) == [slower]
    assert compare.regressions([boundary], 0) == [boundary]


def test_orchestrator_writes_reports_and_fails_regression_gate(
    tmp_path, monkeypatch, capsys
):
    monkeypatch.setattr(compare, "verify_backends", lambda: None)
    commands = []

    def run(command, *, check):
        assert check
        commands.append(command)
        if "benchmarks.run" in command:
            backend = command[command.index("--backend") + 1]
            output = command[command.index("--output") + 1]
            suite(1e-6 if backend == "c" else 1.2e-6).dump(output)

    monkeypatch.setattr(compare.subprocess, "run", run)
    args = argparse.Namespace(
        output_dir=tmp_path,
        json=None,
        overwrite=False,
        check=True,
        max_regression=0.10,
        pyperf_args=["--", "--fast"],
    )
    assert compare.compare(args) == 1
    assert "30 rows exceed 10% regression tolerance" in capsys.readouterr().out
    assert len(commands) == 3
    assert all("--fast" in command for command in commands[:2])
    assert {path.name for path in tmp_path.iterdir()} == {
        "c.json",
        "rust.json",
        "summary.json",
    }
    summary = json.loads((tmp_path / "summary.json").read_text())
    assert summary["statistic"] == "mean"
    assert len(summary["results"]) == 30
    assert all(row["speedup"] < 1 for row in summary["results"])
    with pytest.raises(FileExistsError, match="exists"):
        compare.compare(args)
    assert len(commands) == 3
    args.check = False
    args.overwrite = True
    assert compare.compare(args) == 0


@pytest.mark.parametrize("flag", ["--backend=c", "-oother.json", "--append"])
def test_reserved_runner_options_are_rejected(flag):
    args = argparse.Namespace(pyperf_args=["--", flag])
    with pytest.raises(ValueError, match="managed here"):
        compare.compare(args)


def test_summary_cannot_replace_native_report(tmp_path):
    args = argparse.Namespace(
        output_dir=tmp_path,
        json=Path(tmp_path / "c.json"),
        pyperf_args=[],
    )
    with pytest.raises(ValueError, match="must differ"):
        compare.compare(args)
