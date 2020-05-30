from copy import deepcopy

import pytest

from expertsystem.state.particle import (
    Particle,
    QuantumNumbers,
    ValueWithUncertainty,
)


class TestParticle:
    @staticmethod
    @pytest.mark.parametrize(
        "name, pid, mass, spin, charge", [("gamma", 22, 0.0, 1, 0)],
    )
    def test_properties(name, pid, mass, spin, charge):
        particle = Particle(
            name=name,
            pid=pid,
            mass=mass,
            quantum_numbers=QuantumNumbers(spin=spin, charge=charge),
        )
        assert particle.name == name
        assert particle.pid == pid
        assert particle.mass == mass
        assert particle.quantum_numbers.spin == spin
        assert particle.quantum_numbers.charge == charge
        assert not particle.has_width


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
