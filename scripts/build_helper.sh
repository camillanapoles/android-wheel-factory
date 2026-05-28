#!/bin/bash
# Helper script for building Python wheels for Android
# This script encapsulates the build logic for better testability

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
ANDROID_API=${ANDROID_API:-24}
TARGET=${TARGET:-aarch64-linux-android}
WORKSPACE=${WORKSPACE:-.}

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

log_success() {
    echo -e "${GREEN}✓${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1" >&2
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Validate required tools
validate_tools() {
    local required_tools=("rustup" "pip" "tar" "mkdir")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "Required tool not found: $tool"
            return 1
        fi
    done
    log_success "All required tools are available"
    return 0
}

# Setup Rust environment
setup_rust_env() {
    log_info "Setting up Rust environment for target: $TARGET"
    
    if ! rustup target add "$TARGET" 2>&1; then
        log_warn "Rust target $TARGET may already be installed"
    fi
    
    log_success "Rust environment configured"
}

# Install Maturin
install_maturin() {
    log_info "Installing Maturin build tool..."
    pip install --upgrade pip maturin
    log_success "Maturin installed"
}

# Validate Android NDK
validate_ndk() {
    if [ -z "$ANDROID_NDK_HOME" ]; then
        log_error "ANDROID_NDK_HOME not set"
        return 1
    fi
    
    local ndk_clang="$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin/aarch64-linux-android${ANDROID_API}-clang"
    if [ ! -f "$ndk_clang" ]; then
        log_error "NDK Clang compiler not found at: $ndk_clang"
        return 1
    fi
    
    log_success "Android NDK validated"
    return 0
}

# Setup environment variables
setup_environment() {
    log_info "Configuring environment variables..."
    
    local ndk_toolchain="$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin"
    
    export CARGO_TARGET_AARCH64_LINUX_ANDROID_LINKER="${ndk_toolchain}/aarch64-linux-android${ANDROID_API}-clang"
    export CC_aarch64_linux_android="${ndk_toolchain}/aarch64-linux-android${ANDROID_API}-clang"
    export CXX_aarch64_linux_android="${ndk_toolchain}/aarch64-linux-android${ANDROID_API}-clang++"
    export PYO3_NO_PYTHON_LINKING=1
    
    log_success "Environment variables configured"
}

# Create fake Python library
create_fake_library() {
    local python_version=$1
    local fake_libs_dir="$WORKSPACE/fake_libs"
    
    if [ -z "$python_version" ]; then
        log_error "Python version required for creating fake library"
        return 1
    fi
    
    log_info "Creating fake libpython library..."
    mkdir -p "$fake_libs_dir"
    touch "$fake_libs_dir/libpython${python_version}.so"
    
    if [ ! -f "$fake_libs_dir/libpython${python_version}.so" ]; then
        log_error "Failed to create fake library at $fake_libs_dir/libpython${python_version}.so"
        return 1
    fi
    
    export RUSTFLAGS="-L $fake_libs_dir -C link-arg=-Wl,--unresolved-symbols=ignore-all -C link-arg=-Wl,--allow-shlib-undefined"
    log_success "Fake library created and RUSTFLAGS configured"
}

# Download package source
download_package() {
    local package_name=$1
    local package_version=$2
    local build_dir=$3
    
    if [ -z "$package_name" ]; then
        log_error "Package name is required"
        return 1
    fi
    
    if [ -z "$build_dir" ]; then
        build_dir="build_area"
    fi
    
    mkdir -p "$build_dir"
    cd "$build_dir"
    
    if [ -z "$package_version" ]; then
        log_info "Downloading latest version of $package_name..."
        pip download --no-binary :all: --no-deps "$package_name"
    else
        log_info "Downloading $package_name version $package_version..."
        pip download --no-binary :all: --no-deps "$package_name==$package_version"
    fi
    
    log_success "Package downloaded"
}

# Extract package source
extract_package() {
    local build_dir=${1:-.}
    
    log_info "Extracting package source..."
    
    if [ ! -f "$build_dir"/*.tar.gz ]; then
        log_error "No tar.gz file found in $build_dir"
        return 1
    fi
    
    tar -xzf "$build_dir"/*.tar.gz --one-top-level=src_code --strip-components=1 2>&1 || {
        log_warn "tar extraction with --one-top-level failed, trying alternative method..."
        tar -xzf "$build_dir"/*.tar.gz
    }
    
    cd src_code || cd "$(find . -maxdepth 1 -type d | tail -n 1)"
    
    log_success "Package extracted"
}

# Build wheel
build_wheel() {
    local python_version=$1
    local output_dir=${2:-../../dist}
    
    if [ -z "$python_version" ]; then
        log_error "Python version is required"
        return 1
    fi
    
    log_info "Building wheel for Python $python_version..."
    log_info "Target: $TARGET"
    log_info "Output directory: $output_dir"
    
    mkdir -p "$output_dir"
    
    maturin build \
        --release \
        --target "$TARGET" \
        --out "$output_dir" \
        --interpreter "python${python_version}" \
        --skip-auditwheel \
        --strip
    
    if [ $? -ne 0 ]; then
        log_error "Build failed"
        return 1
    fi
    
    log_success "Wheel built successfully"
}

# Verify wheel artifacts
verify_artifacts() {
    local output_dir=${1:-dist}
    
    log_info "Verifying wheel artifacts..."
    
    if [ ! -d "$output_dir" ]; then
        log_error "Output directory not found: $output_dir"
        return 1
    fi
    
    local wheel_count=$(find "$output_dir" -name "*.whl" -type f | wc -l)
    
    if [ "$wheel_count" -eq 0 ]; then
        log_error "No wheel files found in $output_dir"
        return 1
    fi
    
    log_success "Found $wheel_count wheel file(s)"
    find "$output_dir" -name "*.whl" -type f -exec ls -lh {} \;
    return 0
}

# Main function
main() {
    local command=$1
    shift || true
    
    case "$command" in
        validate)
            validate_tools
            ;;
        setup-rust)
            setup_rust_env
            ;;
        install-maturin)
            install_maturin
            ;;
        validate-ndk)
            validate_ndk
            ;;
        setup-env)
            setup_environment
            ;;
        create-fake-lib)
            create_fake_library "$@"
            ;;
        download)
            download_package "$@"
            ;;
        extract)
            extract_package "$@"
            ;;
        build)
            build_wheel "$@"
            ;;
        verify)
            verify_artifacts "$@"
            ;;
        *)
            echo "Usage: $0 {validate|setup-rust|install-maturin|validate-ndk|setup-env|create-fake-lib|download|extract|build|verify}"
            return 1
            ;;
    esac
}

# Only run main if script is executed directly (not sourced)
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
