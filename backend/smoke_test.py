import asyncio
from app.config import load_config
from app.session import Session

async def main():
    from pathlib import Path
    cfg = load_config(str(Path(__file__).resolve().parent.parent / "config.yml"))
    cfg.experiment.discussion_seconds = 2
    cfg.experiment.voting_seconds = 3

    async def emit(ev): print(ev)

    s = Session(cfg, emit)
    print("slots (server-side only):", [(x.player_id, x.kind) for x in s.slots])
    while (pid := s.join()):
        print("joined as", pid)
    await asyncio.sleep(2.5)
    await s.send_message("A", "I think B should lead")
    await asyncio.sleep(2)
    for p in ["A", "B", "C"]:
        s.vote(p, "B")
    await s._task
    print("RESULT:", s.result)

asyncio.run(main())
