import pytest
import sympy as sy

from expertsystem.amplitude import generate_sympy
from expertsystem.amplitude.sympy import (
    ParameterProperties,
    SuggestedParameterValues,
)
from expertsystem.reaction import Result


def test_generate(jpsi_to_gamma_pi_pi_helicity_solutions: Result):
    result = jpsi_to_gamma_pi_pi_helicity_solutions
    sympy_model = generate_sympy(result)
    assert len(sympy_model.parameters) == 2
    assert len(sympy_model.expression.dynamics) == 4
    assert len(sympy_model.expression.intensities) == 4
    assert len(sympy_model.expression.amplitudes) == 8


class TestSuggestedParameterValues:
    @staticmethod
    @pytest.mark.parametrize("container", [SuggestedParameterValues, dict])
    def test_not_singleton(container):
        parameters1 = container()
        parameters1[sy.Symbol("par1")] = ParameterProperties(1)
        parameters1[sy.Symbol("par2")] = ParameterProperties(2)
        assert len(parameters1) == 2
        parameters2 = container()
        parameters2[sy.Symbol("par3")] = ParameterProperties(1)
        assert len(parameters2) == 1
