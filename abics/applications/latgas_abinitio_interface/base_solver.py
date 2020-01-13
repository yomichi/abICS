from collections import namedtuple


class SolverBase(object):
    """
    Base class defining the common interface of solvers.

    Attributes
    ----------
    path_to_solver : str
        Path to solver program.
    input : SolverBase.Input
        Input manager.
    output : SolverBase.Output
        Output manager.
    """

    class Input(object):
        """
        Input manager.

        Attributes
        ----------
        base_info : Any
            Common parameter.
        pos_info : Any
            Information of position.
        """

        def __init__(self):
            self.base_info = None
            self.pos_info = None

        def update_info_by_structure(self, structure):
            """
            Update information by structure.

            Parameters
            ----------
            structure : pymatgen.Structure
                Atomic structure.

            """
            return None

        def update_info_from_files(self, output_dir, rerun):
            """
            Update information by result files.

            Parameters
            ----------
            output_dir : str
                Path to working directory.
            rerun : int
            """

            return None

        def write_input(self, output_dir):
            """
            Generate input files of the solver program.

            Parameters
            ----------
            output_dir : str
                Path to working directory.
            """
            return None

        def from_directory(self, base_input_dir):
            """
            Set information, base_input and pos_info, from files in the base_input_dir

            Parameters
            ----------
            base_input_dir : str
                Path to the directory including base input files.
            """
            # set information of base_input and pos_info from files in base_input_dir
            base_info = {}
            pos_info = {}
            self.base_info = {}
            self.pos_info = {}

        def cl_args(self, nprocs, nthreads, workdir):
            """
            Generate argument parameters of the solver program.

            Parameters
            ----------
            nprocs : int
                The number of processes.
            nthreads : int
                The number of threads.
            workdir : str
                Path to the working directory.
            """
            return []

    class Output(object):
        """
        Output manager.
        """
        def get_results(self, output_dir):
            """
            Get energy and structure obtained by the solver program.

            Parameters
            ----------
            output_dir : str
                Path to the working directory.

            Returns
            -------
            phys : named_tuple("energy", "structure")
                Total energy and atomic structure.
            """
            Phys = namedtuple("PhysVaules", ("energy", "structure"))
            # Read results from files in output_dir and calculate values
            phys = Phys(0.0, None)
            return phys

    def __init__(self, path_to_solver):
        """
        Initialize the solver.

        Parameters
        ----------
        solver_name : str
            Solver name.
        path_to_solver : str
            Path to the solver.
        """
        self.path_to_solver = path_to_solver
        self.input = SolverBase.Input
        self.output = SolverBase.Output

    def name(self):
        """
        Returns
        -------
        name : str
            Name of solver.
        """
        return "Base solver"

    def solver_run_schemes(self):
        """
        Returns
        -------
        schemes : tuple[str]
            Implemented runner schemes.
        """
        return ()
