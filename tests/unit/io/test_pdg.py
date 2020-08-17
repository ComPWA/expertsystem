# pylint: disable=redefined-outer-name
from particle import Particle

import pytest

from expertsystem import io


@pytest.fixture(scope="module")
def pdg():
    return io.load_pdg()


def test_maybe_qq():
    expected_maybe_qq = {
        "a(0)(980)+",
        "a(0)(980)-",
        "a(0)(980)0",
        "f(0)(1500)",
        "f(0)(500)",
        "f(0)(980)",
        "pi(1)(1400)+",
        "pi(1)(1400)-",
        "pi(1)(1400)0",
        "pi(1)(1600)+",
        "pi(1)(1600)-",
        "pi(1)(1600)0",
    }
    maybe_qq_search_results = Particle.findall(
        lambda p: "qq" in p.quarks.lower()
    )
    assert expected_maybe_qq == {item.name for item in maybe_qq_search_results}


def test_pdg_size(pdg):
    assert len(pdg) == 532


@pytest.mark.parametrize("name", ["D0", "gamma"])
def test_pdg_entries(pdg, particle_database, name):
    assert particle_database[name] == pdg[name]