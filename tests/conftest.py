import pytest

from expertsystem import ui
from expertsystem.particles import ParticleCollection


@pytest.fixture(scope="module")
def particle_database() -> ParticleCollection:
    return ui.load_default_particles()
