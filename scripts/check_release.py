"""Check release tags and built distributions before granting publish access."""

import argparse
from email.parser import BytesParser
from pathlib import Path
import tarfile
import tomllib
from zipfile import ZipFile

from packaging.utils import (
    canonicalize_name,
    parse_sdist_filename,
    parse_wheel_filename,
)
from packaging.version import Version

ROOT = Path(__file__).resolve().parents[1]


def check_tag(tag, version):
    """Require a v-prefixed tag matching the package's normalized version."""
    if not tag.startswith("v") or Version(tag[1:]) != Version(version):
        raise ValueError(
            f"Release tag {tag!r} must match version {version} (v{version})."
        )


def check_distributions(directory, version, expected_wheels, root=ROOT):
    """Check completeness, metadata, notices, and absence of packaged bytecode."""
    files = sorted(directory.iterdir())
    wheels = [path for path in files if path.suffix == ".whl"]
    sdists = [path for path in files if path.name.endswith(".tar.gz")]
    if len(wheels) != expected_wheels or len(sdists) != 1:
        raise ValueError(
            f"Expected {expected_wheels} wheels and one sdist; "
            f"found {len(wheels)} wheels and {len(sdists)} sdists."
        )
    if len(files) != len(wheels) + len(sdists):
        raise ValueError("Distribution directory contains unexpected files.")

    requires_python = tomllib.loads((root / "pyproject.toml").read_text())["project"][
        "requires-python"
    ]
    for path in wheels + sdists:
        if path.suffix == ".whl":
            name, filename_version, _, _ = parse_wheel_filename(path.name)
            with ZipFile(path) as archive:
                contents = {name: archive.read(name) for name in archive.namelist()}
            metadata_suffix = ".dist-info/METADATA"
        else:
            name, filename_version = parse_sdist_filename(path.name)
            with tarfile.open(path) as archive:
                contents = {
                    member.name: archive.extractfile(member).read()
                    for member in archive.getmembers()
                    if member.isfile()
                }
            metadata_suffix = "/PKG-INFO"

        if canonicalize_name(name) != "smaz-py3" or filename_version != Version(
            version
        ):
            raise ValueError(f"Wrong project or version in filename: {path.name}")
        metadata_files = [name for name in contents if name.endswith(metadata_suffix)]
        if len(metadata_files) != 1:
            raise ValueError(f"Expected one package metadata file in {path.name}")
        metadata = BytesParser().parsebytes(contents[metadata_files[0]])
        if (
            canonicalize_name(metadata["Name"] or "") != "smaz-py3"
            or Version(metadata["Version"]) != Version(version)
            or metadata["Requires-Python"] != requires_python
        ):
            raise ValueError(
                f"Wrong project, version, or Python support in {path.name}"
            )
        for license_name in ("LICENSE", "THIRD_PARTY_LICENSES.txt"):
            matches = [name for name in contents if name.endswith("/" + license_name)]
            if len(matches) != 1 or contents[matches[0]].replace(b"\r\n", b"\n") != (
                root / license_name
            ).read_bytes().replace(b"\r\n", b"\n"):
                raise ValueError(f"Missing or stale {license_name} in {path.name}")
        if any(
            "__pycache__" in name.split("/") or name.endswith((".pyc", ".pyo"))
            for name in contents
        ):
            raise ValueError(f"Packaged Python bytecode in {path.name}")
        print(f"Checked {path.name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", default="")
    parser.add_argument("--dist", type=Path)
    parser.add_argument("--expected-wheels", type=int, default=45)
    args = parser.parse_args()
    version = tomllib.loads((ROOT / "Cargo.toml").read_text())["package"]["version"]
    if args.tag:
        check_tag(args.tag, version)
    if args.dist:
        check_distributions(args.dist, version, args.expected_wheels)
    print(f"Release version: {version}")


if __name__ == "__main__":
    main()
