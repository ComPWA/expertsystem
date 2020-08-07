import pytest

from expertsystem.state.particle import DATABASE, create_antiparticle
from expertsystem.ui import load_default_particle_list

load_default_particle_list()


@pytest.mark.parametrize(
    "particle_name, anti_particle_name",
    [("D+", "D-"), ("p", "pbar"), ("mu+", "mu-"), ("W+", "W-")],
)
def test_create_antiparticle(particle_name, anti_particle_name):
    template_particle = DATABASE[particle_name]
    anti_particle = create_antiparticle(template_particle)
    comparision_particle = DATABASE[anti_particle_name]

    assert anti_particle.pid == comparision_particle.pid
    assert anti_particle.mass == comparision_particle.mass
    assert anti_particle.width == comparision_particle.width
    assert anti_particle.state == comparision_particle.state
    assert anti_particle.name == "anti-" + particle_name
