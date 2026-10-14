#!/usr/bin/env python3
"""Generate mediamtx.yml `paths:` from backend/cameras.json.

Usage: python3 tools/gen_mediamtx.py
Reads backend/cameras.json (or backend/cameras.json.example as fallback)
and writes mediamtx.yml next to this repo root, preserving the static
header already present in mediamtx.yml.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAM_FILE = ROOT / "backend" / "cameras.json"
if not CAM_FILE.exists():
    CAM_FILE = ROOT / "backend" / "cameras.json.example"
OUT = ROOT / "mediamtx.yml"

data = json.loads(CAM_FILE.read_text(encoding="utf-8"))

lines = ["paths:"]
for cam in data.get("cameras", []):
    cid = re.sub(r"[^a-zA-Z0-9_-]", "_", cam["id"])
    lines.append(f"  {cid}:")
    lines.append(f"    source: {cam['rtsp']}")

text = OUT.read_text(encoding="utf-8")
# Replace everything from the first "paths:" line to end of file.
head = text.split("paths:")[0].rstrip() + "\n\n"
OUT.write_text(head + "\n".join(lines) + "\n", encoding="utf-8")
print(f"wrote {OUT} with {len(data.get('cameras', []))} paths")
