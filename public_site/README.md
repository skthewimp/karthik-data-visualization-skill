# Public dataviz repair site

This is the small public surface for `https://dataviz.karthiks.co`.

The visitor supplies one PNG or JPEG chart and one prompt. GPT-5.6 Luna rebuilds
the chart inside OpenAI's hosted code-interpreter container, then a fresh Luna
request reviews the source and candidate. The page shows the two charts side by
side, offers a PNG download, and permits one feedback-driven retry. Generated
code, provider output, and internal review machinery are never exposed in the UI.

Screenshot-only repair has an evidence boundary: the app can preserve legible
values and labels, but it cannot verify upstream data and it must not present
visually reconstructed values as exact.

## Run locally

Install the web dependencies in the repository environment and set a direct
OpenAI API key:

```bash
.venv/bin/pip install -r tester/requirements.txt
export OPENAI_API_KEY="..."
.venv/bin/python -m uvicorn public_site.app:app --host 127.0.0.1 --port 8790
```

Open `http://127.0.0.1:8790`. For plain HTTP development, also set
`DATAVIZ_SECURE_COOKIE=0`.

## Runtime controls

| Variable | Default | Purpose |
|---|---:|---|
| `OPENAI_API_KEY` | required | Direct OpenAI API authentication |
| `DATAVIZ_PUBLIC_ROOT` | `.dataviz-public` | Case database and private artifacts |
| `DATAVIZ_REASONING_EFFORT` | `medium` | Luna creator reasoning effort |
| `DATAVIZ_DAILY_CASE_LIMIT` | `50` | Global anonymous cases per UTC day |
| `DATAVIZ_DAILY_IP_LIMIT` | `3` | Cases per hashed IP per UTC day |
| `DATAVIZ_SECURE_COOKIE` | `1` | Send the capability cookie over HTTPS only |
| `DATAVIZ_QUOTA_SALT` | generated locally | Stable salt for privacy-preserving quota hashes |

The app re-encodes uploads, caps files at 8 MB and 25 million pixels, disables
network access inside code interpreter, uses `store=false`, and sends a hashed
anonymous safety identifier. Cases are bound to an HttpOnly browser cookie and
kept locally for about 24 hours by an hourly cleanup pass. The hosted code
container is deleted immediately after its PNG has been downloaded.

The deployment files under `deploy/` run one Uvicorn worker on localhost. Keep it
behind Caddy; do not bind the application port publicly.
