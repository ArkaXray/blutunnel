# BluTunnel

BluTunnel is a public reverse tunnel utility for Xray-based setups.  
It runs in two modes:

- `Europe Mode`: connects to an Iran server and sends active local `xray` ports.
- `Iran Mode`: receives synced ports and opens public listeners dynamically.

The project is an interactive TUI script written in Python (`blutunnel.py`).

## Features

- Interactive menu for setup and runtime control
- Shared key management (generate random or custom key)
- Dynamic port sync from Europe node to Iran node
- High-concurrency reverse workers (`MAX_POOL = 300`)
- Auto dependency check/install for `aiohttp`
- Server analysis (ping/location) using `check-host.net`
- Live uptime/connection stats in runtime

## Architecture

1. On Europe server, BluTunnel scans listening `xray` ports with:
   - `ss -tlnp`
   - filter lines containing `xray`
2. It sends the port list to Iran server through `Sync Port`.
3. Iran server opens/closes public listeners on those ports.
4. Bridge workers tunnel client traffic to `127.0.0.1:<xray_port>` on Europe side.

## Requirements

- Linux server (Ubuntu/Debian recommended)
- Python 3.8+
- `pip3`
- `ss` command (usually from `iproute2`)
- Network access to `check-host.net` (for Server Check menu)
- Open firewall ports for:
  - `Bridge Port` (between Europe <-> Iran)
  - `Sync Port` (between Europe <-> Iran)
  - synced service ports (public on Iran side)

## Installation

### Quick install (one command)

Run directly from GitHub:

```bash
curl -fsSL https://raw.githubusercontent.com/ArkaXray/blutunnel/main/install.sh | bash
```

### Local install script

```bash
chmod +x install.sh
./install.sh
```

`install.sh` does:

- install required packages (`git`, `python3`, `python3-pip`, `iproute2`)
- install `aiohttp`
- clone/update repository to `~/blutunnel` (default)
- run `python3 blutunnel.py`

Optional environment variables:

- `BLUTUNNEL_REPO` (default: `https://github.com/ArkaXray/blutunnel.git`)
- `BLUTUNNEL_BRANCH` (default: `main`)
- `BLUTUNNEL_DIR` (default: `~/blutunnel`)

### Manual install

```bash
sudo apt update
sudo apt install -y python3 python3-pip iproute2
pip3 install aiohttp
python3 blutunnel.py
```

## Usage

Run:

```bash
python3 blutunnel.py
```

Main menu options:

1. Create / Change KEY
2. Show Current KEY
3. Run as Europe
4. Run as Iran
5. Server Check
6. Exit

### Recommended setup order

1. Run script on both servers.
2. Set the same KEY on both sides (`Create / Change KEY`).
3. On Iran server: run `Run as Iran` and choose:
   - `Bridge Port` (example: `4433`)
   - `Sync Port` (example: `4434`)
4. On Europe server: run `Run as Europe` and enter:
   - Iran server IP
   - same `Bridge Port`
   - same `Sync Port`
5. Verify logs and stats, then test tunneled ports from outside.

## Configuration

BluTunnel stores runtime config in:

- `blutunnel_config.json`

Currently this file stores the shared `key`.

## Security Notes

- Auth is based on SHA-256 hash of the shared key.
- Traffic is not encrypted by TLS inside BluTunnel itself.
- Restrict `Bridge Port` and `Sync Port` in firewall to trusted source IPs.
- Use a strong key (at least 8 chars; longer recommended).

## Troubleshooting

- `Invalid IP address`: use a valid IPv4/IPv6 for Iran server.
- `Port must be a number` / `Invalid port number`: choose `1..65535`.
- `Error getting ports`: ensure `ss` exists and xray is running.
- No synced ports on Iran:
  - check shared key equality
  - verify bridge/sync ports are reachable
  - verify `xray` process appears in `ss -tlnp`

## Git / GitHub

Clone:

```bash
git clone https://github.com/ArkaXray/blutunnel.git
cd blutunnel
```

Commit README updates:

```bash
git add README.md
git commit -m "docs: add complete README for blutunnel.py workflow"
git push origin main
```
