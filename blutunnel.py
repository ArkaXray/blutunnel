#!/usr/bin/env python3

import subprocess
import sys
import os
import importlib.util
import asyncio
import socket
import struct
import resource
import hashlib
import json
import secrets
import logging
from typing import Set, Dict, Optional, Tuple
import ipaddress
import time

class DependencyManager:
    REQUIRED_PACKAGES = {'aiohttp': 'aiohttp>=3.8.0'}
    
    @classmethod
    def check_package(cls, package_name):
        if package_name in sys.builtin_module_names:
            return True
        spec = importlib.util.find_spec(package_name)
        return spec is not None
    
    @classmethod
    def install_package(cls, package_name, package_spec=None):
        if not package_spec:
            package_spec = package_name
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_spec])
            return True
        except:
            try:
                subprocess.check_call(["pip3", "install", package_spec])
                return True
            except:
                return False
    
    @classmethod
    def ensure_dependencies(cls):
        missing = []
        print("\033[94m" + "="*50 + "\033[0m")
        print("\033[94m📋 Checking dependencies...\033[0m")
        print("\033[94m" + "="*50 + "\033[0m")
        
        for package, spec in cls.REQUIRED_PACKAGES.items():
            if cls.check_package(package):
                print(f"\033[92m✅ {package:15} Found\033[0m")
            else:
                print(f"\033[93m⚠️  {package:15} Missing\033[0m")
                missing.append((package, spec))
        
        if missing:
            print("\n\033[93m📦 Installing missing packages...\033[0m")
            for package, spec in missing:
                print(f"\033[93mInstalling {package}...\033[0m")
                if cls.install_package(package, spec):
                    print(f"\033[92m  ✅ {package} installed\033[0m")
                else:
                    print(f"\033[91m  ❌ Failed to install {package}\033[0m")
                    print(f"\033[91m     Please install manually: pip3 install {spec or package}\033[0m")
                    sys.exit(1)
            print("\n\033[92m✅ All dependencies installed! Restarting...\033[0m")
            os.execl(sys.executable, sys.executable, *sys.argv)
        
        print("\n\033[92m✅ All dependencies satisfied!\033[0m")
        print("\033[94m" + "="*50 + "\033[0m\n")

DependencyManager.ensure_dependencies()

import aiohttp

