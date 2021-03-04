# cspell:ignore atol
# pylint: disable=no-self-use
import numpy as np
import pytest

from expertsystem.amplitude.kinematics import (
    SubSystem,
    _to_sorted_tuple,
    _to_sorted_tuple_pair,
    compute_helicity_angles,
)
from expertsystem.reaction.topology import create_isobar_topologies

# https://github.com/ComPWA/tensorwaves/blob/3d0ec44/tests/physics/helicity_formalism/test_helicity_angles.py#L61-L98
TEST_DATA = {
    0: np.array(  # pi0
        [
            (1.35527, 0.514208, -0.184219, 1.23296),
            (0.841933, 0.0727385, -0.0528868, 0.826163),
            (0.550927, -0.162529, 0.29976, -0.411133),
            (0.425195, 0.0486171, 0.151922, 0.370309),
            (0.186869, -0.0555915, -0.100214, -0.0597338),
            (1.26375, 0.238921, 0.266712, -1.20442),
            (0.737698, 0.450724, -0.439515, -0.360076),
            (0.965809, 0.552298, 0.440006, 0.644927),
            (0.397113, -0.248155, -0.158587, -0.229673),
            (1.38955, 1.33491, 0.358535, 0.0457548),
        ]
    ).T,
    1: np.array(  # gamma
        [
            (0.755744, -0.305812, 0.284, -0.630057),
            (1.02861, 0.784483, 0.614347, -0.255334),
            (0.356875, -0.20767, 0.272796, 0.0990739),
            (0.70757, 0.404557, 0.510467, -0.276426),
            (0.953902, 0.47713, 0.284575, -0.775431),
            (0.220732, -0.204775, -0.0197981, 0.0799868),
            (0.734602, 0.00590727, 0.709346, -0.190877),
            (0.607787, 0.329157, -0.431973, 0.272873),
            (0.626325, -0.201436, -0.534829, 0.256253),
            (0.386432, -0.196357, 0.00211926, -0.33282),
        ]
    ).T,
    2: np.array(  # pi0
        [
            (0.208274, -0.061663, -0.0211864, 0.144596),
            (0.461193, -0.243319, -0.283044, -0.234866),
            (1.03294, 0.82872, -0.0465425, -0.599834),
            (0.752466, 0.263003, -0.089236, 0.686187),
            (0.746588, 0.656892, -0.107848, 0.309898),
            (0.692537, 0.521569, -0.0448683, 0.43283),
            (0.865147, -0.517582, -0.676002, -0.0734335),
            (1.35759, -0.975278, -0.0207817, -0.934467),
            (0.852141, -0.41665, 0.237646, 0.691269),
            (0.616162, -0.464203, -0.358114, 0.13307),
        ]
    ).T,
    3: np.array(  # pi0
        [
            (0.777613, -0.146733, -0.0785946, -0.747499),
            (0.765168, -0.613903, -0.278416, -0.335962),
            (1.15616, -0.458522, -0.526014, 0.911894),
            (1.21167, -0.716177, -0.573154, -0.780069),
            (1.20954, -1.07843, -0.0765127, 0.525267),
            (0.919879, -0.555715, -0.202046, 0.691605),
            (0.759452, 0.0609506, 0.406171, 0.624387),
            (0.165716, 0.0938229, 0.012748, 0.0166676),
            (1.22132, 0.866241, 0.455769, -0.717849),
            (0.704759, -0.674348, -0.0025409, 0.153994),
        ]
    ).T,
}


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


def test_compute_helicity_angles():
    expected_angles = {
        "phi_1+2+3": np.array(
            [
                2.79758,
                2.51292,
                -1.07396,
                -1.88051,
                1.06433,
                -2.30129,
                2.36878,
                -2.46888,
                0.568649,
                -2.8792,
            ]
        ),
        "theta_1+2+3": np.arccos(
            [
                -0.914298,
                -0.994127,
                0.769715,
                -0.918418,
                0.462214,
                0.958535,
                0.496489,
                -0.674376,
                0.614968,
                -0.0330843,
            ]
        ),
        "phi_2+3,1+2+3": np.array(
            [
                1.04362,
                1.87349,
                0.160733,
                -2.81088,
                2.84379,
                2.29128,
                2.24539,
                -1.20272,
                0.615838,
                2.98067,
            ]
        ),
        "theta_2+3,1+2+3": np.arccos(
            [
                -0.772533,
                0.163659,
                0.556365,
                0.133251,
                -0.0264361,
                0.227188,
                -0.166924,
                0.652761,
                0.443122,
                0.503577,
            ]
        ),
        "phi_2,2+3,1+2+3": np.array(
            [  # WARNING: subsystem solution (ComPWA) results in pi differences
                -2.77203 + np.pi,
                1.45339 - np.pi,
                -2.51096 + np.pi,
                2.71085 - np.pi,
                -1.12706 + np.pi,
                -3.01323 + np.pi,
                2.07305 - np.pi,
                0.502648 - np.pi,
                -1.23689 + np.pi,
                1.7605 - np.pi,
            ]
        ),
        "theta_2,2+3,1+2+3": np.arccos(
            [
                0.460324,
                -0.410464,
                0.248566,
                -0.301959,
                -0.522502,
                0.787267,
                0.488066,
                0.954167,
                -0.553114,
                0.00256349,
            ]
        ),
    }
    topologies = create_isobar_topologies(4)
    topology = topologies[1]
    angles = compute_helicity_angles(TEST_DATA, topology)
    assert len(angles) == len(expected_angles)
    assert set(angles) == set(expected_angles)
    for angle_name in angles:
        np.testing.assert_allclose(
            angles[angle_name],
            expected_angles[angle_name],
            atol=1e-5,
        )
