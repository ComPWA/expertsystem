from typing import Callable

import pytest

from expertsystem.particle import ParticleCollection
from expertsystem.reaction import (
    Result,
    StateTransitionManager,
    load_default_particles,
)
from expertsystem.reaction.default_settings import InteractionTypes


@pytest.fixture(scope="session")
def particle_database() -> ParticleCollection:
    return load_default_particles()


@pytest.fixture(scope="session")
def output_dir(pytestconfig) -> str:
    return f"{pytestconfig.rootpath}/tests/output/"


@pytest.fixture(scope="session")
def y_to_d0_d0bar_pi0_pi0() -> Callable[[str], Result]:
    def _y_to_d0_d0bar_pi0_pi0(formalism: str) -> Result:
        stm = StateTransitionManager(
            initial_state=[("Y(4260)", [-1, +1])],
            final_state=["D0", "D~0", "pi0", "pi0"],
            allowed_intermediate_particles=["D*"],
            formalism_type=formalism,
            number_of_threads=1,
        )
        stm.set_allowed_interaction_types([InteractionTypes.Strong])
        stm.add_final_state_grouping([["D0", "pi0"], ["D~0", "pi0"]])
        problem_sets = stm.create_problem_sets()
        return stm.find_solutions(problem_sets)

    return _y_to_d0_d0bar_pi0_pi0