CONFIG_FILE = "blutunnel_config.json"
BUFFER_SIZE = 65536
SOCK_BUFFER = 2 * 1024 * 1024
MAX_POOL = 300
CONN_TIMEOUT = 30
CHECK_HOST_API = "https://check-host.net"

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[35m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
    GRAY = '\033[90m'
    WHITE = '\033[97m'
    SUCCESS = f'{GREEN}✅{END}'
    ERROR = f'{RED}❌{END}'
    WARNING = f'{YELLOW}⚠️{END}'
    INFO = f'{BLUE}ℹ️{END}'
    PING = f'{CYAN}📡{END}'
    LOCATION = f'{MAGENTA}🌍{END}'
    LOCK = f'{YELLOW}🔒{END}'
    ROCKET = f'{GREEN}🚀{END}'
    SERVER = f'{CYAN}🖥️{END}'
    DATABASE = f'{BLUE}💾{END}'
    KEY = f'{YELLOW}🔑{END}'

class ColoredFormatter(logging.Formatter):
    format_str = "%(asctime)s.%(msecs)03d"
    FORMATS = {
        logging.DEBUG: Colors.GRAY + format_str + Colors.END + " " + Colors.GRAY + "│ %(message)s" + Colors.END,
        logging.INFO: Colors.GREEN + format_str + Colors.END + " " + Colors.CYAN + "│" + Colors.END + " %(message)s",
        logging.WARNING: Colors.YELLOW + format_str + Colors.END + " " + Colors.YELLOW + "│ %(message)s" + Colors.END,
        logging.ERROR: Colors.RED + format_str + Colors.END + " " + Colors.RED + "│ %(message)s" + Colors.END,
        logging.CRITICAL: Colors.RED + Colors.BOLD + format_str + Colors.END + " " + Colors.RED + "│ %(message)s" + Colors.END
    }
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%H:%M:%S")
        return formatter.format(record)

logger = logging.getLogger("BluTunnel")
handler = logging.StreamHandler()
handler.setFormatter(ColoredFormatter())
logger.addHandler(handler)
logger.setLevel(logging.INFO)

class BeautifulUI:
    @staticmethod
    def clear():
        os.system("clear" if os.name == "posix" else "cls")
    
    @staticmethod
    def print_banner():
        BeautifulUI.clear()
        banner = f"""
{Colors.BLUE}╔════════════════════════════════════════════════════════════╗
║                                                                ║
║{Colors.WHITE}                      🔵 {Colors.BOLD}BluTunnel{Colors.END}{Colors.WHITE} v2.0{Colors.BLUE}                        ║
║{Colors.WHITE}                 Public Reverse Tunnel System{Colors.BLUE}                  ║
║                                                                ║
╠════════════════════════════════════════════════════════════════╣
║{Colors.GRAY}                                                              {Colors.BLUE}║
║{Colors.GRAY}      ⚡ High Performance    🔒 Secure    🌍 Global{Colors.BLUE}            ║
║{Colors.GRAY}                                                              {Colors.BLUE}║
╚════════════════════════════════════════════════════════════════╝{Colors.END}
        """
        print(banner)
    
    @staticmethod
    def print_section(title, emoji="📌"):
        print(f"\n{Colors.CYAN}╭─ {emoji} {Colors.BOLD}{title}{Colors.END}")
        print(f"{Colors.CYAN}╰─────────────────────────────────────{Colors.END}\n")
    
    @staticmethod
    def input_with_style(prompt, emoji="💬", default=None):
        if default:
            prompt = f"{prompt} [{Colors.GRAY}{default}{Colors.END}]"
        result = input(f"{Colors.CYAN}┌─[{Colors.YELLOW}{emoji}{Colors.CYAN}] {prompt}: {Colors.END}")
        if not result and default:
            return default
        return result.strip()
    
    @staticmethod
    def print_info(label, value, emoji="•"):
        print(f"  {Colors.CYAN}{emoji}{Colors.END} {Colors.WHITE}{label}:{Colors.END} {Colors.GREEN}{value}{Colors.END}")
    
    @staticmethod
    def print_success(message):
        print(f"  {Colors.SUCCESS} {Colors.GREEN}{message}{Colors.END}")
    
    @staticmethod
    def print_error(message):
        print(f"  {Colors.ERROR} {Colors.RED}{message}{Colors.END}")
    
    @staticmethod
    def print_warning(message):
        print(f"  {Colors.WARNING} {Colors.YELLOW}{message}{Colors.END}")
    
    @staticmethod
    def print_progress_bar(iteration, total, prefix='', suffix='', length=30):
        percent = ("{0:.1f}").format(100 * (iteration / float(total)))
        filled_length = int(length * iteration // total)
        bar = '█' * filled_length + '░' * (length - filled_length)
        print(f'\r  {Colors.CYAN}{prefix}{Colors.END} |{Colors.GREEN}{bar}{Colors.END}| {Colors.YELLOW}{percent}%{Colors.END} {suffix}', end='\r')
        if iteration == total:
            print()
    
    @staticmethod
    def print_table(data, headers):
        if not data:
            return
        col_widths = [len(h) for h in headers]
        for row in data:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        print(f"{Colors.CYAN}┌─" + "─┬─".join(["─" * w for w in col_widths]) + "─┐{Colors.END}")
        header_line = "│ "
        for i, h in enumerate(headers):
            header_line += f"{Colors.YELLOW}{h:^{col_widths[i]}}{Colors.END} │ "
        print(header_line[:-1])
        print(f"{Colors.CYAN}├─" + "─┼─".join(["─" * w for w in col_widths]) + "─┤{Colors.END}")
        for row in data:
            line = "│ "
            for i, cell in enumerate(row):
                line += f"{Colors.WHITE}{str(cell):^{col_widths[i]}}{Colors.END} │ "
            print(line[:-1])
        print(f"{Colors.CYAN}└─" + "─┴─".join(["─" * w for w in col_widths]) + "─┘{Colors.END}")

    @staticmethod
    def print_table(data, headers):
        """Override legacy renderer to avoid malformed ANSI/table output."""
        if not data:
            return
        col_widths = [len(h) for h in headers]
        for row in data:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        sep = "+-" + "-+-".join("-" * w for w in col_widths) + "-+"
        print(f"{Colors.CYAN}{sep}{Colors.END}")
        header_cells = []
        for i, h in enumerate(headers):
            header_cells.append(f"{Colors.YELLOW}{h:^{col_widths[i]}}{Colors.END}")
        print("| " + " | ".join(header_cells) + " |")
        print(f"{Colors.CYAN}{sep}{Colors.END}")
        for row in data:
            row_cells = []
            for i, cell in enumerate(row):
                row_cells.append(f"{Colors.WHITE}{str(cell):^{col_widths[i]}}{Colors.END}")
            print("| " + " | ".join(row_cells) + " |")
        print(f"{Colors.CYAN}{sep}{Colors.END}")

    @staticmethod
    def show_menu():
        BeautifulUI.print_banner()
        BeautifulUI.print_section("Main Menu", "🎯")
        menu_items = [
            ("1", "Create / Change KEY", "🔑"),
            ("2", "Show Current KEY", "👁️"),
            ("3", "Run as Europe", "🇪🇺"),
            ("4", "Run as Iran", "🇮🇷"),
            ("5", "Server Check", "🌍"),
            ("6", "Exit", "🚪")
        ]
        for num, desc, emoji in menu_items:
            print(f"  {Colors.GREEN}[{num}]{Colors.END} {emoji} {desc}")
        print()
        return BeautifulUI.input_with_style("Select Option", "🎯")

class ServerDetector:
    def __init__(self):
        self.session = None
        self.nodes_cache = None
        self.nodes_cache_time = 0
        
    async def ensure_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession(headers={"Accept": "application/json"})
    
    async def close(self):
        if self.session:
            await self.session.close()
    
    async def get_server_info(self, ip):
        try:
            await self.ensure_session()
            async with self.session.get(f"{CHECK_HOST_API}/nodes/hosts") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    nodes = data.get("nodes", {})
                    for node_name, node_info in nodes.items():
                        node_ip = node_info.get("ip", "")
                        if node_ip and ip in node_ip:
                            location = node_info.get("location", [])
                            if len(location) >= 3:
                                country_code = location[0]
                                country = location[1]
                                city = location[2]
                                asn = node_info.get("asn", "Unknown")
                                return country, city, asn
            return None, None, None
        except Exception as e:
            logger.error(f"Error getting server info: {e}")
            return None, None, None
    
    async def check_ping(self, host, max_nodes=5):
        results = {
            "success": False,
            "ping_data": {},
            "is_access": False,
            "avg_ping": None
        }
        try:
            await self.ensure_session()
            url = f"{CHECK_HOST_API}/check-ping"
            params = {"host": host, "max_nodes": max_nodes}
            async with self.session.get(url, params=params) as resp:
                if resp.status != 200:
                    return results
                data = await resp.json()
                if not data.get("ok"):
                    return results
                request_id = data.get("request_id")
                if not request_id:
                    return results
                await asyncio.sleep(3)
                result_url = f"{CHECK_HOST_API}/check-result/{request_id}"
                async with self.session.get(result_url) as result_resp:
                    if result_resp.status != 200:
                        return results
                    ping_data = await result_resp.json()
                    successful_pings = []
                    total_ping = 0
                    ping_count = 0
                    for node, node_results in ping_data.items():
                        if node_results and isinstance(node_results, list):
                            for ping_result in node_results:
                                if ping_result and isinstance(ping_result, list):
                                    if ping_result[0] == "OK" and len(ping_result) >= 3:
                                        ping_time = ping_result[1]
                                        if isinstance(ping_time, (int, float)):
                                            successful_pings.append({
                                                "node": node,
                                                "time": ping_time,
                                                "ip": ping_result[2] if len(ping_result) > 2 else "Unknown"
                                            })
                                            total_ping += ping_time
                                            ping_count += 1
                    results["success"] = True
                    results["ping_data"] = ping_data
                    results["avg_ping"] = total_ping / ping_count if ping_count > 0 else None
                    iran_pings = 0
                    foreign_pings = 0
                    for ping in successful_pings:
                        node = ping["node"]
                        if "ir" in node.lower() or "tehran" in node.lower():
                            iran_pings += 1
                        else:
                            foreign_pings += 1
                    if foreign_pings == 0 and iran_pings > 0:
                        results["is_access"] = True
                    elif foreign_pings > 0:
                        results["is_access"] = False
        except Exception as e:
            logger.error(f"Ping check error: {e}")
        return results
    
    async def display_server_info(self, host):
        BeautifulUI.print_section("Server Analysis", "🔍")
        print(f"  {Colors.PING} Analyzing: {Colors.CYAN}{host}{Colors.END}\n")
        BeautifulUI.print_info("Status", "Checking ping...", "📡")
        ping_results = await self.check_ping(host)
        if ping_results["success"]:
            if ping_results["avg_ping"]:
                BeautifulUI.print_success(f"Average Ping: {ping_results['avg_ping']:.2f}ms")
            else:
                BeautifulUI.print_warning("No successful ping responses")
            print()
            if ping_results["is_access"]:
                BeautifulUI.print_error("⚠️ ACCESS SERVER DETECTED ⚠️")
                BeautifulUI.print_warning("This IP only responds to pings from Iran")
                BeautifulUI.print_warning("It may be an access/server with routing restrictions")
            else:
                BeautifulUI.print_success("✅ This is a normal server (international connectivity)")
            print()
            BeautifulUI.print_info("Ping Details", f"{len(ping_results['ping_data'])} nodes", "📊")
            table_data = []
            for node, node_results in ping_results["ping_data"].items():
                if node_results and isinstance(node_results, list):
                    for i, ping in enumerate(node_results):
                        if ping and isinstance(ping, list):
                            if ping[0] == "OK":
                                location = node.split('.')[0]
                                table_data.append([
                                    location.upper(),
                                    f"{ping[1]:.2f}ms",
                                    ping[2] if len(ping) > 2 else "N/A",
                                    "✅ Success"
                                ])
                            else:
                                table_data.append([
                                    node.split('.')[0].upper(),
                                    "Timeout",
                                    "N/A",
                                    f"❌ {ping[0]}"
                                ])
            if table_data:
                BeautifulUI.print_table(table_data, ["Node", "Ping", "IP", "Status"])
        else:
            BeautifulUI.print_error("Failed to check server")
        country, city, asn = await self.get_server_info(host)
        if country:
            print()
            BeautifulUI.print_info("Location", f"{country} - {city}", "🌍")
            BeautifulUI.print_info("ISP", asn, "🏢")

    async def get_nodes(self, cache_ttl=60):
        now = time.time()
        if self.nodes_cache and (now - self.nodes_cache_time) < cache_ttl:
            return self.nodes_cache
        try:
            await self.ensure_session()
            async with self.session.get(f"{CHECK_HOST_API}/nodes/hosts") as resp:
                if resp.status != 200:
                    return {}
                data = await resp.json()
                nodes = data.get("nodes", {})
                if isinstance(nodes, dict):
                    self.nodes_cache = nodes
                    self.nodes_cache_time = now
                    return nodes
        except Exception as e:
            logger.error(f"Error loading nodes: {e}")
        return {}

    @staticmethod
    def _extract_ping_entries(value):
        entries = []

        def walk(node):
            if not isinstance(node, list):
                return
            if node and isinstance(node[0], str):
                status = node[0]
                ping_time = node[1] if len(node) > 1 else None
                ip = node[2] if len(node) > 2 else "N/A"
                entries.append((status, ping_time, ip))
                return
            for child in node:
                walk(child)

        walk(value)
        return entries

    async def check_ping(self, host, max_nodes=None):
        results = {
            "success": False,
            "ping_data": {},
            "is_access": None,
            "avg_ping": None,
            "rows": []
        }
        try:
            await self.ensure_session()
            nodes = await self.get_nodes()
            total_nodes = len(nodes) if isinstance(nodes, dict) else 0

            params = {"host": host}
            if max_nodes is None:
                # Use all available check-host nodes by default.
                params["max_nodes"] = total_nodes if total_nodes > 0 else 1000
            else:
                params["max_nodes"] = max_nodes

            async with self.session.get(f"{CHECK_HOST_API}/check-ping", params=params) as resp:
                if resp.status != 200:
                    return results
                data = await resp.json()
                if not data.get("ok"):
                    return results
                request_id = data.get("request_id")
                if not request_id:
                    return results

            await asyncio.sleep(3)
            async with self.session.get(f"{CHECK_HOST_API}/check-result/{request_id}") as result_resp:
                if result_resp.status != 200:
                    return results
                ping_data = await result_resp.json()

            total_ping = 0.0
            ping_count = 0
            iran_pings = 0
            foreign_pings = 0
            rows = []

            for node, node_results in ping_data.items():
                node_code = node.split('.')[0].upper()
                entries = self._extract_ping_entries(node_results)
                if not entries:
                    rows.append([node_code, "N/A", "N/A", "No data"])
                    continue

                for status, ping_time, ip in entries:
                    if status == "OK" and isinstance(ping_time, (int, float)):
                        rows.append([node_code, f"{ping_time:.2f}ms", ip if ip else "N/A", "Success"])
                        total_ping += ping_time
                        ping_count += 1
                        if "ir" in node.lower() or "tehran" in node.lower():
                            iran_pings += 1
                        else:
                            foreign_pings += 1
                    else:
                        status_text = str(status) if status is not None else "Unknown"
                        ping_label = "Timeout" if status_text.upper() == "TIMEOUT" else "N/A"
                        rows.append([node_code, ping_label, "N/A", status_text])

            results["success"] = True
            results["ping_data"] = ping_data
            results["rows"] = rows
            if ping_count > 0:
                results["avg_ping"] = total_ping / ping_count
                results["is_access"] = (foreign_pings == 0 and iran_pings > 0)

        except Exception as e:
            logger.error(f"Ping check error: {e}")
        return results

    async def display_server_info(self, host):
        BeautifulUI.print_section("Server Analysis", "S")
        print(f"  {Colors.PING} Analyzing: {Colors.CYAN}{host}{Colors.END}\n")
        BeautifulUI.print_info("Status", "Checking ping...", "P")
        ping_results = await self.check_ping(host)

        if ping_results["success"]:
            if ping_results["avg_ping"] is not None:
                BeautifulUI.print_success(f"Average Ping: {ping_results['avg_ping']:.2f}ms")
            else:
                BeautifulUI.print_warning("No successful ping responses")
            print()

            if ping_results["is_access"] is True:
                BeautifulUI.print_error("ACCESS SERVER DETECTED")
                BeautifulUI.print_warning("This IP only responds to pings from Iran")
                BeautifulUI.print_warning("It may be an access/server with routing restrictions")
            elif ping_results["is_access"] is False:
                BeautifulUI.print_success("This is a normal server (international connectivity)")
            else:
                BeautifulUI.print_warning("Connectivity type could not be determined")

            print()
            BeautifulUI.print_info("Ping Details", f"{len(ping_results['ping_data'])} nodes", "I")
            if ping_results["rows"]:
                BeautifulUI.print_table(ping_results["rows"], ["Node", "Ping", "IP", "Status"])
            else:
                BeautifulUI.print_warning("No node results returned")
        else:
            BeautifulUI.print_error("Failed to check server")

        country, city, asn = await self.get_server_info(host)
        if country:
            print()
            BeautifulUI.print_info("Location", f"{country} - {city}", "L")
            BeautifulUI.print_info("ISP", asn, "D")

def validate_port(port):
    return 1 <= port <= 65535

def validate_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def hash_key(key):
    return hashlib.sha256(key.encode()).digest()

def generate_key():
    return secrets.token_hex(16)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        BeautifulUI.print_error("Invalid config file")
        return {}

def save_config(data):
    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)

def optimize():
    try:
        resource.setrlimit(resource.RLIMIT_NOFILE, (200000, 200000))
    except Exception as e:
        logger.warning(f"Could not set resource limit: {e}")

async def tune(writer):
    sock = writer.get_extra_info("socket")
    if sock:
        try:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, SOCK_BUFFER)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, SOCK_BUFFER)
        except Exception as e:
            logger.debug(f"Tune failed: {e}")

