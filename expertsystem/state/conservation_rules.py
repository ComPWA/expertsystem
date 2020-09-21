"""Collection of quantum number conservation rules for particle reactions.

Contains:
- Functors for quantum number condition checks.
"""

# pylint: disable=abstract-method

from copy import deepcopy
from dataclasses import dataclass
from functools import reduce
from typing import (
    Any,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

from numpy import arange

from expertsystem.data import EdgeQuantumNumbers, NodeQuantumNumbers, Spin

from .particle import is_boson


def is_particle_antiparticle_pair(pid1, pid2):
    # we just check if the pid is opposite in sign
    # this is a requirement of the pid numbers of course
    return pid1 == -pid2


class Rule:
    """Interface for rules.

    A `Rule` performs checks on an `.InteractionNode` and its attached `.Edge` s.
    The `__call__` method contains actual rule logic and has to be overwritten.

    For additive quantum numbers the decorator `additive_quantum_number_rule`
    can simplify the constrution of the appropriate `Rule`.

    Besides the rule logic itself, a `Rule` also has the responsibility of
    stating its run conditions. These run conditions **MUST** be stated by the
    type annotations of the `.__call__` function.
    Generally, the conditions can be separated into two categories:

    * variable conditions
    * toplogical conditions

    Note: currently only variable conditions are being used. Topological
    conditions could be created in the form of `~typing.Tuple` instead of
    `~typing.List`.
    """

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}"

    def __call__(
        self,
        ingoing_edge_qns: List[Any],
        outgoing_edge_qns: List[Any],
        interaction_node_qns: Any,
    ) -> bool:
        raise NotImplementedError


def additive_quantum_number_rule(quantum_number: Any):
    r"""Class decorator for creating an additive conservation `Rule`.

    Use this decorator to create a conservation `Rule` for a quantum number
    to which an additive conservation rule applies:

    .. math:: \sum q_{in} = \sum q_{out}

    Args:
        quantum_number: Quantum number to which you
            want to apply the additive conservation check.
    """

    def decorator(rule_class):
        def new_call(
            self,
            ingoing_edge_qns: List[quantum_number],
            outgoing_edge_qns: List[quantum_number],
            _=None,
        ):  # pylint: disable=unused-argument
            return sum(ingoing_edge_qns) == sum(outgoing_edge_qns)

        rule_class.__call__ = new_call
        rule_class.__doc__ = (
            f"""Decorated via `{additive_quantum_number_rule.__name__}`.\n\n"""
            f"""Check for `.{quantum_number.__name__}` conservation."""
        )
        return rule_class

    return decorator


@additive_quantum_number_rule(EdgeQuantumNumbers.charge)
class ChargeConservation(Rule):
    pass


@additive_quantum_number_rule(EdgeQuantumNumbers.baryon_number)
class BaryonNumberConservation(Rule):
    pass


@additive_quantum_number_rule(EdgeQuantumNumbers.electron_lepton_number)
class ElectronLNConservation(Rule):
    pass


@additive_quantum_number_rule(EdgeQuantumNumbers.muon_lepton_number)
class MuonLNConservation(Rule):
    pass


@additive_quantum_number_rule(EdgeQuantumNumbers.tau_lepton_number)
class TauLNConservation(Rule):
    pass


@additive_quantum_number_rule(EdgeQuantumNumbers.strangeness)
class StrangenessConservation(Rule):
    pass


@additive_quantum_number_rule(EdgeQuantumNumbers.charmness)
class CharmConservation(Rule):
    pass


class ParityConservation(Rule):
    def __call__(
        self,
        ingoing_edge_qns: List[EdgeQuantumNumbers.parity],
        outgoing_edge_qns: List[EdgeQuantumNumbers.parity],
        ang_mom: NodeQuantumNumbers.l_magnitude,
    ):
        r"""Implement :math:`P_{in} = P_{out} \cdot (-1)^L`."""
        parity_in = reduce(lambda x, y: x * y.value, ingoing_edge_qns, 1,)
        parity_out = reduce(lambda x, y: x * y.value, outgoing_edge_qns, 1)
        return parity_in == (parity_out * (-1) ** ang_mom)


