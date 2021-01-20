"""Implementation of the helicity formalism for amplitude model generation."""

import logging
from typing import Dict, Iterable, List, Optional, Tuple

from expertsystem.particle import ParticleCollection
from expertsystem.reaction import Result
from expertsystem.reaction.combinatorics import (
    perform_external_edge_identical_particle_combinatorics,
)
from expertsystem.reaction.quantum_numbers import ParticleWithSpin
from expertsystem.reaction.topology import StateTransitionGraph

from ._graph_info import (
    determine_attached_final_state,
    generate_kinematics,
    generate_particle_collection,
    generate_particles_string,
    get_graph_group_unique_label,
    get_name_hel_list,
    get_parent_recoil_edge,
    get_prefactor,
    get_recoil_edge,
    group_graphs_same_initial_and_final,
)
from .model import (
    AmplitudeModel,
    AmplitudeNode,
    CoefficientAmplitude,
    CoherentIntensity,
    DecayNode,
    DecayProduct,
    FitParameter,
    FitParameters,
    HelicityDecay,
    HelicityParticle,
    IncoherentIntensity,
    IntensityNode,
    Kinematics,
    ParticleDynamics,
    RecoilSystem,
    SequentialAmplitude,
)


class _HelicityAmplitudeNameGenerator:
    """Parameter name generator for the helicity formalism."""

    def __init__(self) -> None:
        self.parity_partner_coefficient_mapping: Dict[str, str] = {}

    def _generate_amplitude_coefficient_couple(
        self, graph: StateTransitionGraph[ParticleWithSpin], node_id: int
    ) -> Tuple[str, str, str]:
        (in_hel_info, out_hel_info) = self._retrieve_helicity_info(
            graph, node_id
        )
        par_name_suffix = self.generate_amplitude_coefficient_name(
            graph, node_id
        )

        pp_par_name_suffix = (
            generate_particles_string(in_hel_info, False)
            + "_to_"
            + generate_particles_string(out_hel_info, make_parity_partner=True)
        )

        priority_name_suffix = par_name_suffix
        if out_hel_info[0][1] < 0 or (
            out_hel_info[0][1] == 0 and out_hel_info[1][1] < 0
        ):
            priority_name_suffix = pp_par_name_suffix

        return (par_name_suffix, pp_par_name_suffix, priority_name_suffix)

    def register_amplitude_coefficient_name(
        self, graph: StateTransitionGraph[ParticleWithSpin]
    ) -> None:
        for node_id in graph.topology.nodes:
            (
                coefficient_suffix,
                parity_partner_coefficient_suffix,
                priority_partner_coefficient_suffix,
            ) = self._generate_amplitude_coefficient_couple(graph, node_id)

            if graph.get_node_props(node_id).parity_prefactor is None:
                continue

            if (
                coefficient_suffix
                not in self.parity_partner_coefficient_mapping
            ):
                if (
                    parity_partner_coefficient_suffix
                    in self.parity_partner_coefficient_mapping
                ):
                    if (
                        parity_partner_coefficient_suffix
                        == priority_partner_coefficient_suffix
                    ):
                        self.parity_partner_coefficient_mapping[
                            coefficient_suffix
                        ] = parity_partner_coefficient_suffix
                    else:
                        self.parity_partner_coefficient_mapping[
                            parity_partner_coefficient_suffix
                        ] = coefficient_suffix
                        self.parity_partner_coefficient_mapping[
                            coefficient_suffix
                        ] = coefficient_suffix

                else:
                    # if neither this coefficient nor its partner are registered just add it
                    self.parity_partner_coefficient_mapping[
                        coefficient_suffix
                    ] = coefficient_suffix

    def generate_unique_amplitude_name(
        self,
        graph: StateTransitionGraph[ParticleWithSpin],
        node_id: Optional[int] = None,
    ) -> str:
        """Generates a unique name for the amplitude corresponding.

        That is, corresponging to the given :class:`StateTransitionGraph`. If
        ``node_id`` is given, it generates a unique name for the partial
        amplitude corresponding to the interaction node of the given
        :class:`StateTransitionGraph`.
        """
        name = ""
        if isinstance(node_id, int):
            nodelist = frozenset({node_id})
        else:
            nodelist = graph.topology.nodes
        for node in nodelist:
            (in_hel_info, out_hel_info) = self._retrieve_helicity_info(
                graph, node
            )

            name += (
                generate_particles_string(in_hel_info)
                + "_to_"
                + generate_particles_string(out_hel_info)
                + ";"
            )
        return name

    @staticmethod
    def _retrieve_helicity_info(
        graph: StateTransitionGraph[ParticleWithSpin], node_id: int
    ) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]:
        topology = graph.topology
        in_edges = topology.get_edge_ids_ingoing_to_node(node_id)
        out_edges = topology.get_edge_ids_outgoing_from_node(node_id)

        in_names_hel_list = get_name_hel_list(graph, in_edges)
        out_names_hel_list = get_name_hel_list(graph, out_edges)

        return (in_names_hel_list, out_names_hel_list)

    def generate_amplitude_coefficient_name(
        self, graph: StateTransitionGraph[ParticleWithSpin], node_id: int
    ) -> str:
        """Generate partial amplitude coefficient name suffix."""
        in_hel_info, out_hel_info = self._retrieve_helicity_info(
            graph, node_id
        )
        return (
            generate_particles_string(in_hel_info, False)
            + "_to_"
            + generate_particles_string(out_hel_info)
        )

    def generate_sequential_amplitude_suffix(
        self, graph: StateTransitionGraph[ParticleWithSpin]
    ) -> str:
        """Generate unique suffix for a sequential amplitude graph."""
        output_suffix = ""
        for node_id in graph.topology.nodes:
            suffix = self.generate_amplitude_coefficient_name(graph, node_id)
            if suffix in self.parity_partner_coefficient_mapping:
                suffix = self.parity_partner_coefficient_mapping[suffix]
            output_suffix += suffix + ";"
        return output_suffix


