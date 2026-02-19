# BluTunnel

BluTunnel is a reverse tunnel project with an interactive terminal flow.

## Quick Install (Bash)
```bash
curl -fsSL https://raw.githubusercontent.com/ArkaXray/blutunnel/main/install.sh | sudo bash
```

After install:
```bash
sudo blutunnel
```

## Persian Guide | راهنمای فارسی
این پروژه الان روی حالت تعاملی تنظیم شده است.

بعد از اجرای `blutunnel`:
1. بنر نمایش داده می شود.
2. گزینه `Europe` یا `Iran` را انتخاب می کنید.
3. پورت ها و تنظیمات لازم را وارد می کنید.

یعنی دیگر نیازی به اجرای دستورهای مستقیم `--mode iran` یا `--mode europe` نیست.

## Modes
- `Europe (XRAY CONNECTOR)`
  - Connects to Iran bridge.
  - Syncs detected Xray ports.
- `Iran (FLEX LISTENER)`
  - Accepts reverse links.
  - Opens ports from auto-sync or manual list.

## Optional systemd Mode
Installer can also configure `systemd` auto-start if you choose `y` during install.

- Service file: `systemd/blutunnel.service`
- Timer file: `systemd/blutunnel.timer`
- Env sample: `blutunnel.env.example`

If enabled, service reads config from:
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
|-- install.sh
|-- blutunnel.env.example
|-- requirements.txt
|-- README.md
|-- logs/
`-- systemd/
    |-- blutunnel.service
    `-- blutunnel.timer
```
