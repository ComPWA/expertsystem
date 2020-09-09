# pylint: disable=redefined-outer-name

from math import factorial

import pytest

from expertsystem.state.particle import (
    _safe_set_spin_projections,
    generate_outer_edge_permutations,
    initialize_graph,
)
from expertsystem.topology import (
    InteractionNode,
    SimpleStateTransitionTopologyBuilder,
    Topology,
)


@pytest.fixture(scope="package")
def three_body_decay() -> Topology:
    two_body_decay_node = InteractionNode("TwoBodyDecay", 1, 2)
    simple_builder = SimpleStateTransitionTopologyBuilder(
        [two_body_decay_node]
    )
    all_graphs = simple_builder.build_graphs(1, 3)
    return all_graphs[0]


@pytest.mark.parametrize(
    "final_state_groupings", [[[["pi0", "pi0"]]], [[["gamma", "pi0"]]],],
)
def test_initialize_graph(
    final_state_groupings, three_body_decay, particle_database
):
    graphs = initialize_graph(
        three_body_decay,
        initial_state=[("J/psi(1S)", [-1, +1])],
        final_state=["gamma", "pi0", "pi0"],
        particles=particle_database,
        final_state_groupings=final_state_groupings,
    )
    assert len(graphs) == 4


@pytest.mark.parametrize(
    "initial_state, final_state",
    [
        (["J/psi(1S)"], ["gamma", "pi0", "pi0"]),
        (["J/psi(1S)"], ["K+", "K-", "pi+", "pi-"]),
        (["e+", "e-"], ["gamma", "pi-", "pi+"]),
        (["e+", "e-"], ["K+", "K-", "pi+", "pi-"]),
    ],
)
def test_generate_outer_edge_permutations(
    initial_state, final_state, three_body_decay, particle_database
):
    initial_state_with_spins = _safe_set_spin_projections(
        initial_state, particle_database
    )
    final_state_with_spins = _safe_set_spin_projections(
        final_state, particle_database
    )
    list_of_permutations = list(
        generate_outer_edge_permutations(
            three_body_decay, initial_state_with_spins, final_state_with_spins,
        )
    )
    n_permutations_final_state = factorial(len(final_state))
    n_permutations_initial_state = factorial(len(initial_state))
    n_permutations = n_permutations_final_state * n_permutations_initial_state
    assert len(list_of_permutations) == n_permutations
