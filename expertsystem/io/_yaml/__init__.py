"""Serialization from and to a YAML recipe file."""

__all__ = [
    "load_particle_collection",
]

import yaml

from expertsystem.data import ParticleCollection

from ._build import _build_particle_collection


def load_particle_collection(filename: str) -> ParticleCollection:
    with open(filename) as yaml_file:
        definition = yaml.load(yaml_file, Loader=yaml.SafeLoader)
    return _build_particle_collection(definition)
