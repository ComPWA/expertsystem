"""Implementation of the helicity formalism for amplitude model generation."""

import json
import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from expertsystem.data import Spin
from expertsystem.nested_dicts import (
    InteractionQuantumNumberNames,
    Labels,
    get_spin_projection,
    remove_spin_projection,
)
from expertsystem.state.properties import (
    get_interaction_property,
    perform_external_edge_identical_particle_combinatorics,
)
from expertsystem.topology import StateTransitionGraph, Topology


def group_graphs_same_initial_and_final(
    graphs: List[StateTransitionGraph[dict]],
) -> List[List[StateTransitionGraph[dict]]]:
    """Match final and initial states in groups.

    Each graph corresponds to a specific state transition amplitude.
    This function groups together graphs, which have the same initial and final
    state (including spin). This is needed to determine the coherency of the
    individual amplitude parts.
    """
    graph_groups: Dict[
        Tuple[tuple, tuple], List[StateTransitionGraph[dict]]
    ] = dict()
    for graph in graphs:
        ise = graph.get_final_state_edges()
        fse = graph.get_initial_state_edges()
        graph_group = (
            tuple(sorted([json.dumps(graph.edge_props[x]) for x in ise])),
            tuple(sorted([json.dumps(graph.edge_props[x]) for x in fse])),
        )
        if graph_group not in graph_groups:
            graph_groups[graph_group] = []
        graph_groups[graph_group].append(graph)

    graph_group_list = list(graph_groups.values())
    return graph_group_list


def get_graph_group_unique_label(
    graph_group: List[StateTransitionGraph[dict]],
) -> str:
    label = ""
    if graph_group:
        ise = graph_group[0].get_initial_state_edges()
        fse = graph_group[0].get_final_state_edges()
        is_names = _get_name_hel_list(graph_group[0], ise)
        fs_names = _get_name_hel_list(graph_group[0], fse)
        label += (
            generate_particles_string(is_names)
            + "_to_"
            + generate_particles_string(fs_names)
        )
    return label


def determine_attached_final_state_string(
    graph: Topology, edge_id: int
) -> str:
    edge_ids = determine_attached_final_state(graph, edge_id)
    fs_string = ""
    for eid in edge_ids:
        fs_string += " " + str(eid)
    return fs_string[1:]


def determine_attached_final_state(graph: Topology, edge_id: int) -> List[int]:
    """Determine all final state particles of a graph.

    These are attached downward (forward in time) for a given edge (resembling
    the root).
    """
    final_state_edge_ids = []
    all_final_state_edges = graph.get_final_state_edges()
    current_edges = [edge_id]
    while current_edges:
        temp_current_edges = current_edges
        current_edges = []
        for current_edge in temp_current_edges:
            if current_edge in all_final_state_edges:
                final_state_edge_ids.append(current_edge)
            else:
                node_id = graph.edges[current_edge].ending_node_id
                current_edges.extend(
                    graph.get_edges_outgoing_from_node(node_id)
                )
    return final_state_edge_ids


def get_recoil_edge(graph: Topology, edge_id: int) -> Optional[int]:
    """Determine the id of the recoil edge for the specified edge of a graph."""
    node_id = graph.edges[edge_id].originating_node_id
    if node_id is None:
        return None
    outgoing_edges = graph.get_edges_outgoing_from_node(node_id)
    outgoing_edges.remove(edge_id)
    if len(outgoing_edges) != 1:
        raise ValueError(
            f"The node with id {node_id} has more than 2 outgoing edges:\n"
            + str(graph)
        )
    return outgoing_edges[0]


def get_parent_recoil_edge(graph: Topology, edge_id: int) -> Optional[int]:
    """Determine the id of the recoil edge of the parent edge."""
    node_id = graph.edges[edge_id].originating_node_id
    if node_id is None:
        return None
    ingoing_edges = graph.get_edges_ingoing_to_node(node_id)
    if len(ingoing_edges) != 1:
        raise ValueError(
            f"The node with id {node_id} does not have a single ingoing edge!\n"
            + str(graph)
        )
    return get_recoil_edge(graph, ingoing_edges[0])


def get_prefactor(graph: StateTransitionGraph[dict]) -> Optional[float]:
    """Calculate the product of all prefactors defined in this graph."""
    prefactor_label = InteractionQuantumNumberNames.ParityPrefactor
    prefactor = None
    for node_id in graph.nodes:
        if node_id in graph.node_props:
            temp_prefactor = __validate_float_type(
                get_interaction_property(
                    graph.node_props[node_id], prefactor_label
                )
            )
            if temp_prefactor is not None:
                if prefactor is None:
                    prefactor = temp_prefactor
                else:
                    prefactor *= temp_prefactor
            else:
                prefactor = None
                break
    return prefactor