class HelicityAmplitudeGenerator:
    """Amplitude model generator for the helicity formalism."""

    def __init__(
        self,
        top_node_no_dynamics: bool = True,
    ) -> None:
        self.top_node_no_dynamics = top_node_no_dynamics
        self.name_generator = _HelicityAmplitudeNameGenerator()
        self.particles: Optional[ParticleCollection] = None
        self.kinematics: Optional[Kinematics] = None
        self.dynamics: Optional[ParticleDynamics] = None
        self.intensities: Optional[IntensityNode] = None
        self.fit_parameters: FitParameters = FitParameters()

    def generate(self, reaction_result: Result) -> AmplitudeModel:
        graphs = reaction_result.transitions
        if len(graphs) < 1:
            raise ValueError(
                f"At least one {StateTransitionGraph.__name__} required to"
                " genenerate an amplitude model!"
            )

        get_initial_state = reaction_result.get_initial_state()
        if len(get_initial_state) != 1:
            raise ValueError(
                "Helicity amplitude model requires exactly one initial state"
            )
        initial_state = get_initial_state[0].name

        self.particles = generate_particle_collection(graphs)
        self.kinematics = generate_kinematics(reaction_result)
        self.dynamics = ParticleDynamics(self.particles, self.fit_parameters)
        if self.top_node_no_dynamics:
            self.dynamics.set_non_dynamic(initial_state)
        self.intensities = self.__generate_intensities(graphs)

        return AmplitudeModel(
            particles=self.particles,
            kinematics=self.kinematics,
            parameters=self.fit_parameters,
            intensity=self.intensities,
            dynamics=self.dynamics,
        )

    def __generate_intensities(
        self, graphs: List[StateTransitionGraph[ParticleWithSpin]]
    ) -> IntensityNode:
        graph_groups = group_graphs_same_initial_and_final(graphs)
        logging.debug("There are %d graph groups", len(graph_groups))

        self.__create_parameter_couplings(graph_groups)
        incoherent_intensity = IncoherentIntensity()
        for graph_group in graph_groups:
            coherent_intensity = self.__generate_coherent_intensity(
                graph_group
            )
            incoherent_intensity.intensities.append(coherent_intensity)
        if len(incoherent_intensity.intensities) == 0:
            raise ValueError("List of incoherent intensities cannot be empty")
        if len(incoherent_intensity.intensities) == 1:
            return incoherent_intensity.intensities[0]
        return incoherent_intensity

    def __create_parameter_couplings(
        self,
        graph_groups: Iterable[List[StateTransitionGraph[ParticleWithSpin]]],
    ) -> None:
        for graph_group in graph_groups:
            for graph in graph_group:
                self.name_generator.register_amplitude_coefficient_name(graph)

    def __generate_coherent_intensity(
        self,
        graph_group: List[StateTransitionGraph[ParticleWithSpin]],
    ) -> CoherentIntensity:
        coherent_amp_name = "coherent_" + get_graph_group_unique_label(
            graph_group
        )
        coherent_intensity = CoherentIntensity(coherent_amp_name)
        for graph in graph_group:
            sequential_graphs = (
                perform_external_edge_identical_particle_combinatorics(graph)
            )
            for seq_graph in sequential_graphs:
                coherent_intensity.amplitudes.append(
                    self.__generate_sequential_decay(seq_graph)
                )
        return coherent_intensity

    def __generate_sequential_decay(
        self, graph: StateTransitionGraph[ParticleWithSpin]
    ) -> AmplitudeNode:
        partial_decays: List[AmplitudeNode] = [
            self._generate_partial_decay(graph, node_id)
            for node_id in graph.topology.nodes
        ]
        sequential_amplitudes = SequentialAmplitude(partial_decays)

        amp_name = self.name_generator.generate_unique_amplitude_name(graph)
        magnitude, phase = self.__generate_amplitude_coefficient(graph)
        prefactor = self.__generate_amplitude_prefactor(graph)
        return CoefficientAmplitude(
            component=amp_name,
            magnitude=magnitude,
            phase=phase,
            amplitude=sequential_amplitudes,
            prefactor=prefactor,
        )

    def _generate_partial_decay(
        self, graph: StateTransitionGraph[ParticleWithSpin], node_id: int
    ) -> DecayNode:
        def create_helicity_particle(
            edge_props: ParticleWithSpin,
        ) -> HelicityParticle:
            if self.particles is None:
                raise ValueError(
                    f"{ParticleCollection.__name__} not yet initialized!"
                )
            particle, spin_projection = edge_props
            return HelicityParticle(particle, spin_projection)

        decay_products: List[DecayProduct] = list()
        topology = graph.topology
        for out_edge_id in topology.get_edge_ids_outgoing_from_node(node_id):
            edge_props = graph.get_edge_props(out_edge_id)
            helicity_particle = create_helicity_particle(edge_props)
            final_state_ids = determine_attached_final_state(
                topology, out_edge_id
            )
            decay_products.append(
                DecayProduct(
                    helicity_particle.particle,
                    helicity_particle.helicity,
                    final_state_ids,
                )
            )

        in_edge_ids = topology.get_edge_ids_ingoing_to_node(node_id)
        if len(in_edge_ids) != 1:
            raise ValueError("This node does not represent a two body decay!")
        ingoing_edge_id = next(iter(in_edge_ids))
        edge_props = graph.get_edge_props(ingoing_edge_id)
        helicity_particle = create_helicity_particle(edge_props)
        helicity_decay = HelicityDecay(helicity_particle, decay_products)

        recoil_edge_id = get_recoil_edge(topology, ingoing_edge_id)
        if recoil_edge_id is not None:
            helicity_decay.recoil_system = RecoilSystem(
                determine_attached_final_state(topology, recoil_edge_id)
            )
            parent_recoil_edge_id = get_parent_recoil_edge(
                topology, ingoing_edge_id
            )
            if parent_recoil_edge_id is not None:
                helicity_decay.recoil_system.parent_recoil_final_state = (
                    determine_attached_final_state(
                        topology, parent_recoil_edge_id
                    )
                )

        return helicity_decay

    def __generate_amplitude_coefficient(
        self, graph: StateTransitionGraph[ParticleWithSpin]
    ) -> Tuple[FitParameter, FitParameter]:
        """Generate coefficient info for a sequential amplitude graph.

        Generally, each partial amplitude of a sequential amplitude graph
        should check itself if it or a parity partner is already defined. If so
        a coupled coefficient is introduced.
        """
        seq_par_suffix = (
            self.name_generator.generate_sequential_amplitude_suffix(graph)
        )
        magnitude = self.__register_parameter(
            name=f"Magnitude_{seq_par_suffix}", value=1.0, fix=False
        )
        phase = self.__register_parameter(
            name=f"Phase_{seq_par_suffix}", value=0.0, fix=False
        )
        return magnitude, phase

    def __generate_amplitude_prefactor(
        self, graph: StateTransitionGraph[ParticleWithSpin]
    ) -> Optional[float]:
        prefactor = get_prefactor(graph)
        if prefactor != 1.0:
            for node_id in graph.topology.nodes:
                raw_suffix = (
                    self.name_generator.generate_amplitude_coefficient_name(
                        graph, node_id
                    )
                )
                if (
                    raw_suffix
                    in self.name_generator.parity_partner_coefficient_mapping
                ):
                    coefficient_suffix = (
                        self.name_generator.parity_partner_coefficient_mapping[
                            raw_suffix
                        ]
                    )
                    if coefficient_suffix != raw_suffix:
                        return prefactor
        return None

    def __register_parameter(
        self, name: str, value: float, fix: bool = False
    ) -> FitParameter:
        if name in self.fit_parameters:
            return self.fit_parameters[name]
        parameter = FitParameter(name=name, value=value, fix=fix)
        self.fit_parameters.add(parameter)
        return parameter
