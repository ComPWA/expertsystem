import pytest

from expertsystem.state.particle import Spin


class TestSpin:
    @staticmethod
    @pytest.mark.parametrize("magnitude, projection", [(-0.5, -0.3), (1, -2)])
    def test_value_error(magnitude, projection):
        with pytest.raises(ValueError):
            Spin(magnitude, projection)

    @staticmethod
    @pytest.mark.parametrize("magnitude, projection", [(0.5, -0.5), (1, 0)])
    def test_properties(magnitude, projection):
        spin = Spin(magnitude, projection)
        assert spin.magnitude == magnitude
        assert spin.projection == projection

    @staticmethod
    def test_equality():
        spin_one1 = Spin(1)
        spin_one2 = Spin(1)
        spin_half = Spin(0.5, -0.5)
        assert spin_one1 != spin_half
        assert spin_one1 == spin_one2
        assert spin_half == 0.5
        assert spin_half != 1
        with pytest.raises(NotImplementedError):
            assert spin_half == "string"
