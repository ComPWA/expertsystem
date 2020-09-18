import pytest

from expertsystem.topology import (
    Edge,
    InteractionNode,
    SimpleStateTransitionTopologyBuilder,
    Topology,
)


class TestEdge:
    @staticmethod
    def test_get_connected_nodes():
        edge = Edge(1, 2)
        assert edge.get_connected_nodes() == {1, 2}
        edge = Edge(originating_node_id=3)
        assert edge.get_connected_nodes() == {3}
        edge = Edge(ending_node_id=4)
        assert edge.get_connected_nodes() == {4}


class TestTopology:
    @staticmethod
    def test_constructor_exceptions():
        with pytest.raises(ValueError):
            assert Topology(edges={0: Edge(None, 1)})
        with pytest.raises(ValueError):
            assert Topology(nodes={0}, edges={0: Edge(1, None)})
        with pytest.raises(ValueError):
            assert Topology(edges={0: Edge(None, None)})
        topology = Topology(nodes={0}, edges={0: Edge(0, None)})
        assert len(topology.nodes) == 1

    @staticmethod
    def test_repr_and_eq(dummy_topology):
        topology = eval(str(dummy_topology))  # pylint: disable=eval-used
        assert topology == dummy_topology
        with pytest.raises(NotImplementedError):
            assert topology == float()

    @staticmethod
    def test_get_surrounding_nodes(dummy_topology):
        assert dummy_topology.get_surrounding_nodes(0) == dummy_topology.nodes
        assert dummy_topology.get_surrounding_nodes(1) == dummy_topology.nodes


class TestInteractionNode:
    @staticmethod
    def test_constructor_exceptions():
        dummy_type_name = "type_name"
        with pytest.raises(TypeError):
            assert InteractionNode(
                dummy_type_name,
                number_of_ingoing_edges="has to be int",  # type: ignore
                number_of_outgoing_edges=2,
            )
        with pytest.raises(TypeError):
            assert InteractionNode(
                dummy_type_name,
                number_of_outgoing_edges="has to be int",  # type: ignore
                number_of_ingoing_edges=2,
            )
        with pytest.raises(ValueError):
            assert InteractionNode(
                dummy_type_name,
                number_of_outgoing_edges=0,
                number_of_ingoing_edges=1,
            )
        with pytest.raises(ValueError):
            assert InteractionNode(
                dummy_type_name,
                number_of_outgoing_edges=1,
                number_of_ingoing_edges=0,
            )


class TestSimpleStateTransitionTopologyBuilder:
    @staticmethod
    def test_two_body_states():
        two_body_decay_node = InteractionNode("TwoBodyDecay", 1, 2)

        simple_builder = SimpleStateTransitionTopologyBuilder(
            [two_body_decay_node]
        )

        all_graphs = simple_builder.build_graphs(1, 3)

        assert len(all_graphs) == 1
