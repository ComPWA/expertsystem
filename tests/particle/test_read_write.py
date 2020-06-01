from copy import deepcopy

from expertsystem.state import particle
from expertsystem.ui.system_control import load_default_particle_list


def test_import_xml():
    load_default_particle_list()
    assert len(particle.deprecated.DATABASE) == 69
    assert "sigma+" in particle.deprecated.DATABASE.keys()
    assert "mu+" in particle.deprecated.DATABASE.keys()

    some_particle = particle.deprecated.DATABASE["gamma"]
    quantum_numbers = some_particle[
        particle.deprecated.LABELS.QuantumNumber.name
    ]
    quantum_number = quantum_numbers[0]
    assert (
        quantum_number[particle.deprecated.LABELS.Class.name]
        == particle.deprecated.StateQuantumNumberNames.Spin.name
    )
    assert int(quantum_number[particle.deprecated.LABELS.Value.name]) == 1


def test_xml_io():
    load_default_particle_list()
    particle.deprecated.write_particle_list_to_xml("test_particle_list.xml")
    particle.deprecated.DATABASE.clear()
    particle.deprecated.load_particle_list_from_xml("test_particle_list.xml")
    assert len(particle.deprecated.DATABASE) == 69


def test_yaml_io():
    load_default_particle_list()
    particles_xml = deepcopy(particle.deprecated.DATABASE)
    particle.deprecated.write_particle_list_to_yaml("test_particle_list.yml")

    particle.deprecated.DATABASE.clear()
    particle.deprecated.load_particle_list_from_yaml("test_particle_list.yml")

    assert particle.deprecated.DATABASE == particles_xml
    particle.deprecated.DATABASE["gamma"]["Pid"] = "23"
    assert particle.deprecated.DATABASE != particles_xml
