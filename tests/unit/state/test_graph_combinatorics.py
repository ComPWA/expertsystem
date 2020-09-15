# pylint: disable=redefined-outer-name

from copy import deepcopy
from math import factorial

import pytest

from expertsystem.state.particle import (
    _safe_set_spin_projections,
    generate_kinematic_permutations,
    generate_outer_edge_permutations,
    generate_spin_permutations,
    get_kinematic_representation,
    initialize_graph,
)
from expertsystem.topology import (
    InteractionNode,
    SimpleStateTransitionTopologyBuilder,
    StateTransitionGraph,
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


class TestKinematicRepresentation:
    @staticmethod
    def test_from_graph(three_body_decay):
        graph1 = StateTransitionGraph.from_topology(three_body_decay)
        graph1.edge_props[0] = "J/psi"
        graph1.edge_props[2] = "pi0"
        graph1.edge_props[3] = "pi0"
        graph1.edge_props[4] = "gamma"
        kinematic_representation1 = get_kinematic_representation(graph1)
        assert kinematic_representation1.initial_state == [
            ["J/psi"],
            ["J/psi"],
        ]
        assert kinematic_representation1.final_state == [
            ["gamma", "pi0"],
            ["gamma", "pi0", "pi0"],
        ]

        graph2 = deepcopy(graph1)
        graph2.edge_props[3] = "gamma"
        graph2.edge_props[4] = "pi0"
        kinematic_representation2 = get_kinematic_representation(graph2)
        assert kinematic_representation1 == kinematic_representation2

        graph3 = deepcopy(graph1)
        graph3.edge_props[2] = "pi0"
        graph3.edge_props[3] = "gamma"
        kinematic_representation3 = get_kinematic_representation(graph3)
        assert kinematic_representation2 != kinematic_representation3


def test_generate_permutations(three_body_decay, particle_database):
    graphs = generate_kinematic_permutations(
        three_body_decay,
        initial_state=[("J/psi(1S)", [-1, +1])],
        final_state=["gamma", "pi0", "pi0"],
        particles=particle_database,
    )
    assert len(graphs) == 2
    graph0_final_state_node1 = [
        graphs[0].edge_props[edge_id]
        for edge_id in graphs[0].get_originating_final_state_edges(1)
    ]
    graph1_final_state_node1 = [
        graphs[1].edge_props[edge_id]
        for edge_id in graphs[1].get_originating_final_state_edges(1)
    ]
    assert graph0_final_state_node1 == [
        ("pi0", [0]),
        ("pi0", [0]),
    ]
    assert graph1_final_state_node1 == [
        ("gamma", [-1, 1]),
        ("pi0", [0]),
    ]

    graph0 = graphs[0]
    output_graphs0 = generate_spin_permutations(graph0, particle_database)
    assert len(output_graphs0) == 4
    assert output_graphs0[0].edge_props[0][1] == -1
    assert output_graphs0[0].edge_props[2][1] == -1
    assert output_graphs0[1].edge_props[0][1] == -1
    assert output_graphs0[1].edge_props[2][1] == +1
    assert output_graphs0[2].edge_props[0][1] == +1
    assert output_graphs0[3].edge_props[0][1] == +1
