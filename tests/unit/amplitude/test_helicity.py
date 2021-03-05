import pytest
import sympy as sp

from expertsystem.amplitude import get_builder
from expertsystem.amplitude.helicity import (
    ParameterProperties,
    SuggestedParameterValues,
)
from expertsystem.reaction import Result


@pytest.mark.parametrize(
    "formalism, n_amplitudes", [("canonical", 16), ("helicity", 8)]
)
def test_generate(
    formalism: str,
    n_amplitudes: int,
    jpsi_to_gamma_pi_pi_canonical_solutions: Result,
    jpsi_to_gamma_pi_pi_helicity_solutions: Result,
):
    if formalism == "canonical":
        result = jpsi_to_gamma_pi_pi_canonical_solutions
    elif formalism == "helicity":
        result = jpsi_to_gamma_pi_pi_helicity_solutions
    else:
        raise NotImplementedError
    sympy_model = get_builder(result).generate()
    assert len(sympy_model.parameters) == 2
    assert len(sympy_model.components) == 4 + n_amplitudes


class TestSuggestedParameterValues:
    @staticmethod
    @pytest.fixture(scope="session")
    def dummy_parameters():
        return SuggestedParameterValues(
            {
                sp.Symbol("par1"): 1.0,
                sp.Symbol("par2"): complex(0, 1),
                sp.Symbol("par3"): -1.0,
                sp.Symbol("par4"): complex(-1, 0),
            }
        )

    @staticmethod
    @pytest.mark.parametrize("container", [SuggestedParameterValues, dict])
    def test_not_singleton(container):
        parameters1 = container()
        parameters1[sp.Symbol("par1")] = ParameterProperties(1)
        parameters1[sp.Symbol("par2")] = ParameterProperties(2)
        assert len(parameters1) == 2
        parameters2 = container()
        parameters2[sp.Symbol("par3")] = ParameterProperties(1)
        assert len(parameters2) == 1

    @staticmethod
    @pytest.mark.parametrize(
        "value",
        [
            int(1),
            float(1.0),
            complex(1.0, 1.0),
        ],
    )
    def test_key_value_conversion(value):
        parameters = SuggestedParameterValues()
        parameters["par1"] = value
        assert "par1" in parameters
        assert sp.Symbol("par1") in parameters
        assert parameters["par1"].value == value

    @staticmethod
    def test_init():
        parameters = SuggestedParameterValues(
            {
                "par1": 1.0,
                "par2": complex(0.0, 1.0),
                sp.Symbol("par3"): -1.0,
                sp.Symbol("par4"): ParameterProperties(complex(-1, 0)),
            }
        )
        for par, value in parameters.items():
            assert isinstance(par, sp.Symbol)
            assert isinstance(value, ParameterProperties)
            assert par.name.startswith("par")
            assert abs(value.value) == 1.0

    @staticmethod
    def test_len(dummy_parameters: SuggestedParameterValues):
        assert len(dummy_parameters) == 4

    @staticmethod
    def test_repr(dummy_parameters: SuggestedParameterValues):
        repr_str = repr(dummy_parameters)
        assert eval(repr_str) == dummy_parameters  # pylint: disable=eval-used

    @staticmethod
    def test_subs_values(dummy_parameters: SuggestedParameterValues):
        assert dummy_parameters.subs_values() == {
            sp.Symbol("par1"): 1.0,
            sp.Symbol("par2"): complex(0, 1),
            sp.Symbol("par3"): -1.0,
            sp.Symbol("par4"): complex(-1, 0),
        }
