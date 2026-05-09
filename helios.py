#!/usr/bin/env python3

import os
import sys
import time
import socket
import subprocess
import threading
import argparse
from datetime import datetime

try:
    import psutil
except ImportError:
    print("Installing psutil...")
    os.system(f"{sys.executable} -m pip install psutil -q")
    import psutil

# ─── ANSI Colors ───────────────────────────────────────────────────────────────
R  = "\033[0m"
BD = "\033[1m"
DIM= "\033[2m"

CYAN   = "\033[96m"
BLUE   = "\033[94m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
MAGENTA= "\033[95m"
WHITE  = "\033[97m"
GRAY   = "\033[90m"

BG_DARK = "\033[48;5;234m"

# ─── ASCII Banner ───────────────────────────────────────────────────────────────
BANNER = f"""{YELLOW}{BD}
  ██╗  ██╗███████╗██╗     ██╗ ██████╗ ███████╗
  ██║  ██║██╔════╝██║     ██║██╔═══██╗██╔════╝
  ███████║█████╗  ██║     ██║██║   ██║███████╗
  ██╔══██║██╔══╝  ██║     ██║██║   ██║╚════██║
  ██║  ██║███████╗███████╗██║╚██████╔╝███████║
  ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝ ╚═════╝ ╚══════╝{R}
{YELLOW}        ☀  {GRAY}Network Intelligence Monitor  {YELLOW}☀{R}
"""

# ─── Helpers ───────────────────────────────────────────────────────────────────
def clear():
    os.system("clear" if os.name != "nt" else "cls")

def bar(pct, width=20, color=GREEN):
    filled = int(width * pct / 100)
    empty  = width - filled
    return f"{color}{'█' * filled}{GRAY}{'░' * empty}{R}"