@dataclass(frozen=True)
class HelcityParityEdgeInput:
    parity: Optional[EdgeQuantumNumbers.parity]
    spin_mag: EdgeQuantumNumbers.spin_magnitude
    spin_proj: EdgeQuantumNumbers.spin_projection


class ParityConservationHelicity(Rule):
    def __call__(
        self,
        ingoing_edge_qns: List[HelcityParityEdgeInput],
        outgoing_edge_qns: List[HelcityParityEdgeInput],
        parity_prefactor: NodeQuantumNumbers.parity_prefactor,
    ):
        r"""Implements parity conservation for helicity formalism.

        Check the following:

        .. math:: A_{-\lambda_1-\lambda_2} = P_1 P_2 P_3 (-1)^{S_2+S_3-S_1}
            A_{\lambda_1\lambda_2}

        Notice that only the special case :math:`\lambda_1=\lambda_2=0` may
        return False.
        """
        if len(ingoing_edge_qns) == 1 and len(outgoing_edge_qns) == 2:
            out_spins = [x.spin_mag for x in outgoing_edge_qns]
            parity_product = reduce(
                lambda x, y: x * y.parity.value,
                ingoing_edge_qns + outgoing_edge_qns,
                1,
            )

            prefactor = parity_product * (-1.0) ** (
                sum(out_spins) - ingoing_edge_qns[0].spin_mag
            )

            daughter_hel = [0 for x in outgoing_edge_qns if x.spin_proj == 0.0]
            if len(daughter_hel) == 2:
                if prefactor == -1:
                    return False

            return prefactor == parity_prefactor
        return True


@dataclass(frozen=True)
class CParityEdgeInput:
    spin_mag: EdgeQuantumNumbers.spin_magnitude
    pid: EdgeQuantumNumbers.pid
    c_parity: Optional[EdgeQuantumNumbers.c_parity] = None


@dataclass(frozen=True)
class CParityNodeInput:
    l_mag: NodeQuantumNumbers.l_magnitude
    s_mag: NodeQuantumNumbers.s_magnitude


class CParityConservation(Rule):
    def __call__(
        self,
        ingoing_edge_qns: List[CParityEdgeInput],
        outgoing_edge_qns: List[CParityEdgeInput],
        interaction_node_qns: CParityNodeInput,
    ) -> bool:
        """Check for :math:`C`-parity conservation.

        Implements :math:`C_{in} = C_{out}`.
        """

        def _get_c_parity_multiparticle(
            part_qns: List[CParityEdgeInput], interaction_qns: CParityNodeInput
        ):
            no_c_parity_part = [x for x in part_qns if x.c_parity is None]
            # if all states have C parity defined, then just multiply them
            if not no_c_parity_part:
                return reduce(lambda x, y: x * y.c_parity.value, part_qns, 1)

            # two particle case
            if len(part_qns) == 2:
                if is_particle_antiparticle_pair(
                    part_qns[0].pid, part_qns[1].pid
                ):
                    ang_mom = interaction_qns.l_mag
                    # if boson
                    if is_boson(part_qns[0].spin_mag):
                        return (-1) ** ang_mom
                    coupled_spin = interaction_qns.s_mag
                    return (-1) ** (ang_mom + coupled_spin)
            return None

        c_parity_in = _get_c_parity_multiparticle(
            ingoing_edge_qns, interaction_node_qns
        )
        if c_parity_in is None:
            return True

        c_parity_out = _get_c_parity_multiparticle(
            outgoing_edge_qns, interaction_node_qns
        )
        if c_parity_out is None:
            return True

        return c_parity_in == c_parity_out


@dataclass(frozen=True)
class GParityEdgeInput:
    isospin: EdgeQuantumNumbers.isospin_magnitude
    spin_mag: EdgeQuantumNumbers.spin_magnitude
    pid: EdgeQuantumNumbers.pid
    g_parity: Optional[EdgeQuantumNumbers.g_parity] = None


@dataclass(frozen=True)
class GParityNodeInput:
    l_mag: NodeQuantumNumbers.l_magnitude
    s_mag: NodeQuantumNumbers.s_magnitude