async def pipe(reader, writer, timeout=CONN_TIMEOUT):
    try:
        while True:
            data = await asyncio.wait_for(reader.read(BUFFER_SIZE), timeout=timeout)
            if not data:
                break
            writer.write(data)
            await asyncio.wait_for(writer.drain(), timeout=timeout)
    except asyncio.TimeoutError:
        logger.debug("Pipe timeout")
    except Exception as e:
        logger.debug(f"Pipe error: {e}")
    finally:
        if not writer.is_closing():
            writer.close()
            try:
                await writer.wait_closed()
            except:
                pass

async def get_xray_ports_safe():
    ports = set()
    try:
        process = await asyncio.create_subprocess_exec(
            'ss', '-tlnp',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, _ = await process.communicate()
        import re
        for line in stdout.decode().splitlines():
            if 'xray' in line:
                found = re.findall(r":(\d+)", line)
                for p in found:
                    p = int(p)
                    if 1 <= p <= 65535:
                        ports.add(p)
    except Exception as e:
        logger.error(f"Error getting ports: {e}")
    return ports

async def start_europe(key):
    BeautifulUI.print_banner()
    BeautifulUI.print_section("Europe Mode", "🇪🇺")
    iran_ip = BeautifulUI.input_with_style("Iran IP", "🌍")
    if not validate_ip(iran_ip):
        BeautifulUI.print_error("Invalid IP address")
        input(f"{Colors.GRAY}Press Enter...{Colors.END}")
        return
    try:
        bridge_p = int(BeautifulUI.input_with_style("Bridge Port", "🔌"))
        sync_p = int(BeautifulUI.input_with_style("Sync Port", "🔄"))
        if not (validate_port(bridge_p) and validate_port(sync_p)):
            BeautifulUI.print_error("Invalid port number")
            input(f"{Colors.GRAY}Press Enter...{Colors.END}")
            return
    except ValueError:
        BeautifulUI.print_error("Port must be a number")
        input(f"{Colors.GRAY}Press Enter...{Colors.END}")
        return
    auth = hash_key(key)
    running = True
    start_time = time.time()
    connection_count = 0
    async def sync_task():
        nonlocal running
        while running:
            try:
                reader, writer = await asyncio.open_connection(iran_ip, sync_p)
                writer.write(auth)
                ports = await get_xray_ports_safe()
                writer.write(struct.pack("!H", len(ports)))
                for p in ports:
                    writer.write(struct.pack("!H", p))
                await writer.drain()
                writer.close()
                await writer.wait_closed()
                logger.info(f"{Colors.GREEN}✓{Colors.END} Synced {len(ports)} ports")
            except Exception as e:
                logger.error(f"Sync failed: {e}")
            await asyncio.sleep(5)
    async def reverse_worker(semaphore, worker_id):
        nonlocal running, connection_count
        backoff = 1
        while running:
            try:
                async with semaphore:
                    reader, writer = await asyncio.wait_for(
                        asyncio.open_connection(iran_ip, bridge_p),
                        timeout=CONN_TIMEOUT
                    )
                    await tune(writer)
                    server_auth = await asyncio.wait_for(
                        reader.readexactly(32),
                        timeout=CONN_TIMEOUT
                    )
                    if server_auth != auth:
                        writer.close()
                        return
                    header = await asyncio.wait_for(
                        reader.readexactly(2),
                        timeout=CONN_TIMEOUT
                    )
                    port = struct.unpack("!H", header)[0]
                    if not validate_port(port):
                        logger.warning(f"Invalid port from server: {port}")
                        writer.close()
                        continue
                    r_reader, r_writer = await asyncio.wait_for(
                        asyncio.open_connection("127.0.0.1", port),
                        timeout=CONN_TIMEOUT
                    )
                    await tune(r_writer)
                    connection_count += 1
                    logger.debug(f"Worker {worker_id} connected to port {port}")
                    await asyncio.gather(
                        pipe(reader, r_writer),
                        pipe(r_reader, writer),
                        return_exceptions=True
                    )
                    backoff = 1
            except asyncio.TimeoutError:
                logger.debug(f"Worker {worker_id} timeout")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 10)
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 10)
    semaphore = asyncio.Semaphore(MAX_POOL)
    print()
    BeautifulUI.print_success("🚀 BluTunnel Europe Starting...")
    print(f"  {Colors.SERVER} Target: {Colors.CYAN}{iran_ip}:{bridge_p}{Colors.END}")
    print(f"  {Colors.INFO} Workers: {Colors.YELLOW}{MAX_POOL}{Colors.END}")
    print()
    sync_task_obj = asyncio.create_task(sync_task())
    workers = []
    for i in range(MAX_POOL):
        task = asyncio.create_task(reverse_worker(semaphore, i))
        workers.append(task)
    async def show_stats():
        while running:
            uptime = time.time() - start_time
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            seconds = int(uptime % 60)
            print(f"\r  {Colors.CYAN}⏱️ Uptime: {Colors.GREEN}{hours:02d}:{minutes:02d}:{seconds:02d}{Colors.END} {Colors.PING} Connections: {Colors.YELLOW}{connection_count}{Colors.END}", end="")
            await asyncio.sleep(1)
    stats_task = asyncio.create_task(show_stats())
    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        print("\n")
        BeautifulUI.print_warning("Shutting down gracefully...")
        running = False
        sync_task_obj.cancel()
        stats_task.cancel()
        for w in workers:
            w.cancel()
        await asyncio.gather(*workers, return_exceptions=True)
        BeautifulUI.print_success("✅ Shutdown complete")

