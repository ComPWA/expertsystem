# cspell:ignore skipif

import os

import pytest

import expertsystem as es
from expertsystem.reaction import InteractionTypes, StateTransitionManager

RUN_SLOW_TEST_CI_BRANCH = "refs/heads/master"


@pytest.mark.parametrize(
    "formalism_type, n_solutions",
    [
        ("helicity", 14),
        ("canonical-helicity", 100),
    ],
)
def test_simple(formalism_type, n_solutions, particle_database):
    result = es.generate_transitions(
        initial_state=[("Y(4260)", [-1, +1])],
        final_state=["D*(2007)0", "D*(2007)~0"],
        particles=particle_database,
        formalism_type=formalism_type,
        allowed_interaction_types="strong",
        number_of_threads=1,
    )
    assert len(result.solutions) == n_solutions
    model = es.generate_amplitudes(result)
    assert len(model.parameters) == 10


@pytest.mark.skipif(
    os.environ.get("GITHUB_REF", "") != RUN_SLOW_TEST_CI_BRANCH,
    reason="Test takes too long. Can be enabled again after Rule refactoring",
)
@pytest.mark.slow
@pytest.mark.parametrize(
    "formalism_type, n_solutions",
    [
        ("helicity", 14),
        ("canonical-helicity", 100),
    ],
)
def test_full(formalism_type, n_solutions, particle_database):
    stm = StateTransitionManager(
        initial_state=[("Y(4260)", [-1, +1])],
        final_state=["D0", "D~0", "pi0", "pi0"],
        particles=particle_database,
        allowed_intermediate_particles=["D*"],
        formalism_type=formalism_type,
        number_of_threads=1,
    )
    stm.set_allowed_interaction_types([InteractionTypes.Strong])
    stm.add_final_state_grouping([["D0", "pi0"], ["D~0", "pi0"]])
    graph_node_setting_pairs = stm.prepare_graphs()
    result = stm.find_solutions(graph_node_setting_pairs)
    assert len(result.solutions) == n_solutions
    model = es.generate_amplitudes(result)
    assert len(model.parameters) == 10