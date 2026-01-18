#!/bin/bash
# Claude Desktop Bridge - Tek komutla başlat

cd "$(dirname "$0")"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

python bridge.py
