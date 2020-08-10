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


def load_pdg() -> ParticleCollection:
    all_pdg_particles = PdgDatabase.findall(
        lambda item: item.charge.is_integer()  # remove quarks
        and item.J is not None  # remove new physics and nuclei
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
    lepton_qn = __calculate_lepton_qn(pdg_particle)
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
            baryon_number=__calculate_baryonnumber(pdg_particle),
            electron_lepton_number=lepton_qn[0],
            muon_lepton_number=lepton_qn[1],
            tau_lepton_number=lepton_qn[2],
            isospin=__create_isospin(pdg_particle),
            parity=__create_parity(pdg_particle.P),
            c_parity=__create_parity(pdg_particle.C),
            g_parity=__create_parity(pdg_particle.G),
        ),
    )


def __compute_quark_numbers(
    pdg_particle: PdgDatabase,
) -> Tuple[int, int, int, int]:
    strangeness = 0
    charmness = 0
    bottomness = 0
    topness = 0
    if pdg_particle.pdgid.is_hadron:
        quark_content = pdg_particle.quarks.replace("sqrt", "")
        for quark in quark_content:
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


def __calculate_lepton_qn(pdg_particle: PdgDatabase) -> Tuple[int, int, int]:
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


def __calculate_baryonnumber(pdg_particle: PdgDatabase) -> int:
    return (
        pdg_particle.pdgid
        / abs(pdg_particle.pdgid)
        * pdg_particle.pdgid.is_baryon
    )


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


def __create_parity(parity_enum: enums.Parity) -> Optional[Parity]:
    if parity_enum in [enums.Parity.o, enums.Parity.u]:
        return None
    return Parity(parity_enum)
