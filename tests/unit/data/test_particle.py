# pylint: disable=redefined-outer-name, no-self-use
import pytest

from expertsystem.data import (
    GellmannNishijima,
    Parity,
    Particle,
    ParticleCollection,
    Spin,
    create_antiparticle,
    create_particle,
)


class TestParticle:
    @pytest.mark.parametrize(
        "instance",
        [Spin(2.5, -0.5), Parity(1)],
    )
    @staticmethod
    def test_repr(instance):
        from_repr = eval(repr(instance))  # pylint: disable=eval-used
        assert from_repr == instance

    @staticmethod
    def test_repr_particle_collection(particle_database):
        from_repr = eval(repr(particle_database))  # pylint: disable=eval-used
        assert from_repr == particle_database

    @staticmethod
    def test_repr_particle(particle_database):
        for particle in particle_database:
            from_repr = eval(repr(particle))  # pylint: disable=eval-used
            assert from_repr == particle

    @staticmethod
    def test_members():
        jpsi = Particle(
            name="J/psi(1S)",
            pid=443,
            mass=3.0969,
            width=9.29e-05,
            spin=1,
            charge=0,
            parity=Parity(-1),
            c_parity=Parity(-1),
            g_parity=Parity(-1),
            isospin=Spin(0.0, 0.0),
        )
        assert jpsi.mass == 3.0969
        assert jpsi.width == 9.29e-05
        assert jpsi.bottomness == 0
        assert not jpsi.is_lepton()

    @pytest.mark.parametrize(
        "name, is_lepton",
        [
            ("J/psi(1S)", False),
            ("p", False),
            ("e+", True),
            ("e-", True),
            ("nu(e)", True),
            ("nu(tau)~", True),
            ("tau+", True),
        ],
    )
    def test_is_lepton(
        self, name, is_lepton, particle_database: ParticleCollection
    ):
        assert particle_database[name].is_lepton() == is_lepton


class TestParity:
    @staticmethod
    def test_init_exceptions():
        with pytest.raises(ValueError):
            Parity(1.2)

    @staticmethod
    def test_init_and_comparison():
        parity = Parity(+1)
        assert parity == +1
        assert int(parity) == +1

    @staticmethod
    def test_neg():
        parity = Parity(+1)
        flipped_parity = -parity
        assert flipped_parity.value == -parity.value


class TestSpin:
    @staticmethod
    def test_init_exceptions():
        with pytest.raises(ValueError):
            Spin(1, -2)

    @staticmethod
    def test_init_and_comparison():
        isospin = Spin(1.5, -0.5)
        assert isospin == 1.5
        assert float(isospin) == 1.5
        assert isospin.magnitude == 1.5
        assert isospin.projection == -0.5

    @staticmethod
    def test_neg():
        isospin = Spin(1.5, -0.5)
        flipped_spin = -isospin
        assert flipped_spin.magnitude == isospin.magnitude
        assert flipped_spin.projection == -isospin.projection


@pytest.mark.parametrize(
    "particle_name",
    ["p", "phi(1020)", "W-", "gamma"],
)
def test_create_particle(particle_database, particle_name):
    template_particle = particle_database[particle_name]
    new_particle = create_particle(
        template_particle,
        name="testparticle",
        pid=89,
        mass=1.5,
        width=0.5,
    )
    assert new_particle.name == "testparticle"
    assert new_particle.pid == 89
    assert new_particle.charge == template_particle.charge
    assert new_particle.spin == template_particle.spin
    assert new_particle.mass == 1.5
    assert new_particle.width == 0.5
    assert new_particle.baryon_number == template_particle.baryon_number
    assert new_particle.strangeness == template_particle.strangeness


@pytest.mark.parametrize(
    "particle_name, anti_particle_name",
    [("D+", "D-"), ("mu+", "mu-"), ("W+", "W-")],
)
def test_create_antiparticle(
    particle_database: ParticleCollection,
    particle_name,
    anti_particle_name,
):
    template_particle = particle_database[particle_name]
    anti_particle = create_antiparticle(
        template_particle, new_name=anti_particle_name
    )
    comparison_particle = particle_database[anti_particle_name]

    assert anti_particle == comparison_particle


def test_create_antiparticle_tilde(particle_database: ParticleCollection):
    anti_particles = particle_database.filter(lambda p: "~" in p.name)
    assert len(anti_particles) == 166
    for anti_particle in anti_particles.values():
        particle_name = anti_particle.name.replace("~", "")
        if "+" in particle_name:
            particle_name = particle_name.replace("+", "-")
        elif "-" in particle_name:
            particle_name = particle_name.replace("-", "+")
        created_particle = create_antiparticle(anti_particle, particle_name)

        assert created_particle == particle_database[particle_name]


class TestGellmannNishijima:
    @staticmethod
    @pytest.mark.parametrize(
        "state",
        [
            Particle(
                "p1",
                1,
                spin=0.0,
                mass=1,
                charge=1,
                isospin=Spin(1.0, 0.0),
                strangeness=2,
            ),
            Particle(
                "p1",
                1,
                spin=1.0,
                mass=1,
                charge=1,
                isospin=Spin(1.5, 0.5),
                charmness=1,
            ),
            Particle(
                "p1",
                1,
                spin=0.5,
                mass=1,
                charge=1.5,  # type: ignore
                isospin=Spin(1.0, 1.0),
                baryon_number=1,
            ),
        ],
    )
    def test_computations(state):
        assert GellmannNishijima.compute_charge(state) == state.charge
        assert (
            GellmannNishijima.compute_isospin_projection(
                charge=state.charge,
                baryon_number=state.baryon_number,
                strangeness=state.strangeness,
                charmness=state.charmness,
                bottomness=state.bottomness,
                topness=state.topness,
            )
            == state.isospin.projection
        )

    @staticmethod
    def test_isospin_none():
        state = Particle("p1", 1, mass=1, spin=0.0, charge=1, isospin=None)
        assert GellmannNishijima.compute_charge(state) is None

    @staticmethod
    def test_exceptions():
        with pytest.raises(ValueError):
            print(
                Particle(
                    name="Fails Gell-Mann–Nishijima formula",
                    pid=666,
                    mass=0.0,
                    spin=1,
                    charge=0,
                    parity=Parity(-1),
                    c_parity=Parity(-1),
                    g_parity=Parity(-1),
                    isospin=Spin(0.0, 0.0),
                    charmness=1,
                )
            )
