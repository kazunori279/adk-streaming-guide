# End-to-end test procedures for the ADK Gemini Live API Toolkit demo app

This document describes how to verify the demo app end to end: first with the
automated WebSocket suite (`tests/test_live_streaming.py`), then with a browser
pass driven by the Chrome DevTools MCP server.

All test artifacts (server logs, screenshots) land in `tests/artifacts/`, or in
`$TEST_ARTIFACT_DIR` when that variable is set.

## 1. Environment setup

### Copy the demo to a temporary directory

Run the tests against a throwaway copy so the source tree stays clean:

```bash
export TEST_DIR="/tmp/bidi-test-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$TEST_DIR"
cp -r src/bidi-demo/. "$TEST_DIR"
cd "$TEST_DIR"
```

### Configure credentials

`app/.env` drives the backend selection. For Vertex AI:

```bash
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=<your-project>
GOOGLE_CLOUD_LOCATION=us-east1
DEMO_AGENT_MODEL=gemini-live-2.5-flash-native-audio
```

For the Gemini API, set `GOOGLE_GENAI_USE_VERTEXAI=FALSE` and `GOOGLE_API_KEY`.

> **Important:** `load_dotenv()` does **not** override variables that are already
> exported in your shell. If your shell exports `GOOGLE_CLOUD_LOCATION` (or any
> other key that also appears in `app/.env`), the shell value wins and the model
> lookup can fail with a `1008 policy violation: Publisher model ... was not
> found`. Either `unset` the conflicting variables or use the automated suite,
> which strips every `app/.env` key from the child process environment.

### Model and region pairings (Vertex AI)

Live models are not available in every region. Verified pairings:

| Model | Region |
|---|---|
| `gemini-live-2.5-flash-native-audio` | `us-east1` |
| `gemini-2.5-flash-native-audio-preview-12-2025` | `us-east1` |

The publisher-model REST `GET` endpoint returns 404 even for models that work,
so it is **not** a valid availability probe — only an actual
`client.aio.live.connect` call is.

## 2. Automated WebSocket suite

`tests/test_live_streaming.py` spawns the real uvicorn server on a free port and
talks to the real Live API. It is the primary regression gate.

```bash
cd "$TEST_DIR"
uv sync --extra dev
uv run pytest tests/test_live_streaming.py -v
```

| Test | What it covers |
|---|---|
| `test_t1_http_surface` | `/` serves `index.html`; `/static/js/app.js` and `/static/css/style.css` return 200 |
| `test_t2_text_turn_native_audio` | Text turn produces audio parts, `outputTranscription`, and `turnComplete` |
| `test_t3_audio_turn_native_audio` | Real synthesized speech streamed as 20 ms PCM frames; asserts `inputTranscription` and a matching reply |
| `test_t4_image_turn` | JPEG sent via `{"type":"image"}` followed by a prompt about it |
| `test_t5_google_search_tool` | A search-triggering prompt yields `executableCode` / `functionCall` / `webSearchQueries` / `groundingChunks` |
| `test_t6_run_config_query_params` | `?proactivity=true&affective_dialog=true` is accepted and applied |
| `test_t7_reconnect_same_session` | Reconnecting with the same `session_id` reuses the session |
| `test_t8_clean_teardown` | Disconnect closes `LiveRequestQueue` with no demo-owned error in the log |

Overrides:

- `TEST_MODEL` — native-audio model id to exercise (default
  `gemini-live-2.5-flash-native-audio`)
- `TEST_ARTIFACT_DIR` — where server logs and generated media are written

Per-test server logs are written to `tests/artifacts/server-<tag>.log`.

`test_t3` needs `say` and `afconvert` (macOS built-ins); `test_t4` needs
`ffmpeg`. Both tests skip when their tool is missing.

### Notes on assertions

- Event JSON encodes `bytes` as **base64url without padding**. Decode with
  `base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))`, not plain
  `b64decode`. (`app/static/js/app.js` already handles this correctly.)
- Realtime blobs sent with `send_realtime()` are streamed rather than
  turn-scoped, so an image needs settle time before the follow-up
  `send_content()` turn. The suite sends 3 frames 0.3 s apart, then waits 2 s.
- ADK 2.5.0's OpenTelemetry instrumentation logs a benign
  `Failed to detach context` traceback when the `run_live()` generator is closed
  from a different asyncio context. `test_t8` asserts only on demo-owned error
  strings for that reason.

## 3. Browser E2E with Chrome DevTools MCP

Start the server from the app directory:

```bash
cd "$TEST_DIR/app"
uv run uvicorn main:app --host 127.0.0.1 --port 8000 \
  > "$TEST_DIR/tests/artifacts/e2e-server.log" 2>&1 &
```

### Step 1: Navigate to the application

```yaml
mcp__chrome-devtools__navigate_page
url: http://127.0.0.1:8000
```

