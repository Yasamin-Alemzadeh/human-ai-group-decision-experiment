import asyncio
import logging
import random
import time
from collections import Counter
from dataclasses import asdict
from typing import Awaitable, Callable
from uuid import uuid4

from .ai_agent import MockAgent, make_agent
from .config import Config
from .db import NullRepo, fire
from .models import Message, Phase, Result, Slot

log = logging.getLogger("session")
PLAYER_IDS = ["A", "B", "C"]
Emit = Callable[[dict], Awaitable[None]]


def _log_task_error(t: asyncio.Task):
    """Background tasks fail silently unless we look at their exception."""
    if not t.cancelled() and t.exception() is not None:
        log.error("Background task failed", exc_info=t.exception())


class Session:
    def __init__(self, cfg: Config, emit: Emit, repo=None):
        self.id = uuid4().hex[:8]
        self.cfg = cfg
        self.emit = emit
        self.repo = repo or NullRepo()

        # Blind condition: player kinds are shuffled over A/B/C
        kinds = list(cfg.experiment.participants)
        random.shuffle(kinds)
        self.slots = [Slot(pid, k) for pid, k in zip(PLAYER_IDS, kinds)]

        self.agents = {s.player_id: make_agent(cfg.ai)
                       for s in self.slots if s.kind == "ai"}
        self._fallback = MockAgent()
        self._ai_tasks: list[asyncio.Task] = []
        self.feedback: dict | None = None

        self.phase = Phase.WAITING
        self.round = 0
        self.ends_at: float | None = None
        self.messages: list[Message] = []
        self.votes: dict[int, dict[str, str]] = {}   # round -> {voter: target}
        self.result: Result | None = None
        self._all_voted = asyncio.Event()
        self._task: asyncio.Task | None = None

    def to_doc(self) -> dict:
        return {
            "_id": self.id,
            "created_at": time.time(),
            "condition": self.cfg.experiment.condition,
            "config": self.cfg.experiment.model_dump(),
            "slots": [{"player_id": s.player_id, "kind": s.kind} for s in self.slots],
        }

    # ---------- waiting room ----------
    def join(self) -> str | None:
        for s in self.slots:
            if s.kind == "human" and not s.joined:
                s.joined = True
                if self.is_full:
                    self._task = asyncio.create_task(self._run())
                    self._task.add_done_callback(_log_task_error)
                return s.player_id
        return None

    def leave(self, pid: str):
        if self._task is None:
            for s in self.slots:
                if s.player_id == pid:
                    s.joined = False

    @property
    def is_full(self) -> bool:
        return all(s.joined for s in self.slots if s.kind == "human")

    # ---------- actions ----------
    async def send_message(self, pid: str, text: str) -> bool:
        if self.phase != Phase.DISCUSSION or not text.strip():
            return False
        msg = Message(pid, text.strip()[:500], self.round)
        self.messages.append(msg)
        fire(self.repo.add_message(self.id, {
            "player": pid, "text": msg.text, "round": msg.round, "ts": msg.ts}))
        await self.emit({"type": "message", "player": pid, "text": msg.text})
        return True

    def vote(self, pid: str, target: str) -> bool:
        if self.phase != Phase.VOTING or target not in PLAYER_IDS:
            return False
        if target == pid and not self.cfg.experiment.allow_self_vote:
            return False
        rv = self.votes.setdefault(self.round, {})
        if pid in rv:
            return False
        rv[pid] = target
        fire(self.repo.set_vote(self.id, self.round, pid, target))
        if len(rv) == 3:
            self._all_voted.set()
        return True

    # ---------- AI behaviour ----------
    def _spawn(self, coro):
        t = asyncio.create_task(coro)
        t.add_done_callback(_log_task_error)
        self._ai_tasks.append(t)

    def _cancel_ai_tasks(self):
        for t in self._ai_tasks:
            t.cancel()
        self._ai_tasks = []

    async def _ai_chat(self, pid: str):
        ai, rnd = self.cfg.ai, self.round
        agent, sent = self.agents[pid], 0
        live = lambda: self.phase == Phase.DISCUSSION and self.round == rnd
        while live() and sent < ai.max_messages_per_round:
            await asyncio.sleep(random.uniform(*ai.reply_delay_seconds))
            if not live():
                return
            if self.messages and self.messages[-1].player == pid:
                continue                      # never speak twice in a row
            try:
                text = await agent.reply(pid, self.messages, rnd, self.feedback)
            except Exception:
                log.exception("AI reply failed, using fallback line")
                text = await self._fallback.reply(pid, self.messages, rnd, self.feedback)
            await asyncio.sleep(min(len(text) * 0.04, 3))   # typing delay
            if live() and await self.send_message(pid, text):
                sent += 1

    async def _ai_vote(self, pid: str):
        rnd = self.round
        try:
            await asyncio.sleep(random.uniform(
                1, max(1.5, self.cfg.experiment.voting_seconds * 0.5)))
            target = await self.agents[pid].vote(pid, self.messages, rnd, self.feedback)
        except Exception:
            log.exception("AI vote failed, using random vote")
            target = random.choice([p for p in PLAYER_IDS if p != pid])
        if self.phase == Phase.VOTING and self.round == rnd:
            self.vote(pid, target)

    # ---------- state machine ----------
    async def _enter(self, phase: Phase, seconds: int | None):
        self.phase = phase
        self.ends_at = time.time() + seconds if seconds else None
        fire(self.repo.set_phase(self.id, phase.value, self.round))
        await self.emit({"type": "state", **self.public_state()})

    async def _run(self):
        e = self.cfg.experiment
        try:
            for r in range(1, e.rounds + 1):
                self.round = r
                await self._enter(Phase.DISCUSSION, e.discussion_seconds)
                for p in self.agents:
                    self._spawn(self._ai_chat(p))
                await asyncio.sleep(e.discussion_seconds)
                self._cancel_ai_tasks()

                self._all_voted.clear()
                await self._enter(Phase.VOTING, e.voting_seconds)
                for p in self.agents:
                    self._spawn(self._ai_vote(p))
                try:
                    await asyncio.wait_for(self._all_voted.wait(), e.voting_seconds)
                except asyncio.TimeoutError:
                    pass                      # missing votes = abstain
                self._cancel_ai_tasks()

                if r < e.rounds:
                    self.feedback = self._counts([r])
                    if e.show_round_feedback:
                        await self.emit({"type": "feedback", "round": r,
                                         "counts": self.feedback})

            self.result = self._tally()
            fire(self.repo.save_result(self.id, asdict(self.result)))
            await self._enter(Phase.RESULTS, None)
        finally:
            self._cancel_ai_tasks()

    # ---------- tally ----------
    def _counts(self, rounds: list[int]) -> dict[str, int]:
        c = Counter({p: 0 for p in PLAYER_IDS})
        for r in rounds:
            c.update(self.votes.get(r, {}).values())
        return dict(c)

    def _tally(self) -> Result:
        last = self.cfg.experiment.rounds
        counts = self._counts([last])
        top = [p for p, n in counts.items() if n == max(counts.values())]
        if len(top) == 1:
            return Result(top[0], counts, "none")

        cum = self._counts(list(range(1, last + 1)))
        top2 = [p for p in top if cum[p] == max(cum[q] for q in top)]
        if len(top2) == 1:
            return Result(top2[0], counts, "cumulative")
        return Result(random.choice(top2), counts, "random")

    # ---------- what the client may see ----------
    def public_state(self) -> dict:
        return {
            "session_id": self.id,
            "phase": self.phase.value,
            "round": self.round,
            "ends_at": self.ends_at,
            "server_now": time.time(),
            "players": PLAYER_IDS,
            "result": (
                {"winner": self.result.winner, "counts": self.result.counts,
                 "tie_break": self.result.tie_break}
                if self.result else None
            ),
        }