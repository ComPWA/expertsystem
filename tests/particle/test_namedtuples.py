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