class GParityConservation(Rule):
    def __call__(
        self,
        ingoing_edge_qns: List[GParityEdgeInput],
        outgoing_edge_qns: List[GParityEdgeInput],
        interaction_qns: GParityNodeInput,
    ):
        """Check for :math:`G`-parity conservation.

        Implements for :math:`G_{in} = G_{out}`.
        """
        no_g_parity_in_part = [
            True for x in ingoing_edge_qns if x.g_parity is None
        ]
        no_g_parity_out_part = [
            True for x in outgoing_edge_qns if x.g_parity is None
        ]
        # if all states have G parity defined, then just multiply them
        if not any(no_g_parity_in_part + no_g_parity_out_part):
            in_g_parity = reduce(
                lambda x, y: x * y.g_parity.value if y.g_parity else x,
                ingoing_edge_qns,
                1,
            )
            out_g_parity = reduce(
                lambda x, y: x * y.g_parity.value if y.g_parity else x,
                outgoing_edge_qns,
                1,
            )
            return in_g_parity == out_g_parity

        # two particle case
        def check_multistate_g_parity(
            isospin: int,
            double_state_qns: Tuple[GParityEdgeInput, GParityEdgeInput],
        ):
            if is_particle_antiparticle_pair(
                double_state_qns[0].pid, double_state_qns[1].pid
            ):
                ang_mom = interaction_qns.l_mag
                # if boson
                if is_boson(double_state_qns[0].spin_mag):
                    return (-1) ** (ang_mom + isospin)
                coupled_spin = interaction_qns.s_mag
                return (-1) ** (ang_mom + coupled_spin + isospin)
            return None

        def check_g_parity_isobar(
            single_state: GParityEdgeInput,
            couple_state: Tuple[GParityEdgeInput, GParityEdgeInput],
        ):
            couple_state_g_parity = check_multistate_g_parity(
                single_state.isospin, (couple_state[0], couple_state[1]),
            )
            single_state_g_parity = (
                ingoing_edge_qns[0].g_parity.value
                if ingoing_edge_qns[0].g_parity
                else None
            )

            if not couple_state_g_parity or not single_state_g_parity:
                return True
            return couple_state_g_parity == single_state_g_parity

        particle_counts = (len(ingoing_edge_qns), len(outgoing_edge_qns))
        if particle_counts == (1, 2):
            return check_g_parity_isobar(
                ingoing_edge_qns[0],
                (outgoing_edge_qns[0], outgoing_edge_qns[1]),
            )

        if particle_counts == (2, 1):
            return check_g_parity_isobar(
                outgoing_edge_qns[0],
                (ingoing_edge_qns[0], ingoing_edge_qns[1]),
            )
        return True


@dataclass(frozen=True)
class IdenticalParticleSymmetryEdgeInput:
    parity: EdgeQuantumNumbers.parity
    spin: EdgeQuantumNumbers.spin
    pid: EdgeQuantumNumbers.pid


class IdenticalParticleSymmetrization(Rule):
    def __call__(
        self,
        ingoing_edge_qns: List[IdenticalParticleSymmetryEdgeInput],
        outgoing_edge_qns: List[IdenticalParticleSymmetryEdgeInput],
        _,
    ):
        """Implementation of particle symmetrization."""

        def _check_particles_identical(
            particles: List[IdenticalParticleSymmetryEdgeInput],
        ):
            """Check if pids and spins match."""
            reference_pid = particles[0].pid
            reference_spin_proj = particles[0].spin.projection
            for particle in particles[1:]:
                if particle.pid != reference_pid:
                    return False
                if particle.spin.projection != reference_spin_proj:
                    return False
            return True

        if _check_particles_identical(outgoing_edge_qns):

            if is_boson(outgoing_edge_qns[0].spin.magnitude):
                # we have a boson, check if parity of mother is even
                parity = ingoing_edge_qns[0].parity
                if parity == -1:
                    # if its odd then return False
                    return False
            else:
                # its fermion
                parity = ingoing_edge_qns[0].parity
                if parity == 1:
                    return False

        return True


