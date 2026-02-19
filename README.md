# BluTunnel

EN: High-performance reverse tunnel to expose Iran-side services through a Europe server with automatic port sync.  
FA: یک تونل معکوس پرفورمنس‌بالا برای ارائه سرویس‌های سمت ایران از طریق سرور اروپا با همگام‌سازی خودکار پورت‌ها.

## One-Command Install | نصب با یک دستور
EN: Run one of these on your server.  
FA: یکی از دستورهای زیر را روی سرور اجرا کنید.

### Iran Server | سرور ایران
```bash
curl -fsSL https://raw.githubusercontent.com/ArkaXray/blutunnel/main/install.sh | sudo bash -s -- --mode iran --bridge-port 4430 --sync-port 4431 --auto-sync y
```

### Europe Server | سرور اروپا
```bash
curl -fsSL https://raw.githubusercontent.com/ArkaXray/blutunnel/main/install.sh | sudo bash -s -- --mode europe --iran-ip 1.2.3.4 --bridge-port 4430 --sync-port 4431
```

EN: Installer actions  
FA: کارهایی که نصاب انجام می‌دهد
- EN: Copies files to `/opt/blutunnel`  
  FA: فایل‌ها را در `/opt/blutunnel` قرار می‌دهد
- EN: Writes config to `/etc/blutunnel/blutunnel.env`  
  FA: تنظیمات را در `/etc/blutunnel/blutunnel.env` می‌نویسد
- EN: Installs and starts `blutunnel.service` and `blutunnel.timer`  
  FA: سرویس و تایمر را نصب و اجرا می‌کند

## Features | ویژگی‌ها
- EN: Reverse architecture (Europe dials back to Iran bridge)  
  FA: معماری معکوس (اروپا به بریج ایران وصل می‌شود)
- EN: Auto-discovery of Xray ports on Europe  
  FA: شناسایی خودکار پورت‌های Xray در اروپا
- EN: Async I/O with large socket buffers  
  FA: ورودی/خروجی async با بافر بزرگ سوکت
- EN: systemd-ready deployment  
  FA: آماده‌ی استقرار با systemd

## Architecture | معماری
- EN: Europe mode sends active ports via sync channel and keeps reverse links via bridge channel.  
  FA: حالت اروپا پورت‌های فعال را از کانال sync می‌فرستد و لینک‌های معکوس را از کانال bridge نگه می‌دارد.
- EN: Iran mode receives reverse links, opens listeners, and forwards user traffic.  
  FA: حالت ایران لینک‌های معکوس را می‌گیرد، پورت‌ها را باز می‌کند و ترافیک کاربر را فوروارد می‌کند.

## Requirements | پیش‌نیازها
- Python 3.8+
- Linux server
- `ss` command (for Europe auto-detection)
- `curl`, `git`, `systemd` (for one-command installer)

## Manual Run | اجرای دستی
### Interactive | تعاملی
```bash
python3 blutunnel.py
```

### Non-interactive CLI | غیرتعاملی با آرگومان
```bash
python3 blutunnel.py --mode europe --iran-ip 1.2.3.4 --bridge-port 4430 --sync-port 4431
python3 blutunnel.py --mode iran --bridge-port 4430 --sync-port 4431 --auto-sync y
```

EN: Use `--manual-ports` when `--auto-sync n`.  
FA: وقتی `--auto-sync n` است از `--manual-ports` استفاده کنید.

```bash
python3 blutunnel.py --mode iran --bridge-port 4430 --sync-port 4431 --auto-sync n --manual-ports 80,443,2083
```

## systemd Setup | تنظیمات systemd
Files | فایل‌ها:
- `systemd/blutunnel.service`
- `systemd/blutunnel.timer`
- `blutunnel.env.example`

Install manually | نصب دستی:
```bash
sudo cp systemd/blutunnel.service /etc/systemd/system/
sudo cp systemd/blutunnel.timer /etc/systemd/system/
sudo mkdir -p /etc/blutunnel
sudo cp blutunnel.env.example /etc/blutunnel/blutunnel.env
sudo systemctl daemon-reload
sudo systemctl enable --now blutunnel.service
sudo systemctl enable --now blutunnel.timer
```

Status | وضعیت:
```bash
sudo systemctl status blutunnel.service
sudo systemctl status blutunnel.timer
```

## Logs | لاگ‌ها
- File | فایل: `logs/blutunnel.log`
- Journal | ژورنال:
```bash
sudo journalctl -u blutunnel.service -f
```

## Security Notes | نکات امنیتی
- EN: Restrict bridge/sync ports with firewall rules.  
  FA: پورت‌های bridge و sync را با فایروال محدود کنید.
- EN: Prefer private network or VPN between servers.  
  FA: بین سرورها شبکه خصوصی یا VPN ترجیح دارد.
- EN: Do not expose unnecessary ports.  
  FA: پورت‌های غیرضروری را باز نگذارید.

## Troubleshooting | عیب‌یابی
- EN: No forwarding -> verify reachability of bridge/sync ports on both nodes.  
  FA: عدم فوروارد -> دسترسی دو طرف به پورت‌های bridge/sync را چک کنید.
- EN: Auto-sync not working -> check `ss -tlnp` and Xray process visibility.  
  FA: مشکل در auto-sync -> خروجی `ss -tlnp` و دیده‌شدن پروسه Xray را بررسی کنید.
- EN: Permission errors on low ports -> run with root/systemd.  
  FA: خطای دسترسی روی پورت‌های پایین -> با root/systemd اجرا کنید.

## Project Structure | ساختار پروژه
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

## License | لایسنس
EN: Add your preferred license in `LICENSE` (MIT / Apache-2.0 / ...).  
FA: لایسنس موردنظر را در فایل `LICENSE` قرار دهید (مثل MIT یا Apache-2.0).
