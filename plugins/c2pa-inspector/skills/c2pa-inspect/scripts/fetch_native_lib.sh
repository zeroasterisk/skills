#!/usr/bin/env bash
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# fetch_native_lib.sh: Fetches precompiled libcredentio_c binary from GitHub Releases
# into the plugin directory for native C-ABI cryptographic validation without Bazel.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${SCRIPT_DIR}/../lib"

VERSION="${1:-0.1.8}"
VERSION="${VERSION#v}"

REPO="ghchinoy/credentio-contributions"
BASE_URL="https://github.com/${REPO}/releases/download/v${VERSION}"

OS="$(uname -s | tr '[:upper:]' '[:lower:]')"
ARCH="$(uname -m)"

case "${ARCH}" in
  x86_64|amd64)
    ARCH_NAME="amd64"
    ;;
  arm64|aarch64)
    ARCH_NAME="arm64"
    ;;
  *)
    echo "ERROR: Unsupported architecture: ${ARCH}" >&2
    exit 1
    ;;
esac

case "${OS}" in
  darwin)
    EXT="dylib"
    PLATFORM="darwin-${ARCH_NAME}"
    ;;
  linux)
    EXT="so"
    PLATFORM="linux-${ARCH_NAME}"
    ;;
  *)
    echo "ERROR: Unsupported OS: ${OS}" >&2
    exit 1
    ;;
esac

TARGET_LIB="libcredentio_c.${EXT}"
DOWNLOAD_URL="${BASE_URL}/libcredentio_c-${PLATFORM}.${EXT}"

echo "=== Fetching prebuilt ${TARGET_LIB} for ${PLATFORM} (v${VERSION}) ==="
mkdir -p "${TARGET_DIR}"

TMP_FILE="$(mktemp /tmp/credentio-plugin-lib.XXXXXX)"
trap 'rm -f "${TMP_FILE}"' EXIT

if curl -fL --progress-bar -o "${TMP_FILE}" "${DOWNLOAD_URL}"; then
  echo "==> Download completed successfully."
else
  FALLBACK_URL="${BASE_URL}/${TARGET_LIB}"
  echo "==> Trying release asset fallback: ${FALLBACK_URL}"
  if ! curl -fL --progress-bar -o "${TMP_FILE}" "${FALLBACK_URL}"; then
    echo "ERROR: Failed to download prebuilt binary from release v${VERSION}." >&2
    exit 1
  fi
fi

cp -f "${TMP_FILE}" "${TARGET_DIR}/${TARGET_LIB}"
chmod 755 "${TARGET_DIR}/${TARGET_LIB}"

echo "SUCCESS: Installed ${TARGET_LIB} into ${TARGET_DIR}/${TARGET_LIB}"
