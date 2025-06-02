# Logs i utilitats diverses
# utils/logger.py

import datetime

def info(msg: str):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[INFO {now}] {msg}")

def error(msg: str):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[ERROR {now}] {msg}")

def debug(msg: str):
    now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[DEBUG {now}] {msg}")
