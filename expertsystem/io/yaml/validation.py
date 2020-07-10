"""JSON validation schema for a YAML recipe file."""

import json
from os.path import dirname, realpath

import jsonschema

import expertsystem


_PACKAGE_PATH = dirname(realpath(expertsystem.__file__))

with open(f"{_PACKAGE_PATH}/schemas/yaml/particle-list.json") as stream:
    _SCHEMA_PARTICLES = json.load(stream)


def particle_list(instance: dict) -> None:
    jsonschema.validate(instance=instance, schema=_SCHEMA_PARTICLES)
