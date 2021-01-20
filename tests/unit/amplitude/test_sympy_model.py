from expertsystem.amplitude import generate_sympy
from expertsystem.reaction import Result


def test_generate(jpsi_to_gamma_pi_pi_helicity_solutions: Result):
    result = jpsi_to_gamma_pi_pi_helicity_solutions
    sympy_model = generate_sympy(result)
    assert len(sympy_model.parameters) == 2
    assert len(sympy_model.expression.dynamics) == 4
    assert len(sympy_model.expression.intensities) == 4
    assert len(sympy_model.expression.amplitudes) == 8
