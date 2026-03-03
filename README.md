# Drilex Monitor

A lightweight Python-based VPS monitoring system that sends real-time hardware and process statistics to a Discord channel via Webhooks.

### Features
* **Live Dashboard:** Edits a single message to keep the channel clean.
* **Hardware Stats:** CPU, RAM, Disk, and Load Average.
* **Network Monitoring:** Total UP/DOWN speeds + Active connections per process.
* **Top Lists:** Real-time TOP 5 processes by CPU/RAM and TOP 3 by Network activity.
* **Anti-RateLimit:** Includes custom headers and error handling for Discord/Cloudflare.

### Installation
1. Install dependencies: `pip install -r requirements.txt`
2. Update `WEBHOOK_URL` & `MONITOR_NICKNAME` in `monitor.py`.
3. Run as a background process: `screen -S drilex-monitor python3 monitor.py`