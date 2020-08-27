import pydot

import pytest

from expertsystem import io


def test_dot_syntax(jpsi_to_gamma_pi_pi_helicity_solutions):
    for i in jpsi_to_gamma_pi_pi_helicity_solutions:
        dot_data = io.dot.convert_to_dot(i)
        assert pydot.graph_from_dot_data(dot_data) is not None


def test_write_dot(jpsi_to_gamma_pi_pi_helicity_solutions):
    single_graph_filename = "test_write_dot.gv"
    multi_graph_filename = "test_write_dot_multi.gv"
    with pytest.raises(NotImplementedError):
        io.write(
            instance="nope, can't write a str", filename=single_graph_filename,
        )
    io.write(
        instance=jpsi_to_gamma_pi_pi_helicity_solutions[0],
        filename=single_graph_filename,
    )
    io.write(
        instance=jpsi_to_gamma_pi_pi_helicity_solutions,
        filename=multi_graph_filename,
    )
    for filename in [single_graph_filename, multi_graph_filename]:
        with open(filename, "r") as stream:
            dot_data = stream.read()
        assert pydot.graph_from_dot_data(dot_data) is not None
