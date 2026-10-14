#!/usr/bin/env python3
"""IAS-Viewer-Server backend — camera registry + web dashboard server.

- No default credentials anywhere: set IVS_API_TOKEN env var to protect
  the mutating API endpoints. Empty token = LAN-only trusted use.
- License: GNU AGPL-3.0 (see /api/license).
"""
import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException, Header
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE = Path(__file__).resolve().parent
CAM_FILE = Path(os.environ.get("IVS_CAMERAS", BASE / "cameras.json"))
WEB_DIR = BASE.parent / "web"
API_TOKEN = os.environ.get("IVS_API_TOKEN", "")
HLS_BASE = os.environ.get("IVS_HLS_BASE", "http://localhost:8888")

print("IAS-Viewer-Server backend starting — licensed under GNU AGPL-3.0; "
      "source: https://github.com/thaarfknight-star/IAS-Viewer-Server")

app = FastAPI(title="IAS-Viewer-Server")


class Camera(BaseModel):
    id: str
    name: str
    rtsp: str
    monitor: str = "mon1"


def load_cams() -> dict:
    if CAM_FILE.exists():
        return json.loads(CAM_FILE.read_text(encoding="utf-8"))
    return {"monitors": {"mon1": "monitor 1"}, "cameras": []}


def save_cams(data: dict) -> None:
    CAM_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def check_auth(authorization: str = "") -> None:
    if API_TOKEN and authorization != f"Bearer {API_TOKEN}":
        raise HTTPException(status_code=401, detail="unauthorized")


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/license")
def license_info():
    return {
        "license": "GNU Affero General Public License v3.0",
        "source": "https://github.com/thaarfknight-star/IAS-Viewer-Server",
        "note": "You are entitled to receive the complete source code of this "
                "running server (AGPL-3.0, section 13).",
    }


@app.get("/api/cameras")
def list_cameras():
    data = load_cams()
    data["hls_base"] = HLS_BASE
    return data


@app.post("/api/cameras")
def add_camera(cam: Camera, authorization: str = Header(default="")):
    check_auth(authorization)
    data = load_cams()
    if any(c["id"] == cam.id for c in data["cameras"]):
        raise HTTPException(status_code=409, detail="camera id already exists")
    data["cameras"].append(cam.model_dump())
    save_cams(data)
    return {"ok": True}


@app.delete("/api/cameras/{cam_id}")
def delete_camera(cam_id: str, authorization: str = Header(default="")):
    check_auth(authorization)
    data = load_cams()
    data["cameras"] = [c for c in data["cameras"] if c["id"] != cam_id]
    save_cams(data)
    return {"ok": True}


app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
