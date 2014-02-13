#!/usr/bin/env python

"""
This module implements basic kinds of jobs for QChem runs.
"""

from __future__ import division
import os
from monty.io import zopen
import shutil
import copy
import subprocess
from custodian.custodian import Job, gzip_dir

__author__ = "Xiaohui Qu"
__version__ = "0.1"
__maintainer__ = "Xiaohui Qu"
__email__ = "xhqu1981@gmail.com"
__status__ = "Alpha"
__date__ = "12/03/13"


class QchemJob(Job):
    """
    A basic QChem Job.
    """

    def __init__(self, qchem_cmd, input_file="mol.qcinp",
                 output_file="mol.qcout", chk_file=None, qclog_file=None,
                 gzipped=False, backup=True, alt_cmd=None):
        """
        This constructor is necessarily complex due to the need for
        flexibility. For standard kinds of runs, it's often better to use one
        of the static constructors.

        Args:
            qchem_cmd ([str]): Command to run QChem as a list args (without
                input/output file name). For example: ["qchem", "-np", "24"]
            input_file (str): Name of the QChem input file.
            output_file (str): Name of the QChem output file.
            chk_file (str): Name of the QChem check point file. None means no
                checkpoint point file. Defaults to None.
            qclog_file (str): Name of the file to redirect the standard output
                to. None means not to record the standard output. Defaults to
                None.
            gzipped (bool): Whether to gzip the final output. Defaults to False.
            backup (bool): Whether to backup the initial input files. If True,
                the input files will be copied with a ".orig" appended.
                Defaults to True.
            alt_cmd (dict of list): Alternate commands.
                For example: {"openmp": ["qchem", "-seq", "-nt", "24"]
                              "half_nodes": ["qchem", "-np", "12"]}
        """
        self.qchem_cmd = copy.deepcopy(qchem_cmd)
        self.input_file = input_file
        self.output_file = output_file
        self.chk_file = chk_file
        self.qclog_file = qclog_file
        self.gzipped = gzipped
        self.backup = backup
        self.current_command = self.qchem_cmd
        self.current_command_name = "general"
        self.alt_cmd = copy.deepcopy(alt_cmd)

    def select_command(self, cmd_name):
        """
        Set the command to run QChem by name. "general" set to the default one.

        Returns:
            True: success
            False: failed
        """
        available_commands = ["general"]
        if self.alt_cmd:
            available_commands.extend(self.alt_cmd.keys())
        if cmd_name not in available_commands:
            return False
        if cmd_name == "general":
            self.current_command = self.qchem_cmd
        else:
            self.current_command = self.alt_cmd[cmd_name]
        self.current_command_name = cmd_name
        return True

    def setup(self):
        if self.backup:
            i = 0
            while os.path.exists("{}.{}.orig".format(self.input_file, i)):
                i += 1
            shutil.copy(self.input_file,
                        "{}.{}.orig".format(self.input_file, i))
            if self.chk_file and os.path.exists(self.chk_file):
                shutil.copy(self.chk_file,
                            "{}.{}.orig".format(self.chk_file, i))
            if os.path.exists(self.output_file):
                shutil.copy(self.output_file,
                            "{}.{}.orig".format(self.output_file, i))
            if self.qclog_file and os.path.exists(self.qclog_file):
                shutil.copy(self.qclog_file,
                            "{}.{}.orig".format(self.qclog_file, i))

    def run(self):
        cmd = copy.deepcopy(self.current_command)
        cmd += [self.input_file, self.output_file]
        if self.chk_file:
            cmd.append(self.chk_file)
        if self.qclog_file:
            with zopen(self.qclog_file, "w") as filelog:
                returncode = subprocess.call(cmd, stdout=filelog)
        else:
            returncode = subprocess.call(cmd)
        return returncode

    def postprocess(self):
        if self.gzipped:
            gzip_dir(".")
