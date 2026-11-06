#!/bin/sh
# Install the tilecov binary — one line:
#
#   curl -fsSL https://yijunyu.github.io/rsi/install.sh | sh
#
# No arguments, no prompts. Installs to ${TILECOV_PREFIX:-$HOME/.local/bin},
# creates it if missing, and prints what to add to PATH if it is not there yet.
#
# Env overrides (both optional):
#   TILECOV_PREFIX   install directory      (default: $HOME/.local/bin)
#   TILECOV_BASE     asset base URL         (default: https://yijunyu.github.io/rsi)
set -eu

BASE="${TILECOV_BASE:-https://yijunyu.github.io/rsi}"
DEST="${TILECOV_PREFIX:-$HOME/.local/bin}"

os=$(uname -s | tr 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' 'abcdefghijklmnopqrstuvwxyz')
arch=$(uname -m)
case "$arch" in
  arm64|aarch64) arch=arm64 ;;
  x86_64|amd64)  arch=x86_64 ;;
  *) echo "install.sh: unsupported architecture: $arch" >&2; exit 1 ;;
esac
case "$os" in
  darwin|linux) : ;;
  *) echo "install.sh: unsupported OS: $os" >&2; exit 1 ;;
esac

asset="tilecov-$os-$arch"
url="$BASE/bin/$asset"

mkdir -p "$DEST"
echo "install.sh: $asset -> $DEST/tilecov"
if ! curl -fsSL "$url" -o "$DEST/tilecov.tmp"; then
  echo "install.sh: no published binary at $url" >&2
  echo "install.sh: published assets are listed at $BASE/README.md" >&2
  rm -f "$DEST/tilecov.tmp"
  exit 1
fi
chmod +x "$DEST/tilecov.tmp"
mv "$DEST/tilecov.tmp" "$DEST/tilecov"

# Verify what landed rather than reporting success for a download.
if ! "$DEST/tilecov" version; then
  echo "install.sh: the downloaded binary does not run on this machine" >&2
  exit 1
fi

case ":$PATH:" in
  *":$DEST:"*) : ;;
  *) echo "install.sh: add this to your shell profile:"
     echo "             export PATH=\"$DEST:\$PATH\"" ;;
esac
