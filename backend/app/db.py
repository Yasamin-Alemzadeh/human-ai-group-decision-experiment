import asyncio
import logging
import time

log = logging.getLogger("db")
_tasks: set[asyncio.Task] = set()


def fire(coro):
    """Run a DB write in the background; the experiment never waits for the database."""
    t = asyncio.create_task(coro)
    _tasks.add(t)
    t.add_done_callback(_tasks.discard)


class NullRepo:
    """No-op repository for tests without a database (e.g. smoke_test.py)."""
    async def create_session(self, doc): pass
    async def add_message(self, sid, msg): pass
    async def set_vote(self, sid, rnd, voter, target): pass
    async def set_phase(self, sid, phase, rnd): pass
    async def save_result(self, sid, result): pass


class Repo(NullRepo):
    def __init__(self, uri: str, db_name: str = "experiment"):
        from pymongo import AsyncMongoClient
        self.client = AsyncMongoClient(uri, serverSelectionTimeoutMS=2000)
        self.col = self.client[db_name]["sessions"]

    async def _update(self, sid: str, update: dict):
        try:
            await self.col.update_one({"_id": sid}, update, upsert=True)
        except Exception as e:
            log.warning("DB write failed (session %s): %s", sid, e)

    async def create_session(self, doc: dict):
        doc = dict(doc)
        sid = doc.pop("_id")
        await self._update(sid, {"$set": doc})

    async def add_message(self, sid, msg):
        await self._update(sid, {"$push": {"messages": msg}})

    async def set_vote(self, sid, rnd, voter, target):
        await self._update(sid, {"$set": {f"votes.{rnd}.{voter}": target}})

    async def set_phase(self, sid, phase, rnd):
        await self._update(sid, {
            "$set": {"phase": phase, "round": rnd},
            "$push": {"phase_log": {"phase": phase, "round": rnd, "ts": time.time()}},
        })

    async def save_result(self, sid, result):
        await self._update(sid, {"$set": {"result": result, "finished_at": time.time()}})