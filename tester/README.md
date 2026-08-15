# Local dataviz repair tester

This is the first UI layer over the bounded `dataviz-fix` case manager. It supports chart paste/upload, structured context, ordinary context prompts, an explicit preservation contract, budgets, feedback acceptance checks, artifact comparison, and loop history.

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

Each click runs one bounded cycle: one creator process, then one fresh reviewer process. Both are ephemeral. On revision, the creator receives the source and latest candidate and must preserve prior passes rather than restarting. A narrow request is treated as an edit boundary: changed regions must pass normally, untouched regions are checked for regression, and pre-existing out-of-scope defects are reported without silently expanding the job. Every candidate gets an exact-hash inspection record before blind review. Matplotlib builders use `dataviz_mcp.rendering.render_chart` so the wrapper preserves renderer geometry and runs complete clipping/collision checks; raster-only or unsupported geometry stays explicitly unknown. The reviewer receives the source, exact candidate, deterministic inspection, a representative delivery-size preview, and an overlapping four-region detail sheet before the versioned intent reveal. A known deterministic defect blocks `Send`. The UI never starts a second cycle automatically. Set `DATAVIZ_CODEX_MODEL` to override the local Codex default, `DATAVIZ_CODEX_REASONING_EFFORT` to override its reasoning effort for faster regression runs, and `DATAVIZ_RUN_TIMEOUT_SECONDS` to change the 900-second per-process timeout.

The creator receives writable Matplotlib and general cache directories and a six-call rendering budget. This is a bounded compatibility path, not the repository's preferred visual language: the creator must apply `karthik-data-visualization` deliberately and cannot accept Matplotlib defaults. It should use the available Python stack rather than probing renderers or compiling another language. An artifact may be preserved unchanged only when no active user check or unresolved evaluator action requires a change.

The local runner records Codex token and latency telemetry when the CLI returns it. Once a complete local cycle exists, the UI shows the median measured cycle-token estimate and refuses a run whose remaining token budget is lower. A token ceiling can stop the next model call; it cannot interrupt a provider call already in progress. The tester does not yet estimate dollar cost, accept browser-supplied API keys, or implement OpenAI/Anthropic/Google provider adapters.

The default runtime directory is `.dataviz-tester/`. Override it with `DATAVIZ_TESTER_ROOT`. The local app accepts PNG and JPEG files up to 15 MB. It binds to localhost in the documented command and has no authentication; do not expose this development server publicly. The local runner trusts the installed Codex client and is for single-user development, not shared hosting.

Run tests:

```bash
python3 -m unittest discover -s tester/tests -v
```
