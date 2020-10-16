from expertsystem.reaction import get_intermediate_state_names
from expertsystem.reaction.solving import Result


def test_get_intermediate_state_names(
    jpsi_to_gamma_pi_pi_helicity_solutions: Result,
):
    states = get_intermediate_state_names(
        jpsi_to_gamma_pi_pi_helicity_solutions.solutions
    )
    assert states == {"f(0)(1500)", "f(0)(980)"}