def _is_clebsch_gordan_coefficient_zero(
    spin1: Spin, spin2: Spin, spin_coupled: Spin
):
    m_1 = spin1.projection
    j_1 = spin1.magnitude
    m_2 = spin2.projection
    j_2 = spin2.magnitude
    proj = spin_coupled.projection
    mag = spin_coupled.magnitude
    is_zero = False
    if (j_1 == j_2 and m_1 == m_2) or (m_1 == 0.0 and m_2 == 0.0):
        if abs(mag - j_1 - j_2) % 2 == 1:
            is_zero = True
    elif j_1 == mag and m_1 == -proj:
        if abs(j_2 - j_1 - mag) % 2 == 1:
            is_zero = True
    elif j_2 == mag and m_2 == -proj:
        if abs(j_1 - j_2 - mag) % 2 == 1:
            is_zero = True
    return is_zero


_SpinType = Union[Spin, EdgeQuantumNumbers.spin, EdgeQuantumNumbers.isospin]


def _check_projections(
    in_spins: Sequence[_SpinType], out_spins: Sequence[_SpinType]
):
    return sum([x.projection for x in in_spins]) == sum(
        [x.projection for x in out_spins]
    )


@dataclass(frozen=True)
class SpinNodeInput:
    l_: NodeQuantumNumbers.l_
    s_: NodeQuantumNumbers.s_


def _check_spin_couplings(in_part, out_part, interaction_qns):
    in_tot_spins = __calculate_total_spins(in_part, interaction_qns)
    out_tot_spins = __calculate_total_spins(out_part, interaction_qns)
    matching_spins = in_tot_spins.intersection(out_tot_spins)
    if len(matching_spins) > 0:
        return True
    return False


def _check_magnitude(
    in_part: List[float],
    out_part: List[float],
    interaction_qns: Optional[SpinNodeInput],
):
    def couple_mags(j_1: float, j_2: float) -> List[float]:
        return [
            x / 2.0
            for x in range(
                int(2 * abs(j_1 - j_2)), int(2 * (j_1 + j_2 + 1)), 2
            )
        ]

    def couple_magnitudes(
        magnitudes: List[float], interaction_qns: Optional[SpinNodeInput]
    ):
        if len(magnitudes) == 1:
            return set(magnitudes)

        coupled_magnitudes = set([magnitudes[0],])
        for mag in magnitudes[1:]:
            temp_set = coupled_magnitudes
            coupled_magnitudes = set()
            for ref_mag in temp_set:
                coupled_magnitudes.update(couple_mags(mag, ref_mag))

        if interaction_qns:
            if interaction_qns.s_.magnitude in coupled_magnitudes:
                return set(
                    couple_mags(
                        interaction_qns.s_.magnitude,
                        interaction_qns.l_.magnitude,
                    )
                )
            return set()  # in case there the spin coupling fails
        return coupled_magnitudes

    in_tot_spins = couple_magnitudes(in_part, interaction_qns)
    out_tot_spins = couple_magnitudes(out_part, interaction_qns)
    matching_spins = in_tot_spins.intersection(out_tot_spins)

    if len(matching_spins) > 0:
        return True
    return False


def __calculate_total_spins(
    spins: List[Spin], interaction_qns: Optional[SpinNodeInput] = None,
):
    total_spins = set()
    if len(spins) == 1:
        return set(spins)
    total_spins = __create_coupled_spins(spins)
    if interaction_qns:
        if interaction_qns.s_ in total_spins:
            return __spin_couplings(interaction_qns.s_, interaction_qns.l_)

    return total_spins


def __create_coupled_spins(spins: List[Spin]):
    """Creates all combinations of coupled spins."""
    spins_daughters_coupled: Set[Spin] = set()
    spin_list = deepcopy(spins)
    while spin_list:
        if spins_daughters_coupled:
            temp_coupled_spins = set()
            tempspin = spin_list.pop()
            for spin in spins_daughters_coupled:
                coupled_spins = __spin_couplings(spin, tempspin)
                temp_coupled_spins.update(coupled_spins)
            spins_daughters_coupled = temp_coupled_spins
        else:
            spins_daughters_coupled.add(spin_list.pop())

    return spins_daughters_coupled


