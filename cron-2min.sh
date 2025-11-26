#!/bin/bash
# Cron job script for 2-minute intervals
# Add this to your crontab: */2 * * * * /path/to/cron-2min.sh

cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null || python3 -m venv venv && source venv/bin/activate
pip install -q -r requirements.txt
python daily_tao_to_discord.py