def section(title, color=CYAN):
    w = 60
    line = "─" * ((w - len(title) - 2) // 2)
    print(f"\n{color}{line} {BD}{title}{R}{color} {line}{R}")

def table_row(cols, widths, colors=None):
    parts = []
    for i, (col, w) in enumerate(zip(cols, widths)):
        c = colors[i] if colors and i < len(colors) else WHITE
        parts.append(f"{c}{str(col):<{w}}{R}")
    print("  " + "  ".join(parts))

def table_header(cols, widths):
    parts = [f"{GRAY}{BD}{str(c):<{w}}{R}" for c, w in zip(cols, widths)]
    print("  " + "  ".join(parts))
    print(f"  {GRAY}{'─' * (sum(widths) + len(widths)*2)}{R}")

# ─── Network Info ──────────────────────────────────────────────────────────────
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "N/A"

def get_hostname():
    return socket.gethostname()

def get_public_ip():
    try:
        result = subprocess.run(
            ["curl", "-s", "--max-time", "3", "https://api.ipify.org"],
            capture_output=True, text=True
        )
        return result.stdout.strip() or "N/A"
    except:
        return "N/A"

# ─── Ping Monitor ──────────────────────────────────────────────────────────────
PING_TARGETS = [
    ("Google DNS",    "8.8.8.8"),
    ("Cloudflare",    "1.1.1.1"),
    ("Google",        "google.com"),
    ("GitHub",        "github.com"),
]

def ping_host(host, count=3):
    try:
        result = subprocess.run(
            ["ping", "-c", str(count), "-W", "2", host],
            capture_output=True, text=True, timeout=10
        )
        output = result.stdout
        for line in output.split("\n"):
            if "min/avg/max" in line or "rtt" in line:
                parts = line.split("=")[-1].strip().split("/")
                if len(parts) >= 2:
                    avg = float(parts[1])
                    return avg, "online"
        if result.returncode == 0:
            return 0.0, "online"
        return None, "offline"
    except:
        return None, "error"

def latency_color(ms):
    if ms is None: return RED
    if ms < 30:    return GREEN
    if ms < 80:    return YELLOW
    return RED

def show_ping(extra_hosts=None):
    section("Ping / Latency Monitor", YELLOW)
    targets = list(PING_TARGETS)
    if extra_hosts:
        for h in extra_hosts:
            name = h if len(h) <= 14 else h[:13] + "…"
            targets.append((name, h))
    print(f"\n  {GRAY}Pinging {len(targets)} targets (3 packets each)...{R}\n")
    table_header(["Target", "Host", "Latency", "Status", "Quality"], [14, 16, 10, 10, 20])

    for name, host in targets:
        ms, status = ping_host(host)
        lc = latency_color(ms)
        ms_str = f"{ms:.1f} ms" if ms is not None else "timeout"
        qual_pct = max(0, 100 - int((ms or 300) * 0.3)) if status == "online" else 0
        qual_bar = bar(qual_pct, 12, lc)
        status_str = f"{GREEN}● online{R}" if status == "online" else f"{RED}✗ offline{R}"
        table_row(
            [name, host, ms_str, "", ""],
            [14, 16, 10, 10, 20],
            [WHITE, GRAY, lc, WHITE, WHITE]
        )
        print(f"  {' '*14}  {' '*16}  {' '*10}  {status_str}  {qual_bar} {GRAY}{qual_pct}%{R}")

# ─── Active Connections ────────────────────────────────────────────────────────
PROTO_COLORS = {
    "tcp":  BLUE,
    "udp":  MAGENTA,
    "tcp6": CYAN,
    "udp6": YELLOW,
}

STATUS_COLORS = {
    "ESTABLISHED": GREEN,
    "LISTEN":      YELLOW,
    "TIME_WAIT":   GRAY,
    "CLOSE_WAIT":  RED,
    "SYN_SENT":    CYAN,
    "FIN_WAIT1":   GRAY,
    "FIN_WAIT2":   GRAY,
}

def show_connections(limit=20, filter_status=None):
    section("Active Connections (netstat)", BLUE)
    conns = psutil.net_connections(kind="inet")

    if filter_status:
        conns = [c for c in conns if c.status == filter_status]

    # Sort: ESTABLISHED first, then LISTEN
    order = {"ESTABLISHED": 0, "LISTEN": 1}
    conns.sort(key=lambda c: (order.get(c.status, 9), c.status))

    stats = {}
    for c in conns:
        stats[c.status] = stats.get(c.status, 0) + 1

    print(f"\n  {GRAY}Total: {WHITE}{BD}{len(conns)}{R} connections  ", end="")
    for st, cnt in sorted(stats.items()):
        col = STATUS_COLORS.get(st, WHITE)
        print(f"  {col}{st}{R}: {BD}{cnt}{R}", end="")
    print(f"\n")

    table_header(["Proto", "Local Address", "Remote Address", "Status", "PID"], [7, 22, 22, 13, 8])

    shown = 0
    for c in conns:
        if shown >= limit: break
        proto = c.type.name.lower() if hasattr(c.type, "name") else str(c.type)
        proto = "tcp" if "SOCK_STREAM" in proto.upper() else "udp"

        laddr = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "-"
        raddr = f"{c.raddr.ip}:{c.raddr.port}" if c.raddr else "-"
        status = c.status or "-"
        pid = str(c.pid) if c.pid else "-"

        pc = PROTO_COLORS.get(proto, WHITE)
        sc = STATUS_COLORS.get(status, GRAY)

        table_row(
            [proto.upper(), laddr, raddr, status, pid],
            [7, 22, 22, 13, 8],
            [pc, WHITE, CYAN, sc, GRAY]
        )
        shown += 1

    if len(conns) > limit:
        print(f"\n  {GRAY}... and {len(conns) - limit} more. Use --limit to show more.{R}")

# ─── Port Scanner ──────────────────────────────────────────────────────────────
COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP",
    53: "DNS", 80: "HTTP", 110: "POP3", 143: "IMAP",
    443: "HTTPS", 445: "SMB", 3306: "MySQL", 3389: "RDP",
    5432: "PostgreSQL", 6379: "Redis", 8080: "HTTP-Alt",
    8443: "HTTPS-Alt", 27017: "MongoDB", 5000: "Dev",
    8000: "Dev", 9200: "Elasticsearch", 11211: "Memcached",
}