def generate_kinematics(graphs: List[StateTransitionGraph[dict]]) -> dict:
    tempdict: dict = {
        "InitialState": {"Particle": []},
        "FinalState": {"Particle": []},
    }
    is_edge_ids = graphs[0].get_initial_state_edges()
    counter = 0
    for edge_id in is_edge_ids:
        tempdict["InitialState"]["Particle"].append(
            {
                "Name": graphs[0].edge_props[edge_id]["Name"],
                "Id": edge_id,
                "PositionIndex": counter,
            }
        )
        counter += 1
    fs_edge_ids = graphs[0].get_final_state_edges()
    counter = 0
    for edge_id in fs_edge_ids:
        tempdict["FinalState"]["Particle"].append(
            {
                "Name": graphs[0].edge_props[edge_id]["Name"],
                "Id": edge_id,
                "PositionIndex": counter,
            }
        )
        counter += 1
    return {"HelicityKinematics": tempdict}


def generate_particle_list(graphs: List[StateTransitionGraph[dict]]) -> dict:
    # create particle entries
    temp_particle_names = []
    particles = []
    for graph in graphs:
        for edge_props in graph.edge_props.values():
            new_edge_props = remove_spin_projection(edge_props)
            par_name = new_edge_props[Labels.Name.name]
            if par_name not in temp_particle_names:
                particles.append(new_edge_props)
                temp_particle_names.append(par_name)
    return {"ParticleList": {"Particle": particles}}


def _embed_dynamics(graphs: List[StateTransitionGraph[dict]]) -> None:
    decay_info = {Labels.Type.name: "nonResonant"}
    decay_info_label = Labels.DecayInfo.name
    for graph in graphs:
        init_edges = graph.get_initial_state_edges()
        if len(init_edges) > 1:
            raise ValueError("Only a single initial state particle allowed")
        edge_props = graph.edge_props[init_edges[0]]
        edge_props[decay_info_label] = decay_info


def generate_particles_string(
    name_hel_list: List[Tuple[str, float]],
    use_helicity: bool = True,
    make_parity_partner: bool = False,
) -> str:
    string = ""
    for name, hel in name_hel_list:
        string += name
        if use_helicity:
            if make_parity_partner:
                string += "_" + str(-1 * hel)
            else:
                string += "_" + str(hel)
        string += "+"
    return string[:-1]


def _get_name_hel_list(
    graph: StateTransitionGraph[dict], edge_ids: List[int]
) -> List[Tuple[str, float]]:
    name_label = Labels.Name.name
    name_hel_list = []
    for i in edge_ids:
        temp_hel = get_spin_projection(graph.edge_props[i])
        # remove .0
        if temp_hel % 1 == 0:
            temp_hel = int(temp_hel)
        name_hel_list.append((graph.edge_props[i][name_label], temp_hel))

    # in order to ensure correct naming of amplitude coefficients the list has
    # to be sorted by name. The same coefficient names have to be created for
    # two graphs that only differ from a kinematic standpoint
    # (swapped external edges)
    return sorted(name_hel_list, key=lambda entry: entry[0])


class HelicityAmplitudeNameGenerator:
    """Parameter name generator for the helicity formalism."""

    def __init__(self) -> None:
        self.parity_partner_coefficient_mapping: Dict[str, str] = {}

    def _generate_amplitude_coefficient_couple(
        self, graph: StateTransitionGraph[dict], node_id: int
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
        self, graph: StateTransitionGraph[dict]
    ) -> None:
        for node_id in graph.nodes:
            (
                coefficient_suffix,
                parity_partner_coefficient_suffix,
                priority_partner_coefficient_suffix,
            ) = self._generate_amplitude_coefficient_couple(graph, node_id)

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
        self, graph: StateTransitionGraph[dict], node_id: Optional[int] = None
    ) -> str:
        """Generates a unique name for the amplitude corresponding.

        That is, corresponging to the given :class:`StateTransitionGraph`. If
        ``node_id`` is given, it generates a unique name for the partial
        amplitude corresponding to the interaction node of the given
        :class:`StateTransitionGraph`.
        """
        name = ""
        if isinstance(node_id, int):
            nodelist = {node_id}
        else:
            nodelist = graph.nodes
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
        graph: StateTransitionGraph[dict], node_id: int
    ) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]:
        in_edges = graph.get_edges_ingoing_to_node(node_id)
        out_edges = graph.get_edges_outgoing_from_node(node_id)

        in_names_hel_list = _get_name_hel_list(graph, in_edges)
        out_names_hel_list = _get_name_hel_list(graph, out_edges)

        return (in_names_hel_list, out_names_hel_list)

    def generate_amplitude_coefficient_name(
        self, graph: StateTransitionGraph[dict], node_id: int
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
        self, graph: StateTransitionGraph[dict]
    ) -> str:
        """Generate unique suffix for a sequential amplitude graph."""
        output_suffix = ""
        for node_id in graph.nodes:
            raw_suffix = self.generate_amplitude_coefficient_name(
                graph, node_id
            )
            if raw_suffix not in self.parity_partner_coefficient_mapping:
                raise KeyError(
                    f"Coefficient name {raw_suffix} not found in mapping!"
                )
            coefficient_suffix = self.parity_partner_coefficient_mapping[
                raw_suffix
            ]
            output_suffix += coefficient_suffix + ";"
        return output_suffix


