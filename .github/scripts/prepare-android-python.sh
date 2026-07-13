#!/usr/bin/env bash
# Prepara um sysroot Python Android para cross-compilação com maturin.
# Baixa o Python compilado para aarch64-linux-android do Termux.
set -euo pipefail

ARCH="${1:-aarch64}"
ANDROID_API="${2:-24}"
PYTHON_VERSION="${3:-3.12}"

SYSROOT_DIR="${RUNNER_TEMP:-/tmp}/android-python-sysroot"
mkdir -p "$SYSROOT_DIR"

# Mapear arch para triple
case "$ARCH" in
  aarch64) TRIPLE="aarch64-linux-android" ;;
  x86_64)  TRIPLE="x86_64-linux-android" ;;
  armv7l)  TRIPLE="armv7a-linux-androideabi" ;;
  i686)    TRIPLE="i686-linux-android" ;;
  *) echo "Arch não suportada: $ARCH"; exit 1 ;;
esac

# Baixar Python do Termux para a arquitetura alvo
# Usamos o repositório termux-packages (python pacote principal)
TERMUX_REPO="https://packages.termux.dev/apt/termux-main/pool/main/p/python/"
# Formato: python_3.12.0_aarch64.deb

echo "=== Baixando Python para $TRIPLE ==="

# Tentar baixar a versão específica do Python do Termux
PY_DEB="python_${PYTHON_VERSION}_${ARCH}.deb"
DEB_URL="${TERMUX_REPO}${PY_DEB}"

if curl -sL -o "${SYSROOT_DIR}/python.deb" "$DEB_URL"; then
    echo "✓ Python deb baixado de $DEB_URL"
    cd "$SYSROOT_DIR"
    ar x python.deb
    tar -xf data.tar.xz || tar -xf data.tar.gz || true
    # Localizar libpython
    find "$SYSROOT_DIR" -name "libpython*.so*" -type f 2>/dev/null | head -5
else
    echo "⚠️ Não foi possível baixar Python do Termux para $ARCH"
    echo "   Tentando fallback: criar libpython stub..."
    # Criar um stub mínimo de libpython para o linker
    mkdir -p "$SYSROOT_DIR/lib"
    # Compilar um stub minimalista
    echo "int Py_IsInitialized() { return 0; }" > /tmp/pystub.c
    NDK_BIN="${ANDROID_NDK_HOME}/toolchains/llvm/prebuilt/linux-x86_64/bin"
    case "$ARCH" in
      aarch64) CC="${NDK_BIN}/aarch64-linux-android${ANDROID_API}-clang" ;;
      x86_64)  CC="${NDK_BIN}/x86_64-linux-android${ANDROID_API}-clang" ;;
      armv7l)  CC="${NDK_BIN}/armv7a-linux-androideabi${ANDROID_API}-clang" ;;
      i686)    CC="${NDK_BIN}/i686-linux-android${ANDROID_API}-clang" ;;
    esac
    # shellcheck disable=SC2086
    "$CC" -shared -o "$SYSROOT_DIR/lib/libpython${PYTHON_VERSION}.so" /tmp/pystub.c
    rm /tmp/pystub.c
    echo "✓ Stub libpython${PYTHON_VERSION}.so criado em $SYSROOT_DIR/lib/"
fi

# Exportar o diretório para uso em steps seguintes
echo "PYO3_CROSS_LIB_DIR=$SYSROOT_DIR/lib" >> "$GITHUB_ENV"
echo "PYO3_CROSS_PYTHON_VERSION=${PYTHON_VERSION}" >> "$GITHUB_ENV"
echo "✓ PYO3_CROSS_LIB_DIR=$SYSROOT_DIR/lib"

# Também configurar maturin para usar o Python de build corretamente
echo "MATURIN_BUILD_ARGS=--target $TRIPLE --skip-auditwheel --strip -i python${PYTHON_VERSION}" >> "$GITHUB_ENV"