scan_results = []
scan_lock = threading.Lock()

def scan_port(host, port, timeout=0.5):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        result = s.connect_ex((host, port))
        s.close()
        if result == 0:
            with scan_lock:
                scan_results.append(port)
    except:
        pass

def show_port_scan(target="127.0.0.1", port_range=None, common_only=True):
    section("Port Scanner", MAGENTA)

    if port_range:
        start, end = port_range
        ports = list(range(start, end + 1))
        print(f"\n  {GRAY}Scanning {WHITE}{BD}{target}{R} {GRAY}ports {start}-{end}...{R}")
    elif common_only:
        ports = list(COMMON_PORTS.keys())
        print(f"\n  {GRAY}Scanning {WHITE}{BD}{target}{R} {GRAY}({len(ports)} common ports)...{R}")
    else:
        ports = list(range(1, 1025))
        print(f"\n  {GRAY}Scanning {WHITE}{BD}{target}{R} {GRAY}ports 1-1024...{R}")

    global scan_results
    scan_results = []

    threads = []
    for port in ports:
        t = threading.Thread(target=scan_port, args=(target, port), daemon=True)
        threads.append(t)
        t.start()
        if len(threads) % 100 == 0:
            print(f"  {GRAY}Progress: {len(threads)}/{len(ports)} ports...{R}", end="\r")

    for t in threads:
        t.join()

    open_ports = sorted(scan_results)
    print(f"  {' ' * 50}", end="\r")  # clear progress line

    if not open_ports:
        print(f"\n  {YELLOW}No open ports found.{R}")
        return

    print(f"\n  {GREEN}{BD}{len(open_ports)}{R} open ports found:\n")
    table_header(["Port", "Service", "Status"], [8, 20, 12])
    for port in open_ports:
        svc = COMMON_PORTS.get(port, "Unknown")
        table_row(
            [str(port), svc, "● OPEN"],
            [8, 20, 12],
            [CYAN, WHITE, GREEN]
        )

# ─── Network Interfaces ────────────────────────────────────────────────────────
def show_interfaces():
    section("Network Interfaces & Bandwidth", GREEN)
    stats = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()
    io    = psutil.net_io_counters(pernic=True)

    print()
    for iface, st in stats.items():
        if not st.isup:
            continue
        speed_str = f"{st.speed} Mbps" if st.speed else "N/A"
        status_col = GREEN if st.isup else RED
        print(f"  {status_col}●{R} {WHITE}{BD}{iface}{R}  {GRAY}{speed_str}{R}")

        # IPs
        if iface in addrs:
            for addr in addrs[iface]:
                if addr.family == socket.AF_INET:
                    print(f"    {GRAY}IPv4: {CYAN}{addr.address}{R}  {GRAY}mask: {addr.netmask}{R}")
                elif addr.family == socket.AF_INET6:
                    print(f"    {GRAY}IPv6: {BLUE}{addr.address}{R}")

        # IO Stats
        if iface in io:
            nic = io[iface]
            sent = nic.bytes_sent / 1024 / 1024
            recv = nic.bytes_recv / 1024 / 1024
            pkts_s = nic.packets_sent
            pkts_r = nic.packets_recv
            errs   = nic.errin + nic.errout
            print(f"    {GRAY}↑ Sent: {GREEN}{sent:>8.1f} MB{R}  {GRAY}({pkts_s:,} pkts){R}")
            print(f"    {GRAY}↓ Recv: {CYAN}{recv:>8.1f} MB{R}  {GRAY}({pkts_r:,} pkts){R}")
            if errs:
                print(f"    {GRAY}Errors: {RED}{errs}{R}")
        print()

