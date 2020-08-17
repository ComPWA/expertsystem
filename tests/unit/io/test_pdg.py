# pylint: disable=redefined-outer-name
import pytest

from expertsystem import io


@pytest.fixture(scope="module")
def pdg():
    return io.load_pdg()


def test_pdg_size(pdg):
    assert len(pdg) == 532


@pytest.mark.parametrize("name", ["D0", "gamma"])
def test_pdg_entries(pdg, particle_database, name):
    assert particle_database[name] == pdg[name]
