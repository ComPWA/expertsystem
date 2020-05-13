"""Tags and tools used when writing to and from XML files."""


__all__ = [
    "CONSTANTS",
    "get_label",
]


from collections import OrderedDict
from enum import Enum

import xmltodict


CONSTANTS = Enum(
    "LabelConstants",
    "Name "
    "Pid "
    "Type "
    "Value "
    "QuantumNumber "
    "Class "
    "Projection "
    "Component "
    "Parameter "
    "PreFactor "
    "DecayInfo",
)

TAGS = [
    CONSTANTS.QuantumNumber,
    CONSTANTS.Parameter,
    CONSTANTS.PreFactor,
    CONSTANTS.DecayInfo,
]


def get_label(enum: Enum) -> str:
    """
    Return the correctly formatted XML label.

    The labels agree with what ComPWA expects and are used by ``xmltodict``.
    """
    attribute_prefix = "@"
    if enum in TAGS:
        return enum.name
    return attribute_prefix + enum.name


def write_dict(
    input_dict: dict, filename: str, overwrite: bool = False
) -> None:
    """Write a dictionary to an XML file."""
    if not filename.endswith("xml"):
        raise FileNotFoundError("Output file has to be an XML file!")
    mode = "a+"
    if overwrite:
        mode = "w"
    with open(filename, mode=mode) as xmlfile:
        xmlstring = xmltodict.unparse(
            OrderedDict({"root": input_dict}),
            pretty=True,
            full_document=False,
        )
        # The root tag needs to be removed again for ComPWA
        xmlstring = xmlstring.replace("<root>", "", 1)
        xmlstring = xmlstring[:-10] + xmlstring[-10:].replace("</root>", "", 1)
        xmlfile.write(xmlstring)
        xmlfile.close()
