# AI Usage Log

## Tools and models

| Purpose | Tool | Model |
|---|---|---|
| Development assistant (planning, code, debugging, step-by-step guidance) | Claude (claude.ai web chat), one single long conversation | Claude Sonnet 5.5 |
| Runtime AI agents inside the app (optional; the default `mock` provider needs no model) | Anthropic Messages API via the `anthropic` Python SDK | `claude-haiku-5-5` |
| Editor | VS Code (no AI coding agent or extension used) | n/a |

No other AI tools were used for this project.

## How I worked

I used the assistant as a tutor and pair programmer and built the application one layer at a time, testing each layer before starting the next: configuration and data model, state machine, WebSocket layer, MongoDB persistence, React frontend, AI agents, Docker. I ran all code myself on Windows (PowerShell, Docker Desktop), pasted real errors and outputs back into the chat, and applied the fixes.

Conventions in this log:
- My prompts were originally written in Persian (with typos and mixed English). They are translated into English here and are faithful to the original meaning.
- Terminal output that I pasted along with a prompt is summarized in square brackets, not reproduced.
- In prompt 19 I accidentally pasted an API key inside a terminal block. It is not reproduced here, and the key was revoked afterwards.

## Prompts

### Phase 0: Task intake

**1.** [pasted the full assessment text] "I applied for an internship and I have to do this task, and I want you to teach me step by step, from the very first step, how to do it."
→ Result: time-boxed plan, repo structure, `config.yml` format, list of open design decisions.

**2.** "I created the ai_logs/ai_prompt.md file and config.yml, and let's continue with the next step, the data model and state machine, step by step."
→ Result: `config.py`, `models.py`, `session.py` (state machine independent of FastAPI/WebSocket), `smoke_test.py`.

### Phase 1: State machine, local setup errors

**3.** [pasted `ModuleNotFoundError: No module named 'app'` from `smoke_test.py`] "This error appeared after running the smoke_test file. How do I fix the error and why did it happen?"
→ Cause: the script was inside `backend/app/`. Fix: moved it to `backend/` and added `app/__init__.py`.

**4.** [pasted `No module named 'yaml'`] "I did all the steps one by one and reached this stage. Diagnose the reason for this error and tell me its solution."
→ Fix: `python -m pip install pyyaml pydantic`; created `requirements.txt`.

**5.** [pasted `No module named 'app.session'`] "I did all the steps one by one and reached this stage. Diagnose the reason for this error and tell me its solution."
→ Cause: `session.py` missing or misnamed in `backend/app/`.

**6.** [pasted `ImportError: cannot import name 'Session'`] "I did all the steps one by one and reached this stage. Diagnose the reason for this error and tell me its solution."
→ Cause: wrong content in `session.py`.

**7.** [pasted `Select-String` output listing `class Phase/Slot/Message/Result` inside `session.py`] "I think the Session class does not exist. How should I create the class?"
→ Cause: the content of `models.py` had been pasted into `session.py`. After restoring both files, the smoke test ran.

**8.** [pasted successful `smoke_test.py` output] "This was the output of the test file. Now tell me the next step, step by step."
→ Analysis of the output; FastAPI layer: `leave()`, `manager.py` (waiting room), `main.py` (WebSocket endpoint), `ws_test.py`.

### Phase 2: WebSocket layer and MongoDB

**9.** [pasted `ws_test.py` output with two simulated clients] "This is the output of running the ws_test file. Analyze the result and explain the next step, storage, step by step and clearly."
→ Analysis; MongoDB design (`db.py`, one document per session, background writes with `fire()`). The assistant replaced its earlier `motor` suggestion with the PyMongo async client.

**10.** [pasted `failed to connect to the docker API ... dockerDesktopLinuxEngine`] "I ran into this problem while running step 6. Tell me how to solve it."
→ Cause: the Docker Desktop engine was not running.

**11.** [pasted `docker version` output showing Client and Server] (no text)
→ Confirmed the engine was up; started the Mongo container.

**12.** [pasted `ws_test` output, `mongosh` output, and a run with Mongo stopped] "If everything is right, let's move on to the third step."
→ Findings: the stored document had no `result`/`finished_at`; the experiment continued to `results` with MongoDB stopped (background writes work).

### Phase 3: React frontend

**13.** [pasted `Select-String` output, a run with Mongo stopped, and PowerShell errors: `node`/`npm` not recognized] "What exactly is the problem with the frontend not being created?"
→ Cause: Node.js was not available in that terminal; the `frontend/` folder was never created.

**14.** [pasted `winget install OpenJS.NodeJS.LTS` output: already installed] "How do I install npm?" (typed with the wrong keyboard layout)
→ npm ships with Node.js; restart the terminal / refresh PATH.

