#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="/opt/blutunnel"
ENV_DIR="/etc/blutunnel"
SERVICE_FILE="/etc/systemd/system/blutunnel.service"
TIMER_FILE="/etc/systemd/system/blutunnel.timer"
BIN_FILE="/usr/local/bin/blutunnel"
PANEL_BIN_FILE="/usr/local/bin/blutunnel-panel"
REPO_URL="https://github.com/ArkaXray/blutunnel.git"

usage() {
  cat <<'EOF'
Usage:
  curl -fsSL https://raw.githubusercontent.com/ArkaXray/blutunnel/main/install.sh | sudo bash
  sudo bash install.sh

This installer sets up BluTunnel interactive mode.
After install, run:
  sudo blutunnel
  sudo blutunnel-panel
EOF
}

need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1"
    exit 1
  fi
}

ask_port() {
  local prompt="$1"
  local default_value="$2"
  local value

  while true; do
    read -r -p "$prompt [$default_value]: " value
    value="${value:-$default_value}"
    if [[ "$value" =~ ^[0-9]+$ ]] && (( value >= 1 && value <= 65535 )); then
      echo "$value"
      return
    fi
    echo "Invalid port. Enter a number between 1 and 65535."
  done
}

prompt_env_config() {
  local mode bridge_port sync_port auto_sync manual_ports iran_ip

  echo
  echo "Configure systemd auto-start mode"
  echo "1) iran"
  echo "2) europe"
  read -r -p "Choice [1/2]: " mode
  if [[ "$mode" == "2" ]]; then
    mode="europe"
  else
    mode="iran"
  fi

  bridge_port="$(ask_port "Tunnel Bridge Port" "4430")"
  sync_port="$(ask_port "Port Sync Port" "4431")"

  iran_ip=""
  auto_sync="y"
  manual_ports=""

  if [[ "$mode" == "europe" ]]; then
    read -r -p "Iran IP: " iran_ip
  else
    read -r -p "Auto-Sync Xray ports? (y/n) [y]: " auto_sync
    auto_sync="${auto_sync:-y}"
    auto_sync="${auto_sync,,}"
    if [[ "$auto_sync" != "y" && "$auto_sync" != "n" ]]; then
      auto_sync="y"
    fi
    if [[ "$auto_sync" == "n" ]]; then
      read -r -p "Manual ports (comma-separated, e.g. 80,443,2083): " manual_ports
    fi
  fi

  mkdir -p "$ENV_DIR"
  cat > "$ENV_DIR/blutunnel.env" <<EOF
MODE=$mode
IRAN_IP=$iran_ip
BRIDGE_PORT=$bridge_port
SYNC_PORT=$sync_port
AUTO_SYNC=$auto_sync
MANUAL_PORTS=$manual_ports
EOF

  echo "Wrote config: $ENV_DIR/blutunnel.env"
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ $# -gt 0 ]]; then
  echo "This installer is interactive-only. Extra arguments are ignored."
fi

if [[ "$EUID" -ne 0 ]]; then
  echo "Please run as root: sudo bash install.sh"
  exit 1
fi

need_cmd python3
need_cmd bash

if [[ -f "blutunnel.py" ]]; then
  mkdir -p "$INSTALL_DIR"
  cp -f blutunnel.py "$INSTALL_DIR/blutunnel.py"
  if [[ -f "blutunnel_panel.py" ]]; then
    cp -f blutunnel_panel.py "$INSTALL_DIR/blutunnel_panel.py"
  fi
  mkdir -p "$INSTALL_DIR/systemd"
  cp -f systemd/blutunnel.service "$INSTALL_DIR/systemd/blutunnel.service"
  cp -f systemd/blutunnel.timer "$INSTALL_DIR/systemd/blutunnel.timer"
  if [[ -f "blutunnel.env.example" ]]; then
    cp -f blutunnel.env.example "$INSTALL_DIR/blutunnel.env.example"
  fi
else
  need_cmd git
  rm -rf "$INSTALL_DIR"
  git clone "$REPO_URL" "$INSTALL_DIR"
fi

cat > "$BIN_FILE" <<'EOF'
#!/usr/bin/env bash
exec /usr/bin/python3 /opt/blutunnel/blutunnel.py "$@"
EOF
chmod +x "$BIN_FILE"

if [[ -f "$INSTALL_DIR/blutunnel_panel.py" ]]; then
  cat > "$PANEL_BIN_FILE" <<'EOF'
#!/usr/bin/env bash
exec /usr/bin/python3 /opt/blutunnel/blutunnel_panel.py "$@"
EOF
  chmod +x "$PANEL_BIN_FILE"
fi

mkdir -p "$ENV_DIR"
if [[ -f "$INSTALL_DIR/blutunnel.env.example" ]]; then
  cp -f "$INSTALL_DIR/blutunnel.env.example" "$ENV_DIR/blutunnel.env.example"
fi

echo
read -r -p "Enable systemd auto-start mode too? (y/N): " enable_service
enable_service="${enable_service:-n}"
enable_service="${enable_service,,}"

if [[ "$enable_service" == "y" ]]; then
  prompt_env_config
  cp -f "$INSTALL_DIR/systemd/blutunnel.service" "$SERVICE_FILE"
  cp -f "$INSTALL_DIR/systemd/blutunnel.timer" "$TIMER_FILE"
  systemctl daemon-reload
  systemctl enable --now blutunnel.service

  read -r -p "Enable 30-minute restart timer? (y/N): " enable_timer
  enable_timer="${enable_timer:-n}"
  enable_timer="${enable_timer,,}"
  if [[ "$enable_timer" == "y" ]]; then
    systemctl enable --now blutunnel.timer
  else
    systemctl disable --now blutunnel.timer >/dev/null 2>&1 || true
  fi

  echo "Systemd service installed."
  echo "Status: systemctl status blutunnel.service"
  echo "Logs:   journalctl -u blutunnel.service -f"
else
  echo "Skipping systemd setup."
fi

echo
echo "BluTunnel is ready."
echo "Run interactive mode with: sudo blutunnel"
if [[ -f "$INSTALL_DIR/blutunnel_panel.py" ]]; then
  echo "Run web panel with:        sudo blutunnel-panel"
fi
