#!/usr/bin/env python3
import html
import os
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
RUNTIME_LOG_FILE = LOG_DIR / "panel-runtime.log"
BLUTUNNEL_PATH = BASE_DIR / "blutunnel.py"

PANEL_HOST = os.getenv("BLUTUNNEL_PANEL_HOST", "127.0.0.1")
PANEL_PORT = int(os.getenv("BLUTUNNEL_PANEL_PORT", "8090"))


class TunnelRuntime:
    def __init__(self):
        self.lock = threading.Lock()
        self.process = None
        self.started_at = None
        self.config = {
            "mode": "iran",
            "iran_ip": "",
            "bridge_port": "4430",
            "sync_port": "4431",
            "auto_sync": "y",
            "manual_ports": "",
        }

    def is_running(self):
        return self.process is not None and self.process.poll() is None

    def start(self, config):
        with self.lock:
            if self.is_running():
                return False, "Tunnel is already running."

            mode = config["mode"]
            iran_ip = config["iran_ip"].strip()
            bridge_port = config["bridge_port"].strip()
            sync_port = config["sync_port"].strip()
            auto_sync = config["auto_sync"].strip().lower()
            manual_ports = config["manual_ports"].strip()

            ok, reason = validate_mode_config(mode, iran_ip, bridge_port, sync_port, auto_sync, manual_ports)
            if not ok:
                return False, reason

            env = os.environ.copy()
            env["MODE"] = mode
            env["IRAN_IP"] = iran_ip
            env["BRIDGE_PORT"] = bridge_port
            env["SYNC_PORT"] = sync_port
            env["AUTO_SYNC"] = auto_sync
            env["MANUAL_PORTS"] = manual_ports

            log_handle = open(RUNTIME_LOG_FILE, "a", encoding="utf-8")
            log_handle.write("\n")
            log_handle.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] starting mode={mode}\n")
            log_handle.flush()

            self.process = subprocess.Popen(
                [sys.executable, str(BLUTUNNEL_PATH)],
                cwd=str(BASE_DIR),
                env=env,
                stdout=log_handle,
                stderr=subprocess.STDOUT,
                text=True,
            )
            self.started_at = time.time()
            self.config = dict(config)
            return True, f"Tunnel started (PID: {self.process.pid})."

    def stop(self):
        with self.lock:
            if not self.is_running():
                self.process = None
                self.started_at = None
                return False, "Tunnel is not running."

            proc = self.process
            proc.terminate()
            try:
                proc.wait(timeout=8)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)

            self.process = None
            self.started_at = None
            return True, "Tunnel stopped."


runtime = TunnelRuntime()


def parse_port(value):
    if not value.isdigit():
        return None
    port = int(value)
    if 1 <= port <= 65535:
        return port
    return None


def parse_manual_ports(raw_text):
    result = []
    for token in raw_text.split(","):
        token = token.strip()
        if not token:
            continue
        port = parse_port(token)
        if port is None:
            return None
        result.append(port)
    return result


def validate_mode_config(mode, iran_ip, bridge_port, sync_port, auto_sync, manual_ports):
    if mode not in {"iran", "europe"}:
        return False, "Mode must be iran or europe."

    if parse_port(bridge_port) is None or parse_port(sync_port) is None:
        return False, "Bridge port and Sync port must be numbers between 1 and 65535."

    if mode == "europe" and not iran_ip:
        return False, "Iran IP is required in europe mode."

    if mode == "iran":
        if auto_sync not in {"y", "n"}:
            return False, "Auto Sync must be y or n."
        if auto_sync == "n":
            ports = parse_manual_ports(manual_ports)
            if ports is None or len(ports) == 0:
                return False, "Manual ports must be valid comma-separated ports."

    return True, "ok"


def read_tail(path, line_count=40):
    if not path.exists():
        return ""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-line_count:])


