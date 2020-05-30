import pytest

from expertsystem.state.particle import (
    Particle,
    ParticleDatabase,
    QuantumNumbers,
)


class TestParticleDatabase:
    database = ParticleDatabase()

    @staticmethod
    def test_construction():
        with pytest.raises(NotImplementedError):
            ParticleDatabase("particle_list.csv")
        with pytest.raises(NotImplementedError):
            ParticleDatabase("particle_list.xml")
        with pytest.raises(NotImplementedError):
            ParticleDatabase("particle_list.yml")

    def test_getters(self):
        assert len(self.database) == 0
        with pytest.raises(LookupError):
            self.database.get_by_pid(211)
        with pytest.raises(LookupError):
            print(self.database["gamma"])
        gamma = Particle(
            name="gamma",
            pid=22,
            mass=0.0,
            quantum_numbers=QuantumNumbers(spin=1, charge=0),
        )
        self.database.add_particle(gamma)
        assert self.database.get_by_pid(22).name == "gamma"

    def test_write(self):
        with pytest.raises(NotImplementedError):
            self.database.write("particle_list.csv")
        with pytest.raises(NotImplementedError):
            self.database.write("particle_list.xml")
        with pytest.raises(NotImplementedError):
            self.database.write("particle_list.yml")
