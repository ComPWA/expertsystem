import pytest

from expertsystem import io
from expertsystem.particle import Particle, ParticleCollection
from expertsystem.reaction import (
    Result,
    create_isobar_topologies,
    create_n_body_topology,
)
from expertsystem.reaction.topology import StateTransitionGraph, Topology


def test_asdict_fromdict(
    particle_selection: ParticleCollection,
    jpsi_to_gamma_pi_pi_canonical_solutions: Result,
    jpsi_to_gamma_pi_pi_helicity_solutions: Result,
):
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
    # StateTransitionGraph
    result = jpsi_to_gamma_pi_pi_canonical_solutions
    for graph in result.transitions:
        asdict = io.asdict(graph)
        fromdict = io.fromdict(asdict)
        assert isinstance(fromdict, StateTransitionGraph)
        assert graph == fromdict
    result = jpsi_to_gamma_pi_pi_helicity_solutions
    for graph in result.transitions:
        asdict = io.asdict(graph)
        fromdict = io.fromdict(asdict)
        assert isinstance(fromdict, StateTransitionGraph)
        assert graph == fromdict


def test_fromdict_exceptions():
    with pytest.raises(NotImplementedError):
        io.fromdict({"non-sense": 1})
