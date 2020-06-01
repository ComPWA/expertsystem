"""Graph module, with its main ingredient, the `.StateTransitionGraph`."""

from collections import OrderedDict
from typing import (
    Callable,
    Dict,
    List,
    Optional,
    Sequence,
)


class StateTransitionGraph:
    """
    Graph class that contains edges and nodes, similar to Feynman graphs.

    The graphs are directed, meaning the edges are ingoing and outgoing to
    specific nodes (since feynman graphs also have a time axis) This class can
    contain the full information of a state transition from a initial state to
    a final state. This information can be attached to the nodes and edges via
    properties.
    """

    def __init__(self) -> None:
        self.nodes: List[int] = []
        self.edges: Dict[int, Edge] = {}
        self.node_props: Dict[int, Dict] = {}
        self.edge_props: Dict[int, Dict] = {}
        self.graph_element_properties_comparator: Optional[Callable] = None

    def set_graph_element_properties_comparator(
        self, comparator: Callable
    ) -> None:
        self.graph_element_properties_comparator = comparator

    def __repr__(self) -> str:
        return_string = (
            f"StateTransitionGraph: nodes: {self.nodes}, edges: {self.edges}\n"
        )
        return_string = return_string + "node props: {\n"
        for node, prop in self.node_props.items():
            return_string = return_string + f"{node}: {prop}\n"
        return_string = return_string + "}\n"
        return_string = return_string + "edge props: {\n"
        for edge, prop in self.edge_props.items():
            return_string = return_string + f"{edge}: {prop}\n"
        return_string = return_string + "}\n"
        return return_string

    def __eq__(self, other: object) -> bool:
        if isinstance(other, StateTransitionGraph):
            if set(self.nodes) != set(other.nodes):
                return False
            if dicts_unequal(self.edges, other.edges):
                return False
            if self.graph_element_properties_comparator is None:
                raise NotImplementedError(
                    "Graph element properties comparator is not set!"
                )
            if not self.graph_element_properties_comparator(
                self.node_props, other.node_props
            ):
                return False
            return self.graph_element_properties_comparator(
                self.edge_props, other.edge_props
            )
        return NotImplemented

    def add_node(self, node_id: int) -> None:
        """Add a node with id node_id.

        Raises:
            ValueError: if node_id already exists
        """
        if node_id in self.nodes:
            raise ValueError(
                "Node with id " + str(node_id) + " already exists!"
            )
        self.nodes.append(node_id)

    def add_edges(self, edge_ids: List[int]) -> None:
        for edge_id in edge_ids:
            if edge_id in self.edges:
                raise ValueError(
                    "Edge with id " + str(edge_id) + " already exists!"
                )
            self.edges[edge_id] = Edge()

    def attach_edges_to_node_ingoing(
        self, ingoing_edge_ids: Sequence[int], node_id: int
    ) -> None:
        # first check if the ingoing edges are all available
        for edge_id in ingoing_edge_ids:
            if edge_id not in self.edges:
                raise ValueError(f"Edge with id {edge_id} does not exist!")
            if self.edges[edge_id].ending_node_id is not None:
                raise ValueError(
                    f"Edge with id {edge_id} is already ingoing "
                    f"to node {self.edges[edge_id].ending_node_id}"
                )
        # update the newly connected edges
        for edge_id in ingoing_edge_ids:
            self.edges[edge_id].ending_node_id = node_id

    def attach_edges_to_node_outgoing(
        self, outgoing_edge_ids: List[int], node_id: int
    ) -> None:
        # first check if the ingoing edges are all available
        for edge_id in outgoing_edge_ids:
            if edge_id not in self.edges:
                raise ValueError(f"Edge with id {edge_id} does not exist!")
            if self.edges[edge_id].originating_node_id is not None:
                raise ValueError(
                    f"Edge with id {edge_id} is already outgoing from "
                    f"node {self.edges[edge_id].originating_node_id}"
                )
        # update the edges
        for edge_id in outgoing_edge_ids:
            self.edges[edge_id].originating_node_id = node_id

    def get_originating_node_list(self, edge_ids: Sequence[int]) -> List[int]:
        """Get list of node ids from which the supplied edges originate."""
        node_list: List[int] = []
        for edge_id in edge_ids:
            originating_node = self.edges[edge_id].originating_node_id
            if originating_node is not None:
                node_list.append(originating_node)
        return node_list

    def swap_edges(self, edge_id1: int, edge_id2: int) -> None:
        old_edge1 = self.edges.pop(edge_id1)
        old_edge2 = self.edges.pop(edge_id2)
        self.edges[edge_id2] = old_edge1
        self.edges[edge_id1] = old_edge2

        val1 = None
        val2 = None
        if edge_id1 in self.edge_props:
            val1 = self.edge_props.pop(edge_id1)
        if edge_id2 in self.edge_props:
            val2 = self.edge_props.pop(edge_id2)
        if val1:
            self.edge_props[edge_id2] = val1
        if val2:
            self.edge_props[edge_id1] = val2

    def verify(self) -> bool:
        """Verify whether the graph is connected.

        Returns:
            True if no dangling parts which are not connected.
        """
        # pylint: disable=no-self-use
        # TODO: Implement verify False as well
        return True


