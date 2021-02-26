# cspell:ignore rpow rtruediv
# pylint: disable=line-too-long,no-self-use,unused-argument
"""Kinematics of an amplitude model."""

import logging
from collections import abc
from enum import Enum, auto
from functools import reduce
from typing import Any, Dict, Iterable, Optional, Sequence, Set, Tuple

import attr
import sympy as sy
from sympy.printing.latex import LatexPrinter

from expertsystem.amplitude.sympy_wrappers import (
    UnevaluatedExpression,
    implement_expr,
    implement_mat_expr,
)
from expertsystem.particle import Particle
from expertsystem.reaction import ParticleWithSpin, StateTransitionGraph


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


class Metric(sy.MatrixExpr):  # pylint: disable=abstract-method
    __metric = sy.diag(1, -1, -1, -1)

    def __new__(cls: type, *args: Any, **hints: Any) -> "Metric":
        evaluate = hints.get("evaluate", False)
        if evaluate:
            return sy.MatrixExpr.__new__(cls, *args).evaluate()  # type: ignore  # pylint: disable=no-member
        return sy.MatrixExpr.__new__(cls, *args)

    def evaluate(self) -> sy.Expr:
        return self.__metric

    @property
    def shape(self) -> Tuple[int, int]:
        return (4, 4)

    def doit(self, **hints: Any) -> sy.Expr:
        return self.__metric

    def _latex(self, printer: LatexPrinter, *args: Any) -> str:
        return R"\boldsymbol{\eta}"


class LorentzVector(sy.MatrixSymbol):
    __metric = Metric()

    def __new__(cls: type, *args: Any) -> "LorentzVector":
        if len(args) < 1:
            raise ValueError("Name required")
        name = args[0]
        if not isinstance(name, (str, sy.core.symbol.Str)):
            raise TypeError(
                f"{name} is of type {type(name)} not of type {str.__name__}"
            )
        name = str(name)
        return sy.MatrixSymbol.__new__(cls, name, 4, 1)

    def __abs__(self) -> sy.Expr:
        return self.norm()

    def dot(self, other: "LorentzVector") -> sy.Expr:
        return sy.Mul(self.T, self.__metric, other)

    def norm(self) -> sy.Expr:
        return sy.sqrt(self.norm_squared())

    def norm_squared(self) -> sy.Expr:
        return self.dot(self)

    def _latex(self, printer: LatexPrinter, *args: Any) -> str:
        return fR"\mathbf{{{self.name}}}"

    def __rpow__(self, other: sy.Expr) -> sy.MatrixExpr:
        return self ** other

    def __rtruediv__(self, other: sy.Expr) -> sy.MatrixExpr:
        return self / other


@implement_expr(n_args=1)
class P3Norm(UnevaluatedExpression):
    @property
    def vector(self) -> "LorentzVector":
        return self.args[0]

    def evaluate(self) -> sy.Expr:
        vector3 = self.vector[1:]
        return (vector3.T * vector3)[0]

    def _latex(self, printer: LatexPrinter, *args: Any) -> str:
        args = tuple(map(printer._print, self.args))
        arg = args[0]
        return fR"\left|\vec{{{arg}}}\right|"


@implement_mat_expr(name=R"\Lambda", n_args=1, shape=(4, 4))
class BoostMatrix(sy.MatrixExpr):  # pylint: disable=abstract-method
    def evaluate(self) -> sy.Expr:
        vector = self.vector
        beta = vector[1:, :] / vector[0]
        gamma = 1 / sy.sqrt(1 - (beta.T * beta)[0])
        b_matrix = gamma * beta
        m_matrix = sy.eye(3) + (gamma - 1) * (b_matrix * b_matrix.T)
        # composition of sub-matrices results is shape (2,2) not (4, 4)
        return sy.Matrix(
            [
                [gamma, *(-b_matrix)],
                [-b_matrix[0], *(m_matrix[0, :])],
                [-b_matrix[1], *(m_matrix[1, :])],
                [-b_matrix[2], *(m_matrix[2, :])],
            ]
        )

    @property
    def vector(self) -> sy.MatrixSymbol:
        return self.args[0]


@implement_mat_expr(name=R"\Lambda_z", n_args=1, shape=(4, 4))
class BoostZ(sy.MatrixExpr):  # pylint: disable=abstract-method
    def evaluate(self) -> sy.Expr:
        beta = self.beta
        gamma = 1 / sy.sqrt(1 - beta ** 2)
        return sy.Matrix(
            [
                [gamma, 0, 0, -gamma * beta],
                [0, 1, 0, 0],
                [0, 0, 1, 0],
                [-gamma * beta, 0, 0, gamma],
            ]
        )

    @property
    def beta(self) -> "sy.Expr":
        return self.args[0]


