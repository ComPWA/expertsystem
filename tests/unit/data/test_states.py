from dataclasses import FrozenInstanceError

import pytest

from expertsystem.data import Particle, Spin


class TestParticle:
    @pytest.mark.parametrize(
        "instance",
        [
            Particle(
                name="jpsi",
                pid=1234,
                mass=3.0969,
                width=9.29e-05,
                spin=1,
                charge=0,
            ),
        ],
    )
    @staticmethod
    def test_repr(instance):
        copy_from_repr = eval(repr(instance))  # pylint: disable=eval-used
        assert copy_from_repr == instance

    @staticmethod
    def test_immutability():
        with pytest.raises(FrozenInstanceError):
            test_state = Particle(
                "MyParticle",
                123,
                mass=1.2,
                width=0.1,
                spin=1,
                charge=0,
                isospin=Spin(1, 0),
            )
            test_state.charge = 1  # type: ignore

    @staticmethod
    def test_complex_energy_equality():
        with pytest.raises(AssertionError):
            assert Particle(
                "MyParticle", pid=123, mass=1.5, width=0.1, spin=1
            ) == Particle("MyParticle", pid=123, mass=1.5, width=0.2, spin=1)

        assert Particle(
            "MyParticle",
            123,
            mass=1.2,
            width=0.1,
            spin=1,
            charge=0,
            isospin=Spin(1, 0),
        ) == Particle(
            "MyParticle",
            123,
            mass=1.2,
            width=0.1,
            spin=1,
            charge=0,
            isospin=Spin(1, 0),
        )


class TestSpin:
    @pytest.mark.parametrize(
        "magnitude, projection",
        [(0.3, 0.3), (1.0, 0.5), (0.5, 0.0), (-0.5, 0.5)],
    )
    @staticmethod
    def test_spin_exceptions(magnitude, projection):
        with pytest.raises(ValueError):
            print(Spin(magnitude, projection))
