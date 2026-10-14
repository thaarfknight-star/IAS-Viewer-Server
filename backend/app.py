#!/usr/bin/env python3
"""IAS-Viewer-Server backend — camera registry, live status, events,
recordings browser, and the web dashboard.

- No default credentials anywhere: set IVS_API_TOKEN env var to protect
  the mutating API endpoints. Empty token = LAN-only trusted use.
- License: GNU AGPL-3.0 (see /api/license).
"""
import json
import os
import threading
import time
import urllib.request
from pathlib import Path

from fastapi import FastAPI, HTTPException, Header
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE = Path(__file__).resolve().parent
CAM_FILE = Path(os.environ.get("IVS_CAMERAS", BASE / "cameras.json"))
DATA_DIR = Path(os.environ.get("IVS_DATA_DIR", str(BASE)))
EVENTS_FILE = DATA_DIR / "events.jsonl"
RECORDINGS_DIR = Path(os.environ.get("IVS_RECORDINGS_DIR", "recordings"))
WEB_DIR = BASE.parent / "web"
API_TOKEN = os.environ.get("IVS_API_TOKEN", "")
HLS_BASE = os.environ.get("IVS_HLS_BASE", "http://localhost:8888")
MTX_API = os.environ.get("IVS_MEDIAMTX_API", "http://localhost:8189")

print("IAS-Viewer-Server backend starting — licensed under GNU AGPL-3.0; "
      "source: https://github.com/thaarfknight-star/IAS-Viewer-Server")

app = FastAPI(title="IAS-Viewer-Server")


class Camera(BaseModel):
    id: str
    name: str
    rtsp: str = ""
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


def mtx_paths() -> dict | None:
    """Return {path_name: path_info} from MediaMTX API, or None on failure."""
    try:
        with urllib.request.urlopen(MTX_API + "/v3/paths/list",
                                    timeout=5) as resp:
            items = json.load(resp).get("items", [])
        return {p.get("name"): p for p in items}
    except Exception:
        return None


def log_event(camera: str, event: str) -> None:
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(EVENTS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": int(time.time()),
                                "camera": camera,
                                "event": event},
                               ensure_ascii=False) + "\n")
        # keep the log bounded
        lines = open(EVENTS_FILE, encoding="utf-8").read().splitlines()
        if len(lines) > 1000:
            open(EVENTS_FILE, "w", encoding="utf-8").write(
                "\n".join(lines[-1000:]) + "\n")
    except Exception:
        pass


def _poller() -> None:
    """Watch camera up/down transitions and log them as events."""
    prev: dict[str, bool] = {}
    while True:
        time.sleep(15)
        try:
            paths = mtx_paths()
            if paths is None:
                continue
            for cam in load_cams().get("cameras", []):
                cid = cam["id"]
                ready = bool(paths.get(cid, {}).get("ready"))
                if cid in prev and prev[cid] != ready:
                    log_event(cid, "up" if ready else "down")
                prev[cid] = ready
        except Exception:
            pass


@app.on_event("startup")
def _start_poller() -> None:
    threading.Thread(target=_poller, daemon=True).start()


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


@app.get("/api/status")
def status():
    """Live per-camera status from the MediaMTX API."""
    paths = mtx_paths()
    if paths is None:
        return {"error": "mediamtx unreachable", "cameras": {}}
    out = {}
    for cam in load_cams().get("cameras", []):
        cid = cam["id"]
        info = paths.get(cid, {})
        out[cid] = {
            "ready": bool(info.get("ready")),
            "tracks": info.get("tracks", []),
        }
    return {"cameras": out}


@app.get("/api/events")
def events(limit: int = 100):
    """Recent camera up/down events (newest first)."""
    if not EVENTS_FILE.exists():
        return {"events": []}
    lines = EVENTS_FILE.read_text(encoding="utf-8").splitlines()
    evs = [json.loads(l) for l in lines[-limit:]]
    return {"events": list(reversed(evs))}


@app.get("/api/recordings")
def recordings():
    """List recorded mp4 files per camera (newest first)."""
    out: dict[str, list[dict]] = {}
    if RECORDINGS_DIR.is_dir():
        for cam_dir in sorted(RECORDINGS_DIR.iterdir()):
            if not cam_dir.is_dir():
                continue
            files = []
            for f in sorted(cam_dir.rglob("*.mp4"),
                            key=lambda p: p.stat().st_mtime,
                            reverse=True)[:200]:
                st = f.stat()
                files.append({"name": f.name,
                              "path": str(f.relative_to(cam_dir)),
                              "size": st.st_size,
                              "mtime": int(st.st_mtime)})
            out[cam_dir.name] = files
    return {"recordings": out}


@app.get("/api/recordings/{cam_id}/{filename:path}")
def download_recording(cam_id: str, filename: str):
    base = (RECORDINGS_DIR / cam_id).resolve()
    target = (base / filename).resolve()
    if not str(target).startswith(str(base)) or not target.is_file():
        raise HTTPException(status_code=404, detail="not found")
    return FileResponse(str(target), media_type="video/mp4",
                        filename=target.name)


app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
