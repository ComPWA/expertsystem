import pytest

from expertsystem.state.particle import Parity, Spin


class TestParity:
    @staticmethod
    @pytest.mark.parametrize("parity_value", [-2, 3.14, dict()])
    def test_value_error(parity_value):
        with pytest.raises(ValueError):
            Parity(parity_value)

    @staticmethod
    def test_equality():
        undefined = Parity()
        parity_even = Parity(+1)
        parity_odd1 = Parity(-1.0)
        parity_odd2 = Parity("-1")
        assert undefined == 0
        assert undefined != 1
        assert undefined != -1.5
        assert parity_even != parity_odd1
        assert parity_even != undefined
        assert parity_even != 2
        assert parity_even != -1
        assert parity_even == +1
        assert parity_even == +1.0
        assert parity_odd2 == parity_odd1
        assert parity_odd2 == -1
        assert parity_odd2 != -1.1
        assert parity_odd2 != +1

    @staticmethod
    def test_undefined():
        parity = Parity()
        assert not parity
        parity = Parity(+1)
        assert parity

    @staticmethod
    @pytest.mark.parametrize(
        "string, expected", [("odd", -1), ("-1", -1), ("even", +1), ("", 0)]
    )
    def test_from_string(string, expected):
        parity = Parity(string)
        assert parity == expected


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
    def test_bool():
        spin = Spin()
        assert not spin
        spin = Spin(0.5)
        assert spin
        spin = Spin(0.5, -0.5)
        assert spin

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
