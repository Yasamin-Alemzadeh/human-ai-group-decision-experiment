import asyncio, json, websockets

async def client(name):
    async with websockets.connect("ws://localhost:8000/ws") as ws:
        async for raw in ws:
            ev = json.loads(raw)
            print(name, ev["type"], ev.get("phase", ""), ev.get("player", ""))
            if ev["type"] == "state" and ev["phase"] == "discussion":
                await ws.send(json.dumps({"type": "message", "text": f"hi from {name}"}))
            if ev["type"] == "state" and ev["phase"] == "voting":
                await ws.send(json.dumps({"type": "vote", "target": "B"}))
            if ev["type"] == "state" and ev["phase"] == "results":
                print(name, "RESULT:", ev["result"])
                return

async def main(n_humans=2):
    await asyncio.gather(*(client(f"c{i}") for i in range(n_humans)))

asyncio.run(main())