import pytest

from expertsystem import io
from expertsystem.particle import Particle, ParticleCollection
from expertsystem.reaction import (
    create_isobar_topologies,
    create_n_body_topology,
)
from expertsystem.reaction.topology import Topology


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
    # Topology
    for n_final_states in range(2, 6):
        for topology in create_isobar_topologies(n_final_states):
            asdict = io.asdict(topology)
            fromdict = io.fromdict(asdict)
            assert isinstance(fromdict, Topology)
            assert topology == fromdict
        for n_initial_states in range(1, 3):
            topology = create_n_body_topology(n_initial_states, n_final_states)
            asdict = io.asdict(topology)
            fromdict = io.fromdict(asdict)
            assert isinstance(fromdict, Topology)
            assert topology == fromdict


def test_fromdict_exceptions():
    with pytest.raises(NotImplementedError):
        io.fromdict({"non-sense": 1})
