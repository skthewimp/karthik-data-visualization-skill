# Local dataviz repair tester

This is the first UI layer over the bounded `dataviz-fix` case manager. It supports chart paste/upload, structured context, ordinary context prompts, budgets, feedback acceptance checks, artifact comparison, and loop history.

Manual mode does **not** call a model. The health endpoint reports `provider_runner: false` so the case console cannot be mistaken for the complete repair product. Candidate charts can still be uploaded manually.

Run locally:

```bash
python3 -m pip install -r tester/requirements.txt
uvicorn tester.app:app --host 127.0.0.1 --port 8787 --reload
```

Open `http://127.0.0.1:8787`.

To use the locally authenticated Codex client against the checked-out skills:

```bash
DATAVIZ_ENABLE_LOCAL_RUNNER=1 \
  uvicorn tester.app:app --host 127.0.0.1 --port 8787
```

Each click runs one bounded cycle: one creator process, then one fresh reviewer process. Both are ephemeral. The creator can write only inside the case directory, and the reviewer receives the source and candidate before the versioned intent reveal. The UI never starts a second cycle automatically. Set `DATAVIZ_CODEX_MODEL` to override the local Codex default and `DATAVIZ_RUN_TIMEOUT_SECONDS` to change the 900-second per-process timeout.

The local runner records Codex token and latency telemetry when the CLI returns it. Once a complete local cycle exists, the UI shows the median measured cycle-token estimate and refuses a run whose remaining token budget is lower. A token ceiling can stop the next model call; it cannot interrupt a provider call already in progress. The tester does not yet estimate dollar cost, accept browser-supplied API keys, or implement OpenAI/Anthropic/Google provider adapters.

The default runtime directory is `.dataviz-tester/`. Override it with `DATAVIZ_TESTER_ROOT`. The local app accepts PNG and JPEG files up to 15 MB. It binds to localhost in the documented command and has no authentication; do not expose this development server publicly. The local runner trusts the installed Codex client and is for single-user development, not shared hosting.

Run tests:

```bash
python3 -m unittest discover -s tester/tests -v
```
