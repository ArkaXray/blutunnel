#!/usr/bin/env python3
import asyncio, os, socket, struct, resource, subprocess, logging

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

async def start_europe():
    iran_ip = input("Iran IP: ")
    bridge_p = int(input("Tunnel Bridge Port: "))
    sync_p = int(input("Port Sync Port: "))

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

async def start_iran():
    bridge_p = int(input("Tunnel Bridge Port: "))
    sync_p = int(input("Port Sync Port: "))
    is_auto = input("Auto-Sync Xray ports? (y/n): ").lower()=='y'
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
        manual_ports=input("Enter ports manually (80,443,2083): ").split(',')
        for p_str in manual_ports:
            if p_str.strip().isdigit(): await open_new_port(int(p_str.strip()))
        log("Manual Ports Opened.")

    await asyncio.Event().wait()

if __name__=="__main__":
    optimize_system()
    print("1) Europe Server\n2) Iran Server")
    choice=input("Choice: ")
    if choice=='1': asyncio.run(start_europe())
    else: asyncio.run(start_iran())
