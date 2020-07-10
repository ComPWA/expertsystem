"""JSON validation schema for a YAML recipe file."""

import json
from os.path import dirname, realpath

import jsonschema

import expertsystem


_EXPERTSYSTEM_PATH = dirname(realpath(expertsystem.__file__))

with open(f"{_EXPERTSYSTEM_PATH}/schemas/yaml/particle-list.json") as stream:
    _SCHEMA_PARTICLES = json.load(stream)
with open(f"{_EXPERTSYSTEM_PATH}/schemas/yaml/amplitude-model.json") as stream:
    _SCHEMA_AMPLITUDE = json.load(stream)

_RESOLVER_PARTICLES = jsonschema.RefResolver.from_schema(_SCHEMA_PARTICLES)


def particle_list(instance: dict) -> None:
    jsonschema.validate(instance=instance, schema=_SCHEMA_PARTICLES)


def amplitude_model(instance: dict) -> None:
    jsonschema.validate(
        instance=instance,
        schema=_SCHEMA_AMPLITUDE,
        resolver=_RESOLVER_PARTICLES,
    )
