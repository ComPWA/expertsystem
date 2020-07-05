from expertsystem.io._xml.validation import validate_particle
from expertsystem.state import particle
from expertsystem.ui.system_control import load_default_particle_list


def test_particle_validation():
    load_default_particle_list(particle.load_particle_list_from_xml)
    for item in particle.DATABASE.values():
        validate_particle(item)
