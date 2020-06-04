from copy import deepcopy

import pytest

from expertsystem.particle import (
    Parameter,
    Parity,
    Particle,
    Spin,
)
from expertsystem.particle import ParticleDatabase


class TestParticleDatabase:
    database = ParticleDatabase()

    def test_construction(self):
        assert len(self.database) == 0

    def test_add(self):
        gamma = Particle(
            name="gamma",
            pid=22,
            mass=0,
            charge=0,
            spin=+1,
            parity=Parity(-1),
            parity_c=Parity(-1),
        )
        self.database.add_particle(gamma)
        assert len(self.database) == 1
        self.database.add_particle(gamma)
        assert len(self.database) == 1
        pi0 = Particle(
            name="pi0",
            pid=111,
            mass=Parameter(0.1349766, 0.000006),
            charge=0,
            spin=Spin(0),
            parity=Parity(-1),
            parity_c=Parity(+1),
            parity_g=Parity(-1),
            isospin=Spin(+1, 0),
        )
        self.database.add_particle(pi0)
        assert len(self.database) == 2

    def test_dict_methods(self):
        if len(self.database) == 0:
            self.test_add()
        assert "gamma" in self.database
        for particle in self.database:
            assert isinstance(particle, Particle)

    def test_getters(self):
        if len(self.database) == 0:
            self.test_add()
        assert self.database.get_by_pid(111).name == "pi0"
        with pytest.raises(LookupError):
            self.database.get_by_pid(666)

        gamma = self.database["gamma"]
        assert gamma.pid == 22
        assert gamma.mass == 0
        assert not gamma.has_width
        assert gamma.spin == 1
        assert gamma.charge == 0
        assert gamma.parity == -1
        assert gamma.parity_c == -1
        assert not gamma.parity_g
        assert gamma.baryon_number == 0
        assert gamma.charmness == 0
        assert gamma.strangeness == 0

    def test_equality(self):
        if len(self.database) == 0:
            self.test_add()
        empty_database = ParticleDatabase()
        with pytest.raises(NotImplementedError):
            assert empty_database == 0
        assert self.database != empty_database
        other_database = deepcopy(self.database)
        assert self.database == other_database
