import pytest

from expertsystem.data import Parameter


@pytest.mark.parametrize("min_value, max_value", [(None, 1.3), (1.6, None)])
def test_setter_exceptions(min_value, max_value):
    with pytest.raises(ValueError):
        Parameter(
            "some_parameter",
            value=1.5,
            min_value=min_value,
            max_value=max_value,
        )


def test_getters():
    par = Parameter("some_parameter", value=0)
    assert par.min_value is None
    assert par.max_value is None
    assert par.name == "some_parameter"
    assert par.error is None
    par.min_value = -1
    par.max_value = 3.1
    assert par.min_value == -1
    assert par.max_value == 3.1
    with pytest.raises(AttributeError):
        par.name = "cannot set name"
