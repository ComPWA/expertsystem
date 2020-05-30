import pytest

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
        with pytest.raises(NotImplementedError):
            self.database.write("particle_list.yml")
