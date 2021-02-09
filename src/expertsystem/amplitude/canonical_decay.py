"""Implementation of the canonical formalism for amplitude model generation."""

from typing import List, Optional

from expertsystem.particle import Spin
from expertsystem.reaction.quantum_numbers import ParticleWithSpin
from expertsystem.reaction.topology import StateTransitionGraph

from ._graph_info import get_angular_momentum, get_coupled_spin
from .helicity_decay import (
    HelicityAmplitudeGenerator,
    _HelicityAmplitudeNameGenerator,
)
from .model import CanonicalDecay, ClebschGordan, DecayNode, HelicityDecay


class _CanonicalAmplitudeNameGenerator(_HelicityAmplitudeNameGenerator):
    """Generate names for canonical partial decays.

    That is, using the properties of the decay.
    """

    def generate_unique_amplitude_name(
        self,
        graph: StateTransitionGraph[ParticleWithSpin],
        node_id: Optional[int] = None,
    ) -> str:
        name = ""
        if isinstance(node_id, int):
            node_ids = frozenset({node_id})
        else:
            node_ids = graph.topology.nodes
        for node in node_ids:
            name += (
                super().generate_unique_amplitude_name(graph, node)[:-1]
                + self._generate_clebsch_gordan_string(graph, node)
                + ";"
            )
        return name

    @staticmethod
    def _generate_clebsch_gordan_string(
        graph: StateTransitionGraph[ParticleWithSpin], node_id: int
    ) -> str:
        node_props = graph.get_node_props(node_id)
        ang_orb_mom = get_angular_momentum(node_props)
        spin = get_coupled_spin(node_props)
        return f"_L_{ang_orb_mom.magnitude}_S_{spin.magnitude}"


class CanonicalAmplitudeGenerator(HelicityAmplitudeGenerator):
    r"""Amplitude model generator for the canonical helicity formalism.

    This class defines a full amplitude in the canonical formalism, using the
    helicity formalism as a foundation. The key here is that we take the full
    helicity intensity as a template, and just exchange the helicity amplitudes
    :math:`F` as a sum of canonical amplitudes :math:`A`:

    .. math::

        F^J_{\lambda_1,\lambda_2} = \sum_{LS} \mathrm{norm}(A^J_{LS})C^2.

    Here, :math:`C` stands for `Clebsch-Gordan factor
    <https://en.wikipedia.org/wiki/Clebsch%E2%80%93Gordan_coefficients>`_.
    """

    def __init__(self, top_node_no_dynamics: bool = True) -> None:
        super().__init__(top_node_no_dynamics)
        self.name_generator = _CanonicalAmplitudeNameGenerator()

    def _generate_partial_decay(  # pylint: disable=too-many-locals
        self, graph: StateTransitionGraph[ParticleWithSpin], node_id: int
    ) -> DecayNode:
        amplitude = super()._generate_partial_decay(graph, node_id)
        if isinstance(amplitude, HelicityDecay):
            helicity_decay = amplitude
        else:
            raise TypeError(
                f"Can only decorate with return value {HelicityDecay.__name__}"
            )

        node_props = graph.get_node_props(node_id)
        ang_mom = get_angular_momentum(node_props)
        if ang_mom.projection != 0.0:
            raise ValueError(f"Projection of L is non-zero!: {ang_mom}")

        spin = get_coupled_spin(node_props)
        if not isinstance(spin, Spin):
            raise ValueError(
                f"{spin.__class__.__name__} is not of type {Spin.__name__}"
            )
        topology = graph.topology
        in_edge_ids = topology.get_edge_ids_ingoing_to_node(node_id)
        out_edge_ids = topology.get_edge_ids_outgoing_from_node(node_id)

        in_edge_id = next(iter(in_edge_ids))
        particle, spin_projection = graph.get_edge_props(in_edge_id)
        parent_spin = Spin(
            particle.spin,
            spin_projection,
        )

        daughter_spins: List[Spin] = []
        for out_edge_id in out_edge_ids:
            particle, spin_projection = graph.get_edge_props(out_edge_id)
            daughter_spin = Spin(
                particle.spin,
                spin_projection,
            )
            if daughter_spin is not None and isinstance(daughter_spin, Spin):
                daughter_spins.append(daughter_spin)

        decay_particle_lambda = (
            daughter_spins[0].projection - daughter_spins[1].projection
        )

        cg_ls = ClebschGordan(
            j_1=ang_mom.magnitude,
            m_1=ang_mom.projection,
            j_2=spin.magnitude,
            m_2=decay_particle_lambda,
            J=parent_spin.magnitude,
            M=decay_particle_lambda,
        )
        cg_ss = ClebschGordan(
            j_1=daughter_spins[0].magnitude,
            m_1=daughter_spins[0].projection,
            j_2=daughter_spins[1].magnitude,
            m_2=-daughter_spins[1].projection,
            J=spin.magnitude,
            M=decay_particle_lambda,
        )

        return CanonicalDecay(
            decaying_particle=helicity_decay.decaying_particle,
            decay_products=helicity_decay.decay_products,
            recoil_system=helicity_decay.recoil_system,
            l_s=cg_ls,
            s2s3=cg_ss,
        )
