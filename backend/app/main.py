from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .config import load_config
from .manager import SessionManager
import os
from .db import Repo

cfg = load_config()
repo = Repo(os.getenv("MONGO_URI", "mongodb://localhost:27017"))
manager = SessionManager(cfg, repo)

app = FastAPI(title="Human-AI Experiment")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health")
def health():
    return {"ok": True, "condition": cfg.experiment.condition}


@app.websocket("/ws")
async def ws_endpoint(ws: WebSocket):
    await ws.accept()
    s, pid = manager.join()
    manager.sockets[s.id][pid] = ws   # no await between join and socket registration

    await manager.broadcast(s.id, {"type": "waiting"})
    await ws.send_json({"type": "welcome", "player": pid, **s.public_state()})
    try:
        while True:
            data = await ws.receive_json()
            if data.get("type") == "message":
                await s.send_message(pid, str(data.get("text", "")))
            elif data.get("type") == "vote":
                ok = s.vote(pid, str(data.get("target", "")))
                await ws.send_json({"type": "vote_ack", "ok": ok})
    except WebSocketDisconnect:
        pass
    finally:
        await manager.leave(s, pid)