import pytest

import expertsystem as es
from expertsystem.reaction import Result


@pytest.mark.parametrize(
    "formalism_type, n_solutions",
    [
        ("helicity", 14),
        ("canonical-helicity", 28),  # two different LS couplings 2*14 = 28
    ],
)
def test_simple(formalism_type, n_solutions, particle_database):
    result = es.generate_transitions(
        initial_state=[("Y(4260)", [-1, +1])],
        final_state=["D*(2007)0", "D*(2007)~0"],
        particles=particle_database,
        formalism_type=formalism_type,
        allowed_interaction_types="strong",
        number_of_threads=1,
    )
    assert len(result.transitions) == n_solutions
    model = es.generate_amplitudes(result)
    assert len(model.parameters) == 9


@pytest.mark.slow
@pytest.mark.parametrize(
    "formalism_type, n_solutions",
    [
        ("helicity", 14),
        ("canonical-helicity", 28),  # two different LS couplings 2*14 = 28
    ],
)
def test_full(y_to_d0_d0bar_pi0_pi0, formalism_type, n_solutions):
    result: Result = y_to_d0_d0bar_pi0_pi0(formalism_type)
    assert len(result.transitions) == n_solutions
    model = es.generate_amplitudes(result)
    assert len(model.parameters) == 9
