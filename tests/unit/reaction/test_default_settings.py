from typing import List

from expertsystem.particle import ParticleCollection
from expertsystem.reaction.combinatorics import arange
from expertsystem.reaction.default_settings import (
    InteractionTypes,
    create_default_interaction_settings,
)
from expertsystem.reaction.quantum_numbers import (
    EdgeQuantumNumbers,
    NodeQuantumNumbers,
)


def spin_range(lower: float, upper: float) -> List[float]:
    return list(arange(lower, upper + 0.5, delta=0.5))


def test_create_default_interaction_settings(
    particle_database: ParticleCollection,
):
    settings = create_default_interaction_settings(
        formalism_type="helicity",
        particles=particle_database,
    )
    assert set(settings) == set(InteractionTypes)
    for interaction_type in InteractionTypes:
        assert settings[interaction_type][0].qn_domains == {
            EdgeQuantumNumbers.baryon_number: [-1, 0, 1],
            EdgeQuantumNumbers.electron_lepton_number: [-1, 0, 1],
            EdgeQuantumNumbers.muon_lepton_number: [-1, 0, 1],
            EdgeQuantumNumbers.tau_lepton_number: [-1, 0, 1],
            EdgeQuantumNumbers.parity: [-1, 1],
            EdgeQuantumNumbers.c_parity: [-1, 1, None],
            EdgeQuantumNumbers.g_parity: [-1, 1, None],
            EdgeQuantumNumbers.spin_magnitude: spin_range(0, 4),
            EdgeQuantumNumbers.spin_projection: spin_range(-4, 4),
            EdgeQuantumNumbers.charge: [-2, -1, 0, 1, 2],
            EdgeQuantumNumbers.isospin_magnitude: spin_range(0.0, 1.5),
            EdgeQuantumNumbers.isospin_projection: spin_range(-1.5, 1.5),
            EdgeQuantumNumbers.strangeness: [-3, -2, -1, 0, 1, 2, 3],
            EdgeQuantumNumbers.charmness: [-1, 0, 1],
            EdgeQuantumNumbers.bottomness: [-1, 0, 1],
        }

    assert settings[InteractionTypes.Weak][1].qn_domains == {
        NodeQuantumNumbers.l_magnitude: [0, 1, 2],
        NodeQuantumNumbers.s_magnitude: [0, 0.5, 1, 1.5, 2],
    }
    assert settings[InteractionTypes.EM][1].qn_domains == {
        NodeQuantumNumbers.l_magnitude: [0, 1, 2],
        NodeQuantumNumbers.s_magnitude: [0, 0.5, 1, 1.5, 2],
        NodeQuantumNumbers.parity_prefactor: [-1, 1],
    }
    assert settings[InteractionTypes.Strong][1].qn_domains == {
        NodeQuantumNumbers.l_magnitude: [0, 1, 2],
        NodeQuantumNumbers.s_magnitude: [0, 0.5, 1, 1.5, 2],
        NodeQuantumNumbers.parity_prefactor: [-1, 1],
    }
