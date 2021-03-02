# cspell:ignore einsum
"""Kinematics of an amplitude model."""

import logging
import textwrap
from collections import abc
from enum import Enum, auto
from typing import Dict, Iterable, Optional, Sequence, Tuple

import attr
import numpy as np
from numpy.lib.scimath import sqrt as complex_sqrt

from expertsystem.io import convert_to_dot
from expertsystem.particle import Particle
from expertsystem.reaction import (
    ParticleWithSpin,
    StateTransitionGraph,
    Topology,
    create_isobar_topologies,
)

from ._graph_info import determine_attached_final_state


class KinematicsType(Enum):
    HELICITY = auto()


def _determine_default_kinematics(
    kinematics_type: Optional[KinematicsType],
) -> KinematicsType:
    if kinematics_type is None:
        return KinematicsType.HELICITY
    return kinematics_type


@attr.s(frozen=True)
class Kinematics:
    initial_state: Dict[int, Particle] = attr.ib()
    final_state: Dict[int, Particle] = attr.ib()
    type: KinematicsType = attr.ib(  # noqa: A003
        default=KinematicsType.HELICITY,
        converter=_determine_default_kinematics,
    )

    def __attrs_post_init__(self) -> None:
        overlapping_ids = set(self.initial_state) & set(self.final_state)
        if len(overlapping_ids) > 0:
            raise ValueError(
                "Initial and final state have overlapping IDs",
                overlapping_ids,
            )

    @property
    def id_to_particle(self) -> Dict[int, Particle]:
        return {**self.initial_state, **self.final_state}

    @staticmethod
    def from_graph(
        graph: StateTransitionGraph[ParticleWithSpin],
        kinematics_type: Optional[KinematicsType] = None,
    ) -> "Kinematics":
        initial_state = dict()
        for state_id in graph.topology.incoming_edge_ids:
            initial_state[state_id] = graph.get_edge_props(state_id)[0]
        final_state = dict()
        for state_id in graph.topology.outgoing_edge_ids:
            final_state[state_id] = graph.get_edge_props(state_id)[0]
        return Kinematics(
            type=kinematics_type,
            initial_state=initial_state,
            final_state=final_state,
        )


def _to_sorted_tuple(instance: Optional[Iterable[int]]) -> Tuple[int, ...]:
    if instance is None:
        return tuple()
    if not isinstance(instance, abc.Iterable):
        raise TypeError(f"Instance {instance} is not iterable")
    if not all(map(lambda i: isinstance(i, int), instance)):
        raise TypeError(f"Not all items in {instance} are {int.__name__}")
    return tuple(sorted(instance))


def _to_sorted_tuple_pair(
    pair: Tuple[Iterable[int], Iterable[int]],
) -> Tuple[Tuple[int, ...], Tuple[int, ...]]:
    if not len(pair) == 2:
        raise ValueError(f"Pair is length {len(pair)}, should be 2")
    return _to_sorted_tuple(pair[0]), _to_sorted_tuple(pair[1])


@attr.s(frozen=True)
class SubSystem:
    """Represents a part of a decay chain (see `SubSystem.description`)."""

    final_states: Tuple[Tuple[int, ...], Tuple[int, ...]] = attr.ib(
        converter=_to_sorted_tuple_pair
    )
    recoil_state: Tuple[int, ...] = attr.ib(
        factory=tuple, converter=_to_sorted_tuple
    )
    parent_recoil_state: Tuple[int, ...] = attr.ib(
        default=None, converter=_to_sorted_tuple
    )

    def __attrs_post_init__(self) -> None:
        angle_group, remnant = self.final_states
        common_items = set(angle_group) & set(remnant)
        common_items |= set(angle_group) & set(self.recoil_state)
        common_items |= set(remnant) & set(self.recoil_state)
        if len(common_items) != 0:
            raise ValueError(f"{self} and has common items {common_items}")

    @property
    def description(self) -> str:
        """Get a helicity angle description for this `SubSystem`.

        Definition is as follows:

        .. image:: /usage/physics/helicity_angles.svg
            :align: center
            :alt: 5-body decay illustration for helicity angle description
            :width: 300 px

        ==================  ==============================================================
        Description         Meaning
        ==================  ==============================================================
        ``"1+2+3_4+5"``     Angle of **B** in restframe of **A**
        ``"1+2_3_vs_4+5"``  Angle of **D** in restframe of **B** with **C** as recoil of B
        ``"1_2_vs_3"``      Angle of **1** in restframe of **D** with **3** as recoil of D
        ``"4_5_vs_1+2+3"``  Angle of **4** in restframe of **C** with **B** as recoil of C
        ==================  ==============================================================

        These cases are constructed in a `SubSystem` as follows:

        >>> from expertsystem.amplitude.kinematics import SubSystem
        >>> SubSystem(final_states=[[1, 2, 3], [4, 5]]).description
        '1+2+3_4+5'
        >>> SubSystem(
        ...     final_states=[[1, 2], [3]],
        ...     recoil_state=[4, 5],
        ... ).description
        '1+2_3_vs_4+5'
        >>> SubSystem(
        ...     final_states=[[1], [2]],
        ...     recoil_state=[3],
        ... ).description
        '1_2_vs_3'
        >>> SubSystem(
        ...     final_states=[[4], [5]],
        ...     recoil_state=[1, 2, 3],
        ... ).description
        '4_5_vs_1+2+3'
        """
        angle_group, remnant = self.final_states
        description = "+".join(str(i) for i in angle_group)
        if remnant:
            description += "_"
            description += "+".join(str(i) for i in remnant)
        if self.recoil_state:
            description += "_vs_"
            description += "+".join(str(i) for i in self.recoil_state)
        return description


