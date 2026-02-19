# BluTunnel

BluTunnel is a reverse tunnel project with two simple ways to use it:
- Terminal menu (`blutunnel`)
- Web panel (`blutunnel-panel`)

## Quick Install (Bash)
```bash
curl -fsSL https://raw.githubusercontent.com/ArkaXray/blutunnel/main/install.sh | sudo bash
```

## Simple Usage

### 1) Terminal Menu
```bash
sudo blutunnel
```

This opens the banner and menu:
- Europe Server
- Iran Server
- Manage Tunnel
- Delete Tunnel

### 2) Web Panel (GUI)
```bash
sudo blutunnel-panel
```

Then open this address in browser:
```text
http://127.0.0.1:8090
```

The panel has:
- Mode selection (Iran / Europe)
- IP + port fields
- Start / Stop buttons
- Runtime status + log preview

## Optional systemd Mode
During install, you can enable systemd auto-start.

Files:
- `systemd/blutunnel.service`
- `systemd/blutunnel.timer`
- `blutunnel.env.example`

If enabled, service uses:
- `/etc/blutunnel/blutunnel.env`

## Requirements
- Python 3.8+
- Linux server
- `ss` command (for Europe auto-detection)
- `curl`, `bash`

## Project Structure
```text
.
|-- blutunnel.py
|-- blutunnel_panel.py
|-- install.sh
|-- blutunnel.env.example
|-- requirements.txt
|-- README.md
|-- logs/
`-- systemd/
    |-- blutunnel.service
    `-- blutunnel.timer
```
