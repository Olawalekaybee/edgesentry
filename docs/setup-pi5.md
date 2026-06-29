# Pi 5 + Hailo-8L Setup Guide

Step-by-step instructions for setting up EdgeSentry on your Raspberry Pi 5 with
a Hailo-8L NPU, connecting over SSH from VS Code.

---

## Prerequisites

| Component | Spec |
|-----------|------|
| Raspberry Pi 5 | 4 GB or 8 GB RAM |
| Storage | 128 GB microSD or NVMe SSD |
| Hailo-8L M.2 module | on M.2 HAT or similar carrier |
| Camera | PiCamera Module 3, or USB webcam |
| Network | WiFi or Ethernet (for SSH access + one-time setup) |
| Power | 27 W USB-C PD supply (official Pi 5 PSU recommended) |

## 1. Flash Raspberry Pi OS

Use [Raspberry Pi Imager](https://www.raspberrypi.com/software/) to flash
**Raspberry Pi OS (64-bit, Bookworm)** to your microSD/SSD. In the settings,
enable SSH and set a username/password.

## 2. Connect via VS Code Remote-SSH

1. Install the **Remote - SSH** extension in VS Code.
2. Open the command palette → `Remote-SSH: Connect to Host`.
3. Enter `<username>@<pi-ip>` (find the IP with `hostname -I` on the Pi).
4. VS Code opens a remote session. All terminals and file editing now happen
   directly on the Pi.

## 3. Install the Hailo runtime

```bash
# Add the Hailo APT repo (see Hailo developer docs for the latest URL)
sudo apt update
sudo apt install -y hailort hailort-driver

# Verify the NPU is detected
hailortcli scan
# Should show: Hailo-8L device
```

## 4. Install Ollama

```bash
curl -fsSL https://ollama.com/install.sh | sh

# Pull the EdgeSentry model
ollama pull qwen2.5:3b-instruct

# Quick test
ollama run qwen2.5:3b-instruct "Say hello in one sentence."
```

## 5. Clone and install EdgeSentry

```bash
git clone https://github.com/<you>/edgesentry.git
cd edgesentry

# Virtual env with system site-packages (for hailort)
python3 -m venv --system-site-packages .venv
source .venv/bin/activate

pip install -r requirements.txt
```

## 6. Configure

```bash
cp .env.example .env
nano .env   # add your Telegram bot token + chat ID
```

Review `config/config.yaml` — update zone polygons, camera source, and model
paths to match your setup.

## 7. Add model files

Copy your v1 `.hef` model files into the `models/` directory:

```bash
cp /path/to/yolov8n.hef models/
cp /path/to/reid_resnet.hef models/
```

## 8. Test without hardware first

```bash
# Seed fake events
python scripts/seed_demo_data.py

# Run web + agent only (no camera or Hailo needed)
python -m edgesentry --no-perception
```

Open `http://<pi-ip>:8000` in your browser. Try the chat.

## 9. Run with full perception

```bash
python -m edgesentry
```

The dashboard shows the live feed, the chat box is active, and the journaler
starts running every hour.

## 10. (Optional) Run on boot via systemd

```bash
sudo tee /etc/systemd/system/edgesentry.service << 'EOF'
[Unit]
Description=EdgeSentry — Agentic RAG Security
After=network.target ollama.service

[Service]
Type=simple
User=<your-username>
WorkingDirectory=/home/<your-username>/edgesentry
ExecStart=/home/<your-username>/edgesentry/.venv/bin/python -m edgesentry
Restart=always
RestartSec=5
Environment=PATH=/home/<your-username>/edgesentry/.venv/bin:/usr/bin

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now edgesentry
```

## 11. Run benchmarks for your README / video

```bash
python scripts/benchmark.py
```

This prints a markdown table of latencies you can paste into the README or show
on screen in your YouTube video.
