from fastapi import WebSocket

from .config import Config
from .session import Session
from .db import fire          

class SessionManager:
    def __init__(self, cfg: Config, repo):
        self.cfg = cfg
        self.repo = repo
        self.sessions: dict[str, Session] = {}
        self.sockets: dict[str, dict[str, WebSocket]] = {}
        self.waiting: Session | None = None

    def _new_session(self) -> Session:
        s = Session(self.cfg, emit=None, repo=self.repo)  # type: ignore[arg-type]
        s.emit = lambda ev, sid=s.id: self.broadcast(sid, ev)
        self.sessions[s.id] = s
        self.sockets[s.id] = {}
        fire(self.repo.create_session(s.to_doc()))
        return s

    def join(self) -> tuple[Session, str]:
        if self.waiting is None or self.waiting.is_full:
            self.waiting = self._new_session()
        s = self.waiting
        pid = s.join()
        if s.is_full:
            self.waiting = None
        return s, pid

    def waiting_info(self, s: Session) -> dict:
        humans = [x for x in s.slots if x.kind == "human"]
        return {"joined": sum(x.joined for x in humans), "needed": len(humans)}

    async def broadcast(self, sid: str, ev: dict):
        for pid, ws in list(self.sockets.get(sid, {}).items()):
            try:
                await ws.send_json(ev)
            except Exception:
                self.sockets[sid].pop(pid, None)

    async def leave(self, s: Session, pid: str):
        self.sockets.get(s.id, {}).pop(pid, None)
        s.leave(pid)
        if s._task is None:  # still in the waiting room
            await self.broadcast(s.id, {"type": "waiting", **self.waiting_info(s)})
        elif not self.sockets.get(s.id):  # everyone has left
            s._task.cancel()
            self.sessions.pop(s.id, None)
            self.sockets.pop(s.id, None)