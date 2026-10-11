"""Measure one backend with pyperf, including Python call and result conversion."""

import subprocess
import sysconfig

import pyperf

from benchmarks.corpus import REFERENCE_COMMIT, load_rust, prepare_inputs


def add_cmdline_args(command, args):
    # pyperf launches fresh workers; preserve the selected backend in each one.
    command.extend(("--backend", args.backend))


def main():
    runner = pyperf.Runner(
        program_args=("-m", "benchmarks.run"), add_cmdline_args=add_cmdline_args
    )
    runner.argparser.add_argument("--backend", choices=("c", "rust"), required=True)
    args = runner.parse_args()
    runner.metadata.update(backend=args.backend, reference_commit=REFERENCE_COMMIT)
    if args.backend == "c":
        from benchmarks.build_reference import build_reference

        module = native = build_reference()
        runner.metadata.update(
            c_compiler=sysconfig.get_config_var("CC") or "platform default",
            c_flags=sysconfig.get_config_var("CFLAGS") or "platform default",
        )
    else:
        module, native = load_rust()
        runner.metadata.update(
            rust_profile=native._build_profile,
            rustc=subprocess.check_output(["rustc", "--version"], text=True).strip(),
        )
    runner.metadata["extension_module"] = native.__file__
    for name, text, encoded in prepare_inputs(module):
        for operation, value in (("compress", text), ("decompress", encoded)):
            runner.timeit(
                f"{name} / {operation}",
                stmt="function(value)",
                setup="function = _function; value = _value",
                globals={"_function": getattr(module, operation), "_value": value},
                metadata={"input_bytes": len(text.encode("utf-8"))},
            )


if __name__ == "__main__":
    main()
