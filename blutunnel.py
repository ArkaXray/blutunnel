import asyncio
import contextlib
import os
import socket
import struct
import subprocess
import sys

try:
    import resource
except ImportError:  # Windows
    resource = None

BUFFER_SIZE = 64 * 1024
OS_SOCK_BUFFER = 2 * 1024 * 1024
CON_COUNT = 500


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def print_banner(mode_name):
    clear_screen()
    CYAN, YELLOW, MAGENTA, BOLD, END = "\033[96m", "\033[93m", "\033[95m", "\033[1m", "\033[0m"
    banner = f"""
{MAGENTA}{BOLD}###########################################
#          🚀 AmirTunnel-Pro              #
#      📢 Channel: @Telhost1              #
###########################################{END}
{CYAN}      AMIR
     (____)              {YELLOW}      .---.
     ( o o)              {YELLOW}     /     \\
  /--- \\ / ---\\          {YELLOW}    (| o o |)
 /            \\         {YELLOW}     |  V  |
|   {MAGENTA}WELCOME{YELLOW}    |   {BOLD}<--->{END}   {YELLOW}    /     \\
 \\            /          {YELLOW}   / /   \\ \\
  \\__________/           {YELLOW}  (__|___|__){END}
    {CYAN}Horned Man{END}             {YELLOW}    Linux Tux{END}
{BOLD}[+] Auto Sync OR Manual Entry
[+] Mode: {mode_name}{END}
-------------------------------------------"""
    safe_print(banner)


def safe_print(text):
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "utf-8"
        fallback = text.encode(encoding, errors="replace").decode(encoding, errors="replace")
        print(fallback)


def parse_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}


def optimize_system():
    try:
        if resource and hasattr(resource, "RLIMIT_NOFILE"):
            resource.setrlimit(resource.RLIMIT_NOFILE, (1000000, 1000000))
    except Exception:
        pass


def tune_socket(writer):
    sock = writer.get_extra_info("socket")
    if not sock:
        return
    with contextlib.suppress(OSError):
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    with contextlib.suppress(OSError):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, OS_SOCK_BUFFER)
    with contextlib.suppress(OSError):
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, OS_SOCK_BUFFER)


async def safe_close(writer):
    writer.close()
    with contextlib.suppress(Exception):
        await writer.wait_closed()


async def fast_pipe(reader, writer):
    try:
        while True:
            data = await reader.read(BUFFER_SIZE)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except Exception:
        pass
    finally:
        await safe_close(writer)


def parse_port(text):
    if not text.isdigit():
        return None
    port = int(text)
    if 1 <= port <= 65535:
        return port
    return None


def prompt_port(label):
    while True:
        value = input(label).strip()
        port = parse_port(value)
        if port is not None:
            return port
        print("Invalid port. Enter a value between 1 and 65535.")


def parse_manual_ports(raw_text):
    ports = []
    for part in raw_text.split(","):
        part = part.strip()
        if not part:
            continue
        port = parse_port(part)
        if port is None:
            continue
        ports.append(port)
    return ports


def get_xray_ports(bridge_p, sync_p):
    try:
        import re

        cmd = "ss -tlnp | grep 'xray-linu'"
        output = subprocess.check_output(cmd, shell=True, text=True)
        ports = set()
        for line in output.splitlines():
            if "127.0.0.1" in line or "::1" in line:
                continue
            found = re.findall(r"[:\]](\d+)\s+", line)
            for p in found:
                p_num = int(p)
                if p_num > 100 and p_num != bridge_p and p_num != sync_p:
                    ports.add(p_num)
        return ports
    except Exception:
        return set()


async def start_europe(iran_ip=None, bridge_p=None, sync_p=None, show_banner=True):
    if show_banner:
        print_banner("EUROPE (XRAY CONNECTOR)")

    if iran_ip is None:
        iran_ip = input("[?] Iran IP: ").strip()
    if bridge_p is None:
        bridge_p = prompt_port("[?] Tunnel Bridge Port: ")
    if sync_p is None:
        sync_p = prompt_port("[?] Port Sync Port: ")

    async def port_sync_task():
        while True:
            try:
                _, writer = await asyncio.open_connection(iran_ip, sync_p)
                current_ports = sorted(get_xray_ports(bridge_p, sync_p))
                data = struct.pack("!B", min(len(current_ports), 255))
                for p in current_ports[:255]:
                    data += struct.pack("!H", p)
                writer.write(data)
                await writer.drain()
                await safe_close(writer)
            except Exception:
                pass
            await asyncio.sleep(3)

    async def create_reverse_link():
        while True:
            try:
                reader, writer = await asyncio.open_connection(iran_ip, bridge_p)
                tune_socket(writer)
                header = await reader.readexactly(2)
                target_port = struct.unpack("!H", header)[0]
                remote_reader, remote_writer = await asyncio.open_connection("127.0.0.1", target_port)
                tune_socket(remote_writer)
                await asyncio.gather(
                    fast_pipe(reader, remote_writer),
                    fast_pipe(remote_reader, writer),
                    return_exceptions=True,
                )
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(1)

    tasks = [asyncio.create_task(port_sync_task())]
    for _ in range(CON_COUNT):
        tasks.append(asyncio.create_task(create_reverse_link()))

    print(f"✅ Running... Sync: {sync_p} | Bridge: {bridge_p}")
    await asyncio.Future()


