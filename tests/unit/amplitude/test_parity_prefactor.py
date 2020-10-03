from typing import NamedTuple

import pytest

from expertsystem import io
from expertsystem.amplitude.helicity_decay import HelicityAmplitudeGenerator
from expertsystem.nested_dicts import InteractionQuantumNumberNames
from expertsystem.state.properties import get_interaction_property
from expertsystem.ui import (
    InteractionTypes,
    StateTransitionManager,
)


class Input(NamedTuple):
    """Helper tuple for tests."""

    initial_state: list
    final_state: list
    intermediate_states: list
    final_state_grouping: list


@pytest.mark.parametrize(
    "test_input, ingoing_state, relative_parity_prefactor",
    [
        (
            Input(
                initial_state=[("J/psi(1S)", [1])],
                final_state=[("gamma", [-1, 1]), ("pi0", [0]), ("pi0", [0])],
                intermediate_states=["f(0)(980)"],
                final_state_grouping=["pi0", "pi0"],
            ),
            "J/psi(1S)",
            1.0,
        ),
        (
            Input(
                initial_state=[("J/psi(1S)", [1])],
                final_state=[("pi0", [0]), ("pi+", [0]), ("pi-", [0])],
                intermediate_states=["rho(770)"],
                final_state_grouping=["pi+", "pi-"],
            ),
            "J/psi(1S)",
            -1.0,
        ),
    ],
)
def test_parity_prefactor(
    test_input: Input,
    ingoing_state: str,
    relative_parity_prefactor: float,
) -> None:
    stm = StateTransitionManager(
        test_input.initial_state,
        test_input.final_state,
        allowed_intermediate_particles=test_input.intermediate_states,
    )
    stm.number_of_threads = 1
    stm.add_final_state_grouping(test_input.final_state_grouping)
    stm.set_allowed_interaction_types([InteractionTypes.EM])
    graph_interaction_settings_groups = stm.prepare_graphs()

    result = stm.find_solutions(graph_interaction_settings_groups)

    for solution in result.solutions:
        in_edge = [
            k
            for k, v in solution.edge_props.items()
            if v["Name"] == ingoing_state
        ]
        assert len(in_edge) == 1
        node_id = solution.edges[in_edge[0]].ending_node_id

        assert isinstance(node_id, int)

        prefactor = get_interaction_property(
            solution.node_props[node_id],
            InteractionQuantumNumberNames.ParityPrefactor,
        )

        assert relative_parity_prefactor == prefactor

    amp_gen = HelicityAmplitudeGenerator()
    amplitude_model = amp_gen.generate(result.solutions)
    io.write(
        instance=amplitude_model,
        filename=f'amplitude_model_prefactor_{"-".join(test_input.intermediate_states)}.xml',
    )

    prefactors = amplitude_model.parameters.filter(
        lambda p: p.name.startswith("PreFactor")
    )
    if len(prefactors) > 0:
        product = 1.0
        for factor in prefactors.values():
            product *= factor.value
        assert relative_parity_prefactor == product
