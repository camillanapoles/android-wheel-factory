#!/bin/bash
# Master test runner script
# Runs all tests for the Android Wheel Factory project

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$SCRIPT_DIR"

# Test results
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Functions
log_section() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

run_test_suite() {
    local suite_name=$1
    local command=$2
    
    echo -e "${YELLOW}Running: $suite_name${NC}"
    echo "Command: $command"
    echo ""
    
    if eval "$command"; then
        echo -e "${GREEN}✓ $suite_name passed${NC}"
        ((PASSED_TESTS++))
    else
        echo -e "${RED}✗ $suite_name failed${NC}"
        ((FAILED_TESTS++))
    fi
    
    ((TOTAL_TESTS++))
    echo ""
}

# Main test execution
log_section "Android Wheel Factory - Test Suite"

# Check for required tools
echo "Checking required tools..."
required_tools=("bash" "python3")
for tool in "${required_tools[@]}"; do
    if ! command -v "$tool" &> /dev/null; then
        echo -e "${RED}✗ $tool not found${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ $tool available${NC}"
done
echo ""

# Test 1: Build Helper Unit Tests
log_section "Test 1: Build Helper Unit Tests"
if [ -f "tests/test_build_helper.sh" ]; then
    run_test_suite "Build Helper Tests" "bash tests/test_build_helper.sh"
else
    echo -e "${YELLOW}⊘ Skipping build helper tests (file not found)${NC}"
fi

# Test 2: Workflow Validation
log_section "Test 2: Workflow Validation Tests"
if command -v python3 &> /dev/null && [ -f "tests/test_workflows.py" ]; then
    # Check for PyYAML
    if python3 -c "import yaml" 2>/dev/null; then
        run_test_suite "Workflow Validation" "python3 tests/test_workflows.py"
    else
        echo -e "${YELLOW}⊘ PyYAML not installed, installing...${NC}"
        pip3 install pyyaml --quiet
        run_test_suite "Workflow Validation" "python3 tests/test_workflows.py"
    fi
else
    echo -e "${YELLOW}⊘ Skipping workflow validation (Python/YAML or test file not found)${NC}"
fi

# Test 3: Integration Tests
log_section "Test 3: Integration Tests"
if command -v python3 &> /dev/null && [ -f "tests/test_integration.py" ]; then
    if python3 -c "import yaml" 2>/dev/null; then
        run_test_suite "Integration Tests" "python3 tests/test_integration.py"
    else
        echo -e "${YELLOW}⊘ PyYAML not installed${NC}"
        run_test_suite "Integration Tests" "python3 tests/test_integration.py"
    fi
else
    echo -e "${YELLOW}⊘ Skipping integration tests (Python or test file not found)${NC}"
fi

# Test 4: Unit Tests
log_section "Test 4: Unit Tests"
if command -v python3 &> /dev/null && [ -f "tests/test_unit.py" ]; then
    if python3 -c "import yaml" 2>/dev/null; then
        run_test_suite "Unit Tests" "python3 tests/test_unit.py"
    else
        echo -e "${YELLOW}⊘ PyYAML not installed${NC}"
        run_test_suite "Unit Tests" "python3 tests/test_unit.py"
    fi
else
    echo -e "${YELLOW}⊘ Skipping unit tests (Python or test file not found)${NC}"
fi

# Summary
log_section "Test Summary"
echo "Total:  $TOTAL_TESTS"
echo "Passed: $PASSED_TESTS"
echo "Failed: $FAILED_TESTS"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi
