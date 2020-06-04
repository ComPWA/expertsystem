from copy import deepcopy

from expertsystem.state import particle
from expertsystem.ui.system_control import load_default_particle_list


def test_import_xml():
    load_default_particle_list()
    assert len(particle.DATABASE) == 69
    assert "sigma+" in particle.DATABASE
    assert "mu+" in particle.DATABASE

    some_particle = particle.DATABASE["gamma"]
    quantum_numbers = some_particle[particle.LABELS.QuantumNumber.name]
    quantum_number = quantum_numbers[0]
    assert (
        quantum_number[particle.LABELS.Class.name]
        == particle.StateQuantumNumberNames.Spin.name
    )
    assert int(quantum_number[particle.LABELS.Value.name]) == 1


def test_xml_io():
    load_default_particle_list()
    particle.write_particle_list_to_xml("test_particle_list.xml")
    particle.DATABASE.clear()
    particle.load_particle_list_from_xml("test_particle_list.xml")
    assert len(particle.DATABASE) == 69


def test_yaml_io():
    load_default_particle_list()
    particles_xml = deepcopy(particle.DATABASE)
    particle.write_particle_list_to_yaml("test_particle_list.yml")

    particle.DATABASE.clear()
    particle.load_particle_list_from_yaml("test_particle_list.yml")

    assert particle.DATABASE == particles_xml
    particle.DATABASE["gamma"]["Pid"] = "23"
    assert particle.DATABASE != particles_xml
