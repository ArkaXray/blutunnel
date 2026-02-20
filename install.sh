#!/bin/bash
echo "🔵 Installing BluTunnel..."
apt update > /dev/null 2>&1
apt install python3 python3-pip -y > /dev/null 2>&1
pip3 install aiohttp > /dev/null 2>&1
echo "✅ Installation complete!"
python3 blutunnel.py