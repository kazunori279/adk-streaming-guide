# bidi-health

Generic uptime probe for ADK apps. One service monitors many apps via a YAML
config; each app is either a **bidi WebSocket** app (text + audio probes) or a
**CUJ** app (one end-to-end HTTP/SSE journey). Designed to be wired up to Cloud
Monitoring uptime checks.

## What it probes

Each app declares a `probe_type` (default `bidi`).

**`probe_type: bidi`** — two end-to-end WebSocket checks:

| Path | What it exercises |
|---|---|
| `GET /check/{app}/live` | WebSocket connect → text frame → ADK → Live API → model → response (works against both half-cascade and native-audio models) |
| `GET /check/{app}/live/audio` | Above + Cloud Text-to-Speech → binary PCM upload → automatic VAD → input transcription → output transcription |

**`probe_type: cuj`** — one end-to-end HTTP check:

| Path | What it exercises |
|---|---|
| `GET /check/{app}/cuj` | `POST /api/chat` (prompt + session_id) → SSE stream → succeeds on a `WorkflowComplete` event with no terminal error frame |

The CUJ probe drives a full ADK-workflow journey (e.g. the Scale Agents demo's
Control Room → Planner → Executor path). Besides health, it **keeps
scale-to-zero backends warm** — running a real journey on each uptime tick
keeps the demo's Agent Engine reasoning engines hot, so live demos don't hit
the cold-start `FAILED_PRECONDITION`. Transient mid-run error frames that the
workflow's re-planner recovers from are not treated as failures — only a
terminal `name: "error"` frame or a missing `WorkflowComplete` is.

Plus:

- `GET /health` — service liveness (no upstream check)
- `GET /apps` — list configured app names

Probes return 200 with transcript JSON on success, 503 on any failure. Routes
that don't apply to an app's `probe_type` return 200 `{"status":"skipped"}`
(e.g. `/live` on a cuj app, or the text route when `text_probe_enabled:
false`), so a mis-pointed uptime check fails loudly on its matcher rather than
silently.

## Configuration

Configure with `apps.yaml`. Path defaults to `./apps.yaml` (override with
`APPS_CONFIG=/path/to/apps.yaml`). See `apps.yaml.example` for the full schema.

Minimal per-app entry (e.g. bidi-demo):

```yaml
- name: bidi-demo-prod
  ws_url: wss://bidi-demo-xxx.us-east1.run.app
  query: "What time is it in Tokyo?"
```

The `name` becomes the URL slug (`/check/bidi-demo-prod/live`). The query
phrase is sent as text and synthesized to PCM for the audio probe.

Optional fields:

| Field | Purpose |
|---|---|
| `audio_query` | Different phrase for audio probe (default: same as `query`) |
| `text_timeout_seconds` / `audio_timeout_seconds` | Per-app timeout override |
| `ws_query_params` | Mapping appended to the WebSocket URL as `?k=v&...` (e.g. `{source: en, target: ja}` for translator language selection) |
| `setup_message` | JSON text frame sent **before** any other payload, for apps that require a per-session handshake (e.g. `'{"glossary":[]}'` for the translator) |
| `text_probe_enabled` | Set `false` for audio-only apps where text input is silently dropped server-side; the text route then short-circuits with `{"status":"skipped"}` |
| `tts_voice` | Override the global default TTS voice for this app's audio probe (`{language_code, ssml_gender}`). Needed for non-English apps so input transcription recognizes the synthesized query (e.g. `{language_code: ja-JP}` for a Japanese agent) |
| `probe_type` | `bidi` (default) or `cuj`. Selects the probe modality — see "What it probes" |
| `http_url` | **Required for `probe_type: cuj`.** `https://…` base URL of the ADK-workflow app; the probe POSTs to `{http_url}/api/chat`. (`ws_url` is required for `bidi` apps instead.) |
| `cuj_timeout_seconds` | Per-app timeout for the CUJ probe (default 60). Keep at/under the uptime check's 60s ceiling; a *cold* first run can exceed it, which is why the probe also serves to keep the backend warm |

All target apps must follow the ADK bidi-demo protocol shape (WebSocket path
`/ws/{user_id}/{session_id}`, JSON text frames, raw PCM binary frames, ADK
Event JSON responses); the optional fields above accommodate apps that vary
slightly within that shape.

Audio-only example:

```yaml
- name: adk-live-translator-prod
  ws_url: wss://live-translation-xxx.us-central1.run.app
  ws_query_params:
    source: en
    target: ja
  setup_message: '{"glossary":[]}'
  text_probe_enabled: false
  query: "What time is it in Tokyo?"
```

CUJ (HTTP/SSE) example — drives one journey and keeps the backend warm:

```yaml
- name: scale-control-room-prod
  probe_type: cuj
  http_url: https://scale-control-room-xxx.us-central1.run.app
  query: "Restock 2 Google Droid figures for the Tokyo office"
  cuj_timeout_seconds: 60
```