**Expected:** page loads with the title "ADK Gemini Live API Toolkit Demo".

### Step 2: Take a snapshot to verify the UI

```yaml
mcp__chrome-devtools__take_snapshot
```

**Expected elements:**

- Heading "ADK Gemini Live API Toolkit Demo"
- Header checkboxes: **Proactivity** (`#enableProactivity`) and
  **Affective Dialog** (`#enableAffectiveDialog`)
- Status indicator (`#statusIndicator`) and status text (`#statusText`) — the
  WebSocket connects automatically on page load, so this settles on
  "● Connected"
- Message input (`#message`, placeholder "Type your message here...") with
  **Send** (`#sendButton`), **Start Audio** (`#startAudioButton`), and
  **📷 Camera** (`#cameraButton`)
- **Event Console** panel with a **Show audio** checkbox (`#showAudioEvents`)
  and a **Clear** button (`#clearConsole`)

There are no API-backend radio buttons, credential fields, model dropdown, or
URL fields — the backend is configured entirely through `app/.env`.

### Step 3: Send a text message

```yaml
mcp__chrome-devtools__fill
uid: <message-input-uid>
value: What is the tallest mountain in Japan? Answer in one short sentence.

mcp__chrome-devtools__click
uid: <send-button-uid>
```

**Expected:**

1. A user bubble appears with the message text
2. Event Console shows `↑ UPSTREAM` for the sent text
3. `↓ DOWNSTREAM` **Output Transcription** events stream in incrementally and
   an agent bubble fills in
4. A **Token Usage** event appears (prompt + response totals)
5. A **Turn Complete** event closes the turn

Transcription events arrive as partials (`finished=false`) followed by one final
event (`finished=true`) carrying the **complete** text — the final event
replaces the accumulated text rather than appending to it.

### Step 4: Verify audio events

```yaml
mcp__chrome-devtools__click
uid: <show-audio-checkbox-uid>

mcp__chrome-devtools__fill
uid: <message-input-uid>
value: Say the word banana once.

mcp__chrome-devtools__click
uid: <send-button-uid>
```

**Expected:** Event Console shows several
`🔊 ... Audio Response: audio/pcm (N bytes)` rows, confirming the browser
receives and decodes the base64url-encoded PCM stream.

### Step 5: Take a screenshot

```yaml
mcp__chrome-devtools__take_screenshot
filePath: <repo>/src/bidi-demo/tests/artifacts/e2e-text-turn.png
fullPage: true
```

### Step 6: Check the browser console

```yaml
mcp__chrome-devtools__list_console_messages
types: ["error", "warn"]
```

**Expected:** only a 404 for `favicon.ico`. Any other error should be
investigated.

### Step 7: Verify clean teardown

Navigate away (or close the tab) to drop the WebSocket, then:

```bash
grep -n "Client disconnected, stopping upstream_task\|Client disconnected normally\|Closing live_request_queue" \
  "$TEST_DIR/tests/artifacts/e2e-server.log"
```

**Expected:** all three lines present, in that order.

### Step 8: Check the server log for errors

```bash
grep -c " - ERROR" "$TEST_DIR/tests/artifacts/e2e-server.log"
```

**Expected:** `0`.

Mic and camera capture require device grants that the MCP server cannot issue,
so audio input and image input stay covered by `test_t3` and `test_t4`.

## 4. Test completion

### 4.1 Stop the server

```bash
lsof -ti:8000 | xargs kill -9
```

### 4.2 Port fixes back to source

Any fix made in `$TEST_DIR` must be applied to `src/bidi-demo/` and the suite
re-run against the source copy.

### 4.3 Write a test log

Write `src/bidi-demo/tests/test_log_<timestamp>.md` recording:

- **Environment**: ADK version, backend, model, region, Python version
- **Results**: per-test outcome for the automated suite and the browser pass
- **Issues found and fixed**: with root cause and the code change
- **Frictions and known noise**: anything that cost time but is not a bug
- **Untested surface**: what the run did not cover

## 5. Troubleshooting

### Server doesn't start

- Check whether the port is in use: `lsof -i :8000`
- Review the log: `cat "$TEST_DIR/tests/artifacts/e2e-server.log"`
- Confirm the venv is synced: `uv sync --extra dev`

### WebSocket closes immediately with 1008

The model is not available in the configured region, usually because a shell
variable shadowed `app/.env`. See "Configure credentials" above.

### WebSocket closes with 1007 "Text output is not supported"

A native-audio model was used with a TEXT response modality. The demo always
requests `["AUDIO"]`, so this indicates a local modification.

### No events appear

- Verify credentials: `gcloud auth application-default print-access-token`
- Check the server log for API errors: `grep -i error "$TEST_DIR/tests/artifacts/e2e-server.log"`
- Confirm the model supports the Live API (models with `live` or
  `native-audio` in the name)
