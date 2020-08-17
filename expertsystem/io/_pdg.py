"""Create a `.ParticleCollection` instance from PDG info."""

import re
from typing import (
    Optional,
    Tuple,
)

from numpy import sign

from particle import Particle as PdgDatabase
from particle.particle import enums

from expertsystem.data import (
    GellmannNishijima,
    Parity,
    Particle,
    ParticleCollection,
    QuantumState,
    Spin,
)


__skip_particles = {
    "K(L)0",  # no isospin projection
    "K(S)0",  # no isospin projection
    "B(s2)*(5840)0",  # isospin(0.5, 0.0) ?
    "B(s2)*(5840)~0",  # isospin(0.5, 0.0) ?
}


def load_pdg() -> ParticleCollection:
    all_pdg_particles = PdgDatabase.findall(
        lambda item: item.charge.is_integer()  # remove quarks
        and item.J is not None  # remove new physics and nuclei
        and abs(item.pdgid) < 1e9  # p and n as nucleus
        and item.name not in __skip_particles
    )
    particle_collection = ParticleCollection()
    for pdg_particle in all_pdg_particles:
        new_particle = __convert_pdg_instance(pdg_particle)
        particle_collection.add(new_particle)
    return particle_collection


# cspell:ignore pdgid
def __convert_pdg_instance(pdg_particle: PdgDatabase) -> Particle:
    def convert_mass_width(value: Optional[float]) -> float:
        if value is None:
            return 0.0
        return (  # https://github.com/ComPWA/expertsystem/issues/178
            float(value) / 1e3
        )

    quark_numbers = __compute_quark_numbers(pdg_particle)
    lepton_numbers = __compute_lepton_numbers(pdg_particle)
    if pdg_particle.pdgid.is_lepton:  # convention: C(fermion)=+1
        parity: Optional[Parity] = Parity(sign(pdg_particle.pdgid))  # type: ignore
    else:
        parity = __create_parity(pdg_particle.P)
    return Particle(
        name=str(pdg_particle.name),
        pid=int(pdg_particle.pdgid),
        mass=convert_mass_width(pdg_particle.mass),
        width=convert_mass_width(pdg_particle.width),
        state=QuantumState[float](
            charge=int(pdg_particle.charge),
            spin=float(pdg_particle.J),
            strangeness=quark_numbers[0],
            charmness=quark_numbers[1],
            bottomness=quark_numbers[2],
            topness=quark_numbers[3],
            baryon_number=__compute_baryonnumber(pdg_particle),
            electron_lepton_number=lepton_numbers[0],
            muon_lepton_number=lepton_numbers[1],
            tau_lepton_number=lepton_numbers[2],
            isospin=__create_isospin(pdg_particle),
            parity=parity,
            c_parity=__create_parity(pdg_particle.C),
            g_parity=__create_parity(pdg_particle.G),
        ),
    )


__remove_from_quark_content = {"sqrt", "Maybe"}


def __compute_quark_numbers(
    pdg_particle: PdgDatabase,
) -> Tuple[int, int, int, int]:
    strangeness = 0
    charmness = 0
    bottomness = 0
    topness = 0
    if pdg_particle.pdgid.is_hadron:
        quark_content = pdg_particle.quarks
        for word in __remove_from_quark_content:
            quark_content = quark_content.replace(word, "")
        strangeness = quark_content.count("S") - quark_content.count("s")
        charmness = quark_content.count("c") - quark_content.count("C")
        bottomness = quark_content.count("B") - quark_content.count("b")
        topness = quark_content.count("t") - quark_content.count("T")
    return (
        strangeness,
        charmness,
        bottomness,
        topness,
    )


def __compute_lepton_numbers(
    pdg_particle: PdgDatabase,
) -> Tuple[int, int, int]:
    electron_lepton_number = 0
    muon_lepton_number = 0
    tau_lepton_number = 0
    if pdg_particle.pdgid.is_lepton:
        lepton_number = int(sign(pdg_particle.pdgid))
        if "e" in pdg_particle.name:
            electron_lepton_number = lepton_number
        elif "mu" in pdg_particle.name:
            muon_lepton_number = lepton_number
        elif "tau" in pdg_particle.name:
            tau_lepton_number = lepton_number
    return electron_lepton_number, muon_lepton_number, tau_lepton_number


def __compute_baryonnumber(pdg_particle: PdgDatabase) -> int:
    return int(sign(pdg_particle.pdgid) * pdg_particle.pdgid.is_baryon)


def __create_isospin(pdg_particle: PdgDatabase) -> Optional[Spin]:
    if pdg_particle.I is None:
        return None
    magnitude = pdg_particle.I
    projection = __compute_isospin_projection(pdg_particle)
    isospin = Spin(magnitude, projection)
    if not (magnitude - projection).is_integer():
        raise ValueError(f"{pdg_particle.name} has isospin {isospin}")
    return isospin


def __compute_isospin_projection(pdg_particle: PdgDatabase) -> float:
    if "qq" in pdg_particle.quarks.lower():
        strangeness, charmness, bottomness, topness = __compute_quark_numbers(
            pdg_particle
        )
        baryon_number = __compute_baryonnumber(pdg_particle)
        projection = GellmannNishijima.compute_isospin_projection(
            charge=pdg_particle.charge,
            baryon_number=baryon_number,
            strangeness=strangeness,
            charmness=charmness,
            bottomness=bottomness,
            topness=topness,
        )
    else:
        projection = 0.0
        if pdg_particle.pdgid.is_hadron:
            quark_content = __filter_quark_content(pdg_particle)
            projection += quark_content.count("u") + quark_content.count("D")
            projection -= quark_content.count("U") + quark_content.count("d")
            projection *= 0.5
    if not (pdg_particle.I - projection).is_integer():
        raise ValueError(f"Cannot have isospin {pdg_particle.I, projection}")
    return projection


def __filter_quark_content(pdg_particle: PdgDatabase) -> str:
    matches = re.search(r"([dDuUsScCbBtT+-]{2,})", pdg_particle.quarks)
    if matches is None:
        return ""
    return matches[1]


def __create_parity(parity_enum: enums.Parity) -> Optional[Parity]:
    if parity_enum in [enums.Parity.o, enums.Parity.u]:
        return None
    return Parity(parity_enum)
