# cspell:ignore stringyfied

"""JSON validation schema for a YAML recipe file."""

import json
from os.path import dirname, realpath

import jsonschema

_EXPERTSYSTEM_PATH = f"{dirname(realpath(__file__))}/../.."

with open(f"{_EXPERTSYSTEM_PATH}/particle/validation.json") as stream:
    __SCHEMA_PARTICLES = json.load(stream)


def particle_collection(instance: dict) -> None:
    jsonschema.validate(instance=instance, schema=__SCHEMA_PARTICLES)
