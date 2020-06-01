import pytest

from expertsystem.state.particle import (
    Particle,
    QuantumNumbers,
    Spin,
)
from expertsystem.state.particle import ParticleDatabase


class TestParticleDatabase:
    database = ParticleDatabase("particle_list.yml")

    @staticmethod
    def test_construction():
        with pytest.raises(NotImplementedError):
            ParticleDatabase("particle_list.csv")
        database = ParticleDatabase("particle_list.xml")
        assert len(database) == 69
        database = ParticleDatabase("particle_list.yml")
        assert len(database) == 69
        database = ParticleDatabase()
        assert len(database) == 0

    @staticmethod
    @pytest.mark.parametrize(
        "input_file", ["particle_list.xml", "particle_list.yml"]
    )
    def test_getters(input_file):
        database = ParticleDatabase(input_file)
        assert len(database) == 69
        assert database.get_by_pid(-211).name == "pi-"
        with pytest.raises(LookupError):
            database.get_by_pid(666)

        gamma = database["gamma"]
        assert gamma.pid == 22
        assert gamma.mass == 0
        assert not gamma.has_width
        assert gamma.quantum_numbers.spin == 1
        assert gamma.quantum_numbers.charge == 0
        assert gamma.quantum_numbers.parity == -1
        assert gamma.quantum_numbers.parity_c == -1
        assert not gamma.quantum_numbers.parity_g
        assert gamma.quantum_numbers.baryon_number == 0
        assert gamma.quantum_numbers.charmness == 0
        assert gamma.quantum_numbers.strangeness == 0

    def test_write(self):
        with pytest.raises(NotImplementedError):
            self.database.write("particle_list.csv")
        with pytest.raises(NotImplementedError):
            self.database.write("particle_list.xml")

    def test_write_yaml(self):
        self.database.write("test_particle_list.yml")
        imported_database = ParticleDatabase("test_particle_list.yml")
        assert imported_database == self.database

    @staticmethod
    def test_equality():
        database_xml = ParticleDatabase("particle_list.xml")
        database_yml = ParticleDatabase("particle_list.yml")
        empty_database = ParticleDatabase()
        with pytest.raises(NotImplementedError):
            assert database_xml == 0
        assert database_xml != empty_database
        assert database_xml == database_yml

        particle = database_xml["gamma"]
        corrupted_particle = Particle(
            name=particle.name,
            pid=particle.pid,
            mass=particle.mass,
            width=particle.width,
            quantum_numbers=QuantumNumbers(
                charge=particle.quantum_numbers.charge,
                spin=Spin(2.5, -1.5),  # only one different, nested value
                isospin=particle.quantum_numbers.isospin,
                parity=particle.quantum_numbers.parity,
                parity_c=particle.quantum_numbers.parity_c,
                parity_g=particle.quantum_numbers.parity_g,
                strangeness=particle.quantum_numbers.strangeness,
                charmness=particle.quantum_numbers.charmness,
                bottomness=particle.quantum_numbers.bottomness,
                topness=particle.quantum_numbers.topness,
                baryon_number=particle.quantum_numbers.baryon_number,
                ln_electron=particle.quantum_numbers.ln_electron,
                ln_muon=particle.quantum_numbers.ln_muon,
                ln_tau=particle.quantum_numbers.ln_tau,
            ),
        )
        database_xml.add_particle(corrupted_particle)
        assert len(database_xml) == len(database_yml)
        assert database_xml != database_yml