async def start_iran(bridge_p=None, sync_p=None, is_auto=None, manual_ports=None, show_banner=True):
    if show_banner:
        print_banner("IRAN (FLEX LISTENER)")

    if bridge_p is None:
        bridge_p = prompt_port("[?] Tunnel Bridge Port: ")
    if sync_p is None:
        sync_p = prompt_port("[?] Port Sync Port: ")
    if is_auto is None:
        is_auto = input("[?] Do you want Auto-Sync Xray ports? (y/n): ").strip().lower() == "y"

    connection_pool = asyncio.Queue()
    active_servers = {}

    async def handle_europe_bridge(reader, writer):
        tune_socket(writer)
        await connection_pool.put((reader, writer))

    async def handle_user_side(reader, writer, target_p):
        tune_socket(writer)
        try:
            e_reader, e_writer = await connection_pool.get()
            e_writer.write(struct.pack("!H", target_p))
            await e_writer.drain()
            await asyncio.gather(
                fast_pipe(reader, e_writer),
                fast_pipe(e_reader, writer),
                return_exceptions=True,
            )
        except Exception:
            await safe_close(writer)

    async def open_new_port(p):
        if p in active_servers:
            return
        try:
            srv = await asyncio.start_server(
                lambda r, w, p=p: handle_user_side(r, w, p),
                "0.0.0.0",
                p,
                backlog=5000,
            )
            asyncio.create_task(srv.serve_forever())
            active_servers[p] = srv
            print(f"✨ Port Active: {p}")
        except Exception as e:
            print(f"❌ Error opening port {p}: {e}")

    async def handle_sync_conn(reader, writer):
        try:
            header = await reader.readexactly(1)
            count = struct.unpack("!B", header)[0]
            for _ in range(count):
                p_data = await reader.readexactly(2)
                p = struct.unpack("!H", p_data)[0]
                await open_new_port(p)
            await safe_close(writer)
        except Exception:
            pass

    await asyncio.start_server(handle_europe_bridge, "0.0.0.0", bridge_p, backlog=10000)

    if is_auto:
        await asyncio.start_server(handle_sync_conn, "0.0.0.0", sync_p, backlog=100)
        print(f"🔍 Auto-Sync Active on port {sync_p}")
    else:
        if manual_ports is None:
            manual_ports = parse_manual_ports(input("[?] Enter ports manually (e.g. 80,443,2083): "))
        for p in manual_ports:
            await open_new_port(p)
        print("✅ Manual Ports Opened.")

    await asyncio.Event().wait()


def load_env_config():
    mode = os.getenv("MODE", "").strip().lower()
    if mode not in {"iran", "europe"}:
        return None

    bridge_p = parse_port(os.getenv("BRIDGE_PORT", "").strip())
    sync_p = parse_port(os.getenv("SYNC_PORT", "").strip())
    if bridge_p is None or sync_p is None:
        print("Invalid environment config: BRIDGE_PORT/SYNC_PORT are required.")
        return None

    if mode == "europe":
        iran_ip = os.getenv("IRAN_IP", "").strip()
        if not iran_ip:
            print("Invalid environment config: IRAN_IP is required in europe mode.")
            return None
        return {
            "mode": "europe",
            "iran_ip": iran_ip,
            "bridge_p": bridge_p,
            "sync_p": sync_p,
        }

    is_auto = parse_bool(os.getenv("AUTO_SYNC", "y"))
    manual_ports = parse_manual_ports(os.getenv("MANUAL_PORTS", ""))
    if not is_auto and not manual_ports:
        print("Invalid environment config: MANUAL_PORTS is required when AUTO_SYNC is off.")
        return None

    return {
        "mode": "iran",
        "bridge_p": bridge_p,
        "sync_p": sync_p,
        "is_auto": is_auto,
        "manual_ports": manual_ports,
    }


def interactive_menu_choice():
    while True:
        print_banner("MAIN MENU")
        print("1) Europe Server")
        print("2) Iran Server")
        print("3) Exit")
        choice = input("Choice: ").strip()
        if choice in {"1", "2", "3"}:
            return choice
        print("Invalid choice.")


if __name__ == "__main__":
    optimize_system()

    config = load_env_config()
    if config:
        if config["mode"] == "europe":
            asyncio.run(start_europe(config["iran_ip"], config["bridge_p"], config["sync_p"], show_banner=False))
        else:
            asyncio.run(
                start_iran(
                    config["bridge_p"],
                    config["sync_p"],
                    config["is_auto"],
                    config["manual_ports"],
                    show_banner=False,
                )
            )
    else:
        choice = interactive_menu_choice()
        if choice == "1":
            asyncio.run(start_europe())
        elif choice == "2":
            asyncio.run(start_iran())
