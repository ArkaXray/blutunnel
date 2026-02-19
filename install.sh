#!/usr/bin/env bash
set -euo pipefail

MODE=""
IRAN_IP=""
BRIDGE_PORT=""
SYNC_PORT=""
AUTO_SYNC="y"
MANUAL_PORTS=""
INSTALL_DIR="/opt/blutunnel"
ENV_DIR="/etc/blutunnel"
SERVICE_FILE="/etc/systemd/system/blutunnel.service"
TIMER_FILE="/etc/systemd/system/blutunnel.timer"
REPO_URL="https://github.com/ArkaXray/blutunnel.git"

usage() {
  cat <<'EOF'
Usage:
  sudo bash install.sh --mode iran --bridge-port 4430 --sync-port 4431 [--auto-sync y|n] [--manual-ports 80,443]
  sudo bash install.sh --mode europe --iran-ip 1.2.3.4 --bridge-port 4430 --sync-port 4431

Options:
  --mode           iran | europe
  --iran-ip        required for europe mode
  --bridge-port    required
  --sync-port      required
  --auto-sync      y|n (iran mode only, default: y)
  --manual-ports   comma list (iran + auto-sync=n)
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode) MODE="${2:-}"; shift 2 ;;
    --iran-ip) IRAN_IP="${2:-}"; shift 2 ;;
    --bridge-port) BRIDGE_PORT="${2:-}"; shift 2 ;;
    --sync-port) SYNC_PORT="${2:-}"; shift 2 ;;
    --auto-sync) AUTO_SYNC="${2:-}"; shift 2 ;;
    --manual-ports) MANUAL_PORTS="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1"; usage; exit 1 ;;
  esac
done

if [[ $EUID -ne 0 ]]; then
  echo "Please run as root: sudo bash install.sh ..."
  exit 1
fi

if [[ -z "$MODE" || -z "$BRIDGE_PORT" || -z "$SYNC_PORT" ]]; then
  usage
  exit 1
fi

if [[ "$MODE" == "europe" && -z "$IRAN_IP" ]]; then
  echo "--iran-ip is required for europe mode"
  exit 1
fi

if [[ "$MODE" != "iran" && "$MODE" != "europe" ]]; then
  echo "--mode must be iran or europe"
  exit 1
fi

if [[ ! -f "blutunnel.py" ]]; then
  rm -rf "$INSTALL_DIR"
  git clone "$REPO_URL" "$INSTALL_DIR"
else
  mkdir -p "$INSTALL_DIR"
  cp -f blutunnel.py "$INSTALL_DIR/blutunnel.py"
  mkdir -p "$INSTALL_DIR/systemd"
  cp -f systemd/blutunnel.service "$INSTALL_DIR/systemd/blutunnel.service"
  cp -f systemd/blutunnel.timer "$INSTALL_DIR/systemd/blutunnel.timer"
fi

mkdir -p "$ENV_DIR"
cat > "$ENV_DIR/blutunnel.env" <<EOF
MODE=$MODE
IRAN_IP=$IRAN_IP
BRIDGE_PORT=$BRIDGE_PORT
SYNC_PORT=$SYNC_PORT
AUTO_SYNC=$AUTO_SYNC
MANUAL_PORTS=$MANUAL_PORTS
EOF

cp -f "$INSTALL_DIR/systemd/blutunnel.service" "$SERVICE_FILE"
cp -f "$INSTALL_DIR/systemd/blutunnel.timer" "$TIMER_FILE"

systemctl daemon-reload
systemctl enable --now blutunnel.service
systemctl enable --now blutunnel.timer

echo "BluTunnel installed and running."
echo "Config file: $ENV_DIR/blutunnel.env"
echo "Service status: systemctl status blutunnel.service"