@implement_mat_expr(name="R_y", n_args=1, shape=(4, 4))
class RotationY(sy.MatrixExpr):  # pylint: disable=abstract-method
    def evaluate(self) -> sy.Expr:
        angle = self.angle
        return sy.Matrix(
            [
                [1, 0, 0, 0],
                [0, sy.cos(angle), 0, sy.sin(angle)],
                [0, 0, 1, 0],
                [0, -sy.sin(angle), 0, sy.cos(angle)],
            ]
        )

    @property
    def angle(self) -> sy.Expr:
        return self.args[0]


@implement_mat_expr(name="R_z", n_args=1, shape=(4, 4))
class RotationZ(sy.MatrixExpr):  # pylint: disable=abstract-method
    def evaluate(self) -> sy.Expr:
        angle = self.angle
        return sy.Matrix(
            [
                [1, 0, 0, 0],
                [0, sy.cos(angle), -sy.sin(angle), 0],
                [0, sy.sin(angle), sy.cos(angle), 0],
                [0, 0, 0, 1],
            ]
        )

    @property
    def angle(self) -> sy.Expr:
        return self.args[0]


@implement_expr(n_args=1)
class Beta(UnevaluatedExpression):
    @property
    def vector(self) -> "LorentzVector":
        return self.args[0]

    def evaluate(self) -> sy.Expr:
        return self.vector[0] / P3Norm(self.vector)

    def _latex(self, printer: LatexPrinter, *args: Any) -> str:
        args = tuple(map(printer._print, self.args))
        arg = args[0]
        return fR"\beta\left({arg}\right)"


@implement_expr(n_args=1)
class Phi(UnevaluatedExpression):
    @property
    def vector(self) -> "LorentzVector":
        return self.args[0]

    def evaluate(self) -> sy.Expr:
        return sy.atan2(self.vector[2], self.vector[1])

    def _latex(self, printer: LatexPrinter, *args: Any) -> str:
        args = tuple(map(printer._print, self.args))
        arg = args[0]
        return fR"\phi\left({arg}\right)"


@implement_expr(n_args=1)
class Theta(UnevaluatedExpression):
    @property
    def vector(self) -> "LorentzVector":
        return self.args[0]

    def evaluate(self) -> sy.Expr:
        return sy.acos(self.vector[3] / P3Norm(self.vector))

    def _latex(self, printer: LatexPrinter, *args: Any) -> str:
        args = tuple(map(printer._print, self.args))
        arg = args[0]
        return fR"\theta\left({arg}\right)"


def reduce_ids(nested_list: list) -> Tuple[int, ...]:
    ids: Set[int] = set()
    for x in nested_list:
        if isinstance(x, list):
            ids.update(reduce_ids(x))
        else:
            ids.add(x)
    return tuple(ids)


def nested_helicity_angles(
    momentum_pool: Dict[int, LorentzVector],
    nested_momenta_ids: list,
) -> Tuple[Dict[sy.Symbol, sy.Expr], Dict[sy.Symbol, sy.Expr]]:
    helicity_angles: Dict[sy.Symbol, sy.Expr] = dict()
    intermediate_momenta: Dict[sy.Symbol, sy.Expr] = dict()
    for momentum_ids in nested_momenta_ids:
        if isinstance(momentum_ids, list):
            # recursively determine all momenta ids in the list
            sub_momenta_ids = reduce_ids(momentum_ids)
            if len(sub_momenta_ids) > 1:
                # add all of these momenta together -> defines new subsystem
                state = sy.MatAdd(
                    *[momentum_pool[i] for i in sub_momenta_ids],
                    evaluate=False,
                )

                # Register a symbol for the momentum of this state. This is
                # required for the eventual lambdifying.
                label = reduce(lambda x, y: x + str(y), sub_momenta_ids, "")
                state_symbol = LorentzVector(f"p_{{{label}}}")
                intermediate_momenta[state_symbol] = state

                # determine angles and beta for current state
                phi_state = Phi(state_symbol)
                theta_state = Theta(state_symbol)
                beta = Beta(state_symbol)

                # register current angle variables
                helicity_angles[sy.Symbol(f"phi_{label}")] = phi_state
                helicity_angles[sy.Symbol(f"theta_{label}")] = theta_state

                # boost all of those momenta into this new subsystem
                new_momentum_pool = {
                    k: sy.MatMul(
                        BoostZ(beta),
                        RotationY(-theta_state),
                        RotationZ(-phi_state),
                        v,
                        evaluate=False,
                    )
                    for k, v in momentum_pool.items()
                    if k in sub_momenta_ids
                }

                # call next recursion
                angles, other_symbols = nested_helicity_angles(
                    new_momentum_pool, momentum_ids
                )
                helicity_angles.update(angles)
                intermediate_momenta.update(other_symbols)

    return helicity_angles, intermediate_momenta
