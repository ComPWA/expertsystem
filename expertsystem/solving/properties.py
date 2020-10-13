"""Collection of data structures and functions for `.topology` properties.

In a `.StateTransitionGraph`, the edges represent quantum states, while the
nodes represent interactions. This module provides tools to modify or extract
these properties.
"""
from collections import OrderedDict
from copy import deepcopy
from itertools import permutations
from typing import Dict, List, Set

from expertsystem.particles import ParticleCollection

from .topology import StateTransitionGraph
from .types import ParticleWithSpin


def filter_particles(
    particle_db: ParticleCollection,
    allowed_particle_names: List[str],
) -> ParticleCollection:
    """Filters `.ParticleCollection` based on the allowed particle names."""
    allowed_particles = ParticleCollection()
    if len(allowed_particle_names) == 0:
        return particle_db

    for particle_name in allowed_particle_names:
        # if isinstance(particle_label, int):
        #     allowed_particles.add(particle_db.find(particle_label))
        # elif isinstance(particle_label, str):
        subset = particle_db.filter(
            lambda p: particle_name  # pylint: disable=cell-var-from-loop
            in p.name
        )
        allowed_particles.update(subset)
    return allowed_particles


def match_external_edges(
    graphs: List[StateTransitionGraph[ParticleWithSpin]],
) -> None:
    if not isinstance(graphs, list):
        raise TypeError("graphs argument is not of type list!")
    if not graphs:
        return
    ref_graph_id = 0
    _match_external_edge_ids(graphs, ref_graph_id, "get_final_state_edges")
    _match_external_edge_ids(graphs, ref_graph_id, "get_initial_state_edges")


def _match_external_edge_ids(  # pylint: disable=too-many-locals
    graphs: List[StateTransitionGraph[ParticleWithSpin]],
    ref_graph_id: int,
    external_edge_getter_function: str,
) -> None:
    ref_graph = graphs[ref_graph_id]
    # create external edge to particle mapping
    ref_edge_id_particle_mapping = _create_edge_id_particle_mapping(
        ref_graph, external_edge_getter_function
    )

    for graph in graphs[:ref_graph_id] + graphs[ref_graph_id + 1 :]:
        edge_id_particle_mapping = _create_edge_id_particle_mapping(
            graph, external_edge_getter_function
        )
        # remove matching entries
        ref_mapping_copy = deepcopy(ref_edge_id_particle_mapping)
        edge_ids_mapping = {}
        for key, value in edge_id_particle_mapping.items():
            if key in ref_mapping_copy and value == ref_mapping_copy[key]:
                del ref_mapping_copy[key]
            else:
                for key_2, value_2 in ref_mapping_copy.items():
                    if value == value_2:
                        edge_ids_mapping[key] = key_2
                        del ref_mapping_copy[key_2]
                        break
        if len(ref_mapping_copy) != 0:
            raise ValueError(
                "Unable to match graphs, due to inherent graph"
                " structure mismatch"
            )
        swappings = _calculate_swappings(edge_ids_mapping)
        for edge_id1, edge_id2 in swappings.items():
            graph.swap_edges(edge_id1, edge_id2)


def perform_external_edge_identical_particle_combinatorics(
    graph: StateTransitionGraph,
) -> List[StateTransitionGraph]:
    """Create combinatorics clones of the `.StateTransitionGraph`.

    In case of identical particles in the initial or final state. Only
    identical particles, which do not enter or exit the same node allow for
    combinatorics!
    """
    if not isinstance(graph, StateTransitionGraph):
        raise TypeError("graph argument is not of type StateTransitionGraph!")
    temp_new_graphs = _external_edge_identical_particle_combinatorics(
        graph, "get_final_state_edges"
    )
    new_graphs = []
    for new_graph in temp_new_graphs:
        new_graphs.extend(
            _external_edge_identical_particle_combinatorics(
                new_graph, "get_initial_state_edges"
            )
        )
    return new_graphs


def _external_edge_identical_particle_combinatorics(
    graph: StateTransitionGraph[ParticleWithSpin],
    external_edge_getter_function: str,
) -> List[StateTransitionGraph]:
    # pylint: disable=too-many-locals
    new_graphs = [graph]
    edge_particle_mapping = _create_edge_id_particle_mapping(
        graph, external_edge_getter_function
    )
    identical_particle_groups: Dict[str, Set[int]] = {}
    for key, value in edge_particle_mapping.items():
        if value not in identical_particle_groups:
            identical_particle_groups[value] = set()
        identical_particle_groups[value].add(key)
    identical_particle_groups = {
        key: value
        for key, value in identical_particle_groups.items()
        if len(value) > 1
    }
    # now for each identical particle group perform all permutations
    for edge_group in identical_particle_groups.values():
        combinations = permutations(edge_group)
        graph_combinations = set()
        ext_edge_combinations = []
        ref_node_origin = graph.get_originating_node_list(edge_group)
        for comb in combinations:
            temp_edge_node_mapping = tuple(sorted(zip(comb, ref_node_origin)))
            if temp_edge_node_mapping not in graph_combinations:
                graph_combinations.add(temp_edge_node_mapping)
                ext_edge_combinations.append(dict(zip(edge_group, comb)))
        temp_new_graphs = []
        for new_graph in new_graphs:
            for combination in ext_edge_combinations:
                graph_copy = deepcopy(new_graph)
                swappings = _calculate_swappings(combination)
                for edge_id1, edge_id2 in swappings.items():
                    graph_copy.swap_edges(edge_id1, edge_id2)
                temp_new_graphs.append(graph_copy)
        new_graphs = temp_new_graphs
    return new_graphs


def _calculate_swappings(id_mapping: Dict[int, int]) -> OrderedDict:
    """Calculate edge id swappings.

    Its important to use an ordered dict as the swappings do not commute!
    """
    swappings: OrderedDict = OrderedDict()
    for key, value in id_mapping.items():
        # go through existing swappings and use them
        newkey = key
        while newkey in swappings:
            newkey = swappings[newkey]
        if value != newkey:
            swappings[value] = newkey
    return swappings


def _create_edge_id_particle_mapping(
    graph: StateTransitionGraph[ParticleWithSpin],
    external_edge_getter_function: str,
) -> Dict[int, str]:
    return {
        i: graph.edge_props[i][0].name
        for i in getattr(graph, external_edge_getter_function)()
    }
