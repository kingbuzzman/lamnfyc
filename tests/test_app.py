import os
import shutil
import nose
import tempfile
import unittest
import mock

import lamnfyc.cli
import lamnfyc.utils
import lamnfyc.context_managers


from inspect import getargspec  # noqa

import ipdb  # noqa
from ipdb.__main__ import def_colors, def_exec_lines  # noqa
from IPython import version_info as ipython_version  # noqa
from IPython.terminal.interactiveshell import TerminalInteractiveShell  # noqa

def _get_debugger_cls():
    if ipython_version < (5, 0, 0):
        from IPython.core.debugger import Pdb
        return Pdb
    return TerminalInteractiveShell().debugger_cls

def _init_pdb(context=3):
    debugger_cls = _get_debugger_cls()
    if 'context' in getargspec(debugger_cls.__init__)[0]:
        p = debugger_cls(def_colors, context=context)
    else:
        p = debugger_cls(def_colors)
    p.rcLines += def_exec_lines
    return p

ipdb.__main__._init_pdb = _init_pdb


from contextlib import contextmanager
import sys, os

@contextmanager
def redirect_stdout_stderr(stream):
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    sys.stdout = stream
    sys.stderr = stream
    try:
        yield
    finally:
        sys.stdout = old_stdout
        sys.stderr = old_stderr


class TestApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Tests that the base yaml file works as intended
        simple = """
packages:
  - name: python
    version: 2.7.6

environment:
  required:
    - SUPER_SECRET

  defaults:
    DEFAULT_ONE: "VALUE_ONE"
    DEFAULT_TWO: "VALUE_TWO"
"""
        cls.temp_folder = tempfile.mkdtemp()

        # Saves everything inside a temporary folder to tests hierarchies
        with lamnfyc.context_managers.chdir(cls.temp_folder):
            with open('othername.yaml', 'w') as file_obj:
                file_obj.write(simple)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_folder)

    def test_install_options(self):
        with lamnfyc.context_managers.chdir(self.temp_folder):
            # Makes sure that the yaml config file gets created
            nose.tools.assert_false(os.path.exists('lamnfyc.yaml'))
            with self.assertRaises(SystemExit) as exc:
                parsed = lamnfyc.cli.parser().parse_args(['--init'])
            # Make sure that we quit "properly"
            nose.tools.assert_equals(str(exc.exception), '0')
            nose.tools.assert_true(os.path.exists('lamnfyc.yaml'))

            # Init environment
            parsed = lamnfyc.cli.parser().parse_args(['env'])
            nose.tools.assert_equals(parsed.init, False)
            nose.tools.assert_equals(parsed.environment, 'env')
            nose.tools.assert_in('lamnfyc.yaml', parsed.config)

            # Init custom environment config
            parsed = lamnfyc.cli.parser().parse_args(['-c' 'othername.yaml', 'env'])
            nose.tools.assert_equals(parsed.init, False)
            nose.tools.assert_equals(parsed.config, 'othername.yaml')
            nose.tools.assert_equals(parsed.environment, 'env')

            # Invalid options
            # Redirect all the output to /dev/null
            with redirect_stdout_stderr(open(os.devnull, 'w')):
                # Errors because the file already exists
                with self.assertRaises(SystemExit) as exc:
                    lamnfyc.cli.parser().parse_args(['--init'])
                nose.tools.assert_equals(str(exc.exception), '2')

                # Environment agument is required
                with self.assertRaises(SystemExit) as exc:
                    lamnfyc.cli.parser().parse_args([''])
                nose.tools.assert_equals(str(exc.exception), '2')

                # Verbosity value is not vallid
                with self.assertRaises(SystemExit) as exc:
                    lamnfyc.cli.parser().parse_args(['-v' 'NOT_VALID', 'env'])
                nose.tools.assert_equals(str(exc.exception), '2')

                # Config path is not valid
                with self.assertRaises(SystemExit) as exc:
                    lamnfyc.cli.parser().parse_args(['-c' 'NOT_VALID', 'env'])
                nose.tools.assert_equals(str(exc.exception), '2')
