from os.path import dirname, realpath

import pytest

import expertsystem
from expertsystem import io
from expertsystem.data import (
    Particle,
    ParticleCollection,
    QuantumState,
    create_particle,
)


EXPERTSYSTEM_PATH = dirname(realpath(expertsystem.__file__))
_XML_FILE = f"{EXPERTSYSTEM_PATH}/particle_list.xml"
_YAML_FILE = f"{EXPERTSYSTEM_PATH}/particle_list.yml"


def test_not_implemented_errors():
    with pytest.raises(NotImplementedError):
        io.load_particle_collection(f"{EXPERTSYSTEM_PATH}/../README.md")
    with pytest.raises(NotImplementedError):
        dummy = ParticleCollection()
        io.write(dummy, f"{EXPERTSYSTEM_PATH}/particle_list.csv")
    with pytest.raises(Exception):
        dummy = ParticleCollection()
        io.write(dummy, "no_file_extension")
    with pytest.raises(NotImplementedError):
        io.write(666, "wont_work_anyway.xml")


@pytest.mark.parametrize("input_file", [_XML_FILE, _YAML_FILE])
def test_load_particle_collection(input_file):
    particles = io.load_particle_collection(input_file)
    assert len(particles) == 68
    assert "J/psi(1S)" in particles
    j_psi = particles["J/psi(1S)"]
    assert j_psi.pid == 443
    particle_names = list(particles.keys())
    for name, particle_name in zip(particle_names, particles):
        assert name == particle_name


@pytest.mark.parametrize("input_file", [_XML_FILE, _YAML_FILE])
def test_write_particle_collection(input_file):
    particles_imported = io.load_particle_collection(input_file)
    file_extension = input_file.split(".")[-1]
    output_file = f"exported_particle_list.{file_extension}"
    io.write(particles_imported, output_file)
    particles_exported = io.load_particle_collection(output_file)
    for name in particles_imported:
        assert particles_imported[name] == particles_exported[name]


def test_yaml_to_xml():
    yaml_particle_collection = io.load_particle_collection(_YAML_FILE)
    xml_file = "particle_list_test.xml"
    io.write(yaml_particle_collection, xml_file)
    xml_particle_collection = io.load_particle_collection(xml_file)
    assert xml_particle_collection == yaml_particle_collection
    dummy_particle = Particle(
        name="0", pid=0, mass=0, state=QuantumState[float](charge=0, spin=0)
    )
    yaml_particle_collection += dummy_particle
    assert xml_particle_collection != yaml_particle_collection


def test_equivalence_xml_yaml_particle_list():
    xml_particle_collection = io.load_particle_collection(_XML_FILE)
    yml_particle_collection = io.load_particle_collection(_YAML_FILE)
    for name in xml_particle_collection:
        assert xml_particle_collection[name] == yml_particle_collection[name]


class TestInternalParticleDict:
    @staticmethod
    def test_find(particle_database):
        f2_1950 = particle_database.find(9050225)
        assert f2_1950.name == "f(2)(1950)"
        assert f2_1950.mass == 1.936
        phi = particle_database.find("phi(1020)")
        assert phi.pid == 333
        assert phi.width == 0.004249

    @staticmethod
    @pytest.mark.parametrize("search_term", [666, "non-existing"])
    def test_find_fail(particle_database, search_term):
        with pytest.raises(LookupError):
            particle_database.find(search_term)

    @staticmethod
    def test_find_subset(particle_database):
        search_result = particle_database.find_subset("f(0)")
        f0_1500_from_subset = search_result["f(0)(1500)"]
        assert len(search_result) == 2
        assert f0_1500_from_subset.mass == 1.506
        assert f0_1500_from_subset is particle_database["f(0)(1500)"]
        assert f0_1500_from_subset is not particle_database["f(0)(980)"]

        # test iadd
        particle_database += search_result

        search_result = particle_database.find_subset(22)
        gamma_from_subset = search_result["gamma"]
        assert len(search_result) == 1
        assert gamma_from_subset.pid == 22
        assert gamma_from_subset is particle_database["gamma"]

    @staticmethod
    def test_exceptions(particle_database):
        new_particle = create_particle(
            template_particle=particle_database["gamma"], name="gamma_new"
        )
        particle_database += new_particle
        with pytest.raises(LookupError):
            particle_database.find_subset(22)
        with pytest.raises(NotImplementedError):
            particle_database.find_subset(3.14)  # type: ignore
        with pytest.raises(NotImplementedError):
            particle_database.find(3.14)  # type: ignore
        with pytest.raises(NotImplementedError):
            particle_database += 3.14  # type: ignore
        with pytest.raises(NotImplementedError):
            assert new_particle == "gamma"
