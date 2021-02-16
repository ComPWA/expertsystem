# pylint: disable=no-self-use
import pytest

from expertsystem.amplitude.kinematics import (
    SubSystem,
    _to_sorted_tuple,
    _to_sorted_tuple_pair,
)


class TestSubSystem:
    @pytest.mark.parametrize(
        "final_states, recoil_state, expected_final_states, expected_recoil_state",
        [
            ([[3, 4], [2]], None, ((3, 4), (2,)), tuple()),
            ([[3], [4]], [2], ((3,), (4,)), (2,)),
            ([[1, 2], [2]], [], None, None),
            ([[1, 2], []], [1], None, None),
        ],
    )
    def test_init(
        self,
        final_states,
        recoil_state,
        expected_final_states,
        expected_recoil_state,
    ):
        if expected_final_states is None or expected_recoil_state is None:
            with pytest.raises(ValueError):
                SubSystem(final_states, recoil_state)
        else:
            subsystem = SubSystem(final_states, recoil_state)
            assert subsystem.final_states == expected_final_states
            assert subsystem.recoil_state == expected_recoil_state

    @pytest.mark.parametrize(
        "final_states, recoil_state, description",
        [
            # 3-body
            ([[3, 4], [2]], None, "3+4_2"),
            ([[3], [4]], [2], "3_4_vs_2"),
            # 5-body
            ([[1, 2, 3], [4, 5]], None, "1+2+3_4+5"),
            ([[1, 2, 3], [4, 5]], None, "1+2+3_4+5"),
            ([[1, 2], [3]], [4, 5], "1+2_3_vs_4+5"),
            ([[1], [2]], [3], "1_2_vs_3"),
            ([[4], [5]], [1, 2, 3], "4_5_vs_1+2+3"),
        ],
    )
    def test_description(
        self,
        final_states,
        recoil_state,
        description,
    ):
        subsystem = SubSystem(final_states, recoil_state)
        assert subsystem.description == description


@pytest.mark.parametrize(
    "iterable, expected",
    [
        (1, None),
        ([1.5, 2.5], None),
        (None, tuple()),
        ([5, 4, 3], (3, 4, 5)),
        ([1, 2, 3, 3], (1, 2, 3, 3)),
    ],
)
def test_to_sorted_tuple(iterable, expected):
    if expected is None:
        with pytest.raises(TypeError):
            _to_sorted_tuple(iterable)
    else:
        assert _to_sorted_tuple(iterable) == expected


@pytest.mark.parametrize(
    "iterable, expected",
    [
        ([[1]], None),
        ([[1], [2], [3]], None),
        ([[3, 4], [2]], ((3, 4), (2,))),
        ([[3], [4]], ((3,), (4,))),
    ],
)
def test_to_sorted_tuple_pair(iterable, expected):
    if expected is None:
        with pytest.raises(ValueError):
            _to_sorted_tuple_pair(iterable)
    else:
        assert _to_sorted_tuple_pair(iterable) == expected
