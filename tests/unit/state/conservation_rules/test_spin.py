import pytest

from expertsystem.data import Spin
from expertsystem.state.conservation_rules import (
    IsoSpinConservation,
    SpinConservation,
    SpinNodeInput,
)


@pytest.mark.parametrize(
    "rule_input, expected",
    [
        (
            (
                [Spin(0, 0)],
                [Spin(0, 0), Spin(0, 0)],
                SpinNodeInput(l_=Spin(ang_mom_mag, 0.0), s_=Spin(0, 0)),
            ),
            expected,
        )
        for ang_mom_mag, expected in [
            (0, True),
            (1, False),
            (2, False),
            (3, False),
        ]
    ]
    + [
        (
            (
                [Spin(spin_mag, 0)],
                [Spin(0, 0), Spin(0, 0)],
                SpinNodeInput(l_=Spin(spin_mag, 0), s_=Spin(0, 0)),
            ),
            expected,
        )
        for spin_mag, expected in zip([0, 1, 2], [True] * 3)
    ]
    + [
        (
            (
                [Spin(spin_mag, 0)],
                [Spin(1, -1), Spin(1, 1)],
                SpinNodeInput(l_=Spin(1, 0), s_=Spin(spin_mag, 0)),
            ),
            expected,
        )
        for spin_mag, expected in [
            (0, False),
            (1, False),
            (2, False),
            (3, False),
        ]
    ]
    + [
        (
            (
                [Spin(1, -1)],
                [Spin(0, 0), Spin(1, -1)],
                SpinNodeInput(l_=Spin(0, 0), s_=Spin(1, -1)),
            ),
            True,
        ),
        (
            (
                [Spin(1, 0)],
                [Spin(1, 1), Spin(1, -1)],
                SpinNodeInput(l_=Spin(1, 0), s_=Spin(2, 0)),
            ),
            True,
        ),
    ],
)
def test_spin_all_defined(rule_input, expected):
    spin_rule = SpinConservation(use_projection=True)

    assert spin_rule(*rule_input) is expected


@pytest.mark.parametrize(
    "rule_input, expected",
    [
        (
            (
                [Spin(1, 1)],
                [Spin(spin2_mag, 0), Spin(1, -1),],
                SpinNodeInput(
                    l_=Spin(ang_mom_mag, 0), s_=Spin(coupled_spin_mag, -1)
                ),
            ),
            True,
        )
        for spin2_mag, ang_mom_mag, coupled_spin_mag in zip(
            (0, 0, 1), (2, 1, 2), (1, 1, 2)
        )
    ]
    + [
        (
            (
                [Spin(1, 1)],
                [Spin(spin2_mag, 0), Spin(1, -1),],
                SpinNodeInput(
                    l_=Spin(ang_mom_mag, 0), s_=Spin(coupled_spin_mag, 0)
                ),
            ),
            False,
        )
        for spin2_mag, ang_mom_mag, coupled_spin_mag in zip(
            (1, 0, 1), (0, 1, 2), (0, 2, 0)
        )
    ],
)
def test_spin_ignore_z_component(rule_input, expected):
    spin_rule = SpinConservation(False)

    assert spin_rule(*rule_input) is expected


@pytest.mark.parametrize(
    "coupled_isospin_mag, isospin_mag1, isospin_mag2, expected",
    [
        (1, 1, 1, False),
        (2, 1, 1, True),
        (2, 1, 2, False),
        (3, 1, 2, True),
        (0, 2, 2, True),
        (1, 2, 2, False),
        (2, 2, 2, True),
        (3, 2, 2, False),
    ],
)
def test_isospin_clebsch_gordan_zeros(
    coupled_isospin_mag, isospin_mag1, isospin_mag2, expected
):
    isospin_rule = IsoSpinConservation()

    assert (
        isospin_rule(
            [Spin(coupled_isospin_mag, 0)],
            [Spin(isospin_mag1, 0), Spin(isospin_mag2, 0)],
        )
        is expected
    )
