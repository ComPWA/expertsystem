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
def __get_lepton_qn(pdg_particle: PdgDatabase) -> tuple:
    electron_lepton_number = 0
    muon_lepton_number = 0
    tau_lepton_number = 0
    if pdg_particle.pdgid.is_lepton:
        if "e" in pdg_particle.name:
            electron_lepton_number = pdg_particle.pdgid / abs(
                pdg_particle.pdgid
            )
        if "mu" in pdg_particle.name:
            muon_lepton_number = pdg_particle.pdgid / abs(pdg_particle.pdgid)
        if "tau" in pdg_particle.name:
            tau_lepton_number = pdg_particle.pdgid / abs(pdg_particle.pdgid)

    return electron_lepton_number, muon_lepton_number, tau_lepton_number


def __get_hadron_qn(
    pdg_particle: PdgDatabase,
) -> Tuple[int, float, int, int, int, int]:
    baryonnumber = 0
    spin_projection = 0.0
    strangeness = 0
    charmness = 0
    bottomness = 0
    topness = 0
    baryonnumber = (
        pdg_particle.pdgid
        / abs(pdg_particle.pdgid)
        * pdg_particle.pdgid.is_baryon
    )
    if pdg_particle.pdgid.is_hadron:
        for quark in pdg_particle.quarks:
            if quark in ["u", "D"]:
                spin_projection += 0.5
            elif quark in ["U", "d"]:
                spin_projection -= 0.5
            elif quark == "S":
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
        baryonnumber,
        spin_projection,
        strangeness,
        charmness,
        bottomness,
        topness,
    )


def __create_parity(parity_enum: enums.Parity) -> Optional[Parity]:
    if parity_enum in [enums.Parity.o, enums.Parity.u]:
        return None
    return Parity(parity_enum)


def __create_spin(magnitude: float, projection: float) -> Optional[Spin]:
    if magnitude is not None:
        return Spin(magnitude, projection)
    return None


def load_pdg() -> ParticleCollection:
    all_pdg_particles = PdgDatabase.findall(
        lambda item: item.charge.is_integer()  # remove quarks
        and item.J is not None  # remove new physics and nucleus
    )
    particle_collection = ParticleCollection()
    for item in all_pdg_particles:
        mass = 0
        if item.mass is not None:
            mass = item.mass
        isospin = item.I
        hadron_qn = __get_hadron_qn(item)
        lepton_qn = __get_lepton_qn(item)
        new_particle = Particle(
            name=str(item.name),
            pid=int(item.pdgid),
            mass=float(mass),
            width=0.0,
            state=QuantumState[float](
                charge=int(item.charge),
                spin=float(item.J),
                strangeness=hadron_qn[2],
                charmness=hadron_qn[3],
                bottomness=hadron_qn[4],
                topness=hadron_qn[5],
                baryon_number=hadron_qn[0],
                electron_lepton_number=lepton_qn[0],
                muon_lepton_number=lepton_qn[1],
                tau_lepton_number=lepton_qn[2],
                isospin=__create_spin(isospin, hadron_qn[1]),
                parity=__create_parity(item.P),
                c_parity=__create_parity(item.C),
                g_parity=__create_parity(item.G),
            ),
        )
        particle_collection.add(new_particle)
    return particle_collection
