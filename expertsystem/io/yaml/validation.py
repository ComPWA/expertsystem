"""JSON validation schema for a YAML recipe file."""

import json
from os.path import dirname, realpath

import jsonschema

import expertsystem


_PACKAGE_PATH = dirname(realpath(expertsystem.__file__))

with open(f"{_PACKAGE_PATH}/schemas/yaml/particle-list.json") as stream:
    _SCHEMA_PARTICLES = json.load(stream)
with open(f"{_PACKAGE_PATH}/schemas/yaml/amplitude-model.json") as stream:
    _SCHEMA_AMPLITUDE = json.load(stream)


def particle_list(instance: dict) -> None:
    jsonschema.validate(instance=instance, schema=_SCHEMA_PARTICLES)


def amplitude_model(instance: dict) -> None:
    jsonschema.validate(instance=instance, schema=_SCHEMA_PARTICLES)
