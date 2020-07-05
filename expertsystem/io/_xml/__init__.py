"""Serialization from and to an XML recipe file."""

__all__ = [
    "load_particle_collection",
]

import json

import xmltodict

from expertsystem.data import ParticleCollection

from ._build import _build_particle_collection


def load_particle_collection(filename: str) -> ParticleCollection:
    with open(filename, "rb") as stream:
        definition = xmltodict.parse(stream)
    definition = definition.get("root", definition)
    json.loads(json.dumps(definition))  # remove OrderedDict
    return _build_particle_collection(definition)
