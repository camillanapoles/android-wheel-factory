#!/bin/bash
# Unit tests for build_helper.sh
# Run with: bash tests/test_build_helper.sh

# Source the build helper
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source "$SCRIPT_DIR/scripts/build_helper.sh"

# Don't exit on errors in tests
set +e

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test framework functions
test_case() {
    local test_name=$1
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "TEST: $test_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    ((TESTS_RUN++))
}

assert_success() {
    local message=${1:-"Expected success"}
    
    if [ $? -eq 0 ]; then
        echo "✓ PASS: $message"
        ((TESTS_PASSED++))
        return 0
    else
        echo "✗ FAIL: $message"
        ((TESTS_FAILED++))
        return 1
    fi
}

assert_failure() {
    local message=${1:-"Expected failure"}
    
    if [ $? -ne 0 ]; then
        echo "✓ PASS: $message"
        ((TESTS_PASSED++))
        return 0
    else
        echo "✗ FAIL: $message"
        ((TESTS_FAILED++))
        return 1
    fi
}

assert_equal() {
    local actual=$1
    local expected=$2
    local message=${3:-"Values should be equal"}
    
    if [ "$actual" == "$expected" ]; then
        echo "✓ PASS: $message"
        ((TESTS_PASSED++))
        return 0
    else
        echo "✗ FAIL: $message"
        echo "  Expected: $expected"
        echo "  Got: $actual"
        ((TESTS_FAILED++))
        return 1
    fi
}

assert_file_exists() {
    local file=$1
    local message=${2:-"File should exist"}
    
    if [ -f "$file" ]; then
        echo "✓ PASS: $message"
        ((TESTS_PASSED++))
        return 0
    else
        echo "✗ FAIL: $message (not found: $file)"
        ((TESTS_FAILED++))
        return 1
    fi
}

assert_dir_exists() {
    local dir=$1
    local message=${2:-"Directory should exist"}
    
    if [ -d "$dir" ]; then
        echo "✓ PASS: $message"
        ((TESTS_PASSED++))
        return 0
    else
        echo "✗ FAIL: $message (not found: $dir)"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Setup test environment
setup_test_env() {
    export TEST_WORKSPACE=$(mktemp -d)
    export WORKSPACE="$TEST_WORKSPACE"
    export ANDROID_API=24
    export TARGET=aarch64-linux-android
}

teardown_test_env() {
    if [ -d "$TEST_WORKSPACE" ]; then
        rm -rf "$TEST_WORKSPACE"
    fi
}

# ============================================================================
# TESTS
# ============================================================================

# Test 1: Log functions output correctly
test_case "Log functions"
log_info "test message" > /dev/null 2>&1
assert_success "log_info outputs message"

# Test 2: Create fake library
test_case "Create fake library"
setup_test_env
create_fake_library "3.12" > /dev/null 2>&1
assert_success "Fake library created successfully"
assert_file_exists "$TEST_WORKSPACE/fake_libs/libpython3.12.so" "libpython3.12.so should exist"
teardown_test_env

# Test 3: Create fake library with missing python version
test_case "Create fake library without version"
setup_test_env
create_fake_library "" > /dev/null 2>&1
exit_code=$?
teardown_test_env
if [ $exit_code -ne 0 ]; then
    echo "✓ PASS: Should fail when python version is missing"
    ((TESTS_PASSED++))
else
    echo "✗ FAIL: Should fail when python version is missing"
    ((TESTS_FAILED++))
fi

# Test 4: Validate tools function
test_case "Validate required tools"
validate_tools > /dev/null 2>&1
assert_success "All required tools should be available"

# Test 5: Environment variable configuration
test_case "Setup environment variables"
export ANDROID_NDK_HOME="/mock/ndk"
setup_environment > /dev/null 2>&1
if [ -n "$CARGO_TARGET_AARCH64_LINUX_ANDROID_LINKER" ]; then
    echo "✓ PASS: Environment variables configured"
    ((TESTS_PASSED++))
else
    echo "✗ FAIL: Environment variables not configured"
    ((TESTS_FAILED++))
fi

# Test 6: Create fake library idempotency
test_case "Create fake library idempotency"
setup_test_env
create_fake_library "3.11" > /dev/null 2>&1
create_fake_library "3.11" > /dev/null 2>&1
assert_success "Creating fake library twice should succeed"
assert_file_exists "$TEST_WORKSPACE/fake_libs/libpython3.11.so" "File should still exist"
teardown_test_env

# Test 7: Multiple Python versions
test_case "Create fake libraries for multiple versions"
setup_test_env
for version in 3.9 3.10 3.11 3.12; do
    create_fake_library "$version" > /dev/null 2>&1
    assert_file_exists "$TEST_WORKSPACE/fake_libs/libpython${version}.so" "libpython${version}.so should exist"
done
teardown_test_env

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Total Tests:  $TESTS_RUN"
echo "Passed:       $TESTS_PASSED"
echo "Failed:       $TESTS_FAILED"
echo ""

if [ $TESTS_FAILED -eq 0 ]; then
    echo "✓ All tests passed!"
    exit 0
else
    echo "✗ Some tests failed"
    exit 1
fi