# ─── Live Monitor ──────────────────────────────────────────────────────────────
def live_monitor(interval=2):
    prev_io = psutil.net_io_counters()
    prev_time = time.time()

    print(f"\n  {GRAY}Live monitor active. Press {WHITE}Ctrl+C{GRAY} to exit.{R}\n")
    print(f"  {GRAY}{'─' * 56}{R}")
    print(f"  {GRAY}{'Time':<10} {'↑ Upload':>12} {'↓ Download':>12} {'Conns':>8}{R}")
    print(f"  {GRAY}{'─' * 56}{R}")

    try:
        while True:
            time.sleep(interval)
            now_io   = psutil.net_io_counters()
            now_time = time.time()
            elapsed  = now_time - prev_time

            up_bps   = (now_io.bytes_sent - prev_io.bytes_sent) / elapsed
            down_bps = (now_io.bytes_recv - prev_io.bytes_recv) / elapsed

            def fmt(bps):
                if bps > 1_000_000: return f"{bps/1_000_000:.1f} MB/s"
                if bps > 1_000:     return f"{bps/1_000:.1f} KB/s"
                return f"{bps:.0f} B/s"

            conns = len(psutil.net_connections())
            ts    = datetime.now().strftime("%H:%M:%S")
            up_col   = RED if up_bps > 500_000 else GREEN
            down_col = RED if down_bps > 2_000_000 else CYAN

            print(f"  {GRAY}{ts:<10}{R} {up_col}{fmt(up_bps):>12}{R} {down_col}{fmt(down_bps):>12}{R} {WHITE}{conns:>8}{R}")

            prev_io   = now_io
            prev_time = now_time
    except KeyboardInterrupt:
        print(f"\n\n  {GRAY}Live monitor stopped.{R}")

# ─── Summary Dashboard ─────────────────────────────────────────────────────────
def show_dashboard():
    clear()
    print(BANNER)

    # Host info
    hostname  = get_hostname()
    local_ip  = get_local_ip()
    ts        = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print(f"  {GRAY}Hostname : {WHITE}{BD}{hostname}{R}")
    print(f"  {GRAY}Local IP : {CYAN}{BD}{local_ip}{R}")
    print(f"  {GRAY}Time     : {GRAY}{ts}{R}")

    show_interfaces()
    show_ping()
    show_connections(limit=15)
    show_port_scan(target="127.0.0.1")

    print(f"\n  {GRAY}{'─' * 60}{R}")
    print(f"  {GRAY}Press {WHITE}Ctrl+C{GRAY} to exit  •  Run with {WHITE}--help{GRAY} for more options{R}\n")