def __spin_couplings(spin1, spin2):
    r"""Implement the coupling of two spins.

    :math:`|S_1 - S_2| \leq S \leq |S_1 + S_2|` and :math:`M_1 + M_2 = M`
    """
    j_1 = spin1.magnitude
    j_2 = spin2.magnitude

    sum_proj = spin1.projection + spin2.projection
    possible_spins = [
        Spin(x, sum_proj)
        for x in arange(abs(j_1 - j_2), j_1 + j_2 + 1, 1).tolist()
        if x >= abs(sum_proj)
    ]

    return [
        x
        for x in possible_spins
        if not _is_clebsch_gordan_coefficient_zero(spin1, spin2, x)
    ]


class IsoSpinConservation(Rule):
    r"""Check for isospin conservation.

    Implements

    .. math::
        |I_1 - I_2| \leq I \leq |I_1 + I_2|

    Also checks :math:`I_{1,z} + I_{2,z} = I_z` and if Clebsch-Gordan
    coefficients are all 0.
    """

    def __call__(
        self,
        ingoing_isospins: List[EdgeQuantumNumbers.isospin],
        outgoing_isospins: List[EdgeQuantumNumbers.isospin],
        _=None,
    ):
        if not _check_projections(ingoing_isospins, outgoing_isospins):
            return False
        return _check_spin_couplings(ingoing_isospins, outgoing_isospins, None)


class SpinConservation(Rule):
    r"""Check for spin conservation.

    Implements

    .. math::
        |S_1 - S_2| \leq S \leq |S_1 + S_2|

    and

    .. math::
        |L - S| \leq J \leq |L + S|

    Also checks :math:`M_1 + M_2 = M` and if Clebsch-Gordan coefficients
    are all 0.
    """

    def __init__(self, use_projection=True):
        self.__use_projection = use_projection
        super().__init__()

    def __call__(
        self,
        ingoing_spins: List[EdgeQuantumNumbers.spin],
        outgoing_spins: List[EdgeQuantumNumbers.spin],
        interaction_qns: SpinNodeInput,
    ):
        # L and S can only be used if one side is a single state
        # and the other side contains of two states (isobar)
        # So do a full check if this is the case
        if (len(ingoing_spins) == 1 and len(outgoing_spins) == 2) or (
            len(ingoing_spins) == 2 and len(outgoing_spins) == 1
        ):
            if self.__use_projection:
                return _check_spin_couplings(
                    ingoing_spins, outgoing_spins, interaction_qns
                )

            return _check_magnitude(
                [x.magnitude for x in ingoing_spins],
                [x.magnitude for x in outgoing_spins],
                interaction_qns,
            )

        # otherwise don't use S and L and just check magnitude
        # are integral or non integral on both sides
        return (
            sum([x.magnitude for x in ingoing_spins]).is_integer()
            == sum([x.magnitude for x in outgoing_spins]).is_integer()
        )


class ClebschGordanCheckHelicityToCanonical(Rule):
    def __call__(
        self,
        ingoing_spins: List[EdgeQuantumNumbers.spin],
        outgoing_spins: List[EdgeQuantumNumbers.spin],
        interaction_qns: SpinNodeInput,
    ):
        """Implement Clebsch-Gordan checks.

        For :math:`S_1, S_2` to :math:`S` and the :math:`L,S` to :math:`J` coupling
        based on the conversion of helicity to canonical amplitude sums.
        """
        if len(ingoing_spins) == 1 and len(outgoing_spins) == 2:
            out_spin1 = outgoing_spins[0]
            out_spin2 = -outgoing_spins[1]

            helicity_diff = out_spin1.projection + out_spin2.projection
            ang_mom = interaction_qns.l_
            coupled_spin: Spin = interaction_qns.s_
            if coupled_spin.magnitude < abs(helicity_diff) or ingoing_spins[
                0
            ].magnitude < abs(helicity_diff):
                return False
            coupled_spin = Spin(coupled_spin.magnitude, helicity_diff)
            if _is_clebsch_gordan_coefficient_zero(
                out_spin1, out_spin2, coupled_spin
            ):
                return False
            in_spin = Spin(ingoing_spins[0].magnitude, helicity_diff)
            return not _is_clebsch_gordan_coefficient_zero(
                ang_mom, coupled_spin, in_spin
            )
        return False


