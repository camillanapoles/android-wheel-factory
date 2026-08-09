#!/usr/bin/env python3
"""
Workflow YAML validation tests
Tests for GitHub Actions workflow YAML syntax and structure
"""

import os
import sys
import yaml
from pathlib import Path

class WorkflowValidator:
    """Validates GitHub Actions workflows"""
    
    def __init__(self, workflows_dir):
        self.workflows_dir = Path(workflows_dir)
        self.errors = []
        self.warnings = []
    
    def validate_yaml_syntax(self, file_path):
        """Validate YAML syntax"""
        try:
            with open(file_path, 'r') as f:
                yaml.safe_load(f)
            return True
        except yaml.YAMLError as e:
            self.errors.append(f"YAML syntax error in {file_path.name}: {e}")
            return False
    
    def validate_workflow_structure(self, file_path):
        """Validate workflow structure"""
        try:
            with open(file_path, 'r') as f:
                workflow = yaml.safe_load(f)
            
            if not isinstance(workflow, dict):
                self.errors.append(f"{file_path.name}: Root must be a dictionary")
                return False
            
            # In YAML, 'on:' is parsed as boolean True due to YAML spec
            # So we check for both 'on' and True as valid trigger keys
            has_trigger = 'on' in workflow or True in workflow
            
            required_keys = {'name', 'jobs'}
            missing_keys = required_keys - set(workflow.keys())
            if missing_keys:
                self.errors.append(f"{file_path.name}: Missing required keys: {missing_keys}")
                return False
            
            if not has_trigger:
                self.errors.append(f"{file_path.name}: Missing 'on' trigger configuration")
                return False
            
            # Validate jobs structure
            jobs = workflow.get('jobs', {})
            if not isinstance(jobs, dict) or not jobs:
                self.errors.append(f"{file_path.name}: jobs must be a non-empty dictionary")
                return False
            
            for job_name, job_config in jobs.items():
                if not isinstance(job_config, dict):
                    self.errors.append(f"{file_path.name}: job '{job_name}' must be a dictionary")
                    return False
                
                if 'runs-on' not in job_config and 'uses' not in job_config:
                    self.errors.append(f"{file_path.name}: job '{job_name}' missing 'runs-on' or 'uses'")
                    return False
            
            return True
        
        except Exception as e:
            self.errors.append(f"Error validating {file_path.name}: {e}")
            return False
    
    def validate_inputs(self, file_path):
        """Validate workflow inputs"""
        try:
            with open(file_path, 'r') as f:
                workflow = yaml.safe_load(f)
            
            # In YAML, 'on:' is parsed as boolean True
            on_config = workflow.get('on', workflow.get(True, {}))
            
            # Handle case where 'on' is a string (e.g., 'on: push') instead of a dict
            if isinstance(on_config, str):
                # No workflow_dispatch inputs in this case
                return True
            
            if not isinstance(on_config, dict):
                return True
            
            workflow_dispatch = on_config.get('workflow_dispatch', {})
            if workflow_dispatch:
                inputs = workflow_dispatch.get('inputs', {})
                for input_name, input_config in inputs.items():
                    if not isinstance(input_config, dict):
                        self.errors.append(f"{file_path.name}: input '{input_name}' must be a dictionary")
                        return False
                    
                    # Validate required fields
                    if 'description' not in input_config:
                        self.warnings.append(f"{file_path.name}: input '{input_name}' missing 'description'")
            
            return True
        
        except Exception as e:
            self.errors.append(f"Error validating inputs in {file_path.name}: {e}")
            return False
    
    def validate_all(self):
        """Validate all workflow files"""
        if not self.workflows_dir.exists():
            self.errors.append(f"Workflows directory not found: {self.workflows_dir}")
            return False
        
        yaml_files = list(self.workflows_dir.glob("*.yml")) + list(self.workflows_dir.glob("*.yaml"))
        
        if not yaml_files:
            self.errors.append(f"No workflow files found in {self.workflows_dir}")
            return False
        
        all_valid = True
        for file_path in yaml_files:
            print(f"Validating {file_path.name}...")
            
            valid = self.validate_yaml_syntax(file_path)
            valid = self.validate_workflow_structure(file_path) and valid
            valid = self.validate_inputs(file_path) and valid
            
            if not valid:
                all_valid = False
        
        return all_valid
    
    def report(self):
        """Print validation report"""
        print("\n" + "="*70)
        print("WORKFLOW VALIDATION REPORT")
        print("="*70)
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
        
        if not self.errors and not self.warnings:
            print("\n✅ All workflows are valid!")
        
        print("="*70 + "\n")
        
        return len(self.errors) == 0


def main():
    """Main entry point"""
    repo_root = Path(__file__).parent.parent
    workflows_dir = repo_root / ".github" / "workflows"
    
    validator = WorkflowValidator(workflows_dir)
    all_valid = validator.validate_all()
    all_valid = validator.report() and all_valid
    
    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
