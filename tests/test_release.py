"""Reject inconsistent release artifacts before a publishing job can start."""

import io
import tarfile
from zipfile import ZipFile

import pytest

from scripts.check_release import check_distributions, check_tag


@pytest.fixture
def release_files(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nrequires-python = ">=3.11"\n')
    for name in ("LICENSE", "THIRD_PARTY_LICENSES.txt"):
        (tmp_path / name).write_text(f"{name} text\n")
    dist = tmp_path / "dist"
    dist.mkdir()

    def build(
        *,
        filename_version="1.2.0",
        metadata_version="1.2.0",
        extra=None,
        license_newline=b"\n",
    ):
        metadata = (
            "Metadata-Version: 2.4\nName: smaz-py3\n"
            f"Version: {metadata_version}\nRequires-Python: >=3.11\n\n"
        ).encode()
        licenses = {
            name: (tmp_path / name)
            .read_bytes()
            .replace(b"\r\n", b"\n")
            .replace(b"\n", license_newline)
            for name in ("LICENSE", "THIRD_PARTY_LICENSES.txt")
        }
        info = f"smaz_py3-{filename_version}.dist-info"
        with ZipFile(
            dist / f"smaz_py3-{filename_version}-cp312-cp312-any.whl", "w"
        ) as z:
            z.writestr(f"{info}/METADATA", metadata)
            for name, data in licenses.items():
                z.writestr(f"{info}/licenses/{name}", data)
            if extra:
                z.writestr(*extra)
        with tarfile.open(dist / f"smaz_py3-{filename_version}.tar.gz", "w:gz") as t:
            files = {"PKG-INFO": metadata}
            files.update(licenses)
            for name, data in files.items():
                member = tarfile.TarInfo(f"smaz_py3-{filename_version}/{name}")
                member.size = len(data)
                t.addfile(member, io.BytesIO(data))
        return dist

    return tmp_path, build


@pytest.mark.parametrize("tag", ["v1.2.0", "v1.2.0rc1"])
def test_matching_release_tag(tag):
    check_tag(tag, tag[1:])


@pytest.mark.parametrize("tag", ["1.2.0", "v1.2.1", "vgarbage"])
def test_wrong_release_tag(tag):
    with pytest.raises(ValueError):
        check_tag(tag, "1.2.0")


@pytest.mark.parametrize("license_newline", [b"\n", b"\r\n"])
@pytest.mark.parametrize("source_newline", [b"\n", b"\r\n"])
def test_complete_release(release_files, license_newline, source_newline):
    root, build = release_files
    for name in ("LICENSE", "THIRD_PARTY_LICENSES.txt"):
        path = root / name
        data = path.read_bytes().replace(b"\r\n", b"\n")
        path.write_bytes(data.replace(b"\n", source_newline))
    check_distributions(
        build(license_newline=license_newline), "1.2.0", expected_wheels=1, root=root
    )


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"filename_version": "1.1.0"}, "filename"),
        ({"metadata_version": "1.1.0"}, "Wrong project, version"),
        ({"extra": ("benchmarks/__pycache__/run.pyc", b"bytecode")}, "bytecode"),
    ],
)
def test_inconsistent_artifacts(release_files, kwargs, message):
    root, build = release_files
    with pytest.raises(ValueError, match=message):
        check_distributions(build(**kwargs), "1.2.0", expected_wheels=1, root=root)


def test_missing_wheel(release_files):
    root, build = release_files
    with pytest.raises(ValueError, match="Expected 2 wheels"):
        check_distributions(build(), "1.2.0", expected_wheels=2, root=root)


def test_stale_license(release_files):
    root, build = release_files
    dist = build()
    (root / "THIRD_PARTY_LICENSES.txt").write_text("Updated notices\n")
    with pytest.raises(ValueError, match="Missing or stale THIRD_PARTY_LICENSES"):
        check_distributions(dist, "1.2.0", expected_wheels=1, root=root)


def test_unexpected_artifact(release_files):
    root, build = release_files
    dist = build()
    (dist / "benchmark.json").write_text("{}")
    with pytest.raises(ValueError, match="unexpected files"):
        check_distributions(dist, "1.2.0", expected_wheels=1, root=root)