class HelicityAmplitudeGenerator:
    """Amplitude model generator for the helicity formalism."""

    def __init__(
        self,
        top_node_no_dynamics: bool = True,
    ) -> None:
        self.particle_list: dict = {}
        self.helicity_amplitudes: dict = {}
        self.kinematics: dict = {}
        self.top_node_no_dynamics = top_node_no_dynamics
        self.name_generator = HelicityAmplitudeNameGenerator()
        self.fit_parameter_names: Set[str] = set()

    def generate(self, graphs: List[StateTransitionGraph[dict]]) -> dict:
        if len(graphs) < 1:
            raise ValueError(
                f"At least one {StateTransitionGraph.__name__} required to"
                " genenerate an amplitude model!"
            )
        if self.top_node_no_dynamics:
            _embed_dynamics(graphs)
        self.particle_list = generate_particle_list(graphs)
        self.kinematics = generate_kinematics(graphs)

        graph_groups = group_graphs_same_initial_and_final(graphs)
        logging.debug("There are %d graph groups", len(graph_groups))

        self.fix_parameters_unambiguously()
        self.create_parameter_couplings(graph_groups)
        self.generate_amplitude_info(graph_groups)

        recipe_dict = self.particle_list
        recipe_dict.update(self.kinematics)
        recipe_dict.update(self.helicity_amplitudes)
        return recipe_dict

    def fix_parameters_unambiguously(self) -> None:
        """Fix parameters, so that the total amplitude is unambiguous.

        "Ambiguous" means with regard to the fit parameters. In other words:
        all fit parameters per graph, except one, will all be fixed. It's fine
        if they are all already fixed.
        """

    def create_parameter_couplings(
        self, graph_groups: List[List[StateTransitionGraph[dict]]]
    ) -> None:
        for graph_group in graph_groups:
            for graph in graph_group:
                self.name_generator.register_amplitude_coefficient_name(graph)

    def generate_amplitude_info(  # pylint: disable=too-many-locals
        self, graph_groups: List[List[StateTransitionGraph[dict]]]
    ) -> None:
        class_label = Labels.Class.name
        name_label = Labels.Name.name
        component_label = Labels.Component.name
        type_label = Labels.Type.name
        parameter_label = Labels.Parameter.name

        # for each graph group we create a coherent amplitude
        coherent_intensities = []
        for graph_group in graph_groups:
            seq_partial_decays = []

            for graph in graph_group:
                sequential_graphs = (
                    perform_external_edge_identical_particle_combinatorics(
                        graph
                    )
                )
                for seq_graph in sequential_graphs:
                    seq_partial_decays.append(
                        self.generate_sequential_decay(seq_graph)
                    )

            # in each coherent amplitude we create a product of partial decays
            coherent_amp_name = "coherent_" + get_graph_group_unique_label(
                graph_group
            )
            coherent_intensities.append(
                {
                    class_label: "CoherentIntensity",
                    component_label: coherent_amp_name,
                    "Amplitude": seq_partial_decays,
                }
            )

        # now wrap it with an incoherent intensity
        incoherent_amp_name = "incoherent"

        if len(coherent_intensities) > 1:
            coherent_intensities_dict = {
                class_label: "IncoherentIntensity",
                "Intensity": coherent_intensities,
            }
        else:
            coherent_intensities_dict = coherent_intensities[0]

        self.helicity_amplitudes = {
            "Intensity": {
                class_label: "StrengthIntensity",
                component_label: incoherent_amp_name + "_with_strength",
                parameter_label: {
                    class_label: "Double",
                    type_label: "Strength",
                    name_label: "strength_" + incoherent_amp_name,
                    "Value": 1,
                    "Fix": True,
                },
                "Intensity": {
                    class_label: "NormalizedIntensity",
                    "Intensity": coherent_intensities_dict,
                },
            }
        }

    def generate_sequential_decay(
        self, graph: StateTransitionGraph[dict]
    ) -> dict:
        # pylint: disable=too-many-locals
        class_label = Labels.Class.name
        name_label = Labels.Name.name
        component_label = Labels.Component.name
        partial_decays = [
            self.generate_partial_decay(graph, node_id)
            for node_id in graph.nodes
        ]

        amp_name = self.name_generator.generate_unique_amplitude_name(graph)
        amp_coefficient_infos = self.generate_amplitude_coefficients(graph)
        sequential_amplitude_dict = {
            class_label: "SequentialAmplitude",
            "Amplitude": partial_decays,
        }

        par_label = Labels.Parameter.name
        coefficient_amplitude_dict = {
            class_label: "CoefficientAmplitude",
            component_label: amp_name,
            par_label: amp_coefficient_infos[par_label],
            "Amplitude": sequential_amplitude_dict,
        }

        prefactor_label = Labels.PreFactor.name
        if prefactor_label in amp_coefficient_infos:
            coefficient_amplitude_dict.update(
                {prefactor_label: amp_coefficient_infos[prefactor_label]}
            )

        self.fit_parameter_names.add(
            amp_coefficient_infos[par_label][0][name_label]
        )
        self.fit_parameter_names.add(
            amp_coefficient_infos[par_label][1][name_label]
        )

        return coefficient_amplitude_dict

    @staticmethod
    def generate_partial_decay(
        graph: StateTransitionGraph[dict], node_id: Optional[int] = None
    ) -> Dict[str, Any]:
        class_label = Labels.Class.name
        name_label = Labels.Name.name
        decay_products = []
        for out_edge_id in graph.get_edges_outgoing_from_node(node_id):
            decay_products.append(
                {
                    name_label: graph.edge_props[out_edge_id][name_label],
                    "FinalState": determine_attached_final_state_string(
                        graph, out_edge_id
                    ),
                    "Helicity": get_spin_projection(
                        graph.edge_props[out_edge_id]
                    ),
                }
            )

        in_edge_ids = graph.get_edges_ingoing_to_node(node_id)
        if len(in_edge_ids) != 1:
            raise ValueError("This node does not represent a two body decay!")
        dec_part = graph.edge_props[in_edge_ids[0]]

        recoil_edge_id = get_recoil_edge(graph, in_edge_ids[0])
        parent_recoil_edge_id = get_parent_recoil_edge(graph, in_edge_ids[0])
        recoil_system_dict = {}
        if recoil_edge_id is not None:
            tempdict = {
                "RecoilFinalState": determine_attached_final_state_string(
                    graph, recoil_edge_id
                )
            }
            if parent_recoil_edge_id is not None:
                tempdict.update(
                    {
                        "ParentRecoilFinalState": determine_attached_final_state_string(
                            graph, parent_recoil_edge_id
                        )
                    }
                )
            recoil_system_dict["RecoilSystem"] = tempdict

        partial_decay_dict: Dict[str, Any] = {
            class_label: "HelicityDecay",
            "DecayParticle": {
                name_label: dec_part[name_label],
                "Helicity": get_spin_projection(dec_part),
            },
            "DecayProducts": {"Particle": decay_products},
        }

        partial_decay_dict.update(recoil_system_dict)

        return partial_decay_dict

    def generate_amplitude_coefficients(
        self, graph: StateTransitionGraph[dict]
    ) -> dict:
        """Generate coefficient info for a sequential amplitude graph.

        Generally, each partial amplitude of a sequential amplitude graph
        should check itself if it or a parity partner is already defined. If so
        a coupled coefficient is introduced.
        """
        seq_par_suffix = (
            self.name_generator.generate_sequential_amplitude_suffix(graph)
        )

        par_label = Labels.Parameter.name
        amplitude_coefficient_infos: dict = {
            par_label: [
                {
                    "Class": "Double",
                    "Type": "Magnitude",
                    "Name": "Magnitude_" + seq_par_suffix,
                    "Value": 1.0,
                    "Fix": False,
                },
                {
                    "Class": "Double",
                    "Type": "Phase",
                    "Name": "Phase_" + seq_par_suffix,
                    "Value": 0.0,
                    "Fix": False,
                },
            ]
        }

        # add potential prefactor
        for node_id in graph.nodes:
            raw_suffix = (
                self.name_generator.generate_amplitude_coefficient_name(
                    graph, node_id
                )
            )
            coefficient_suffix = (
                self.name_generator.parity_partner_coefficient_mapping[
                    raw_suffix
                ]
            )
            if coefficient_suffix != raw_suffix:
                prefactor = get_prefactor(graph)
                if prefactor != 1.0 and prefactor is not None:
                    prefactor_label = Labels.PreFactor.name
                    amplitude_coefficient_infos[prefactor_label] = {
                        "Real": prefactor
                    }

        return amplitude_coefficient_infos


def __validate_float_type(
    interaction_property: Optional[Union[Spin, float]]
) -> Optional[float]:
    if interaction_property is not None and not isinstance(
        interaction_property, (float, int)
    ):
        raise TypeError(
            f"{interaction_property.__class__.__name__} is not of type {float.__name__}"
        )
    return interaction_property
