import pytest

from benchmarks.build_reference import build_reference


@pytest.fixture(scope="session")
def c_reference():
    return build_reference()
