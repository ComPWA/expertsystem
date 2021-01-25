"""."""

import logging
from typing import Dict, Sequence, Tuple

import attr

from .model import Kinematics


@attr.s(frozen=True)
class SubSystem:
    """Represents a part of a decay chain.

    A SubSystem resembles a decaying state and its ingoing and outgoing state.
    It is uniquely defined by:

    Attrs:
        final_states: `tuple` of `tuple` s containing unique ids.
            Represents the final state content of the decay products.
        recoil_state: `tuple` of unique ids representing the recoil partner
            of the decaying state.
        parent_recoil_state: `tuple` of unique ids representing the recoil
            partner of the parent state.
    """

    final_states: Tuple[Tuple[int, ...], ...] = attr.ib()
    recoil_state: Tuple[int, ...] = attr.ib()
    parent_recoil_state: Tuple[int, ...] = attr.ib()


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
            label = "mSq_"
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
            subsystem: SubSystem to which the registered angles correspond.

        Return:
            A pair of `str` keys representing the angles. Can be used as a name
            for `sympy.core.symbol.Symbol`.

        """
        logging.debug("registering helicity angles in kinematics")
        if subsystem not in self.registered_subsystems:
            suffix = ""
            for final_state in subsystem.final_states:
                suffix += "_"
                for particle_uid in final_state:
                    suffix += str(particle_uid) + "+"
                suffix = suffix[:-1]
            if subsystem.recoil_state:
                suffix += "_vs_"
                for particle_uid in subsystem.recoil_state:
                    suffix += str(particle_uid) + "+"
                suffix = suffix[:-1]

            self.registered_subsystems[subsystem] = (
                "theta" + suffix,
                "phi" + suffix,
            )
        return self.registered_subsystems[subsystem]

    def register_subsystem(self, subsystem: SubSystem) -> Tuple[str, ...]:
        r"""Register all kinematic variables of the :class:`~SubSystem`.

        Args:
            subsystem: SubSystem to which the registered kinematic variables
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
