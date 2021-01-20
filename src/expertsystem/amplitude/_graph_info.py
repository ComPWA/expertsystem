from typing import Dict, List, Optional, Tuple, Union

from expertsystem.amplitude.model import Kinematics
from expertsystem.particle import ParticleCollection, Spin
from expertsystem.reaction import Result
from expertsystem.reaction.quantum_numbers import ParticleWithSpin
from expertsystem.reaction.topology import StateTransitionGraph


def group_graphs_same_initial_and_final(
    graphs: List[StateTransitionGraph[ParticleWithSpin]],
) -> List[List[StateTransitionGraph[ParticleWithSpin]]]:
    """Match final and initial states in groups.

    Each graph corresponds to a specific state transition amplitude.
    This function groups together graphs, which have the same initial and final
    state (including spin). This is needed to determine the coherency of the
    individual amplitude parts.
    """
    graph_groups: Dict[
        Tuple[tuple, tuple], List[StateTransitionGraph[ParticleWithSpin]]
    ] = dict()
    for graph in graphs:
        ise = graph.get_final_state_edge_ids()
        fse = graph.get_initial_state_edge_ids()
        graph_group = (
            tuple(
                sorted(
                    [
                        (
                            graph.get_edge_props(x)[0].name,
                            graph.get_edge_props(x)[1],
                        )
                        for x in ise
                    ]
                )
            ),
            tuple(
                sorted(
                    [
                        (
                            graph.get_edge_props(x)[0].name,
                            graph.get_edge_props(x)[1],
                        )
                        for x in fse
                    ]
                )
            ),
        )
        if graph_group not in graph_groups:
            graph_groups[graph_group] = []
        graph_groups[graph_group].append(graph)

    graph_group_list = list(graph_groups.values())
    return graph_group_list


def get_graph_group_unique_label(
    graph_group: List[StateTransitionGraph[ParticleWithSpin]],
) -> str:
    label = ""
    if graph_group:
        ise = graph_group[0].get_initial_state_edge_ids()
        fse = graph_group[0].get_final_state_edge_ids()
        is_names = get_name_hel_list(graph_group[0], ise)
        fs_names = get_name_hel_list(graph_group[0], fse)
        label += (
            generate_particles_string(is_names)
            + "_to_"
            + generate_particles_string(fs_names)
        )
    return label


def determine_attached_final_state(
    graph: StateTransitionGraph[ParticleWithSpin], edge_id: int
) -> List[int]:
    """Determine all final state particles of a graph.

    These are attached downward (forward in time) for a given edge (resembling
    the root).
    """
    final_state_edge_ids = []
    all_final_state_edges = graph.get_final_state_edge_ids()
    current_edges = [edge_id]
    while current_edges:
        temp_current_edges = current_edges
        current_edges = []
        for current_edge in temp_current_edges:
            if current_edge in all_final_state_edges:
                final_state_edge_ids.append(current_edge)
            else:
                node_id = graph.edges[current_edge].ending_node_id
                if node_id:
                    current_edges.extend(
                        graph.get_edge_ids_outgoing_from_node(node_id)
                    )
    return final_state_edge_ids


def get_recoil_edge(
    graph: StateTransitionGraph[ParticleWithSpin], edge_id: int
) -> Optional[int]:
    """Determine the id of the recoil edge for the specified edge of a graph."""
    node_id = graph.edges[edge_id].originating_node_id
    if node_id is None:
        return None
    outgoing_edges = graph.get_edge_ids_outgoing_from_node(node_id)
    outgoing_edges.remove(edge_id)
    if len(outgoing_edges) != 1:
        raise ValueError(
            f"The node with id {node_id} has more than 2 outgoing edges:\n"
            + str(graph)
        )
    return outgoing_edges[0]


def get_parent_recoil_edge(
    graph: StateTransitionGraph[ParticleWithSpin], edge_id: int
) -> Optional[int]:
    """Determine the id of the recoil edge of the parent edge."""
    node_id = graph.edges[edge_id].originating_node_id
    if node_id is None:
        return None
    ingoing_edges = graph.get_edge_ids_ingoing_to_node(node_id)
    if len(ingoing_edges) != 1:
        raise ValueError(
            f"The node with id {node_id} does not have a single ingoing edge!\n"
            + str(graph)
        )
    return get_recoil_edge(graph, ingoing_edges[0])


def get_prefactor(
    graph: StateTransitionGraph[ParticleWithSpin],
) -> float:
    """Calculate the product of all prefactors defined in this graph."""
    prefactor = 1.0
    for node_id in graph.nodes:
        node_props = graph.get_node_props(node_id)
        if node_props:
            temp_prefactor = __validate_float_type(node_props.parity_prefactor)
            if temp_prefactor is not None:
                prefactor *= temp_prefactor
    return prefactor


def generate_particle_collection(
    graphs: List[StateTransitionGraph[ParticleWithSpin]],
) -> ParticleCollection:
    particles = ParticleCollection()
    for graph in graphs:
        for edge_props in map(graph.get_edge_props, graph.edges):
            particle_name = edge_props[0].name
            if particle_name not in particles:
                particles.add(edge_props[0])
    return particles


def generate_kinematics(result: Result) -> Kinematics:
    graph = next(iter(result.solutions))
    return Kinematics.from_graph(graph)


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


def get_name_hel_list(
    graph: StateTransitionGraph[ParticleWithSpin], edge_ids: List[int]
) -> List[Tuple[str, float]]:
    name_hel_list = []
    for i in edge_ids:
        temp_hel = graph.get_edge_props(i)[1]
        # remove .0
        if temp_hel % 1 == 0:
            temp_hel = int(temp_hel)
        name_hel_list.append((graph.get_edge_props(i)[0].name, temp_hel))

    # in order to ensure correct naming of amplitude coefficients the list has
    # to be sorted by name. The same coefficient names have to be created for
    # two graphs that only differ from a kinematic standpoint
    # (swapped external edges)
    return sorted(name_hel_list, key=lambda entry: entry[0])


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
