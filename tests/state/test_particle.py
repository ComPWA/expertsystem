from expertsystem.state.particle import DATABASE, create_antiparticle
from expertsystem.ui import load_default_particle_list


def test_create_antiparticle():
    load_default_particle_list()
    template_particle = DATABASE["D+"]
    anti_particle = create_antiparticle(template_particle)
    comparision_particle = DATABASE["D-"]

    assert anti_particle.pid == comparision_particle.pid
    assert anti_particle.mass == comparision_particle.mass
    assert anti_particle.width == comparision_particle.width
    assert anti_particle.state == comparision_particle.state
    assert anti_particle.name == "anti-D+"

    template_particle = DATABASE["p"]
    anti_particle = create_antiparticle(template_particle)
    comparision_particle = DATABASE["pbar"]

    assert anti_particle.pid == comparision_particle.pid
    assert anti_particle.mass == comparision_particle.mass
    assert anti_particle.width == comparision_particle.width
    assert anti_particle.state == comparision_particle.state
    assert anti_particle.name == "anti-p"
