from codecs import open
from os import path

from setuptools import Extension, find_packages, setup

__version__ = "1.0.1"

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="smaz-py3",
    version=__version__,
    description="Small string compression using smaz, supports Python 3.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/originell/smaz-py3",
    download_url="https://github.com/originell/smaz-py3/tarball/" + __version__,
    license="BSD",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "License :: OSI Approved :: MIT License",
    ],
    keywords="smaz string compression",
    packages=find_packages(exclude=["docs", "tests*"]),
    ext_modules=[
        Extension(
            "smaz", [path.join(here, "smazmodule.c"), path.join(here, "smaz", "smaz.c")]
        )
    ],
    include_package_data=True,
    author="Luis Nell",
    author_email="luis@originell.org",
)
