from expertsystem.io._xml._build import _build_particle  # noqa: I202
from expertsystem.io._xml.validation import validate_particle
from expertsystem.state import particle
from expertsystem.ui.system_control import load_default_particle_list


load_default_particle_list(particle.load_particle_list_from_xml)


def test_particle_validation():
    for item in particle.DATABASE.values():
        validate_particle(item)


def test_build_particle():
    definition = particle.DATABASE["J/psi"]
    j_psi = _build_particle(definition)
    assert j_psi.pid == 443
    assert j_psi.mass == 3.0969
    assert j_psi.width == 9.29e-05
    assert j_psi.spin == 1
    assert j_psi.charge == 0
    assert j_psi.parity == -1
    assert j_psi.c_parity == -1
    assert j_psi.g_parity == -1
    assert j_psi.isospin is None
