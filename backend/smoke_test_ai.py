import asyncio
from pathlib import Path
from app.config import load_config
from app.session import Session


async def main():
    cfg = load_config(str(Path(__file__).resolve().parent.parent / "config.yml"))
    cfg.experiment.participants = ["human", "ai", "ai"]
    cfg.experiment.discussion_seconds = 12
    cfg.experiment.voting_seconds = 8
    cfg.ai.provider = "mock"

    async def emit(ev):
        print(ev)

    s = Session(cfg, emit)
    print("slots:", [(x.player_id, x.kind) for x in s.slots])
    s.join()
    await s._task
    print("VOTES:", s.votes)
    print("RESULT:", s.result)


asyncio.run(main())