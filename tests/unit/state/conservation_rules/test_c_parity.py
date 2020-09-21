from itertools import product

import pytest

from expertsystem.data import Parity
from expertsystem.state.conservation_rules import (
    CParityConservation,
    CParityEdgeInput,
    CParityNodeInput,
)


@pytest.mark.parametrize(
    "rule_input, expected",
    [
        (
            (
                [CParityEdgeInput(spin_mag=0.0, pid=1, c_parity=Parity(-1))],
                [
                    CParityEdgeInput(spin_mag=0.0, pid=1, c_parity=Parity(-1)),
                    CParityEdgeInput(spin_mag=0.0, pid=1, c_parity=Parity(1)),
                ],
                None,
            ),
            True,
        ),
        (
            (
                [CParityEdgeInput(spin_mag=0.0, pid=1, c_parity=Parity(1))],
                [
                    CParityEdgeInput(spin_mag=0.0, pid=1, c_parity=Parity(-1)),
                    CParityEdgeInput(spin_mag=0.0, pid=1, c_parity=Parity(1)),
                ],
                None,
            ),
            False,
        ),
    ],
)
def test_c_parity_all_defined(rule_input, expected):
    rule = CParityConservation()

    assert rule(*rule_input) is expected


@pytest.mark.parametrize(
    "rule_input, expected",
    [
        (
            (
                [
                    CParityEdgeInput(
                        spin_mag=0, pid=123, c_parity=Parity(c_parity)
                    )
                ],
                [
                    CParityEdgeInput(spin_mag=0, pid=100),
                    CParityEdgeInput(spin_mag=0, pid=-100),
                ],
                CParityNodeInput(l_mag=l_mag, s_mag=0),
            ),
            (-1) ** l_mag == c_parity,
        )
        for c_parity, l_mag in product([-1, 1], range(0, 5))
    ],
)
def test_c_parity_multiparticle_boson(rule_input, expected):
    rule = CParityConservation()

    assert rule(*rule_input) is expected


@pytest.mark.parametrize(
    "rule_input, expected",
    [
        (
            (
                [
                    CParityEdgeInput(
                        spin_mag=0, pid=123, c_parity=Parity(c_parity)
                    )
                ],
                [
                    CParityEdgeInput(spin_mag=0.5, pid=100),
                    CParityEdgeInput(spin_mag=0.5, pid=-100),
                ],
                CParityNodeInput(l_mag=l_mag, s_mag=s_mag),
            ),
            (s_mag + l_mag) % 2 == abs(c_parity - 1) / 2,
        )
        for c_parity, s_mag, l_mag in product(
            [-1, 1], range(0, 5), range(0, 5)
        )
    ],
)
def test_c_parity_multiparticle_fermion(rule_input, expected):
    rule = CParityConservation()

    assert rule(*rule_input) is expected
