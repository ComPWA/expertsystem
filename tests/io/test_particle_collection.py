from os.path import dirname, realpath

import expertsystem
from expertsystem.io import (
    load_particle_collection,
    write,
)

_PACKAGE_PATH = dirname(realpath(expertsystem.__file__))
_YAML_FILE = f"{_PACKAGE_PATH}/particle_list.yml"


def test_yaml_to_xml():
    # Load default particle list from YAML into a ParticleCollection instance
    yaml_particle_collection = load_particle_collection(_YAML_FILE)
    xml_file = "particle_list_test.xml"
    # Dump that ParticleCollection to XML
    write(yaml_particle_collection, xml_file)
    # Load the XML output back into another ParticleCollection instance
    xml_particle_collection = load_particle_collection(xml_file)
    # Check equivalence of the two instances
    for xml_particle, yaml_particle in zip(
        xml_particle_collection.values(), yaml_particle_collection.values()
    ):
        assert xml_particle == yaml_particle
