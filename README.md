<div align="center">

```
  ██╗  ██╗███████╗██╗     ██╗ ██████╗ ███████╗
  ██║  ██║██╔════╝██║     ██║██╔═══██╗██╔════╝
  ███████║█████╗  ██║     ██║██║   ██║███████╗
  ██╔══██║██╔══╝  ██║     ██║██║   ██║╚════██║
  ██║  ██║███████╗███████╗██║╚██████╔╝███████║
  ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝ ╚═════╝ ╚══════╝
```

**☀ Network Intelligence Monitor**

**Python 3.6+** | **Linux** | **MIT License**

*Illuminate your network. See everything.*

</div>

---

## Overview

HELIOS is a terminal-based network monitoring tool for Linux. It gives you a real-time view of your network interfaces, active connections, open ports, and latency — all in a clean, color-coded CLI dashboard.

Inspired by [Pulsar](https://github.com/your-pulsar-link), HELIOS focuses purely on network intelligence.

---

## Features

| Feature | Command |
|---|---|
| Full dashboard | `helios` |
| Ping / latency monitor | `helios --ping` |
| Active connections (netstat-style) | `helios --conns` |
| Port scanner | `helios --scan <HOST>` |
| Network interfaces + bandwidth | `helios --ifaces` |
| Real-time bandwidth monitor | `helios --live` |
| Public IP lookup | `helios --pubip` |

---

## Preview

```
  ██╗  ██╗███████╗██╗     ██╗ ██████╗ ███████╗
  ...
        ☀  Network Intelligence Monitor  ☀

  Hostname : mypc
  Local IP : 192.168.1.100
  Time     : 2026-05-09 19:16:38

────────────── Network Interfaces & Bandwidth ──────────────

  ● ens160  10000 Mbps
    IPv4: 192.168.1.100  mask: 255.255.255.0
    ↑ Sent:      8.1 MB  (69,974 pkts)
    ↓ Recv:    238.6 MB  (195,049 pkts)

────────────── Ping / Latency Monitor ──────────────

  Target          Host              Latency
  Google DNS      8.8.8.8           4.2 ms    ● online  ████████░░░░ 98%
  Cloudflare      1.1.1.1           3.8 ms    ● online  ████████░░░░ 98%
  GitHub          github.com        18.1 ms   ● online  ██████░░░░░░ 94%

────────────── Active Connections ──────────────

  TCP   192.168.1.100:52341   142.250.74.46:443    ESTABLISHED
  TCP   0.0.0.0:22            0.0.0.0:*            LISTEN
  ...
```

---

## Requirements

- Linux (Ubuntu, Debian, Arch, Fedora, etc.)
- Python 3.6+
- `psutil` — installed automatically

---

## Installation

**One-liner install:**

```bash
curl -fsSL https://raw.githubusercontent.com/yourusername/helios/main/install.sh | bash
```

Or if you prefer to inspect before running:

```bash
curl -fsSL https://raw.githubusercontent.com/yourusername/helios/main/install.sh -o install.sh
bash install.sh
```

That's it. The installer will:

1. Check for Python 3
2. Install `psutil` if missing
3. Copy `helios` to `/usr/local/bin` so it's available system-wide

**Verify:**

```bash
helios --help
```

---

## Usage

```bash
# Full dashboard
helios

# Ping default targets (Google DNS, Cloudflare, GitHub)
helios --ping

# Ping custom hosts (adds to default list)
helios --ping github.com 192.168.1.1 8.8.4.4

# Active connections
helios --conns

# Filter by status
helios --conns --status ESTABLISHED
helios --conns --status LISTEN

# Limit results
helios --conns --limit 50

# Scan common ports on a host
helios --scan 192.168.1.1

# Scan a custom port range
helios --scan 192.168.1.1 --ports 1-1024

# Scan all ports 1-1024
helios --scan localhost --all-ports

# Network interfaces + bandwidth stats
helios --ifaces

# Real-time upload/download monitor
helios --live

# Show public IP
helios --pubip

# Help
helios --help
```

---

## Connection States

| State | Meaning |
|---|---|
| 🟢 `ESTABLISHED` | Active connection with data flowing |
| 🟡 `LISTEN` | Port waiting for incoming connections |
| ⚫ `TIME_WAIT` | Connection waiting to close |
| 🔴 `CLOSE_WAIT` | Remote side closed, waiting locally |
| 🔵 `SYN_SENT` | Connection attempt in progress |

---

## Uninstall

```bash
bash install.sh --uninstall
```

---

## Disclaimer

HELIOS is provided for educational and personal use only. The authors take no responsibility for any misuse, damage, or legal issues arising from the use of this tool. Port scanning and network monitoring may be restricted or illegal on networks you do not own or have explicit permission to test. Always ensure you have proper authorization before scanning any network or host. Use at your own risk.

---

## License

MIT — do whatever you want with it.

---

<div align="center">
<sub>Built with ☀ — part of the <strong>Pulsar</strong> tools family</sub>
</div>