Here `query` is the objective sent to `/api/chat`. Point the Cloud Monitoring
uptime check at `/check/scale-control-room-prod/cuj` with matcher `SUCCESS`.

## Local Development

```bash
cd src/bidi-health
uv sync
cp apps.yaml.example apps.yaml
# Edit apps.yaml — point ws_url at a running bidi app

cd app
uv run --project .. uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

In another terminal:

```bash
curl http://localhost:8001/health
curl http://localhost:8001/apps
curl http://localhost:8001/check/bidi-demo-prod/live
curl http://localhost:8001/check/bidi-demo-prod/live/audio
curl http://localhost:8001/check/scale-control-room-prod/cuj   # cuj app
```

## Deploy to Cloud Run

```bash
cd src/bidi-health
cp apps.yaml.example apps.yaml
# Edit apps.yaml with your real WebSocket URLs

gcloud run deploy bidi-health \
  --source . \
  --project "${GOOGLE_CLOUD_PROJECT}" \
  --region "${GOOGLE_CLOUD_LOCATION}" \
  --allow-unauthenticated \
  --timeout 60 \
  --min-instances 0 \
  --max-instances 1
```

The `apps.yaml` is baked into the container image at build time (see
`Dockerfile`). Re-deploy whenever the config changes. For larger fleets,
consider mounting via Secret Manager instead.

## Cloud Monitoring uptime checks

One uptime check per `(app, probe-type)` you want monitored. The matcher
word (e.g. `Tokyo`, `東京`) lives in the uptime check, not in `apps.yaml`
— it's a Cloud Monitoring concern. Non-ASCII matchers (Japanese, etc.) are
supported by gcloud and round-trip cleanly through the API.

Audio probe (covers both audio I/O *and* the text path implicitly):

```bash
gcloud monitoring uptime create "bidi-demo-prod /check/.../live/audio" \
  --resource-type=uptime-url \
  --resource-labels=host=bidi-health-xxx.us-east1.run.app,project_id=PROJECT \
  --protocol=https \
  --path=/check/bidi-demo-prod/live/audio \
  --port=443 \
  --request-method=get \
  --matcher-content=Tokyo \
  --period=5 \
  --timeout=60 \
  --regions=europe,asia-pacific,usa-iowa \
  --validate-ssl=true \
  --project=PROJECT
```

For the matching alert policy (uses Monitoring REST API since gcloud doesn't
have first-class support for uptime-based alert policies):

```bash
TOKEN=$(gcloud auth print-access-token)
CHECK_ID=...      # from gcloud monitoring uptime list-configs
CHANNEL=projects/PROJECT/notificationChannels/...

cat > policy.json <<EOF
{
  "displayName": "bidi-demo-prod /check/.../live/audio uptime failure",
  "combiner": "OR",
  "conditions": [{
    "conditionThreshold": {
      "filter": "metric.type=\"monitoring.googleapis.com/uptime_check/check_passed\" AND metric.label.check_id=\"${CHECK_ID}\" AND resource.type=\"uptime_url\"",
      "comparison": "COMPARISON_GT",
      "thresholdValue": 2,
      "duration": "600s",
      "trigger": {"count": 1},
      "aggregations": [{
        "alignmentPeriod": "1200s",
        "perSeriesAligner": "ALIGN_NEXT_OLDER",
        "crossSeriesReducer": "REDUCE_COUNT_FALSE",
        "groupByFields": ["resource.label.*"]
      }]
    },
    "displayName": "Failure of uptime check_id ${CHECK_ID}"
  }],
  "notificationChannels": ["${CHANNEL}"],
  "enabled": true
}
EOF

curl -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d @policy.json \
  "https://monitoring.googleapis.com/v3/projects/PROJECT/alertPolicies"
