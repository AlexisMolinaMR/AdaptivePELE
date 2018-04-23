import argparse
import glob
import os
import numpy as np
from AdaptivePELE.utilities import utilities
from AdaptivePELE.atomset import atomset


def parseArgs():
    parser = argparse.ArgumentParser(description="Get representative structures "
                                     "by selecting the ones closest to the "
                                     "cluster centers")
    parser.add_argument('representatives', type=str, help="Path to the representative structures summary file")
    parser.add_argument('structures_path', type=str, help="Path to the simulation structures")
    parser.add_argument('-o', type=str, default="", help="Path where to store the structures")
    parser.add_argument('-c', '--clusters', default=['a'], nargs="*", help="Clusters to extract, if not specified it will extract all")
    parser.add_argument("-t", "-trajectoryName", type=str, default="trajectory", help="Name of the trajectory files, e.g for trajectory_1.pdb the name is trajectory")
    parser.add_argument("--top", type=str, default=None, help="Topology file for non-pdb trajectories")
    args = parser.parse_args()
    return args


def main(representatives_files, path_structures, output="", clusters=None, trajNames="trajectory", topology=None):
    if clusters is None:
        clusters = ['a']
    # Load the representative structures file
    try:
        clusters_info = np.loadtxt(representatives_files, skiprows=1)
    except IOError:
        raise IOError("Couldn't find a representative file in %s, please check that the path is correct" % representatives_files)
    # Organize to minimise pdb loading
    if clusters != ['a']:
        clusters_info = clusters_info[map(int, clusters)]

    extract_info = {}
    for row in clusters_info:
        index = (row[1], row[2])
        value = (row[0], row[3])
        if index in extract_info:
            extract_info[index].append(value)
        else:
            extract_info[index] = [value]

    # Write appropiate pdbs
    destFolder = output
    if not output:
        destFolder, _ = os.path.split(representatives_files)
        destFolder = os.path.join(destFolder, "representative_structures_pdbs")

    if not os.path.exists(destFolder):
        os.makedirs(destFolder)
    else:
        destFolder += "_%d"
        it = 1
        while os.path.exists(destFolder % it):
            it += 1
        destFolder %= it
        os.makedirs(destFolder)
    structureFolder = os.path.join(path_structures, "%d", trajNames+"_%d*")
    for trajFile, extraInfo in extract_info.items():
        pdbFile = glob.glob(structureFolder % trajFile)
        try:
            snapshots = utilities.getSnapshots(pdbFile, topology=topology)
        except IOError:
            raise IOError("Unable to open %s, please check that the path to structures provided is correct" % pdbFile)
        if not isinstance(snapshots[0], basestring):
            topology_contents = utilities.getTopologyFile(topology)
        else:
            topology_contents = None

        for pair in extraInfo:
            if topology_contents is None:
                with open(os.path.join(destFolder, "cluster_%d.pdb" % pair[0]), "w") as fw:
                    fw.write(snapshots[int(pair[1])])
                    fw.write("\n")
            else:
                PDB = atomset.PDB()
                PDB.initialise(snapshots[int(pair[1])])
                PDB.writePDB(os.path.join(destFolder, "cluster_%d.pdb" % pair[0]), topology=topology_contents)


if __name__ == "__main__":
    arg = parseArgs()
    main(arg.representatives, arg.structures_path, arg.o, arg.clusters, arg.t, arg.top)
