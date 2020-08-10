"""Create a `.ParticleCollection` instance from PDG info."""

from typing import Optional, Tuple

from particle import Particle as PdgDatabase
from particle.particle import enums

from expertsystem.data import (
    Parity,
    Particle,
    ParticleCollection,
    QuantumState,
    Spin,
)


# cspell:ignore pdgid
def __calculate_lepton_qn(pdg_particle: PdgDatabase) -> tuple:
    electron_lepton_number = 0
    muon_lepton_number = 0
    tau_lepton_number = 0
    if pdg_particle.pdgid.is_lepton:
        lepton_number = pdg_particle.pdgid / abs(pdg_particle.pdgid)
        if "e" in pdg_particle.name:
            electron_lepton_number = lepton_number
        elif "mu" in pdg_particle.name:
            muon_lepton_number = lepton_number
        elif "tau" in pdg_particle.name:
            tau_lepton_number = lepton_number
    return electron_lepton_number, muon_lepton_number, tau_lepton_number


def __compute_quark_numbers(
    pdg_particle: PdgDatabase,
) -> Tuple[int, int, int, int]:
    strangeness = 0
    charmness = 0
    bottomness = 0
    topness = 0
    if pdg_particle.pdgid.is_hadron:
        for quark in pdg_particle.quarks:
            if quark == "S":
                strangeness += 1
            elif quark == "s":
                strangeness -= 1
            elif quark == "c":
                charmness += 1
            elif quark == "C":
                charmness -= 1
            elif quark == "b":
                bottomness += 1
            elif quark == "B":
                bottomness -= 1
            elif quark == "t":
                topness += 1
            elif quark == "T":
                topness -= 1
    return (
        strangeness,
        charmness,
        bottomness,
        topness,
    )


def __create_parity(parity_enum: enums.Parity) -> Optional[Parity]:
    if parity_enum in [enums.Parity.o, enums.Parity.u]:
        return None
    return Parity(parity_enum)


def __create_isospin(pdg_particle: PdgDatabase) -> Optional[Spin]:
    if pdg_particle.I is None:
        return None
    return Spin(pdg_particle.I, __compute_isospin_projection(pdg_particle))


def __compute_isospin_projection(pdg_particle: PdgDatabase) -> float:
    spin_projection = 0.0
    if pdg_particle.pdgid.is_hadron:
        for quark in pdg_particle.quarks:
            if quark in ["u", "D"]:
                spin_projection += 0.5
            elif quark in ["U", "d"]:
                spin_projection -= 0.5
    return spin_projection


def __calculate_baryonnumber(pdg_particle: PdgDatabase,) -> int:
    return (
        pdg_particle.pdgid
        / abs(pdg_particle.pdgid)
        * pdg_particle.pdgid.is_baryon
    )


def load_pdg() -> ParticleCollection:
    all_pdg_particles = PdgDatabase.findall(
        lambda item: item.charge.is_integer()  # remove quarks
        and item.J is not None  # remove new physics and nuclei
    )
    particle_collection = ParticleCollection()
    for item in all_pdg_particles:
        quark_numbers = __compute_quark_numbers(item)
        lepton_qn = __calculate_lepton_qn(item)
        new_particle = Particle(
            name=str(item.name),
            pid=int(item.pdgid),
            mass=0.0 if item.mass is None else float(item.mass),
            width=0.0 if item.width is None else float(item.width),
            state=QuantumState[float](
                charge=int(item.charge),
                spin=float(item.J),
                strangeness=quark_numbers[0],
                charmness=quark_numbers[1],
                bottomness=quark_numbers[2],
                topness=quark_numbers[3],
                baryon_number=__calculate_baryonnumber(item),
                electron_lepton_number=lepton_qn[0],
                muon_lepton_number=lepton_qn[1],
                tau_lepton_number=lepton_qn[2],
                isospin=__create_isospin(item),
                parity=__create_parity(item.P),
                c_parity=__create_parity(item.C),
                g_parity=__create_parity(item.G),
            ),
        )
        particle_collection.add(new_particle)
    return particle_collection
