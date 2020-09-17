# pylint: disable=redefined-outer-name
import logging

import pytest

from expertsystem.amplitude.canonical_decay import CanonicalAmplitudeGenerator
from expertsystem.amplitude.helicity_decay import HelicityAmplitudeGenerator
from expertsystem.topology import Topology
from expertsystem.ui import (
    InteractionTypes,
    StateTransitionManager,
)


logging.basicConfig(level=logging.ERROR)


@pytest.fixture(scope="module")
def jpsi_to_gamma_pi_pi_canonical_solutions():
    stm = StateTransitionManager(
        initial_state=[("J/psi(1S)", [-1, 1])],
        final_state=["gamma", "pi0", "pi0"],
        allowed_intermediate_particles=["f(0)(980)", "f(0)(1500)"],
        formalism_type="canonical-helicity",
    )
    stm.set_allowed_interaction_types([InteractionTypes.EM])
    graph_interaction_settings_groups = stm.prepare_graphs()
    solutions, _ = stm.find_solutions(graph_interaction_settings_groups)
    return solutions


@pytest.fixture(scope="module")
def jpsi_to_gamma_pi_pi_helicity_solutions():
    stm = StateTransitionManager(
        initial_state=[("J/psi(1S)", [-1, 1])],
        final_state=["gamma", "pi0", "pi0"],
        allowed_intermediate_particles=["f(0)(980)", "f(0)(1500)"],
    )
    stm.set_allowed_interaction_types(
        [InteractionTypes.Strong, InteractionTypes.EM]
    )
    graph_interaction_settings_groups = stm.prepare_graphs()
    solutions, _ = stm.find_solutions(graph_interaction_settings_groups)
    return solutions


@pytest.fixture(scope="module")
def jpsi_to_gamma_pi_pi_canonical_amplitude_generator(
    jpsi_to_gamma_pi_pi_canonical_solutions,
):
    amplitude_generator = CanonicalAmplitudeGenerator()
    amplitude_generator.generate(jpsi_to_gamma_pi_pi_canonical_solutions)
    return amplitude_generator


@pytest.fixture(scope="module")
def jpsi_to_gamma_pi_pi_helicity_amplitude_generator(
    jpsi_to_gamma_pi_pi_helicity_solutions,
):
    amplitude_generator = HelicityAmplitudeGenerator()
    amplitude_generator.generate(jpsi_to_gamma_pi_pi_helicity_solutions)
    return amplitude_generator


@pytest.fixture(scope="package")
def dummy_topology():
    r"""Create a dummy `Topology`.

    Has the following shape:

    .. code-block::

        e0 -- (N0) -- e1 -- (N1) -- e3
                \             \
                 e2            e4
    """
    topology = Topology()
    topology.add_node(0)
    topology.add_node(1)
    topology.add_edges([0, 1, 2, 3, 4])
    topology.attach_edges_to_node_ingoing([0], 0)
    topology.attach_edges_to_node_ingoing([1], 1)
    topology.attach_edges_to_node_outgoing([1, 2], 0)
    topology.attach_edges_to_node_outgoing([3, 4], 1)
    return topology
