import os
import unittest

import numpy as np

from pymatgen import Structure

from abics.applications.latgas_abinitio_interface.qe import QESolver

from qe_tools.parsers import PwInputFile


class TestQE(unittest.TestCase):
    def setUp(self):
        self.solver = QESolver(".")
        self.rootdir = os.path.dirname(__file__)
        self.datadir = os.path.join(self.rootdir, "data", "qe")
        self.workdir = os.path.join(self.rootdir, "res", "qe")

    def test_get_results(self):
        res = self.solver.output.get_results(self.datadir)
        res.structure.to("POSCAR", os.path.join(self.workdir, "pos.vasp"))
        ref = Structure.from_file(os.path.join(self.datadir, "..", "pos.vasp"))
        ref_energy = -1039.9018832347706
        self.assertTrue(res.structure.matches(ref))
        self.assertTrue(np.isclose(res.energy, ref_energy))

    def test_input(self):
        self.solver.input.from_directory(os.path.join(self.datadir, "baseinput"))
        A = 4.0*np.eye(3)
        r = np.array([[0.0, 0.0, 0.0], [0.5, 0.5, 0.5]])
        st = Structure(A, ["Al", "Al"], r, coords_are_cartesian=False)

        self.solver.input.update_info_by_structure(st)
        self.solver.input.write_input(self.workdir)
        res = PwInputFile(os.path.join(self.workdir, "scf.in"))
        ref = PwInputFile(os.path.join(self.datadir, "scf.in"))

        res.namelists["CONTROL"]["pseudo_dir"] = ref.namelists["CONTROL"]["pseudo_dir"]
        res.namelists["CONTROL"]["outdir"] = ref.namelists["CONTROL"]["outdir"]

        self.assertEqual(res.namelists, ref.namelists)

        self.assertTrue(np.allclose(res.cell_parameters["cell"], ref.cell_parameters["cell"]))
        self.assertTrue(np.allclose(res.atomic_positions["positions"], ref.atomic_positions["positions"]))

    def test_cl_algs(self):
        nprocs = 2
        nthreads = 4
        workdir = "work"
        res = self.solver.input.cl_args(nprocs, nthreads, workdir)
        self.assertEqual(res, ["-in", os.path.join(workdir, "scf.in")])

