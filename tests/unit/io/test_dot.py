import pydot

from expertsystem.io.dot import convert_to_dot


def test_dot_syntax(jpsi_to_gamma_pi_pi_helicity_solutions):
    for i in jpsi_to_gamma_pi_pi_helicity_solutions:
        dot_data = convert_to_dot(i)
        assert pydot.graph_from_dot_data(dot_data) is not None
