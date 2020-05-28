import pytest

from expertsystem.state.particle import Spin


class TestSpin:
    @staticmethod
    @pytest.mark.parametrize("magnitude, projection", [(-0.5, -0.3), (1, -2)])
    def test_value_error(magnitude, projection):
        with pytest.raises(ValueError):
            Spin(magnitude, projection)