async def start_iran(key):
    BeautifulUI.print_banner()
    BeautifulUI.print_section("Iran Mode", "🇮🇷")
    try:
        bridge_p = int(BeautifulUI.input_with_style("Bridge Port", "🌉"))
        sync_p = int(BeautifulUI.input_with_style("Sync Port", "🔄"))
        if not (validate_port(bridge_p) and validate_port(sync_p)):
            BeautifulUI.print_error("Invalid port number")
            input(f"{Colors.GRAY}Press Enter...{Colors.END}")
            return
    except ValueError:
        BeautifulUI.print_error("Port must be a number")
        input(f"{Colors.GRAY}Press Enter...{Colors.END}")
        return
    auth = hash_key(key)
    pool = asyncio.Queue(maxsize=MAX_POOL)
    active_ports = {}
    running = True
    connection_count = 0
    start_time = time.time()
    async def handle_bridge(reader, writer):
        nonlocal connection_count
        await tune(writer)
        try:
            writer.write(auth)
            await writer.drain()
            await asyncio.wait_for(pool.put((reader, writer)), timeout=5)
            connection_count += 1
        except asyncio.TimeoutError:
            logger.warning("Bridge queue full")
            writer.close()
        except Exception as e:
            logger.error(f"Bridge error: {e}")
            writer.close()
    async def handle_user(reader, writer, port):
        try:
            e_reader, e_writer = await asyncio.wait_for(pool.get(), timeout=5)
            try:
                e_writer.write(struct.pack("!H", port))
                await e_writer.drain()
                await asyncio.gather(
                    pipe(reader, e_writer),
                    pipe(e_reader, writer),
                    return_exceptions=True
                )
            finally:
                if not e_writer.is_closing():
                    e_writer.close()
        except asyncio.TimeoutError:
            logger.debug(f"No available bridge for port {port}")
            writer.close()
        except Exception as e:
            logger.error(f"User handler error: {e}")
            writer.close()
    async def open_port(p):
        if p in active_ports:
            return
        try:
            srv = await asyncio.start_server(
                lambda r, w, p=p: handle_user(r, w, p),
                "0.0.0.0",
                p,
                limit=BUFFER_SIZE
            )
            asyncio.create_task(srv.serve_forever())
            active_ports[p] = srv
            BeautifulUI.print_success(f"Port {p} opened")
        except Exception as e:
            logger.error(f"Failed to open port {p}: {e}")
    async def close_unused(new_ports):
        to_close = []
        for p, srv in list(active_ports.items()):
            if p not in new_ports:
                srv.close()
                await srv.wait_closed()
                to_close.append(p)
                BeautifulUI.print_warning(f"Port {p} closed")
        for p in to_close:
            del active_ports[p]
    async def handle_sync(reader, writer):
        try:
            client_auth = await asyncio.wait_for(
                reader.readexactly(32),
                timeout=CONN_TIMEOUT
            )
            if client_auth != auth:
                logger.warning("Invalid auth from sync")
                writer.close()
                return
            count_data = await asyncio.wait_for(
                reader.readexactly(2),
                timeout=CONN_TIMEOUT
            )
            count = struct.unpack("!H", count_data)[0]
            if count > 1000:
                logger.warning(f"Too many ports: {count}")
                writer.close()
                return
            ports = set()
            for _ in range(count):
                port_data = await asyncio.wait_for(
                    reader.readexactly(2),
                    timeout=CONN_TIMEOUT
                )
                p = struct.unpack("!H", port_data)[0]
                if validate_port(p):
                    ports.add(p)
                    await open_port(p)
            await close_unused(ports)
            logger.info(f"{Colors.GREEN}✓{Colors.END} Synced {len(ports)} ports")
        except asyncio.TimeoutError:
            logger.debug("Sync timeout")
        except Exception as e:
            logger.error(f"Sync error: {e}")
        finally:
            writer.close()
    print()
    BeautifulUI.print_success("🚀 BluTunnel Iran Starting...")
    print(f"  {Colors.SERVER} Bridge Port: {Colors.CYAN}{bridge_p}{Colors.END}")
    print(f"  {Colors.SERVER} Sync Port: {Colors.CYAN}{sync_p}{Colors.END}")
    print()
    bridge_server = await asyncio.start_server(
        handle_bridge, 
        "0.0.0.0", 
        bridge_p,
        limit=BUFFER_SIZE
    )
    sync_server = await asyncio.start_server(
        handle_sync,
        "0.0.0.0",
        sync_p,
        limit=BUFFER_SIZE
    )
    async def show_stats():
        while running:
            uptime = time.time() - start_time
            hours = int(uptime // 3600)
            minutes = int((uptime % 3600) // 60)
            seconds = int(uptime % 60)
            print(f"\r  {Colors.CYAN}⏱️ Uptime: {Colors.GREEN}{hours:02d}:{minutes:02d}:{seconds:02d}{Colors.END} {Colors.PING} Connections: {Colors.YELLOW}{connection_count}{Colors.END} {Colors.SERVER} Ports: {Colors.YELLOW}{len(active_ports)}{Colors.END}", end="")
            await asyncio.sleep(1)
    stats_task = asyncio.create_task(show_stats())
    try:
        async with bridge_server, sync_server:
            await asyncio.Future()
    except KeyboardInterrupt:
        print("\n")
        BeautifulUI.print_warning("Shutting down gracefully...")
        running = False
        stats_task.cancel()
        for srv in active_ports.values():
            srv.close()
            await srv.wait_closed()
        BeautifulUI.print_success("✅ Shutdown complete")

async def server_check():
    BeautifulUI.print_banner()
    BeautifulUI.print_section("Server Check", "🌍")
    host = BeautifulUI.input_with_style("Enter IP or Domain", "🔍")
    print()
    detector = ServerDetector()
    await detector.display_server_info(host)
    await detector.close()
    print()
    input(f"{Colors.GRAY}Press Enter to continue...{Colors.END}")

def handle_key_management(config):
    BeautifulUI.print_banner()
    BeautifulUI.print_section("Key Management", "🔑")
    print("  " + Colors.WHITE + "1) Generate Random KEY" + Colors.END)
    print("  " + Colors.WHITE + "2) Enter Custom KEY" + Colors.END)
    print()
    opt = BeautifulUI.input_with_style("Select", "🎯")
    if opt == "1":
        key = generate_key()
        BeautifulUI.print_success(f"Generated Key: {Colors.CYAN}{key}{Colors.END}")
    elif opt == "2":
        key = BeautifulUI.input_with_style("Enter KEY", "🔑")
        if len(key) < 8:
            BeautifulUI.print_error("KEY must be at least 8 characters")
            input(f"{Colors.GRAY}Press Enter...{Colors.END}")
            return
    else:
        BeautifulUI.print_error("Invalid option")
        input(f"{Colors.GRAY}Press Enter...{Colors.END}")
        return
    config["key"] = key
    save_config(config)
    BeautifulUI.print_success("KEY saved successfully!")
    input(f"{Colors.GRAY}Press Enter...{Colors.END}")

def handle_show_key(config):
    BeautifulUI.print_banner()
    BeautifulUI.print_section("Current KEY", "👁️")
    key = config.get("key", "Not Set")
    if key != "Not Set":
        print(f"  {Colors.KEY} {Colors.CYAN}{key}{Colors.END}")
    else:
        BeautifulUI.print_warning("No KEY set yet")
    print()
    input(f"{Colors.GRAY}Press Enter...{Colors.END}")

def main():
    try:
        optimize()
        while True:
            try:
                choice = BeautifulUI.show_menu()
                config = load_config()
                if choice == "1":
                    handle_key_management(config)
                elif choice == "2":
                    handle_show_key(config)
                elif choice == "3":
                    if "key" not in config:
                        BeautifulUI.print_error("Create KEY first")
                        input(f"{Colors.GRAY}Press Enter...{Colors.END}")
                        continue
                    asyncio.run(start_europe(config["key"]))
                elif choice == "4":
                    if "key" not in config:
                        BeautifulUI.print_error("Create KEY first")
                        input(f"{Colors.GRAY}Press Enter...{Colors.END}")
                        continue
                    asyncio.run(start_iran(config["key"]))
                elif choice == "5":
                    asyncio.run(server_check())
                elif choice == "6":
                    BeautifulUI.print_banner()
                    BeautifulUI.print_success("Goodbye! 👋")
                    sys.exit(0)
                else:
                    BeautifulUI.print_error("Invalid Option")
                    input(f"{Colors.GRAY}Press Enter...{Colors.END}")
            except KeyboardInterrupt:
                print("\n")
                BeautifulUI.print_success("Goodbye! 👋")
                sys.exit(0)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                input(f"{Colors.GRAY}Press Enter...{Colors.END}")
    except Exception as e:
        print(f"\033[91m❌ Fatal error: {e}\033[0m")
        sys.exit(1)

if __name__ == "__main__":
    main()
