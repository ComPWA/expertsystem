"""Tags used when writing to and from XML files."""


from enum import Enum


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

Tags = [
    CONSTANTS.QuantumNumber,
    CONSTANTS.Parameter,
    CONSTANTS.PreFactor,
    CONSTANTS.DecayInfo,
]


def get_label(enum):
    """
    Return the the correctly formatted XML label as required by ComPWA and
    ``xmltodict``.
    """
    attribute_prefix = "@"
    if enum in Tags:
        return enum.name
    return attribute_prefix + enum.name
