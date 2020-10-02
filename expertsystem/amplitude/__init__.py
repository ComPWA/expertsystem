"""All modules related to amplitude model creation."""

__all__ = [
    "abstract_generator",
    "canonical_decay",
    "helicity_decay",
    "write_model",
]

from typing import Any, Dict

import xmltodict

import yaml

from expertsystem import io

from . import _yaml_adapter
from . import abstract_generator
from . import canonical_decay
from . import helicity_decay


def write_model(amplitude_model: dict, filename: str) -> None:
    file_extension = filename.lower().split(".")[-1]
    if file_extension in ["xml"]:
        __write_recipe_to_xml(amplitude_model, filename)
    elif file_extension in ["yaml", "yml"]:
        __write_recipe_to_yml(amplitude_model, filename)
    else:
        raise NotImplementedError(
            f'Cannot write to file type "{file_extension}"'
        )


def __write_recipe_to_xml(recipe_dict: Dict[str, Any], filename: str) -> None:
    xmlstring = xmltodict.unparse(
        {"root": recipe_dict}, pretty=True, indent="  "
    )
    with open(filename, mode="w") as xmlfile:
        xmlfile.write(xmlstring)


def __write_recipe_to_yml(recipe_dict: Dict[str, Any], filename: str) -> None:
    particle_dict = _yaml_adapter.to_particle_dict(recipe_dict)
    parameter_list = _yaml_adapter.to_parameter_list(recipe_dict)
    kinematics = _yaml_adapter.to_kinematics_dict(recipe_dict)
    dynamics = _yaml_adapter.to_dynamics(recipe_dict)
    intensity = _yaml_adapter.to_intensity(recipe_dict)

    class IncreasedIndent(yaml.Dumper):
        # pylint: disable=too-many-ancestors
        def increase_indent(self, flow=False, indentless=False):  # type: ignore
            return super(IncreasedIndent, self).increase_indent(flow, False)

        def write_line_break(self, data=None):  # type: ignore
            """See https://stackoverflow.com/a/44284819."""
            super().write_line_break(data)
            if len(self.indents) == 1:
                super().write_line_break()

    output_dict = {
        "Kinematics": kinematics,
        "Parameters": parameter_list,
        "Intensity": intensity,
        "ParticleList": particle_dict,
        "Dynamics": dynamics,
    }
    io.yaml.validation.amplitude_model(output_dict)

    with open(filename, "w") as output_stream:
        yaml.dump(
            output_dict,
            output_stream,
            sort_keys=False,
            Dumper=IncreasedIndent,
            default_flow_style=False,
        )
