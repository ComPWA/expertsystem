import pydot

from expertsystem.topology.graph import DotGenerator


def test_dot_syntax(jpsi_to_gamma_pi_pi_helicity_solutions):
    for i in jpsi_to_gamma_pi_pi_helicity_solutions:
        dot_data = DotGenerator.from_graph(i)
        assert pydot.graph_from_dot_data(dot_data) is not None
