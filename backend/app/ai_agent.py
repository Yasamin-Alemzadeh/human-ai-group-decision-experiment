import asyncio
import logging
import os
import random
import re
from collections import Counter

from .config import AIConfig

log = logging.getLogger("ai")
PLAYERS = ["A", "B", "C"]

SYSTEM = """You are Player {me} in an anonymous 3-person text chat (Players A, B, C). \
The group must elect one of the three as "Decision Maker" for a later experiment. \
You are an ordinary participant; you may support yourself or someone else based on the discussion.
Rules:
- Write ONE short sentence (max 25 words), casual, like a real person typing quickly.
- No markdown, no emojis, no lists, no quotes around the message.
- Never say or hint that you are an AI, bot or language model. If asked, answer like a human participant.
- Do not repeat what you already said; react to what others wrote.
- Output only the message text."""


def _transcript(messages, me: str) -> str:
    if not messages:
        return "(no messages yet)"
    return "\n".join(f"Player {m.player}{' (you)' if m.player == me else ''}: {m.text}"
                     for m in messages)


class MockAgent:
    
    LINES = [
        "Hi all, any thoughts on who should lead?",
        "I think we should pick whoever is most active here.",
        "Fair point, I'm fine with either of you honestly.",
        "Let's just agree on one person so we don't tie.",
        "I'd go with someone who's been giving clear reasons.",
        "Sounds reasonable to me, I'm leaning that way.",
    ]

    def __init__(self):
        self._unused = list(self.LINES)

    async def reply(self, me, messages, rnd, feedback):
        if not self._unused:
            self._unused = list(self.LINES)
        line = random.choice(self._unused)
        self._unused.remove(line)
        return line

    async def vote(self, me, messages, rnd, feedback):
        talk = Counter(m.player for m in messages if m.player != me)
        others = [p for p in PLAYERS if p != me]
        if talk:
            best = max(talk.values())
            return random.choice([p for p in others if talk.get(p, 0) == best])
        return random.choice(others)


class LLMAgent:
    def __init__(self, cfg: AIConfig, fallback: MockAgent):
        from anthropic import AsyncAnthropic
        self.client = AsyncAnthropic()          # ANTHROPIC_API_KEY is read from the environment
        self.cfg = cfg
        self.fallback = fallback

    async def _ask(self, system: str, user: str, max_tokens: int) -> str:
        resp = await asyncio.wait_for(
            self.client.messages.create(
                model=self.cfg.model, max_tokens=max_tokens, system=system,
                messages=[{"role": "user", "content": user}]),
            timeout=self.cfg.llm_timeout_seconds)
        return resp.content[0].text.strip()

    async def reply(self, me, messages, rnd, feedback):
        ctx = f"Round {rnd}.\n"
        if feedback:
            ctx += f"Round 1 vote counts: {feedback}\n"
        ctx += "Chat so far:\n" + _transcript(messages, me) + "\n\nYour next message:"
        try:
            text = (await self._ask(SYSTEM.format(me=me), ctx, 80)).strip('"')
            return text[:300] or await self.fallback.reply(me, messages, rnd, feedback)
        except Exception as e:
            log.warning("LLM reply failed, using mock: %s", e)
            return await self.fallback.reply(me, messages, rnd, feedback)

    async def vote(self, me, messages, rnd, feedback):
        ctx = ("Chat so far:\n" + _transcript(messages, me) +
               "\n\nVote for the Decision Maker. Answer with exactly one letter: A, B or C.")
        try:
            m = re.search(r"[ABC]", await self._ask(SYSTEM.format(me=me), ctx, 5))
            if m:
                return m.group(0)
        except Exception as e:
            log.warning("LLM vote failed, using mock: %s", e)
        return await self.fallback.vote(me, messages, rnd, feedback)


def make_agent(cfg: AIConfig):
    mock = MockAgent()
    if cfg.provider == "anthropic":
        if os.getenv("ANTHROPIC_API_KEY"):
            return LLMAgent(cfg, mock)
        log.warning("ANTHROPIC_API_KEY not set; falling back to mock agent")
    return mock