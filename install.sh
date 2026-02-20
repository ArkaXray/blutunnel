#!/usr/bin/env bash
set -euo pipefail

REPO_URL="${BLUTUNNEL_REPO:-https://github.com/ArkaXray/blutunnel.git}"
BRANCH="${BLUTUNNEL_BRANCH:-main}"
INSTALL_DIR="${BLUTUNNEL_DIR:-$HOME/blutunnel}"

if [ "$(id -u)" -eq 0 ]; then
  SUDO=""
else
  SUDO="sudo"
fi

echo "[BluTunnel] Installing dependencies..."
$SUDO apt-get update -y >/dev/null
$SUDO apt-get install -y git python3 python3-pip iproute2 >/dev/null

echo "[BluTunnel] Installing Python dependency: aiohttp..."
export PIP_ROOT_USER_ACTION=ignore
python3 -m pip install --upgrade pip >/dev/null
python3 -m pip install aiohttp >/dev/null

if [ -d "$INSTALL_DIR/.git" ]; then
  echo "[BluTunnel] Existing install found at $INSTALL_DIR, updating..."
  if git -C "$INSTALL_DIR" fetch origin "$BRANCH" >/dev/null 2>&1 \
    && git -C "$INSTALL_DIR" checkout "$BRANCH" >/dev/null 2>&1 \
    && git -C "$INSTALL_DIR" pull --ff-only origin "$BRANCH" >/dev/null 2>&1; then
    :
  else
    echo "[BluTunnel] Update conflict detected. Reinstalling clean copy..."
    rm -rf "$INSTALL_DIR"
    git clone --branch "$BRANCH" "$REPO_URL" "$INSTALL_DIR" >/dev/null
  fi
else
  echo "[BluTunnel] Cloning repository into $INSTALL_DIR..."
  rm -rf "$INSTALL_DIR"
  git clone --branch "$BRANCH" "$REPO_URL" "$INSTALL_DIR" >/dev/null
fi

echo "[BluTunnel] Starting BluTunnel..."
cd "$INSTALL_DIR"

if [ -t 0 ] && [ -t 1 ]; then
  exec python3 blutunnel.py
elif [ -e /dev/tty ]; then
  echo "[BluTunnel] Re-attaching to /dev/tty for interactive menu..."
  exec python3 blutunnel.py </dev/tty >/dev/tty 2>&1
else
  echo "[BluTunnel] No interactive TTY found."
  echo "[BluTunnel] Run manually: cd \"$INSTALL_DIR\" && python3 blutunnel.py"
  exit 1
fi
