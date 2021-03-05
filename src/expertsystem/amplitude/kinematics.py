# cspell:ignore einsum
"""Kinematics of an amplitude model in the helicity formalism."""

import textwrap
from typing import Dict, Set, Tuple

import attr
import numpy as np
from numpy.lib.scimath import sqrt as complex_sqrt

from expertsystem.io import convert_to_dot
from expertsystem.particle import Particle
from expertsystem.reaction import Topology, create_isobar_topologies
from expertsystem.reaction.quantum_numbers import ParticleWithSpin
from expertsystem.reaction.topology import FrozenDict, StateTransitionGraph

from ._graph_info import assert_isobar_topology, determine_attached_final_state


@attr.s(frozen=True)
class ReactionInfo:
    initial_state: FrozenDict[int, Particle] = attr.ib(converter=FrozenDict)
    final_state: FrozenDict[int, Particle] = attr.ib(converter=FrozenDict)

    def __attrs_post_init__(self) -> None:
        initial_state_ids = set(self.initial_state)
        final_state_ids = set(self.final_state)
        if initial_state_ids & final_state_ids:
            raise ValueError(
                f"Initial state IDs {initial_state_ids} overlap"
                f" with final state IDs {final_state_ids}"
            )
        particles = {
            *self.initial_state.values(),
            *self.final_state.values(),
        }
        if not all(map(lambda p: isinstance(p, Particle), particles)):
            raise ValueError(
                f"Not all items in state ID mappings are {Particle.__name__}"
            )

    @staticmethod
    def from_graph(
        graph: StateTransitionGraph[ParticleWithSpin],
    ) -> "ReactionInfo":
        return ReactionInfo(
            initial_state={
                i: graph.get_edge_props(i)[0]
                for i in graph.topology.incoming_edge_ids
            },
            final_state={
                i: graph.get_edge_props(i)[0]
                for i in graph.topology.outgoing_edge_ids
            },
        )


@attr.s(on_setattr=attr.setters.frozen)
class HelicityKinematics:
    """Converter for four-momenta to kinematic variable data.

    The `.convert` method forms the bridge between four-momentum data for the
    decay you are studying and the kinematic variables that are in the
    `.HelicityModel`. These are invariant mass and the :math:`theta` and
    :math:`phi` helicity angles.
    """

    final_state_ids: Tuple[int, ...] = attr.ib(factory=tuple, init=False)
    registered_topologies: Set[Topology] = attr.ib(factory=set, init=False)

    def register_topology(self, topology: Topology) -> None:
        if len(self.registered_topologies) == 0:
            object.__setattr__(
                self,
                "final_state_ids",
                tuple(sorted(topology.outgoing_edge_ids)),
            )
        if len(topology.incoming_edge_ids) != 1:
            raise ValueError(
                f"Topology has {len(topology.incoming_edge_ids)} incoming"
                " edges, so is not isobar"
            )
        if len(self.registered_topologies) != 0:
            existing_topology = next(iter(self.registered_topologies))
            if (
                (
                    topology.incoming_edge_ids
                    != existing_topology.incoming_edge_ids
                )
                or (
                    topology.outgoing_edge_ids
                    != existing_topology.outgoing_edge_ids
                )
                or (
                    topology.outgoing_edge_ids
                    != existing_topology.outgoing_edge_ids
                )
                or (topology.nodes != existing_topology.nodes)
            ):
                raise ValueError("Edge or node IDs of topology do not match")
        self.registered_topologies.add(topology)

    def convert(
        self, momentum_pool: Dict[int, np.ndarray]
    ) -> Dict[str, np.ndarray]:
        output = dict()
        for topology in self.registered_topologies:
            output.update(compute_helicity_angles(momentum_pool, topology))
            output.update(compute_invariant_masses(momentum_pool, topology))
        return output


