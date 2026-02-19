# BluTunnel

High-performance reverse tunnel for exposing Iran-side services through a Europe server with automatic port sync.

## One-Command Install And Run
Run this on your server:

### Iran server
```bash
curl -fsSL https://raw.githubusercontent.com/ArkaXray/blutunnel/main/install.sh | sudo bash -s -- --mode iran --bridge-port 4430 --sync-port 4431 --auto-sync y
```

### Europe server
```bash
curl -fsSL https://raw.githubusercontent.com/ArkaXray/blutunnel/main/install.sh | sudo bash -s -- --mode europe --iran-ip 1.2.3.4 --bridge-port 4430 --sync-port 4431
```

The installer will:
- place project files in `/opt/blutunnel`
- write config to `/etc/blutunnel/blutunnel.env`
- install and start `blutunnel.service` and `blutunnel.timer`

## Why BluTunnel?
- Reverse architecture: Europe node actively dials back to Iran bridge.
- Auto-discovery mode for Xray ports on Europe.
- Async I/O with large buffers for high throughput.
- Simple deployment with `systemd` service + timer.

## Architecture
- **Europe mode**:
  - Sends active service ports to Iran every few seconds (`sync` channel).
  - Maintains a pool of reverse links to Iran (`bridge` channel).
- **Iran mode**:
  - Receives reverse links from Europe and keeps them in a connection pool.
  - Opens listener ports and forwards inbound client traffic through an available reverse link.

## Requirements
- Python 3.8+
- Linux server(s) for production usage
- `ss` command available on Europe server (used for auto port detection)
- `curl`, `git`, and `systemd` for one-command installer

Install dependencies:

```bash
pip install -r requirements.txt
```

## Quick Start
Run manually (interactive mode):

```bash
python3 blutunnel.py
```

You will be prompted for mode:

1. `Europe Server`
2. `Iran Server`

### Europe inputs
- `Iran IP`
- `Tunnel Bridge Port`
- `Port Sync Port`

### Iran inputs
- `Tunnel Bridge Port`
- `Port Sync Port`
- `Auto-Sync Xray ports? (y/n)`
  - `y`: ports are created automatically from Europe sync
  - `n`: enter ports manually (`80,443,2083` style)

Run manually (non-interactive CLI mode):

```bash
python3 blutunnel.py --mode europe --iran-ip 1.2.3.4 --bridge-port 4430 --sync-port 4431
python3 blutunnel.py --mode iran --bridge-port 4430 --sync-port 4431 --auto-sync y
```

## systemd Deployment
Provided files:
- `systemd/blutunnel.service`
- `systemd/blutunnel.timer`

Example install:

```bash
sudo cp systemd/blutunnel.service /etc/systemd/system/
sudo cp systemd/blutunnel.timer /etc/systemd/system/
sudo mkdir -p /etc/blutunnel
sudo cp blutunnel.env.example /etc/blutunnel/blutunnel.env
sudo systemctl daemon-reload
sudo systemctl enable --now blutunnel.service
sudo systemctl enable --now blutunnel.timer
```

Check status:

```bash
sudo systemctl status blutunnel.service
sudo systemctl status blutunnel.timer
```

Config file used by service:
- `/etc/blutunnel/blutunnel.env`

## Logs
- App log file: `logs/blutunnel.log`
- Realtime service log:

```bash
sudo journalctl -u blutunnel.service -f
```

## Security Notes
- Restrict `bridge` and `sync` ports with firewall rules.
- Prefer running over private network or VPN between nodes.
- Do not expose unnecessary listener ports.

## Troubleshooting
- **No traffic forwarding**:
  - Check both nodes can reach each other on bridge/sync ports.
  - Verify Europe node has active reverse links.
- **Ports not auto-created**:
  - Ensure Xray process is visible in `ss -tlnp` output.
  - Confirm sync port is open and reachable.
- **Permission issues**:
  - Run with sufficient privileges for low ports (<1024).

## Project Structure

```text
.
|-- blutunnel.py
|-- install.sh
|-- blutunnel.env.example
|-- requirements.txt
|-- README.md
|-- logs/
`-- systemd/
    |-- blutunnel.service
    `-- blutunnel.timer
```

## License
Add your preferred license (MIT/Apache-2.0/etc.) in a `LICENSE` file.