class HelicityConservation(Rule):
    def __call__(
        self,
        ingoing_spins: List[EdgeQuantumNumbers.spin],
        outgoing_spins: List[EdgeQuantumNumbers.spin],
        _,
    ):
        r"""Implementation of helicity conservation.

        Check for :math:`|\lambda_2-\lambda_3| \leq S_1`.
        """
        if len(ingoing_spins) == 1 and len(outgoing_spins) == 2:
            mother_spin = ingoing_spins[0].magnitude
            daughter_hel = [x.projection for x in outgoing_spins]
            if mother_spin >= abs(daughter_hel[0] - daughter_hel[1]):
                return True
        return False


@dataclass(frozen=True)
class GellMannNishijimaEdgeInput:
    charge: EdgeQuantumNumbers.charge
    isospin_proj: Optional[EdgeQuantumNumbers.isospin_projection] = None
    strangeness: Optional[EdgeQuantumNumbers.strangeness] = None
    charmness: Optional[EdgeQuantumNumbers.charmness] = None
    bottomness: Optional[EdgeQuantumNumbers.bottomness] = None
    topness: Optional[EdgeQuantumNumbers.topness] = None
    baryon_number: Optional[EdgeQuantumNumbers.baryon_number] = None
    electron_ln: Optional[EdgeQuantumNumbers.electron_lepton_number] = None
    muon_ln: Optional[EdgeQuantumNumbers.muon_lepton_number] = None
    tau_ln: Optional[EdgeQuantumNumbers.tau_lepton_number] = None


class GellMannNishijimaRule(Rule):
    def __call__(
        self,
        ingoing_edge_qns: List[GellMannNishijimaEdgeInput],
        outgoing_edge_qns: List[GellMannNishijimaEdgeInput],
        _,
    ):
        r"""Check the Gell-Mann–Nishijima formula.

        :math:`Q=I_3+\frac{Y}{2}` for each particle.
        """

        def calculate_hypercharge(particle: GellMannNishijimaEdgeInput):
            """Calculate the hypercharge :math:`Y=S+C+B+T+B`."""
            return sum(
                [
                    0.0 if x is None else x
                    for x in [
                        particle.strangeness,
                        particle.charmness,
                        particle.bottomness,
                        particle.topness,
                        particle.baryon_number,
                    ]
                ]
            )

        for particle in ingoing_edge_qns + outgoing_edge_qns:
            if particle.electron_ln or particle.muon_ln or particle.tau_ln:
                # if particle is a lepton then skip the check
                continue
            isospin_3 = 0.0
            if particle.isospin_proj:
                isospin_3 = particle.isospin_proj
            if float(particle.charge) != (
                isospin_3 + 0.5 * calculate_hypercharge(particle)
            ):
                return False
        return True


@dataclass(frozen=True)
class MassEdgeInput:
    mass: EdgeQuantumNumbers.mass
    width: Optional[EdgeQuantumNumbers.width] = None


class MassConservation(Rule):
    """Mass conservation rule."""

    def __init__(self, width_factor):
        self.__width_factor = width_factor
        super().__init__()

    def __call__(
        self,
        ingoing_edge_qns: List[MassEdgeInput],
        outgoing_edge_qns: List[MassEdgeInput],
        _=None,
    ):
        r"""Implements mass conservation.

        :math:`M_{out} - N \cdot W_{out} < M_{in} + N \cdot W_{in}`

        It makes sure that the net mass outgoing state :math:`M_{out}` is
        smaller than the net mass of the ingoing state :math:`M_{in}`. Also the
        width :math:`W` of the states is taken into account.
        """
        mass_in = sum([x.mass for x in ingoing_edge_qns])
        width_in = sum([x.width for x in ingoing_edge_qns if x.width])
        mass_out = sum([x.mass for x in outgoing_edge_qns])
        width_out = sum([x.width for x in outgoing_edge_qns if x.width])

        return (mass_out - self.__width_factor * width_out) < (
            mass_in + self.__width_factor * width_in
        )