def get_helicity_angle_label(
    topology: Topology, edge_id: int
) -> Tuple[str, str]:
    """Generate labels that can be used to identify helicity angles.

    >>> from expertsystem.amplitude.kinematics import get_helicity_angle_label
    >>> from expertsystem.reaction import create_isobar_topologies
    >>> topologies = create_isobar_topologies(5)
    >>> topology = topologies[0]
    >>> for i in topology.intermediate_edge_ids | topology.outgoing_edge_ids:
    ...     phi_label, theta_label = get_helicity_angle_label(topology, i)
    ...     print(f"{i}: '{phi_label}'")
    0: 'phi_0,0+3+4'
    1: 'phi_1,1+2'
    2: 'phi_2,1+2'
    3: 'phi_3,3+4,0+3+4'
    4: 'phi_4,3+4,0+3+4'
    5: 'phi_0+3+4'
    6: 'phi_1+2'
    7: 'phi_3+4,0+3+4'
    >>> topology = topologies[1]
    >>> for i in topology.intermediate_edge_ids | topology.outgoing_edge_ids:
    ...     phi_label, theta_label = get_helicity_angle_label(topology, i)
    ...     print(f"{i}: '{phi_label}'")
    0: 'phi_0,0+1'
    1: 'phi_1,0+1'
    2: 'phi_2,2+3+4'
    3: 'phi_3,3+4,2+3+4'
    4: 'phi_4,3+4,2+3+4'
    5: 'phi_0+1'
    6: 'phi_2+3+4'
    7: 'phi_3+4,2+3+4'
    """
    assert_isobar_topology(topology)

    def recursive_label(topology: Topology, edge_id: int) -> str:
        edge = topology.edges[edge_id]
        if edge.ending_node_id is None:
            label = f"{edge_id}"
        else:
            attached_final_state_ids = determine_attached_final_state(
                topology, edge_id
            )
            label = "+".join(map(str, attached_final_state_ids))
        if edge.originating_node_id is not None:
            in_edges = topology.get_edge_ids_ingoing_to_node(
                edge.originating_node_id
            )
            in_edge_id = next(iter(in_edges))
            if in_edge_id not in topology.incoming_edge_ids:
                label += f",{recursive_label(topology, in_edge_id)}"
        return label

    label = recursive_label(topology, edge_id)
    return f"phi_{label}", f"theta_{label}"


assert get_helicity_angle_label.__doc__ is not None
get_helicity_angle_label.__doc__ += f"""

.. panels::
  :body: text-center

  .. graphviz::

    {textwrap.indent(convert_to_dot(create_isobar_topologies(5)[0]), '    ')}

  :code:`topologies[0]`

  ---

  .. graphviz::

    {textwrap.indent(convert_to_dot(create_isobar_topologies(5)[1]), '    ')}

  :code:`topologies[1]`
"""


def compute_helicity_angles(  # pylint: disable=too-many-locals
    momentum_pool: Dict[int, np.ndarray], topology: Topology
) -> Dict[str, np.ndarray]:
    if topology.outgoing_edge_ids != set(momentum_pool):
        raise ValueError(
            f"Momentum IDs {set(momentum_pool)} do not match "
            f"final state edge IDs {set(topology.outgoing_edge_ids)}"
        )

    def __recursive_helicity_angles(  # pylint: disable=too-many-locals
        momentum_pool: Dict[int, np.ndarray], node_id: int
    ) -> Dict[str, np.ndarray]:
        helicity_angles: Dict[str, np.ndarray] = {}
        child_edge_ids = sorted(
            topology.get_edge_ids_outgoing_from_node(node_id)
        )
        if all(
            topology.edges[i].ending_node_id is None for i in child_edge_ids
        ):
            edge_id = child_edge_ids[0]
            four_momentum = momentum_pool[edge_id]
            phi_label, theta_label = get_helicity_angle_label(
                topology, edge_id
            )
            helicity_angles[phi_label] = compute_phi(four_momentum)
            helicity_angles[theta_label] = compute_theta(four_momentum)
        for edge_id in child_edge_ids:
            edge = topology.edges[edge_id]
            if edge.ending_node_id is not None:
                # recursively determine all momenta ids in the list
                sub_momenta_ids = determine_attached_final_state(
                    topology, edge_id
                )
                if len(sub_momenta_ids) > 1:
                    # add all of these momenta together -> defines new subsystem
                    four_momentum = sum(  # type: ignore
                        momentum_pool[i] for i in sub_momenta_ids
                    )

                    # boost all of those momenta into this new subsystem
                    phi = compute_phi(four_momentum)
                    theta = compute_theta(four_momentum)
                    p3_norm = np.sqrt(np.sum(four_momentum[1:] ** 2, axis=0))
                    beta = p3_norm / four_momentum[0]
                    new_momentum_pool = {
                        k: np.einsum(
                            "ij...,j...",
                            get_boost_z_matrix(beta),
                            np.einsum(
                                "ij...,j...",
                                get_rotation_matrix_y(-theta),
                                np.einsum(
                                    "ij...,j...",
                                    get_rotation_matrix_z(-phi),
                                    v,
                                ).T,
                            ).T,
                        ).T
                        for k, v in momentum_pool.items()
                        if k in sub_momenta_ids
                    }

                    # register current angle variables
                    phi_label, theta_label = get_helicity_angle_label(
                        topology, edge_id
                    )
                    helicity_angles[phi_label] = compute_phi(four_momentum)
                    helicity_angles[theta_label] = compute_theta(four_momentum)

                    # call next recursion
                    angles = __recursive_helicity_angles(
                        new_momentum_pool,
                        edge.ending_node_id,
                    )
                    helicity_angles.update(angles)

        return helicity_angles

    initial_state_id = next(iter(topology.incoming_edge_ids))
    initial_state_edge = topology.edges[initial_state_id]
    assert initial_state_edge.ending_node_id is not None
    return __recursive_helicity_angles(
        momentum_pool, initial_state_edge.ending_node_id
    )


