import pytest

from expertsystem import io
from expertsystem.particle import Particle, ParticleCollection


def test_asdict_fromdict(particle_selection: ParticleCollection):
    # ParticleCollection
    asdict = io.asdict(particle_selection)
    fromdict = io.fromdict(asdict)
    assert isinstance(fromdict, ParticleCollection)
    assert particle_selection == fromdict
    # Particle
    for particle in particle_selection:
        asdict = io.asdict(particle)
        fromdict = io.fromdict(asdict)
        assert isinstance(fromdict, Particle)
        assert particle == fromdict


def test_fromdict_exceptions():
    with pytest.raises(NotImplementedError):
        io.fromdict({"non-sense": 1})
