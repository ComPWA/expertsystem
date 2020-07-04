from os.path import dirname, realpath

import pytest

import expertsystem
from expertsystem.io import (
    load_particle_collection,
    write,
)
from expertsystem.io._yaml._build import _build_spin  # noqa: I202

_PACKAGE_PATH = dirname(realpath(expertsystem.__file__))


def test_not_implemented():
    with pytest.raises(NotImplementedError):
        load_particle_collection(f"{_PACKAGE_PATH}/../README.md")


def test_particle_collection():
    particles = load_particle_collection(
        f"{_PACKAGE_PATH}/../particle_list.yml"
    )
    assert len(particles) == 69
    assert "J/psi" in particles
    j_psi = particles["J/psi"]
    assert j_psi.pid == 443
    assert j_psi.mass == 3.0969
    assert j_psi.width == 9.29e-05
    assert j_psi.spin == 1
    assert j_psi.charge == 0
    assert j_psi.parity == -1
    assert j_psi.cparity == -1
    assert j_psi.gparity == -1
    assert j_psi.isospin is None


@pytest.mark.parametrize(
    "definition", [1, -0.5, {"Value": 2.0}, ["item1", "item2"]]
)
def test_build_spin_exceptions(definition):
    with pytest.raises(ValueError):
        _build_spin(definition)


def test_write_particle_collection():
    particles_imported = load_particle_collection(
        f"{_PACKAGE_PATH}/../particle_list.yml"
    )
    write(particles_imported, "test_particle_list.yml")
    particles_exported = load_particle_collection("test_particle_list.yml")
    assert len(particles_imported) == len(particles_exported)
    for imported, exported in zip(
        particles_imported.values(), particles_exported.values()
    ):
        assert imported == exported