**15.** [pasted `npm.ps1 cannot be loaded because running scripts is disabled`] "Installing node and npm went without problems, but this error is still there. Tell me step by step and clearly how to fix it."
→ Fix: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`; created the Vite project.

**16.** "All steps were completed fully; let's go to the next step and the components."
→ Result: `useExperiment.js` (useReducer + WebSocket), `Waiting`, `Chat`, `Timer`, `Results`, `App.jsx`, CSS; `server_now` added for timer sync; `StrictMode` removed to avoid duplicate sockets.

**17.** [quoted two steps from the assistant's reply: run backend + Mongo + `npm run dev`; open two tabs with `2h1ai`] "Tell me how to do these two steps, step by step."
→ Manual test procedure with three terminals and two browser tabs. The flow worked.

### Phase 4: AI agents

**18.** "Everything worked correctly and now let's go to step 4. Explain it step by step and clearly."
→ `ai_agent.py` (MockAgent, LLMAgent, fallback to mock), AI chat/vote tasks in `session.py`, config additions.

**19.** [pasted a PowerShell block: `uvicorn` run from `C:\Windows\system32`, an `$env:ANTHROPIC_API_KEY` line (key not reproduced), then a `cd`; followed by `ModuleNotFoundError: No module named 'app'`] "Why does this error appear when running the backend?"
→ Cause: commands in the wrong order (uvicorn ran before `cd backend`). I was told to revoke the exposed key immediately and did so.

**20.** "Once more, tell me the commands of each terminal in order and in full detail for running with Anthropic."
→ Terminal-by-terminal procedure; how to tell real LLM replies from mock fallback.

**21.** "I think there are no errors so far and we should go to my step 5."
→ Docker Compose step (Dockerfiles, `docker-compose.yml`, `.env` handling).

### Phase 5: Docker Compose

**22.** [pasted a backend log with `AttributeError: 'Session' object has no attribute 'leave'` and two `ANTHROPIC_API_KEY not set; falling back to mock agent` warnings] "This error appeared in the backend terminal before I started step 5. Tell me step by step how to solve it."
→ The `leave()` method had not been added to `Session`; the key warning is the intended mock fallback, not an error.

**23.** [pasted `docker compose up --build` failing with `failed to read dockerfile: open Dockerfile: no such file or directory`] "This error occurred in step 6. Explain step by step how to debug it."
→ Hint from `transferring dockerfile: 2B`; checks for filenames and file contents.

**24.** [pasted `Get-ChildItem` errors from running in `C:\Windows\system32`] "What exactly do you mean by the repo root?"
→ Explained the repo root and how to open a terminal there.

**25.** [pasted `Get-ChildItem backend, frontend` output showing `Dockerfile.dockerfile` and `.dockerignore.dockerfile`] (no text)
→ Cause: VS Code had appended `.dockerfile` to the names. Renamed the files; added `frontend/.dockerignore`.

**26.** [pasted a successful `docker compose up --build` log: all three services up] "This is the result of step 4."
→ Confirmed the stack was healthy; test plan for the three conditions.

**27.** [pasted logs: `restart backend`, a `mongosh` result for a `3h` session, `down -v`, `up --build`] "State whether all the steps were right for testing, and roughly how long the next steps will take to prepare."
→ Assessment: build from scratch and config reload verified; a full session, the other two conditions in Docker, and `result` storage were still to be verified. Time estimate for README, log, and slides.

**28.** "Now tell me, one by one, the commands I have to run in each terminal, from the beginning."
→ Final command list for Docker-based runs.

**29.** [pasted a `cd` command with a corrupted path (characters lost while pasting)] "Fix this error."
→ Cause: broken path from copy/paste; corrected command with quotes; suggested opening the terminal from VS Code.

### Phase 6: Delivery, Git, and interview preparation

**30.** "Tell me the next steps, step by step, exactly what I need to do until I finish the task."
→ Delivery checklist: final tests, config defaults, repo cleanup, log, README, GitHub, slides.

**31.** "Write the README for me completely, write the content of the prompt file for me, and complete this whole task so that I get ready for the interview."
→ Draft `README.md`, draft of this log, slide outline, interview Q&A, final checklist.

**32.** [pasted the draft of this log] "Complete this section yourself according to the chats and answers, so that I only have to copy and paste the text into the file."
→ A complete version of this log.

**33.** "Tell me the next step, connecting to Git, step by step and completely."
→ Git/GitHub procedure: `.gitignore`, secret scan, commit, push, fresh-clone test.

**34.** [pasted PowerShell errors from running `.gitignore` lines as commands, a rename error, and the secret-scan result] "Are these right before creating the repository?"
→ The lines were file content, not commands; created `.gitignore` and `.env.example` via PowerShell; the scan found only a README placeholder.

**35.** [pasted `git init/add/commit/push` output and a fresh-clone `docker compose up --build` log] "I think everything is right now, and we need to move on to the slides and an explanation of the project for myself."
→ Review of the logs: found unverified result storage, a blind-condition leak in the waiting room (participant counts), a duplicate test file; slide outline and code walkthrough.

**36.** [quoted a point from the assistant's reply: the README says `docker-compose.yml` but the file is `docker-compose.yaml`; make them the same] "How do I do this?"
→ `git mv docker-compose.yaml docker-compose.yml`; verified with `docker compose config`.

**37.** "Write the email I have to send for me, and after that teach me the project from the beginning to the end as if I know nothing about programming."
→ Submission email draft and a beginner-level explanation of the whole project.

**38.** [pasted the invitation email from the hiring team] "Write exactly in reply to this email."
→ Reply email with the repository link.

**39.** [pasted the interview requirements: a 5-minute presentation with 3 to 5 slides on structure, technical choices, and AI use; a live demo and code walkthrough] "Give me a neat and clean slide deck for the 5-minute explanation and an oral explanation script for the live interview. I have to do these tasks; do the tasks one by one and"
→ A 5-slide deck, a 5-minute script, a demo and code walkthrough plan.

### Phase 7: Fixing the AI agents after a live demo

**40.** "I ran a live demo in the two-humans-and-one-agent mode, and the agent did not vote at all and did not participate. Tell me how to fix this problem completely."
→ Cause: AI logic runs in background tasks whose exceptions were silent, plus incompletely applied earlier edits. Fix: consolidated `session.py`, task error logging, fallback reply/vote, `AIConfig` fields, `smoke_test_ai.py`.

**41.** [pasted corrupted PowerShell commands, Docker logs showing a restart loop with `ImportError: cannot import name 'AIConfig' ... circular import`, and the same traceback from `smoke_test_ai.py`] "These are the outputs I got. Tell me exactly where the problem is and how I can solve it."
→ Cause: the contents of `session.py` had been pasted into `config.py`, creating a circular import that crashed the backend container. Fix: restored `config.py` and `session.py`.

**42.** "Send me the correct content of the Session file."
→ Full `session.py`.

**43.** [pasted `smoke_test_ai.py` output: one AI message, then `AttributeError: 'Message' object has no attribute 'player'`] "Now this is the output of the command `cd backend`, `python smoke_test_ai.py`. Where exactly is the problem?"
→ Cause: field-name mismatch. `Message` in `models.py` used `player_id` while `session.py` and `ai_agent.py` read `.player`, so AI tasks died after the first message and votes fell back to random. Fix: renamed the field to `player`. The task-error logging added earlier exposed this bug.

**44.** [pasted a `select-string` error from running in `C:\Windows\system32`] (no text)
→ Cause: wrong working directory; changed to the project root.

**45.** [pasted a successful `smoke_test_ai.py` output: both AI agents chat and vote, no tracebacks] (no text)
→ Verified: AI agents send up to 3 messages per round, vote every round, and the tie-break works.

### Phase 8: Git synchronization

**46.** [pasted a `git push` rejection: remote contains work that I do not have locally] (no text)
→ Explained the cause; advised to inspect before any force-push.

**47.** [pasted `git status` and `git log --oneline -3`] (no text)
→ Local commit confirmed; run `git fetch` first.

**48.** [pasted `git fetch` output, `git log main..origin/main`, and `git diff --stat main...origin/main`] (no text)
→ The remote commit only renamed the compose file and removed a duplicate test file; merge is safe.

**49.** [pasted `git log` after the merge and a directory listing] "Is everything right now?"
→ Merge pushed. Remaining checks: waiting-room counts, log entries, default config, Docker re-test.

**50.** [pasted `mongosh` output of a session that was still in round 2] (no text)
→ Messages, phase log, and AI votes confirmed in the database; `result` is only written at the end of a session and has to be checked after the Results screen.

**51.** "In my interview they told me to translate all prompts and code comments into English, and I have to update all code and files on GitHub with one push and delete the whole commit history. Help me step by step in this stage."
→ Backup, English comments and log, single clean commit, force push.

## Notes on how the assistant's output was used

- Architecture kept after review: session state machine independent of FastAPI/WebSocket, server-side timers, MongoDB writes in the background, LLM agent with mock fallback.
- The assistant corrected one of its own earlier suggestions (`motor` replaced by the PyMongo async client).
- Problems found by running and testing: wrong file contents (`models.py` in `session.py`, `session.py` in `config.py`), missing `result`/`finished_at` in the stored document, missing `leave()` method, misnamed Dockerfiles, a leaked API key, a field-name mismatch that silenced the AI agents, and a waiting-room participant count that revealed the human/AI composition.
- Each step's code was run locally and its real output pasted back before moving on.