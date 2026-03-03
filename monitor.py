import psutil
import requests
import time
import os
import datetime
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

# --- CONFIGURATION ---
WEBHOOK_URL = "https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN"
MONITOR_NICKNAME = "Drilex-VPS"  # Set your custom nickname here
ID_FILE = f"/tmp/drilex_{MONITOR_NICKNAME}_id.txt"
INTERVAL = 30 
HEADERS = {"User-Agent": f"DrilexMonitor/1.1 ({MONITOR_NICKNAME})"}

def get_size(bytes):
    for unit in ['', 'K', 'M', 'G', 'T']:
        if bytes < 1024: return f"{bytes:.1f}{unit}B"
        bytes /= 1024

def get_stats():
    cpu_total = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    boot_time = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M")
    load = os.getloadavg()

    n1 = psutil.net_io_counters()
    time.sleep(1)
    n2 = psutil.net_io_counters()
    up_speed = (n2.bytes_sent - n1.bytes_sent)
    down_speed = (n2.bytes_recv - n1.bytes_recv)

    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
        try:
            pinfo = proc.info
            pinfo['rss'] = pinfo['memory_info'].rss if pinfo['memory_info'] else 0
            try:
                pinfo['out_conn'] = len(proc.net_connections(kind='inet'))
            except:
                pinfo['out_conn'] = 0
            processes.append(pinfo)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    top_cpu = sorted(processes, key=lambda x: x['cpu_percent'], reverse=True)[:5]
    top_ram = sorted(processes, key=lambda x: x['rss'], reverse=True)[:5]
    top_net = sorted(processes, key=lambda x: x['out_conn'], reverse=True)[:3]

    cpu_t = "PID    | CPU%  | NAME\n" + "\n".join([f"{str(p['pid']).ljust(6)} | {str(p['cpu_percent']).ljust(5)} | {str(p['name'])[:12]}" for p in top_cpu])
    ram_t = "PID    | RAM   | NAME\n" + "\n".join([f"{str(p['pid']).ljust(6)} | {get_size(p['rss']).ljust(5)} | {str(p['name'])[:12]}" for p in top_ram])
    net_t = "PID    | CONN  | NAME (Active)\n" + "\n".join([f"{str(p['pid']).ljust(6)} | {str(p['out_conn']).ljust(5)} | {str(p['name'])[:12]}" for p in top_net])

    return {
        "cpu": cpu_total, "ram": ram.percent, "disk": disk.percent,
        "up": get_size(up_speed), "down": get_size(down_speed),
        "cpu_t": cpu_t, "ram_t": ram_t, "net_t": net_t,
        "boot": boot_time, "load": f"{load[0]}, {load[1]}, {load[2]}"
    }

def run():
    msg_id = None
    if os.path.exists(ID_FILE):
        with open(ID_FILE, "r") as f: msg_id = f.read().strip()

    print(f"🚀 [{MONITOR_NICKNAME}] Drilex Monitor Started ({INTERVAL}s interval)")

    while True:
        try:
            d = get_stats()
            payload = {
                "username": f"Drilex Monitor [{MONITOR_NICKNAME}]",
                "embeds": [{
                    "title": f"🛰️ {MONITOR_NICKNAME} - GLOBAL STATUS",
                    "color": 3066993 if d['cpu'] < 80 else 15158332,
                    "fields": [
                        {"name": "💻 System Info", "value": f"CPU: `{d['cpu']}%` | RAM: `{d['ram']}%` | Disk: `{d['disk']}%`"},
                        {"name": "📈 Load Average", "value": f"`{d['load']}`", "inline": True},
                        {"name": "⏱️ Uptime Since", "value": f"`{d['boot']}`", "inline": True},
                        {"name": "🌐 Network Speed", "value": f"⬆️ `{d['up']}/s` | ⬇️ `{d['down']}/s`", "inline": False},
                        {"name": "🔥 TOP 5 CPU", "value": f"```\n{d['cpu_t']}```", "inline": False},
                        {"name": "🧠 TOP 5 RAM", "value": f"```\n{d['ram_t']}```", "inline": False},
                        {"name": "📡 TOP 3 NET (Active Connections)", "value": f"```\n{d['net_t']}```", "inline": False}
                    ],
                    "footer": {"text": f"Node: {MONITOR_NICKNAME} • Last Sync: {time.strftime('%H:%M:%S')}"}
                }]
            }

            if not msg_id:
                r = requests.post(f"{WEBHOOK_URL}?wait=True", json=payload, headers=HEADERS)
                if r.status_code in [200, 201]:
                    msg_id = r.json()['id']
                    with open(ID_FILE, "w") as f: f.write(msg_id)
            else:
                r = requests.patch(f"{WEBHOOK_URL}/messages/{msg_id}", json=payload, headers=HEADERS)
                if r.status_code == 404:
                    msg_id = None
                    if os.path.exists(ID_FILE): os.remove(ID_FILE)
                elif r.status_code == 429:
                    print(f"⚠️ [{MONITOR_NICKNAME}] Rate Limited. Waiting 60s...")
                    time.sleep(60)
                else:
                    print(f"✅ [{MONITOR_NICKNAME}] Heartbeat sent.")

        except Exception as e:
            print(f"❌ [{MONITOR_NICKNAME}] Error: {e}")
        
        time.sleep(INTERVAL - 2)

if __name__ == "__main__":
    run()