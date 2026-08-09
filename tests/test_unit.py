#!/usr/bin/env python3
"""
Unit tests for workflow validation
"""

import sys
import unittest
from pathlib import Path
import tempfile
import yaml

# Add tests directory to path
sys.path.insert(0, str(Path(__file__).parent))

from test_workflows import WorkflowValidator


class TestWorkflowValidation(unittest.TestCase):
    """Test suite for workflow validation"""
    
    def setUp(self):
        """Set up test fixtures"""
        import shutil
        self.temp_dir = tempfile.mkdtemp()
        self.temp_path = Path(self.temp_dir)
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if self.temp_path.exists():
            shutil.rmtree(self.temp_path)
        # Clear errors and warnings for next test
        self.errors = []
        self.warnings = []
    
    def create_workflow_file(self, name, content):
        """Helper to create a test workflow file"""
        path = self.temp_path / name
        path.write_text(content)
        return path
    
    def test_validator_init(self):
        """Test WorkflowValidator initialization"""
        validator = WorkflowValidator(self.temp_path)
        self.assertEqual(validator.workflows_dir, self.temp_path)
        self.assertEqual(validator.errors, [])
        self.assertEqual(validator.warnings, [])
    
    def test_valid_yaml_syntax(self):
        """Test validation of valid YAML syntax"""
        workflow_content = """
name: Test Workflow
on: push
jobs:
  test:
    runs-on: ubuntu-latest
"""
        workflow_file = self.create_workflow_file("test.yml", workflow_content)
        
        validator = WorkflowValidator(self.temp_path)
        result = validator.validate_yaml_syntax(workflow_file)
        
        self.assertTrue(result)
        self.assertEqual(len(validator.errors), 0)
    
    def test_invalid_yaml_syntax(self):
        """Test validation of invalid YAML syntax"""
        workflow_content = """
name: Test Workflow
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps
      - name: Test
"""
        workflow_file = self.create_workflow_file("invalid.yml", workflow_content)
        
        validator = WorkflowValidator(self.temp_path)
        result = validator.validate_yaml_syntax(workflow_file)
        
        self.assertFalse(result)
        self.assertGreater(len(validator.errors), 0)
    
    def test_valid_workflow_structure(self):
        """Test validation of valid workflow structure"""
        workflow_content = """
name: Valid Workflow
on:
  workflow_dispatch:
    inputs:
      package_name:
        description: Package name
        required: true
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
"""
        workflow_file = self.create_workflow_file("valid.yml", workflow_content)
        
        validator = WorkflowValidator(self.temp_path)
        result = validator.validate_workflow_structure(workflow_file)
        
        self.assertTrue(result)
        self.assertEqual(len(validator.errors), 0)
    
    def test_missing_name(self):
        """Test workflow missing name"""
        workflow_content = """
on: push
jobs:
  build:
    runs-on: ubuntu-latest
"""
        workflow_file = self.create_workflow_file("no_name.yml", workflow_content)
        
        validator = WorkflowValidator(self.temp_path)
        result = validator.validate_workflow_structure(workflow_file)
        
        self.assertFalse(result)
        self.assertTrue(any('name' in str(e) for e in validator.errors))
    
    def test_missing_jobs(self):
        """Test workflow missing jobs"""
        workflow_content = """
name: No Jobs
on: push
"""
        workflow_file = self.create_workflow_file("no_jobs.yml", workflow_content)
        
        validator = WorkflowValidator(self.temp_path)
        result = validator.validate_workflow_structure(workflow_file)
        
        self.assertFalse(result)
    
    def test_missing_runs_on(self):
        """Test job missing runs-on or uses"""
        workflow_content = """
name: Missing runs-on
on: push
jobs:
  build:
    steps:
      - run: echo test
"""
        workflow_file = self.create_workflow_file("no_runs_on.yml", workflow_content)
        
        validator = WorkflowValidator(self.temp_path)
        result = validator.validate_workflow_structure(workflow_file)
        
        self.assertFalse(result)
        self.assertTrue(any('runs-on' in str(e) for e in validator.errors))
    
    def test_workflow_dispatch_inputs(self):
        """Test workflow_dispatch inputs validation"""
        workflow_content = """
name: Test Inputs
on:
  workflow_dispatch:
    inputs:
      test_input:
        description: Test input
        required: true
jobs:
  build:
    runs-on: ubuntu-latest
"""
        workflow_file = self.create_workflow_file("with_inputs.yml", workflow_content)
        
        validator = WorkflowValidator(self.temp_path)
        result = validator.validate_inputs(workflow_file)
        
        self.assertTrue(result)
        self.assertEqual(len(validator.errors), 0)
    
    def test_input_missing_description(self):
        """Test input missing description"""
        workflow_content = """
name: No Input Description
on:
  workflow_dispatch:
    inputs:
      bad_input:
        required: true
jobs:
  build:
    runs-on: ubuntu-latest
"""
        workflow_file = self.create_workflow_file("bad_input.yml", workflow_content)
        
        validator = WorkflowValidator(self.temp_path)
        result = validator.validate_inputs(workflow_file)
        
        self.assertEqual(len(validator.warnings), 1)
        self.assertTrue(any('bad_input' in str(w) for w in validator.warnings))
    
    def test_validate_all_with_multiple_files(self):
        """Test validation of multiple workflow files"""
        workflows = [
            ("valid1.yml", """
name: Valid 1
on: push
jobs:
  build:
    runs-on: ubuntu-latest
"""),
            ("valid2.yml", """
name: Valid 2
on: push
jobs:
  test:
    runs-on: ubuntu-latest
"""),
        ]
        
        for name, content in workflows:
            self.create_workflow_file(name, content)
        
        validator = WorkflowValidator(self.temp_path)
        result = validator.validate_all()
        
        self.assertTrue(result)
        self.assertEqual(len(validator.errors), 0)
    
    def test_validate_all_with_mixed_valid_invalid(self):
        """Test validation with mixed valid and invalid files"""
        workflows = [
            ("valid.yml", """
name: Valid
on: push
jobs:
  build:
    runs-on: ubuntu-latest
"""),
            ("invalid.yml", """
name: Invalid
on: push
"""),
        ]
        
        for name, content in workflows:
            self.create_workflow_file(name, content)
        
        validator = WorkflowValidator(self.temp_path)
        result = validator.validate_all()
        
        self.assertFalse(result)
        self.assertGreater(len(validator.errors), 0)


class TestWorkflowEnvironment(unittest.TestCase):
    """Test cases for workflow environment validation"""
    
    def test_workflow_env_vars(self):
        """Test that workflows define required environment variables"""
        repo_root = Path(__file__).parent.parent
        workflows_dir = repo_root / ".github" / "workflows"
        
        required_env_vars = {
            'ANDROID_API',
            'TARGET',
        }
        
        workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
        self.assertGreater(len(workflow_files), 0, "No workflow files found")
        
        for workflow_file in workflow_files:
            with open(workflow_file, 'r') as f:
                content = yaml.safe_load(f)
            
            # Check if env vars are defined at top level OR in job level
            env_vars = content.get('env', {})
            jobs = content.get('jobs', {})
            
            # If no top-level env, check if jobs have env vars
            for job_name, job_config in jobs.items():
                if isinstance(job_config, dict):
                    job_env = job_config.get('env', {})
                    env_vars.update(job_env)
            
            # Skip test workflows that don't need Android vars
            if workflow_file.name == 'tests.yml':
                continue
            
            for var in required_env_vars:
                self.assertIn(var, env_vars, 
                    f"{workflow_file.name} missing {var}")


def run_tests():
    """Run all tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestWorkflowValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkflowEnvironment))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
