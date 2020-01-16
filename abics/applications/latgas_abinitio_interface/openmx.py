from .base_solver import SolverBase
from collections import namedtuple
import numpy as np
import os.path
import scipy.constants as spc
from pymatgen.io.cif import CifParser

hartree2eV = spc.value("Hartree energy in eV")
Bohr2AA = spc.value('Bohr radius') * 1e10

class OpenMXSolver(SolverBase):
    """
    This class defines the OpenMX solver.
    """

    def __init__(self, path_to_solver):
        """
        Initialize the solver.

        Parameters
        ----------
        path_to_solver : str
                      Path to the solver.
        """
        super(OpenMXSolver, self).__init__(path_to_solver)
        self.path_to_solver = path_to_solver
        self.input = OpenMXSolver.Input()
        self.output = OpenMXSolver.Output()

    def name(self):
        """
        Return the solver name.

        Returns
        -------
        "OpenMX"

        """
        return "OpenMX"

    class Input(object):
        def __init__(self):
            self.base_info = None
            self.pos_info = None
            self.openmx_vec_list = ["Atoms.UnitVectors", "Atoms.SpeciesAndCoordinates", "MD.Fixed.XYZ"]

        def cleanup(self, rundir):
            """
            Clean up the directory where the solver runs.

            Parameters
            ----------
            rundir: str
                Name of the directory where the solver runs.
            -------

            """

            checkfile = os.path.join(rundir, self.datadir, self.filetocheck)
            if os.path.exists(checkfile):
                os.remove(checkfile)

        def from_directory(self, base_input_dir):
            """

            Get base information for OpenMX from the input directory.

            Parameters
            ----------
            base_input_dir: str
                Name of the directory where the base input file is located.

            Returns
            -------
            self.base_openmx_input:  Dictionary
                        Dictionary for base information of the solver.
            """
            #TODO
            # check the base input file name (now, set "base.dat")
            self.base_openmx_input = self.OpenMXInputFile(os.path.join(os.getcwd(), base_input_dir, "base.dat"))
            return self.base_openmx_input

        def update_info_by_structure(self, structure, seldyn_arr=None):
            """
            Update base_openmx_input by structure

            Parameters
            ----------
            structure: pymatgen.core.Structure
                Structure for getting atom's species and coordinates
            seldyn_arr:


            """
            A = structure.lattice.matrix
            #Update unitvector information
            self.base_openmx_input["Atoms.UnitVectors.Unit"] = "Ang"
            self.base_openmx_input["Atoms.UnitVectors"] = A # numpy.ndarray
            nat = len(structure.sites)
            self.base_openmx_input["Atoms.Number"] = nat
            self.base_openmx_input["Atoms.SpeciesAndCoordinates.Unit"] = "FRAC"
            self.base_openmx_input["Atoms.SpeciesAndCoordinates"] = [[0, "", 0.0, 0.0, 0.0, 0.0, 0.0]]*nat
            spin_up = structure.site_properties["spin_up"]
            spin_down = structure.site_properties["spin_down"]

            for idx, site in enumerate(structure.sites):
                self.base_openmx_input["Atoms.SpeciesAndCoordinates"][idx] =[idx, site.specie, site.a, site.b, site.c, spin_up[idx], spin_down[idx]]

            #TODO Structure relaxation (issue 24)
            #Use MD.type, MD.Fixed.XYZ

        def write_input(self, output_dir):
            """
            Generate input files at each directory.

            Parameters
            ----------
            output_dir: str


            """
            with open(output_dir, "w") as f:
                for key, values in self.openmx_dict.items():
                    if key in self.openmx_vec_list:
                        print_stamp = "<{}\n".format(key)
                        for value_list in values:
                            for value in value_list:
                                print_stamp += " {}".format(value)
                            print_stamp += "\n"
                        print_stamp += "{}>\n".format(key)
                    else:
                        print_stamp = key
                        for value_list in values:
                            print_stamp += " {}".format(value_list)
                        print_stamp += "\n"
                    f.write(print_stamp)

        def cl_args(self, nprocs, nthreads, output_dir):
            """
            Make command line to execute OpenMX from args.

            Parameters
            ----------
            nprocs: int
                Number of processes (not used).

            nthreads: int
                Number of threads (not used).

            output_dir: str
                Output directory.

            Returns
            -------
            clargs: Dictionary
                command line arguments
            """
            clargs = [output_dir, "{}.dat".format(self.base_openmx_input["System.Name"])]
            return clargs

        def OpenMXInputFile(self, current_dir, base_input_dir, file_name):
            """

            Read base input file for setting initial conditions.

            Parameters
            ----------
            current_dir: str

            base_input_dir: str

            file_name: str

            Returns
            -------
            OpenMX_dict: dictionary


            """
            input_dir = os.path.join(current_dir, base_input_dir, file_name)
            OpenMX_dict = {}
            with open(input_dir, "r") as f:
                lines = f.readlines()
                # delete comment out
                list_flag = False
                for line in lines:
                    line = line.split("#")[0]
                    if len(line) >= 2:
                        words = line.split()
                        if words[0][0] == "<":
                            list_flag = True
                            vec_list = []
                        elif words[0][-1:] == ">":
                            OpenMX_dict[line[:-2]] = vec_list
                            self.openmx_vec_list.append(line[:-2])
                            list_flag = False
                        else:
                            if list_flag is False:
                                OpenMX_dict[words[0]] = words[1:]
                            else:
                                vec_list.append(words)
                        self.openmx_vec_list = list( set(self.openmx_vec_list) )
                return OpenMX_dict

        #def submit: Use submit defined in run_base_mpi.py

    class Output(object):
        def __init__(self):
            pass

        def get_results(self, output_dir):
            """
            Read results from files in output_dir and calculate values

            Parameters
            ----------
            output_dir: str
                    Name of output directory

            Returns
            -------
            Phys: namedtuple
                results

            """
            # Read results from files in output_dir and calculate values
            output_file = "{}.out".format(self.base_openmx_input["System.Name"])
            with open(output_file, "r") as fi:
                lines = fi.readlines()
                lines_strip = [line.strip() for line in lines]
                # Get total energy
                Utot = float([line for line in lines_strip if 'Utot.' in line][0].split()[1])
                # Change energy unit from Hartree to eV
                Utot *= hartree2eV

            # Get Cell information from dat# file
            A = np.zeros((3, 3))
            output_file = "{}.dat#".format(self.base_openmx_input["System.Name"])
            with open(output_file, "r") as fi:
                lines = fi.readlines()
                lines_strip = [line.strip() for line in lines]
                # Get Cell information
                # Read Atoms.UnitVectors.Unit
                Atoms_UnitVectors_Unit = [line.split()[1] for line in lines_strip if 'Atoms.UnitVectors.Unit' in line][
                    0]
                print(Atoms_UnitVectors_Unit)
                line_number_unit_vector_start = \
                [i for i, line in enumerate(lines_strip) if '<Atoms.UnitVectors' in line][0]
                print(line_number_unit_vector_start)
                for i, line in enumerate(
                        lines_strip[line_number_unit_vector_start + 1: line_number_unit_vector_start + 4]):
                    A[:, i] = list(line.split())
                if Atoms_UnitVectors_Unit == "AU":
                    A *= Bohr2AA

            # Note:
            # Since xyz format of OpenMX is not correct (3 columns are added at each line).
            # pymatgen.io.xyz can not work.
            output_file = "{}.xyz".format(self.base_openmx_input["System.Name"])
            species = []
            positions = []
            with open(output_file, "r") as fi:
                # Get atomic species and positions
                lines = fi.readlines()
                lines_strip = [line.strip().split() for line in lines]
                for line in lines_strip[2:]:
                    species.append(line[0])
                    positions.append([float(s) for s in line[1:4]])
            structure = Structure(A, species, positions, coords_are_cartesian=True)
            Phys = namedtuple("PhysVaules", ("energy", "structure"))
            return Phys(np.float64(Utot), structure)

    def solver_run_schemes(self):
        return ('mpi_spawn_ready',)



