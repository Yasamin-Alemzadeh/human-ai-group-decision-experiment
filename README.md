# Multi-Participant Human-AI Group Decision Experiment

A lightweight real-time web application simulating a **3-participant group decision-making experiment**. Participants discuss in text for two rounds, vote on who should be the **Decision Maker**, and see the final result. Participants never learn whether the others are humans or AI agents (blind condition).

**Stack:** React (Vite) · FastAPI (Python) · MongoDB · Docker Compose

## Quick start

Requirements: Docker Desktop (running).

```bash
docker compose up --build
```

- App: http://localhost:5173
- Backend health check: http://localhost:8000/api/health

The default configuration needs **no API key**: AI agents run in `mock` mode.

To start from a clean state (removes stored data):

```bash
docker compose down -v
docker compose up --build
```

## Switching conditions

All experiment parameters live in [`config.yml`](config.yml). Edit the file, then restart the backend (no rebuild needed):

```bash
docker compose restart backend
```

Close old browser tabs afterwards, since the restart drops existing connections.

| Condition | `condition` | `participants` | Browser tabs to open |
|---|---|---|---|
| 3 humans | `3h` | `[human, human, human]` | 3 (e.g. 2 tabs + 1 incognito window) |
| 2 humans + 1 AI | `2h1ai` | `[human, human, ai]` | 2 |
| 1 human + 2 AI | `1h2ai` | `[human, ai, ai]` | 1 |

`participants` is the source of truth; `condition` is a label stored with each session.

Other parameters:

| Key | Meaning | Default |
|---|---|---|
| `rounds` | Number of discussion + voting rounds | 2 |
| `discussion_seconds` | Discussion length per round | 60 |
| `voting_seconds` | Voting window per round | 15 |
| `allow_self_vote` | Whether a player may vote for themselves | true |
| `show_round_feedback` | Show anonymous vote counts after round 1 | true |
| `ai.provider` | `mock` or `anthropic` | mock |
| `ai.model` | Model used when provider is `anthropic` | claude-haiku-5-5 |
| `ai.reply_delay_seconds` | Random delay range before an AI replies | [2, 6] |
| `ai.max_messages_per_round` | Cap on messages per AI per round | 3 |
| `ai.llm_timeout_seconds` | LLM call timeout before falling back to mock | 5 |

## Using a real LLM for the AI agents (optional)

1. Create a `.env` file next to `docker-compose.yml` (see `.env.example`):
   ```
   ANTHROPIC_API_KEY=your-key
   ```
2. Set `ai.provider: "anthropic"` in `config.yml`.
3. Recreate the backend so it picks up the new environment:
   ```bash
   docker compose up -d --force-recreate backend
   ```

If the key is missing, or an LLM call fails or times out, the agent falls back to the scripted mock agent and the experiment continues. Failures are logged (`docker compose logs backend`).

## Experiment flow

1. **Waiting room.** Each browser connection takes the next free human slot of the current session. The experiment starts when all human slots are filled.
2. **Rounds.** For each of 2 rounds: timed text discussion, then a timed vote.
3. **Feedback.** After round 1, anonymous vote counts per player are shown to everyone.
4. **Result.** After round 2, the Decision Maker, final counts, and tie-break information are shown.

## Architecture

```
React (Vite, nginx) ──WebSocket──▶ FastAPI ──▶ SessionManager ──▶ Session (state machine)
                                                                   ├── AI agents (mock | LLM)
                                                                   └── Repo ──▶ MongoDB
```

- `backend/app/session.py`: the experiment itself (phases, timers, voting, tally). It has no dependency on FastAPI or WebSockets; it only receives an `emit` callback, so it can be tested without a server (`backend/smoke_test.py`).
- `backend/app/manager.py`: waiting room and mapping of sessions to sockets.
- `backend/app/ai_agent.py`: `MockAgent` and `LLMAgent` behind the same `reply()` / `vote()` interface.
- `backend/app/db.py`: MongoDB persistence (one document per session).
- `frontend/src/useExperiment.js`: WebSocket connection and a reducer holding UI state. The frontend contains no experiment logic; it only renders server events.

State machine per session: `waiting → (discussion → voting) × rounds → results`.

## Key design decisions

- **Blind condition.** Player letters (A/B/C) are randomly assigned to human/AI slots. The server never sends a participant's `kind` (human/ai) to any client; it is stored only in the database for researchers.
- **Server-authoritative timers.** The server controls phase changes and sends `ends_at` plus `server_now`; clients compute the countdown with a clock offset, so differing client clocks do not matter.
- **Voting rules.** Votes are final (first vote counts). Missing votes count as abstentions. A voting phase ends early once all 3 votes are in. Self-voting is allowed (configurable).
- **Intermediate feedback.** After round 1, only the vote count per player is shown, not who voted for whom. This gives round 2 something to discuss while preserving anonymity.
- **Final result and tie-breaking.** The winner is determined by round 2 votes. Ties are broken by cumulative votes across both rounds, then by random draw. The result states which rule was applied.
- **AI behaviour.** Agents reply with a random delay, a typing delay proportional to message length, and a per-round message cap. The LLM system prompt asks for one short casual sentence and forbids revealing AI identity. The agent votes after a random delay inside the voting window.
- **Resilience.** Database writes run in the background and failures are only logged, so a MongoDB outage never blocks the experiment. LLM errors fall back to the mock agent.
- **Single WebSocket per participant.** React `StrictMode` is disabled because it double-mounts effects in development, which would open two sockets and occupy two slots for one person.

## Trade-offs and known limitations (4-hour scope)

- **No reconnect/refresh support.** A closed or refreshed tab loses its slot; a session started with a dropped participant continues without them. Reconnect tokens would fix this.
- **Single backend process.** Session state is held in memory, so there is no horizontal scaling. MongoDB is a record of the experiment, not the source of live state.
- **AI anonymity is best-effort.** It relies on prompting and timing and is not guaranteed; the LLM may occasionally sound less human. The mock agent is intentionally simple.
- **Security hardening skipped.** CORS is open (`*`), MongoDB runs without authentication and is not exposed to the host, and there is no participant authentication or rate limiting.
- **Waiting room is minimal.** Sessions are filled in order of arrival; there is no timeout for a session that never fills.
- **Tests are manual scripts, not an automated suite.**

## Manual tests

With the stack running (any condition with 2 human slots):

```bash
cd backend
pip install websockets
python ws_test.py        # simulates 2 human clients through a full session
python smoke_test.py     # runs the state machine without network or database
```

Inspect the stored data of the latest session:

```bash
docker compose exec mongo mongosh experiment --eval "db.sessions.find().sort({created_at:-1}).limit(1)"
```

Each session document contains: configuration, slots (including `kind`), phase log, messages, votes per round, and the final result.

## Project structure

```
├── docker-compose.yml
├── config.yml
├── .env.example
├── ai_logs/ai_prompts.md      # AI usage log (all prompts, models, tools)
├── backend/                   # FastAPI app, Dockerfile, requirements.txt
└── frontend/                  # React app, Dockerfile (nginx)
```

## AI usage

See [`ai_logs/ai_prompts.md`](ai_logs/ai_prompts.md) for the tools, exact models, and all prompts used during development.