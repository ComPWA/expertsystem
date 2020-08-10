"""Create a `.ParticleCollection` instance from PDG info."""

from particle import Particle as PdgDatabase

from expertsystem.data import (
    Particle,
    ParticleCollection,
    QuantumState,
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


def __get_hadron_qn(pdg_particle: PdgDatabase) -> tuple:
    baryonnumber = 0
    spin_projection = 0.0
    strangeness = 0
    charmness = 0
    bottomness = 0
    topness = 0
    baryonnumber = (
        pdg_particle.pdgid
        / abs(pdg_particle.pdgid)
        * pdg_particle.pdgid.pdgid.is_baryon
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


def load_pdg() -> ParticleCollection:
    all_pdg_particles = PdgDatabase.findall()
    particle_collection = ParticleCollection()
    for item in all_pdg_particles:
        if not item.charge.is_integer():  # skip quarks
            continue
        mass = 0
        parity = [None, None, None]
        if item.mass is not None:
            mass = item.mass
        isospin = item.I
        if item.P != 5:
            parity[0] = item.P
        if item.C != 5:
            parity[1] = item.C
        if item.G != 5:
            parity[2] = item.G
        hadron_qn = __get_hadron_qn(item)
        lepton_qn = __get_lepton_qn(item)
        new_particle = Particle(
            name=str(item.name),
            pid=int(item.pdgid),
            mass=float(mass),
            width=0.0,
            state=QuantumState[float](
                charge=int(item.charge),
                spin=float(hadron_qn[1]),
                strangeness=hadron_qn[2],
                charmness=hadron_qn[3],
                bottomness=hadron_qn[4],
                topness=hadron_qn[5],
                baryon_number=hadron_qn[0],
                electron_lepton_number=lepton_qn[0],
                muon_lepton_number=lepton_qn[1],
                tau_lepton_number=lepton_qn[2],
                isospin=isospin,
                parity=parity[0],
                c_parity=parity[1],
                g_parity=parity[2],
            ),
        )
        particle_collection.add(new_particle)
    return particle_collection
