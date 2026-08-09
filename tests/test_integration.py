#!/usr/bin/env python3
"""
Integration tests for Android wheel building
Tests for the build process workflow
"""

import os
import sys
import subprocess
from pathlib import Path

class IntegrationTester:
    """Integration tests for Android wheel building"""
    
    def __init__(self):
        self.repo_root = Path(__file__).parent.parent
        self.tests_passed = 0
        self.tests_failed = 0
        self.tests_skipped = 0
    
    def run_test(self, test_name, test_func, skip_if_missing=None):
        """Run a single test"""
        print(f"\n{'─'*70}")
        print(f"TEST: {test_name}")
        print(f"{'─'*70}")
        
        if skip_if_missing:
            for tool in skip_if_missing:
                result = subprocess.run(
                    ["which", tool],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    print(f"⊘ SKIP: {tool} not found in PATH")
                    self.tests_skipped += 1
                    return
        
        try:
            test_func()
            print("✓ PASS")
            self.tests_passed += 1
        except AssertionError as e:
            print(f"✗ FAIL: {e}")
            self.tests_failed += 1
        except Exception as e:
            print(f"✗ ERROR: {e}")
            self.tests_failed += 1
    
    def test_build_helper_exists(self):
        """Test that build_helper.sh exists"""
        helper_script = self.repo_root / "scripts" / "build_helper.sh"
        assert helper_script.exists(), f"build_helper.sh not found at {helper_script}"
        assert helper_script.is_file(), f"build_helper.sh is not a file"
        print(f"  Found: {helper_script}")
    
    def test_build_helper_executable(self):
        """Test that build_helper.sh is executable"""
        helper_script = self.repo_root / "scripts" / "build_helper.sh"
        assert os.access(helper_script, os.X_OK), "build_helper.sh is not executable"
        print(f"  File is executable")
    
    def test_build_helper_bash_syntax(self):
        """Test that build_helper.sh has valid bash syntax"""
        helper_script = self.repo_root / "scripts" / "build_helper.sh"
        result = subprocess.run(
            ["bash", "-n", str(helper_script)],
            capture_output=True,
            text=True
        )
        assert result.returncode == 0, f"Bash syntax error: {result.stderr}"
        print(f"  Bash syntax is valid")
    
    def test_build_helper_functions(self):
        """Test that build_helper.sh exports expected functions"""
        helper_script = self.repo_root / "scripts" / "build_helper.sh"
        
        # Check for expected function definitions
        with open(helper_script, 'r') as f:
            content = f.read()
        
        expected_functions = [
            'log_info',
            'log_success',
            'log_error',
            'log_warn',
            'validate_tools',
            'setup_rust_env',
            'install_maturin',
            'validate_ndk',
            'setup_environment',
            'create_fake_library',
            'download_package',
            'extract_package',
            'build_wheel',
            'verify_artifacts',
            'main'
        ]
        
        for func in expected_functions:
            assert f'{func}()' in content, f"Function {func} not found"
            print(f"  ✓ Found function: {func}")
    
    def test_workflow_files_exist(self):
        """Test that workflow files exist"""
        workflows_dir = self.repo_root / ".github" / "workflows"
        assert workflows_dir.exists(), f"Workflows directory not found at {workflows_dir}"
        
        workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
        assert len(workflow_files) > 0, "No workflow files found"
        
        print(f"  Found {len(workflow_files)} workflow files:")
        for f in workflow_files:
            print(f"    - {f.name}")
    
    def test_workflow_yaml_validity(self):
        """Test that workflow YAML is valid"""
        try:
            import yaml
        except ImportError:
            raise AssertionError("PyYAML not installed. Run: pip install pyyaml")
        
        workflows_dir = self.repo_root / ".github" / "workflows"
        workflow_files = list(workflows_dir.glob("*.yml")) + list(workflows_dir.glob("*.yaml"))
        
        for workflow_file in workflow_files:
            with open(workflow_file, 'r') as f:
                try:
                    yaml.safe_load(f)
                    print(f"  ✓ Valid: {workflow_file.name}")
                except yaml.YAMLError as e:
                    raise AssertionError(f"YAML error in {workflow_file.name}: {e}")
    
    def test_readme_exists(self):
        """Test that README.md exists"""
        readme = self.repo_root / "README.md"
        assert readme.exists(), "README.md not found"
        assert readme.is_file(), "README.md is not a file"
        
        with open(readme, 'r') as f:
            content = f.read()
            assert len(content) > 0, "README.md is empty"
        
        print(f"  README.md found ({len(content)} chars)")
    
    def test_readme_documentation(self):
        """Test that README contains important documentation"""
        readme = self.repo_root / "README.md"
        with open(readme, 'r') as f:
            content = f.read().lower()
        
        # Check for key sections
        required_sections = [
            'objetivo',
            'como funciona',
            'uso',
            'requisitos',
        ]
        
        for section in required_sections:
            assert section in content, f"README missing section: {section}"
            print(f"  ✓ Found section: {section}")
    
    def test_test_files_exist(self):
        """Test that test files exist"""
        tests_dir = self.repo_root / "tests"
        assert tests_dir.exists(), f"tests directory not found at {tests_dir}"
        
        test_files = list(tests_dir.glob("test_*.sh")) + list(tests_dir.glob("test_*.py"))
        assert len(test_files) > 0, "No test files found"
        
        print(f"  Found {len(test_files)} test files:")
        for f in test_files:
            print(f"    - {f.name}")
    
    def run_all_tests(self):
        """Run all integration tests"""
        print("\n" + "="*70)
        print("INTEGRATION TESTS")
        print("="*70)
        
        self.run_test(
            "build_helper.sh exists",
            self.test_build_helper_exists
        )
        
        self.run_test(
            "build_helper.sh is executable",
            self.test_build_helper_executable
        )
        
        self.run_test(
            "build_helper.sh has valid bash syntax",
            self.test_build_helper_bash_syntax,
            skip_if_missing=["bash"]
        )
        
        self.run_test(
            "build_helper.sh exports expected functions",
            self.test_build_helper_functions
        )
        
        self.run_test(
            "Workflow files exist",
            self.test_workflow_files_exist
        )
        
        self.run_test(
            "Workflow YAML is valid",
            self.test_workflow_yaml_validity
        )
        
        self.run_test(
            "README.md exists",
            self.test_readme_exists
        )
        
        self.run_test(
            "README has required documentation",
            self.test_readme_documentation
        )
        
        self.run_test(
            "Test files exist",
            self.test_test_files_exist
        )
        
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        total = self.tests_passed + self.tests_failed + self.tests_skipped
        
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Total:   {total}")
        print(f"Passed:  {self.tests_passed}")
        print(f"Failed:  {self.tests_failed}")
        print(f"Skipped: {self.tests_skipped}")
        print("="*70 + "\n")
        
        return self.tests_failed == 0


def main():
    """Main entry point"""
    tester = IntegrationTester()
    tester.run_all_tests()
    
    sys.exit(0 if tester.tests_failed == 0 else 1)


if __name__ == "__main__":
    main()
