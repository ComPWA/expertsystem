"""Kinematics of an amplitude model."""

import logging
from collections import abc
from typing import Dict, Iterable, Optional, Sequence, Tuple

import attr

from .model import Kinematics


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

    reaction_info: Kinematics = attr.ib()
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
