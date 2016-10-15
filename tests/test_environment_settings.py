import os
import shutil
import nose
import tempfile
import unittest

import lamnfyc.utils
import lamnfyc.context_managers


class TestEnvironment(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        simple = """
environment:
  required:
    - SUPER_SECRET

  defaults:
    DEFAULT_ONE: "VALUE_ONE"
    DEFAULT_TWO: "VALUE_TWO"
"""
        dependency = """
environment:
  inherits: simple.yaml

  defaults:
    DEFAULT_ONE: "OVERRIDEN_ONE"
    DEFAULT_THREE: "VALUE_THREE"
"""

        dependency2 = """
environment:
  inherits: ../dependency.yaml
  required:
    - SUPER_SECRET_TWO

  defaults:
    DEFAULT_THREE: "OVERRIDEN_THREE"
    DEFAULT_FOUR: "VALUE_FOUR"
"""

        cls.temp_folder = tempfile.mkdtemp()

        with lamnfyc.context_managers.chdir(cls.temp_folder):
            with open('simple.yaml', 'w') as file_obj:
                file_obj.write(simple)

            with open('dependency.yaml', 'w') as file_obj:
                file_obj.write(dependency)

            os.makedirs('level')
            with open('level/dependency2.yaml', 'w') as file_obj:
                file_obj.write(dependency2)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_folder)

    def test_simple_yaml(self):
        with lamnfyc.context_managers.chdir(self.temp_folder):
            config = lamnfyc.utils.Configuration('simple.yaml')

            nose.tools.assert_equals(config.env['DEFAULT_ONE'], 'VALUE_ONE')
            nose.tools.assert_equals(config.env['DEFAULT_TWO'], 'VALUE_TWO')
            nose.tools.assert_equals(config.env['SUPER_SECRET'], None)

    def test_dependency_yaml(self):
        with lamnfyc.context_managers.chdir(self.temp_folder):
            config = lamnfyc.utils.Configuration('dependency.yaml')

            nose.tools.assert_equals(config.env['DEFAULT_ONE'], 'OVERRIDEN_ONE')
            nose.tools.assert_equals(config.env['DEFAULT_TWO'], 'VALUE_TWO')
            nose.tools.assert_equals(config.env['DEFAULT_THREE'], 'VALUE_THREE')
            nose.tools.assert_equals(config.env['SUPER_SECRET'], None)

    def test_dependency2_yaml(self):
        with lamnfyc.context_managers.chdir(self.temp_folder):
            config = lamnfyc.utils.Configuration('level/dependency2.yaml')

            nose.tools.assert_equals(config.env['DEFAULT_ONE'], 'OVERRIDEN_ONE')
            nose.tools.assert_equals(config.env['DEFAULT_TWO'], 'VALUE_TWO')
            nose.tools.assert_equals(config.env['DEFAULT_THREE'], 'OVERRIDEN_THREE')
            nose.tools.assert_equals(config.env['DEFAULT_FOUR'], 'VALUE_FOUR')
            nose.tools.assert_equals(config.env['SUPER_SECRET'], None)
            nose.tools.assert_equals(config.env['SUPER_SECRET_TWO'], None)