def compute_phi(state: np.ndarray) -> np.ndarray:
    return np.arctan2(state[2], state[1])


def compute_theta(state: np.ndarray) -> np.ndarray:
    p3_norm = np.sqrt(np.sum(state[1:] ** 2, axis=0))
    return np.arccos(state[3] / p3_norm)


def get_boost_z_matrix(beta: np.ndarray) -> np.ndarray:
    n_events = len(beta)
    gamma = 1 / np.sqrt(1 - beta ** 2)
    zeros = np.zeros(n_events)
    ones = np.ones(n_events)
    return np.array(
        [
            [gamma, zeros, zeros, -gamma * beta],
            [zeros, ones, zeros, zeros],
            [zeros, zeros, ones, zeros],
            [-gamma * beta, zeros, zeros, gamma],
        ]
    )


def get_rotation_matrix_z(angle: np.ndarray) -> np.ndarray:
    n_events = len(angle)
    zeros = np.zeros(n_events)
    ones = np.ones(n_events)
    return np.array(
        [
            [ones, zeros, zeros, zeros],
            [zeros, np.cos(angle), -np.sin(angle), zeros],
            [zeros, np.sin(angle), np.cos(angle), zeros],
            [zeros, zeros, zeros, ones],
        ]
    )


def get_rotation_matrix_y(angle: np.ndarray) -> np.ndarray:
    n_events = len(angle)
    zeros = np.zeros(n_events)
    ones = np.ones(n_events)
    return np.array(
        [
            [ones, zeros, zeros, zeros],
            [zeros, np.cos(angle), zeros, np.sin(angle)],
            [zeros, zeros, ones, zeros],
            [zeros, -np.sin(angle), zeros, np.cos(angle)],
        ]
    )


def get_invariant_mass_label(topology: Topology, edge_id: int) -> str:
    final_state_ids = determine_attached_final_state(topology, edge_id)
    return f"m_{''.join(map(str, sorted(final_state_ids)))}"


def compute_invariant_masses(
    momentum_pool: Dict[int, np.ndarray], topology: Topology
) -> Dict[str, np.ndarray]:
    """Compute the invariant masses for all final state combinations."""
    if topology.outgoing_edge_ids != set(momentum_pool):
        raise ValueError(
            f"Momentum IDs {set(momentum_pool)} do not match "
            f"final state edge IDs {set(topology.outgoing_edge_ids)}"
        )
    invariant_masses = dict()
    for edge_id in topology.edges:
        attached_edge_ids = determine_attached_final_state(topology, edge_id)
        total_momentum: np.ndarray = sum(  # type: ignore
            momentum_pool[i] for i in attached_edge_ids
        )
        values = compute_invariant_mass(total_momentum)
        name = get_invariant_mass_label(topology, edge_id)
        invariant_masses[name] = values
    return invariant_masses


def compute_invariant_mass(four_momenta: np.ndarray) -> np.ndarray:
    return complex_sqrt(
        four_momenta[0] ** 2 - np.sum(four_momenta[1:] ** 2, axis=0)
    )