def render_page(message="", error=False):
    with runtime.lock:
        cfg = dict(runtime.config)
        running = runtime.is_running()
        pid = runtime.process.pid if running else "-"
        uptime = int(time.time() - runtime.started_at) if running and runtime.started_at else 0

    mode = cfg.get("mode", "iran")
    mode_iran_checked = "checked" if mode == "iran" else ""
    mode_europe_checked = "checked" if mode == "europe" else ""
    auto_sync_checked = "checked" if cfg.get("auto_sync", "y") == "y" else ""
    log_preview = html.escape(read_tail(RUNTIME_LOG_FILE, line_count=40))
    message_color = "#b42318" if error else "#0b6e4f"

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>BluTunnel Panel</title>
  <style>
    :root {{
      --bg: #f4f7f5;
      --card: #ffffff;
      --ink: #102a2b;
      --accent: #0f766e;
      --line: #d7e2de;
      --warn: #b42318;
    }}
    body {{
      margin: 0;
      font-family: Segoe UI, Tahoma, Arial, sans-serif;
      background: radial-gradient(circle at top right, #dff7ef 0%, var(--bg) 55%);
      color: var(--ink);
    }}
    .wrap {{
      max-width: 900px;
      margin: 24px auto;
      padding: 0 14px;
    }}
    .card {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 16px;
      margin-bottom: 14px;
      box-shadow: 0 10px 24px rgba(16, 42, 43, 0.06);
    }}
    h1 {{
      margin: 0 0 4px;
      font-size: 28px;
      color: var(--accent);
    }}
    p {{ margin: 0 0 8px; }}
    .grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 10px;
    }}
    .full {{ grid-column: 1 / -1; }}
    label {{
      display: block;
      font-size: 13px;
      margin-bottom: 4px;
    }}
    input[type=text] {{
      width: 100%;
      box-sizing: border-box;
      padding: 10px 12px;
      border: 1px solid var(--line);
      border-radius: 10px;
      font-size: 14px;
    }}
    .actions {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 8px;
    }}
    button {{
      border: 0;
      border-radius: 10px;
      padding: 10px 14px;
      font-size: 14px;
      cursor: pointer;
      background: var(--accent);
      color: #fff;
    }}
    button.secondary {{
      background: #334155;
    }}
    .status {{
      font-size: 15px;
      line-height: 1.8;
    }}
    .msg {{
      padding: 10px 12px;
      border-radius: 10px;
      background: #f9fafb;
      border: 1px solid var(--line);
      color: {message_color};
      margin-bottom: 8px;
      white-space: pre-wrap;
    }}
    pre {{
      margin: 0;
      background: #0b1720;
      color: #d1f6ed;
      border-radius: 10px;
      padding: 12px;
      overflow: auto;
      max-height: 320px;
      font-size: 12px;
    }}
    @media (max-width: 720px) {{
      .grid {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="card">
      <h1>BluTunnel Panel</h1>
      <p>Simple web UI for start/stop and mode config.</p>
      <p><strong>Channel:</strong> @azadnamaa</p>
    </div>

    <div class="card">
      {"<div class='msg'>" + html.escape(message) + "</div>" if message else ""}
      <form method="post" action="/start">
        <div class="grid">
          <div class="full">
            <label>Mode</label>
            <label><input type="radio" name="mode" value="iran" {mode_iran_checked}> Iran</label>
            <label><input type="radio" name="mode" value="europe" {mode_europe_checked}> Europe</label>
          </div>

          <div>
            <label>Iran IP (required for Europe)</label>
            <input type="text" name="iran_ip" value="{html.escape(cfg.get("iran_ip", ""))}">
          </div>
          <div>
            <label>Auto Sync (Iran)</label>
            <label><input type="checkbox" name="auto_sync" value="y" {auto_sync_checked}> enabled</label>
          </div>
          <div>
            <label>Tunnel Bridge Port</label>
            <input type="text" name="bridge_port" value="{html.escape(cfg.get("bridge_port", "4430"))}">
          </div>
          <div>
            <label>Port Sync Port</label>
            <input type="text" name="sync_port" value="{html.escape(cfg.get("sync_port", "4431"))}">
          </div>
          <div class="full">
            <label>Manual Ports (Iran when Auto Sync off) ex: 80,443,2083</label>
            <input type="text" name="manual_ports" value="{html.escape(cfg.get("manual_ports", ""))}">
          </div>
        </div>
        <div class="actions">
          <button type="submit">Start Tunnel</button>
        </div>
      </form>
      <div class="actions">
        <form method="post" action="/stop"><button class="secondary" type="submit">Stop Tunnel</button></form>
        <form method="get" action="/"><button class="secondary" type="submit">Refresh</button></form>
      </div>
    </div>

    <div class="card status">
      <div><strong>Running:</strong> {"yes" if running else "no"}</div>
      <div><strong>PID:</strong> {pid}</div>
      <div><strong>Uptime:</strong> {uptime}s</div>
      <div><strong>Log File:</strong> {html.escape(str(RUNTIME_LOG_FILE))}</div>
    </div>

    <div class="card">
      <h3 style="margin-top:0">Runtime Log (last 40 lines)</h3>
      <pre>{log_preview}</pre>
    </div>
  </div>
</body>
</html>
"""


class PanelHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/":
            self.send_error(404)
            return

        params = parse_qs(parsed.query)
        msg = params.get("msg", [""])[0]
        err = params.get("err", ["0"])[0] == "1"
        self._send_html(render_page(message=msg, error=err))

    def do_POST(self):
        parsed = urlparse(self.path)
        content_len = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_len).decode("utf-8", errors="replace")
        form = parse_qs(raw)

        if parsed.path == "/start":
            config = {
                "mode": pick(form, "mode", "iran"),
                "iran_ip": pick(form, "iran_ip", ""),
                "bridge_port": pick(form, "bridge_port", "4430"),
                "sync_port": pick(form, "sync_port", "4431"),
                "auto_sync": "y" if pick(form, "auto_sync", "") == "y" else "n",
                "manual_ports": pick(form, "manual_ports", ""),
            }
            ok, msg = runtime.start(config)
            self._send_html(render_page(message=msg, error=not ok))
            return

        if parsed.path == "/stop":
            ok, msg = runtime.stop()
            self._send_html(render_page(message=msg, error=not ok))
            return

        self.send_error(404)

    def _send_html(self, body):
        payload = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        return


def pick(form, key, default):
    values = form.get(key, [])
    if not values:
        return default
    return values[0].strip()


def main():
    if not BLUTUNNEL_PATH.exists():
        raise SystemExit(f"blutunnel.py not found: {BLUTUNNEL_PATH}")

    server = ThreadingHTTPServer((PANEL_HOST, PANEL_PORT), PanelHandler)
    print(f"BluTunnel panel running at http://{PANEL_HOST}:{PANEL_PORT}")
    print("Press Ctrl+C to stop panel.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
