#!/usr/bin/env python3
import argparse
import asyncio
import logging
import os
import resource
import socket
import struct
import subprocess

BUFFER_SIZE = 64*1024
OS_SOCK_BUFFER = 2*1024*1024
CON_COUNT = 500
LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "blutunnel.log")

os.makedirs(LOG_DIR, exist_ok=True)
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def log(msg):
    print(msg)
    logging.info(msg)


def parse_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y", "on"}

def optimize_system():
    try:
        resource.setrlimit(resource.RLIMIT_NOFILE, (1000000,1000000))
    except: pass

def tune_socket(writer):
    sock = writer.get_extra_info('socket')
    if sock:
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY,1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF,OS_SOCK_BUFFER)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF,OS_SOCK_BUFFER)

async def fast_pipe(reader, writer):
    try:
        while True:
            data = await reader.read(BUFFER_SIZE)
            if not data: break
            writer.write(data)
            await writer.drain()
    except: pass
    finally:
        writer.close()
        await writer.wait_closed()

async def start_europe(iran_ip, bridge_p, sync_p):

    def get_xray_ports():
        try:
            import re
            output = subprocess.check_output("ss -tlnp | grep 'xray-linu'", shell=True).decode()
            ports=set()
            for line in output.splitlines():
                if "127.0.0.1" in line or "::1" in line: continue
                found = re.findall(r'[:\]](\d+)\s+', line)
                for p in found:
                    p_num=int(p)
                    if p_num>100 and p_num!=bridge_p and p_num!=sync_p: ports.add(p_num)
            return ports
        except: return set()

    async def port_sync_task():
        while True:
            try:
                reader, writer = await asyncio.open_connection(iran_ip, sync_p)
                current_ports=list(get_xray_ports())
                data=struct.pack('!B',len(current_ports))
                for p in current_ports:
                    data+=struct.pack('!H',p)
                writer.write(data)
                await writer.drain()
                writer.close()
            except: pass
            await asyncio.sleep(3)

    async def create_reverse_link():
        while True:
            try:
                reader, writer = await asyncio.open_connection(iran_ip, bridge_p)
                tune_socket(writer)
                header = await reader.readexactly(2)
                target_port = struct.unpack('!H',header)[0]
                remote_reader, remote_writer = await asyncio.open_connection('127.0.0.1',target_port)
                tune_socket(remote_writer)
                await asyncio.gather(fast_pipe(reader,remote_writer),fast_pipe(remote_reader,writer),return_exceptions=True)
            except asyncio.CancelledError: break
            except: await asyncio.sleep(1)

    tasks=[asyncio.create_task(port_sync_task())]
    for _ in range(CON_COUNT):
        tasks.append(asyncio.create_task(create_reverse_link()))
    log(f"Running Europe Tunnel Sync:{sync_p} Bridge:{bridge_p}")
    await asyncio.Future()

async def start_iran(bridge_p, sync_p, is_auto, manual_ports):
    connection_pool=asyncio.Queue()
    active_servers={}

    async def handle_europe_bridge(reader, writer):
        tune_socket(writer)
        await connection_pool.put((reader,writer))

    async def handle_user_side(reader, writer, target_p):
        tune_socket(writer)
        try:
            e_reader, e_writer = await connection_pool.get()
            e_writer.write(struct.pack('!H',target_p))
            await e_writer.drain()
            await asyncio.gather(fast_pipe(reader,e_writer),fast_pipe(e_reader,writer),return_exceptions=True)
        except: writer.close()

    async def open_new_port(p):
        if p not in active_servers:
            try:
                srv = await asyncio.start_server(lambda r,w,p=p: handle_user_side(r,w,p),'0.0.0.0',p,backlog=5000)
                asyncio.create_task(srv.serve_forever())
                active_servers[p]=srv
                log(f"Port Active: {p}")
            except Exception as e: log(f"Error opening port {p}: {e}")

    async def handle_sync_conn(reader, writer):
        try:
            header = await reader.readexactly(1)
            count=struct.unpack('!B',header)[0]
            for _ in range(count):
                p_data=await reader.readexactly(2)
                p=struct.unpack('!H',p_data)[0]
                await open_new_port(p)
            writer.close()
        except: pass

    await asyncio.start_server(handle_europe_bridge,'0.0.0.0',bridge_p,backlog=10000)

    if is_auto:
        await asyncio.start_server(handle_sync_conn,'0.0.0.0',sync_p,backlog=100)
        log(f"Auto-Sync Active on port {sync_p}")
    else:
        for p_str in manual_ports:
            if p_str.strip().isdigit():
                await open_new_port(int(p_str.strip()))
        log("Manual Ports Opened.")

    await asyncio.Event().wait()

def build_args():
    parser = argparse.ArgumentParser(description="BluTunnel reverse tunnel")
    parser.add_argument("--mode", choices=["europe", "iran"], help="Run mode")
    parser.add_argument("--iran-ip", help="Iran server IP (required in europe mode)")
    parser.add_argument("--bridge-port", type=int, help="Tunnel bridge port")
    parser.add_argument("--sync-port", type=int, help="Port sync port")
    parser.add_argument("--auto-sync", help="Enable auto sync in iran mode: y/n")
    parser.add_argument("--manual-ports", default="", help="Comma-separated manual ports for iran mode")
    return parser.parse_args()


def interactive_config():
    print("1) Europe Server\n2) Iran Server")
    choice = input("Choice: ").strip()
    if choice == "1":
        return {
            "mode": "europe",
            "iran_ip": input("Iran IP: ").strip(),
            "bridge_port": int(input("Tunnel Bridge Port: ").strip()),
            "sync_port": int(input("Port Sync Port: ").strip()),
            "auto_sync": None,
            "manual_ports": [],
        }

    is_auto = input("Auto-Sync Xray ports? (y/n): ").strip().lower() == "y"
    manual_ports = []
    if not is_auto:
        manual_ports = [p.strip() for p in input("Enter ports manually (80,443,2083): ").split(",")]

    return {
        "mode": "iran",
        "iran_ip": None,
        "bridge_port": int(input("Tunnel Bridge Port: ").strip()),
        "sync_port": int(input("Port Sync Port: ").strip()),
        "auto_sync": is_auto,
        "manual_ports": manual_ports,
    }


def args_config(args):
    if not args.mode:
        return None
    if not args.bridge_port or not args.sync_port:
        raise ValueError("--bridge-port and --sync-port are required when --mode is set")
    if args.mode == "europe" and not args.iran_ip:
        raise ValueError("--iran-ip is required in europe mode")
    auto_sync = parse_bool(args.auto_sync) if args.auto_sync is not None else True
    manual_ports = [p.strip() for p in args.manual_ports.split(",") if p.strip()]
    return {
        "mode": args.mode,
        "iran_ip": args.iran_ip,
        "bridge_port": args.bridge_port,
        "sync_port": args.sync_port,
        "auto_sync": auto_sync,
        "manual_ports": manual_ports,
    }


if __name__=="__main__":
    optimize_system()
    args = build_args()
    try:
        config = args_config(args) or interactive_config()
    except Exception as e:
        raise SystemExit(f"Invalid arguments: {e}")

    if config["mode"] == "europe":
        asyncio.run(start_europe(config["iran_ip"], config["bridge_port"], config["sync_port"]))
    else:
        asyncio.run(start_iran(config["bridge_port"], config["sync_port"], config["auto_sync"], config["manual_ports"]))
