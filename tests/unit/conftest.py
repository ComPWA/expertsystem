import pytest

from expertsystem import ui
from expertsystem.data import ParticleCollection
from expertsystem.state.particle import DATABASE


@pytest.fixture(scope="module")
def particle_database() -> ParticleCollection:
    ui.load_default_particle_list()
    return DATABASE
