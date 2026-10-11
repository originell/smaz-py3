"""Build the frozen C extension under a separate import name for comparisons."""

import importlib.util
import sys
import sysconfig
from pathlib import Path

from setuptools import Distribution, Extension
from setuptools.command.build_ext import build_ext

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "benchmarks" / "reference"


def build_reference():
    """Compile and load the original wrapper and codec, without changing either."""
    # Each Python ABI needs its own objects; setuptools only checks source mtimes.
    abi = f"{sys.implementation.cache_tag}-{sysconfig.get_platform()}"
    output = ROOT / "target" / "c-reference" / abi
    extension = Extension(
        "smaz_c",
        sources=[
            str(REFERENCE / "smazmodule.c"),
            str(REFERENCE / "smaz" / "smaz.c"),
        ],
        define_macros=[("PyInit_smaz", "PyInit_smaz_c")],
    )
    command = build_ext(Distribution({"ext_modules": [extension]}))
    command.ensure_finalized()
    command.build_lib = str(output)
    command.build_temp = str(output / "temp")
    command.run()
    path = output / ("smaz_c" + sysconfig.get_config_var("EXT_SUFFIX"))
    spec = importlib.util.spec_from_file_location("smaz_c", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    print(build_reference().__file__)