@attr.s(on_setattr=attr.setters.frozen)
class HelicityKinematics:
    """Kinematics of the helicity formalism.

    General usage is

        1. Register kinematic variables via the three methods
           (:meth:`register_invariant_mass`, :meth:`register_helicity_angles`,
           :meth:`register_subsystem`) first.
        2. Then convert events to these kinematic variables.
    """

    registered_inv_masses: Dict[Tuple[int, ...], str] = attr.ib(
        default=dict(), init=False
    )
    registered_subsystems: Dict[SubSystem, Tuple[str, str]] = attr.ib(
        default=dict(), init=False
    )

    def register_invariant_mass(self, final_state: Sequence[int]) -> str:
        """Register an invariant mass :math:`s`.

        Args:
            final_state: collection of particle unique id's

        Return:
            A `str` key representing the invariant mass. Can be used as a name
            for `sympy.core.symbol.Symbol`.

        """
        logging.debug("registering invariant mass in kinematics")
        _final_state: tuple = tuple(sorted(final_state))
        if _final_state not in self.registered_inv_masses:
            label = "m_"
            for particle_uid in _final_state:
                label += str(particle_uid) + "+"
            label = label[:-1]
            self.registered_inv_masses[_final_state] = label
        return self.registered_inv_masses[_final_state]

    def register_helicity_angles(
        self, subsystem: SubSystem
    ) -> Tuple[str, str]:
        r"""Register helicity angles :math:`(\theta, \phi)` of a `SubSystem`.

        Args:
            subsystem: `SubSystem` to which the registered angles correspond.

        Return:
            A pair of `str` keys representing the angles. Can be used as a name
            for `sympy.core.symbol.Symbol`.

        """
        logging.debug("registering helicity angles in kinematics")
        if subsystem not in self.registered_subsystems:
            self.registered_subsystems[subsystem] = (
                f"theta_{subsystem.description}",
                f"phi_{subsystem.description}",
            )
        return self.registered_subsystems[subsystem]

    def register_subsystem(self, subsystem: SubSystem) -> Tuple[str, ...]:
        r"""Register all kinematic variables of the `SubSystem`.

        Args:
            subsystem: `SubSystem` to which the registered kinematic variables
                correspond.

        Return:
            A tuple of `str` keys representing the :math:`(s, \theta, \phi)`.
            Can be used as a name for `sympy.core.symbol.Symbol`.

        """
        state_fs: list = []
        for fs_uid in subsystem.final_states:
            state_fs += fs_uid
        invmass_name = self.register_invariant_mass(list(set(state_fs)))
        angle_names = self.register_helicity_angles(subsystem)
        return (invmass_name,) + angle_names


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
            if len(in_edges) != 1:
                raise ValueError(
                    f"Not an isobar topology: edge {edge.originating_node_id}"
                    f" has {len(in_edges)} incoming edges"
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


def generate_kinematic_variables(
    decay_products_final_state_ids: Tuple[Tuple[int, ...], Tuple[int, ...]],
    recoil_final_state_ids: Tuple[int, ...],
    parent_recoil_final_state_ids: Tuple[int, ...],
) -> Tuple[str, str, str]:
    """Generate kinematic sympy variables of a helicity decay.

    Kinematic variables are:
    - invariant mass
    - helicity angle theta
    - helicity angle phi
    """
    kinematics = HelicityKinematics()
    subsystem = SubSystem(
        final_states=decay_products_final_state_ids,
        recoil_state=recoil_final_state_ids,
        parent_recoil_state=parent_recoil_final_state_ids,
    )
    inv_mass, theta, phi = kinematics.register_subsystem(subsystem)
    return inv_mass, theta, phi
