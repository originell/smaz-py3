from os import path

from setuptools import Extension, setup, find_packages

__version__ = "1.1.4"

setup(
    version=__version__,
    packages=find_packages(exclude=["docs", "tests*"]),
    ext_modules=[
        Extension(
            "smaz", ["smazmodule.c", path.join("smaz", "smaz.c")]
        )
    ],
)
