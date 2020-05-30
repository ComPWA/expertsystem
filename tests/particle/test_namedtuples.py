from copy import deepcopy

import pytest

from expertsystem.state.particle import ValueWithUncertainty


class TestValueWithUncertainty:
    @staticmethod
    def test_equality():
        value = ValueWithUncertainty(1.2, 0.15)
        value_copy = deepcopy(value)
        value_different_value = ValueWithUncertainty(-5.3, 0.15)
        value_different_uncertainty = ValueWithUncertainty(1.2, 0.12)
        assert value == 1.2
        assert value == value_copy
        assert value != value_different_value
        assert value != value_different_uncertainty

    @staticmethod
    @pytest.mark.parametrize(
        "definition, key, value, uncertainty",
        [
            ({}, "", 0, 0.0),
            ({"Mass": 1.5}, "Mass", 1.5, 0.0),
            ({"Value": 3.14, "Error": 0.01}, "", 3.14, 0.01),
        ],
    )
    def test_from_dict(definition, key, value, uncertainty):
        variable = ValueWithUncertainty.from_dict(definition, key)
        assert variable == value
        assert variable.uncertainty == uncertainty

        undefined = ValueWithUncertainty.from_dict({})
        assert undefined == 0.0