# ─── Help Screen ───────────────────────────────────────────────────────────────
def show_help():
    clear()
    print(BANNER)

    W = 62

    def hline():
        print(f"  {GRAY}{'─' * W}{R}")

    def cmd(flag, args_hint, desc, example=None):
        flag_str  = f"{YELLOW}{BD}{flag}{R}"
        args_str  = f"{CYAN}{args_hint}{R}" if args_hint else ""
        desc_str  = f"{WHITE}{desc}{R}"
        print(f"  {flag_str} {args_str}")
        print(f"    {GRAY}{desc_str}{R}")
        if example:
            print(f"    {GRAY}↳ {DIM}{example}{R}")
        print()

    print(f"  {GRAY}{'─' * W}{R}")
    print(f"  {YELLOW}{BD}  HELIOS — Network Intelligence Monitor{R}")
    print(f"  {GRAY}  Illuminate your network. See everything.{R}")
    print(f"  {GRAY}{'─' * W}{R}\n")

    # ── Modes
    print(f"  {YELLOW}☀  MODES{R}\n")

    cmd("helios",        "",
        "Full dashboard — interfaces + ping + connections + port scan",
        "helios")

    cmd("--ping",        "[HOST ...]",
        "Latency monitor — pings default targets + any hosts you add",
        "helios --ping github.com 192.168.1.1")

    cmd("--conns",       "[--limit N] [--status STATUS]",
        "Active connections (netstat-style)",
        "helios --conns --status ESTABLISHED --limit 30")

    cmd("--scan",        "<HOST>",
        "Port scanner — detect open ports on a target host",
        "helios --scan 192.168.1.1")

    cmd("--ifaces",      "",
        "Network interfaces + bandwidth stats",
        "helios --ifaces")

    cmd("--live",        "",
        "Real-time upload/download speed monitor",
        "helios --live")

    cmd("--pubip",       "",
        "Show your public (external) IP address",
        "helios --pubip")

    # ── Options
    hline()
    print(f"\n  {YELLOW}⚙  OPTIONS{R}\n")

    cmd("--ports",       "<START-END>",
        "Use with --scan: scan a custom port range",
        "helios --scan 10.0.0.1 --ports 1-1024")

    cmd("--all-ports",   "",
        "Use with --scan: scan ports 1-1024 instead of common ports only",
        "helios --scan localhost --all-ports")

    cmd("--limit",       "<N>",
        "Use with --conns: max connections to display (default: 20)",
        "helios --conns --limit 50")

    cmd("--status",      "<STATUS>",
        "Use with --conns: filter connections by status",
        "helios --conns --status LISTEN")

    # ── Connection states reference
    hline()
    print(f"\n  {YELLOW}◈  CONNECTION STATES{R}\n")
    statuses = [
        ("ESTABLISHED", GREEN,  "Active connection with data flowing"),
        ("LISTEN",      YELLOW, "Port waiting for incoming connections"),
        ("TIME_WAIT",   GRAY,   "Connection waiting to close"),
        ("CLOSE_WAIT",  RED,    "Remote side closed, waiting locally"),
        ("SYN_SENT",    CYAN,   "Connection attempt in progress"),
    ]
    for st, col, desc in statuses:
        print(f"  {col}●{R} {WHITE}{BD}{st:<15}{R}  {GRAY}{desc}{R}")

    print()
    hline()
    print(f"  {GRAY}  Exit: {WHITE}Ctrl+C{R}")
    print(f"  {GRAY}{'─' * W}{R}\n")


# ─── CLI Entry ─────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--ping",      nargs="*", metavar="HOST")
    parser.add_argument("--conns",     action="store_true")
    parser.add_argument("--scan",      metavar="HOST", nargs="?", const="127.0.0.1")
    parser.add_argument("--ports",     metavar="START-END")
    parser.add_argument("--all-ports", action="store_true")
    parser.add_argument("--live",      action="store_true")
    parser.add_argument("--ifaces",    action="store_true")
    parser.add_argument("--limit",     type=int, default=20)
    parser.add_argument("--status",    metavar="STATUS")
    parser.add_argument("--pubip",     action="store_true")
    parser.add_argument("--help", "-h", action="store_true")

    args = parser.parse_args()

    if args.help:
        show_help()
        return

    clear()
    print(BANNER)

    if args.pubip:
        print(f"  {GRAY}Fetching public IP...{R}")
        pub = get_public_ip()
        print(f"  {GRAY}Public IP: {WHITE}{BD}{pub}{R}\n")
        return

    if args.live:
        show_interfaces()
        live_monitor()
        return

    if args.ping is not None:
        show_ping(extra_hosts=args.ping if args.ping else None)
        print()
        return

    if args.ifaces:
        show_interfaces()
        return

    if args.conns:
        show_connections(limit=args.limit, filter_status=args.status)
        print()
        return

    if args.scan is not None:
        target = args.scan if args.scan else "127.0.0.1"
        port_range = None
        if args.ports:
            try:
                s, e = args.ports.split("-")
                port_range = (int(s), int(e))
            except:
                print(f"  {RED}Invalid port range. Use format: 1-1024{R}\n")
                sys.exit(1)
        show_port_scan(target=target, port_range=port_range, common_only=not args.all_ports)
        print()
        return

    # Default: full dashboard
    show_dashboard()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {GRAY}HELIOS terminated.{R}\n")
        sys.exit(0)