```

**Order of operations matters when removing**: an uptime check cannot be
deleted while an alert policy references it. Delete the policy first, then
the check. (gcloud surfaces this only as a generic `INVALID_ARGUMENT`.)

For audio-only apps where you've set `text_probe_enabled: false`, only
create the audio uptime check — the text route would always return
`{"status":"skipped"}`, which would either always pass or always fail any
matcher you set, depending on your matcher word.

## Tuning the alert policy

The example policy above (`thresholdValue: 2`, `duration: 600s`) is intentionally
loose: it requires more than one region's series to be failing for >10 minutes
before paging. Tighter values (`thresholdValue: 1`, `duration: 300s`) flap on
single transient probe failures, which are common — see "Live API quota
flapping" below.

## Native audio transcription patterns

The audio probe must handle three distinct `outputTranscription` event
orderings depending on the model and whether grounding tools are used:

| Pattern | Apps | Partials | `finished=true` | `turnComplete` order |
|---|---|---|---|---|
| **Standard** | bidi-demo | Cumulative (each event contains full text so far) | Sent with full text | After `finished` |
| **Grounding** | grounding-demo | Cumulative, arrive **after** `turnComplete` | Sent with full text, also after `turnComplete` | Before any output |
| **Translator** | adk-live-translator, casestudiesforest (`gemini-3.1-flash-live`) | Incremental (each event is a new chunk) | **Never sent** | After last chunk |

The probe uses `append` (not replace) for output transcription so both
cumulative and incremental patterns produce usable text. For cumulative
apps the appended text is redundant (e.g. `"The GrandThe Grand Sapphire…"`)
but the content matcher still finds the expected substring.

Exit conditions, checked in order:

1. `outputTranscription.finished == true` with non-empty output — covers
   standard and grounding patterns once late transcription arrives.
2. `turnComplete` with output already collected — covers the translator
   and any app that never sends `finished=true`.
3. `turnComplete` with **no** output yet — enters a 15-second drain loop
   waiting for late transcription (grounding pattern). The outer
   per-app timeout (`audio_timeout_seconds`, default 30s) caps total
   probe duration.

## Probe retry behavior

Both `text_probe` and `audio_probe` retry **once** on
`websockets.ConnectionClosed` with a 2-second backoff. This masks the most
common transient upstream failure: an ADK app that drops the WebSocket
without a clean close frame because Live API connect threw an exception
(commonly `RESOURCE_EXHAUSTED`).

Timeouts are **not** retried — a slow upstream stays slow, and retrying just
adds load. Look for `closed early ...; retrying once` warnings in the
bidi-health logs to spot transient upstream blips that the retry papered
over.

## Live API quota flapping

If probes flap with `"no close frame received or sent"` errors that resolve
within minutes, the upstream app is almost certainly hitting Live API
concurrent session quota. The error surfaces in the **upstream app's** logs
(not bidi-health's), as:

```
google.genai.errors.APIError: 1011 RESOURCE_EXHAUSTED:
Maximum concurrent sessions exceeded.
```

### The us-central1 cap

`bidi_gen_concurrent_reqs_per_project_per_base_model` is **30 in us-central1**
for every Live API model, vs **5000** in us-east1, us-east4, europe-*, and
most other regions (1000 for the `gemini-3.1-flash-live-preview-*` model).
The cap is per project per base model, so all apps in the project sharing the
same model in the same region compete for the same 30 slots.

If your app lives in us-central1, the cheapest fix is to redeploy in another
region (us-east1, us-west1, etc.) — same model, 5000-session cap, no quota
request needed.

### Checking the quota

```bash
TOKEN=$(gcloud auth print-access-token)
PROJECT=your-project-id

curl -s -H "Authorization: Bearer $TOKEN" \
  "https://cloudquotas.googleapis.com/v1/projects/${PROJECT}/locations/global/services/aiplatform.googleapis.com/quotaInfos?pageSize=500" \
  | jq -r '.quotaInfos[]
      | select(.metric == "aiplatform.googleapis.com/bidi_gen_concurrent_reqs_per_project_per_base_model")
      | .dimensionsInfos[]
      | "\(.dimensions.region // "?") \(.dimensions.base_model // "(default)") = \(.details.value)"'
```

### Checking usage

Vertex AI **does not export Live API session usage** to Cloud Monitoring as
of writing — `serviceruntime.googleapis.com/quota/concurrent/usage` filtered
on the bidi quota metric returns no series, and there is no equivalent
`aiplatform.googleapis.com/*` metric. Real-time concurrent session counts
are not directly observable.

The best proxy is counting `RESOURCE_EXHAUSTED` events in the upstream app's
logs:

```bash
gcloud logging read \
  'resource.type=cloud_run_revision
   AND resource.labels.service_name=YOUR-UPSTREAM-SERVICE
   AND severity=ERROR
   AND textPayload:"RESOURCE_EXHAUSTED: Maximum concurrent sessions exceeded"' \
  --project=YOUR-PROJECT --limit=5000 --freshness=30d \
  --format='value(timestamp)' \
  | awk -F'T' '{print $1}' | sort | uniq -c
```

Each connect failure logs the exception twice (once from
`google.genai.live.connect`, once from the wrapping `websocket_endpoint`),
so divide raw counts by 2 for actual failure events. Cloud Logging default
retention is 30 days — for longer history, route to a longer-retention
bucket or BigQuery sink.

For a chartable signal, create a logs-based metric on the same filter and
alert on its rate.

## Architecture

```
src/bidi-health/
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── README.md
├── apps.yaml.example
└── app/
    ├── main.py     # FastAPI app, routes, lifespan TTS preload
    ├── config.py   # Pydantic models, YAML loader
    ├── probes.py   # text_probe(), audio_probe(), cuj_probe()
    └── tts.py      # Cloud TTS synthesis with PCM cache
```

TTS is synthesized once per unique `(query, voice)` tuple at startup and
cached in-process. Multiple apps sharing the same probe phrase share the
synthesized PCM payload.