class InteractionNode:
    """Struct-like definition of an interaction node."""

    # pylint: disable=too-few-public-methods
    # TODO: Turn InteractionNode into a data class

    def __init__(
        self,
        type_name: str,
        number_of_ingoing_edges: int,
        number_of_outgoing_edges: int,
    ):
        self.type_name = str(type_name)
        self.number_of_ingoing_edges = int(number_of_ingoing_edges)
        self.number_of_outgoing_edges = int(number_of_outgoing_edges)
        if self.number_of_ingoing_edges < 1:
            raise ValueError("NumberOfIngoingEdges has to be larger than 0")
        if self.number_of_outgoing_edges < 1:
            raise ValueError("NumberOfOutgoingEdges has to be larger than 0")


class Edge:
    """struct-like definition of an edge"""

    def __init__(self) -> None:
        self.ending_node_id: Optional[int] = None
        self.originating_node_id: Optional[int] = None

    def __repr__(self) -> str:
        return str((self.ending_node_id, self.originating_node_id))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Edge):
            return (
                self.ending_node_id == other.ending_node_id
                and self.originating_node_id == other.originating_node_id
            )
        return NotImplemented


def are_graphs_isomorphic(  # pylint: disable=unused-argument
    graph1: StateTransitionGraph, graph2: StateTransitionGraph
) -> bool:
    """Check if two graphs are isomorphic.

    Returns:
        ``True`` if two graphs have a one-to-one mapping of the node IDs and
        edge IDs.
    """
    # TODO: https://github.com/ComPWA/expertsystem/issues/5
    return False


def get_initial_state_edges(graph: StateTransitionGraph) -> List[int]:
    if not isinstance(graph, StateTransitionGraph):
        raise TypeError("graph must be a StateTransitionGraph")
    initial_state_edges: List[int] = []
    for edge_id, edge in graph.edges.items():
        if edge.originating_node_id is None:
            initial_state_edges.append(edge_id)
    return sorted(initial_state_edges)


def get_final_state_edges(graph: StateTransitionGraph) -> List[int]:
    fs_list: List[int] = []
    for edge_id, edge in graph.edges.items():
        if edge.ending_node_id is None:
            fs_list.append(edge_id)
    return sorted(fs_list)


def get_intermediate_state_edges(graph: StateTransitionGraph) -> List[int]:
    final_state_edges: List[int] = []
    for edge_id, edge in graph.edges.items():
        if (
            edge.ending_node_id is not None
            and edge.originating_node_id is not None
        ):
            final_state_edges.append(edge_id)
    return sorted(final_state_edges)


def get_edges_ingoing_to_node(
    graph: StateTransitionGraph, node_id: int
) -> List[int]:
    if not isinstance(graph, StateTransitionGraph):
        raise TypeError("graph must be a StateTransitionGraph")
    edge_list: List[int] = []
    for edge_id, edge in graph.edges.items():
        if edge.ending_node_id == node_id:
            edge_list.append(edge_id)
    return edge_list


def get_edges_outgoing_to_node(
    graph: StateTransitionGraph, node_id: int
) -> List[int]:
    if not isinstance(graph, StateTransitionGraph):
        raise TypeError("graph must be a StateTransitionGraph")
    edge_list: List[int] = []
    for edge_id, edge in graph.edges.items():
        if edge.originating_node_id == node_id:
            edge_list.append(edge_id)
    return edge_list


def get_originating_final_state_edges(
    graph: StateTransitionGraph, node_id: int
) -> List[int]:
    if not isinstance(graph, StateTransitionGraph):
        raise TypeError("graph must be a StateTransitionGraph")
    final_state_edges: List[int] = get_final_state_edges(graph)
    edge_list: List[int] = []
    temp_edge_list = get_edges_outgoing_to_node(graph, node_id)
    while temp_edge_list:
        new_temp_edge_list = []
        for edge_id in temp_edge_list:
            if edge_id in final_state_edges:
                edge_list.append(edge_id)
            else:
                new_node_id = graph.edges[edge_id].ending_node_id
                if new_node_id is not None:
                    new_temp_edge_list.extend(
                        get_edges_outgoing_to_node(graph, new_node_id)
                    )
        temp_edge_list = new_temp_edge_list
    return edge_list


def get_originating_initial_state_edges(
    graph: StateTransitionGraph, node_id: int
) -> List[int]:
    if not isinstance(graph, StateTransitionGraph):
        raise TypeError("graph must be a StateTransitionGraph")
    is_edges = get_initial_state_edges(graph)
    edge_list = []
    temp_edge_list = get_edges_ingoing_to_node(graph, node_id)
    while temp_edge_list:
        new_temp_edge_list = []
        for edge_id in temp_edge_list:
            if edge_id in is_edges:
                edge_list.append(edge_id)
            else:
                new_node_id = graph.edges[edge_id].originating_node_id
                if new_node_id is not None:
                    new_temp_edge_list.extend(
                        get_edges_ingoing_to_node(graph, new_node_id)
                    )
        temp_edge_list = new_temp_edge_list
    return edge_list


def dicts_unequal(dict1: dict, dict2: dict) -> bool:
    return OrderedDict(sorted(dict1.items())) != OrderedDict(
        sorted(dict2.items())
    )
