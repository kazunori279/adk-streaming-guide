"""Integration tests for the bidi-demo WebSocket server against a live model.

These tests spawn the real uvicorn server and talk to the real Live API, so
they need working credentials in ``app/.env`` (Vertex AI ADC or an API key).

Run with::

    uv run --extra dev pytest tests/test_live_streaming.py -v -s

Environment override:

* ``TEST_MODEL`` -- native-audio model id to exercise
"""

import asyncio
import base64
import contextlib
import json
import os
import pathlib
import socket
import subprocess
import sys
import time
import wave

import httpx
import pytest
import websockets

DEMO_ROOT = pathlib.Path(__file__).resolve().parents[1]
APP_DIR = DEMO_ROOT / "app"
ARTIFACT_DIR = pathlib.Path(
    os.getenv("TEST_ARTIFACT_DIR", DEMO_ROOT / "tests" / "artifacts")
)

MODEL = os.getenv("TEST_MODEL", "gemini-live-2.5-flash-native-audio")

TURN_TIMEOUT = 90.0


# ---------------------------------------------------------------------------
# Server fixtures
# ---------------------------------------------------------------------------


def _free_port() -> int:
  with socket.socket() as s:
    s.bind(("127.0.0.1", 0))
    return s.getsockname()[1]


class Server:
  """A running uvicorn instance for the demo app."""

  def __init__(self, port: int, log_path: pathlib.Path, proc):
    self.port = port
    self.log_path = log_path
    self.proc = proc

  @property
  def http(self) -> str:
    return f"http://127.0.0.1:{self.port}"

  @property
  def ws(self) -> str:
    return f"ws://127.0.0.1:{self.port}"

  def log(self) -> str:
    return self.log_path.read_text(errors="replace")


def _dotenv_keys() -> set[str]:
  """Keys declared in app/.env."""
  path = APP_DIR / ".env"
  if not path.exists():
    return set()
  keys = set()
  for line in path.read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
      keys.add(line.split("=", 1)[0].strip())
  return keys


def _start_server(model: str, tag: str) -> Server:
  ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
  port = _free_port()
  log_path = ARTIFACT_DIR / f"server-{tag}.log"
  # `load_dotenv()` does not override pre-existing environment variables, so
  # drop anything app/.env declares to keep the run reproducible regardless
  # of the developer's shell.
  env = {k: v for k, v in os.environ.items() if k not in _dotenv_keys()}
  env.update(DEMO_AGENT_MODEL=model, PYTHONUNBUFFERED="1")
  log = log_path.open("w")
  proc = subprocess.Popen(
      [
          sys.executable,
          "-m",
          "uvicorn",
          "main:app",
          "--host",
          "127.0.0.1",
          "--port",
          str(port),
      ],
      cwd=APP_DIR,
      env=env,
      stdout=log,
      stderr=subprocess.STDOUT,
  )

  deadline = time.time() + 45
  while time.time() < deadline:
    if proc.poll() is not None:
      raise RuntimeError(
          f"server for {model} exited early:\n{log_path.read_text()}"
      )
    try:
      if httpx.get(f"http://127.0.0.1:{port}/", timeout=2).status_code == 200:
        break
    except Exception:  # noqa: BLE001 - server not up yet
      time.sleep(0.3)
  else:
    proc.kill()
    raise RuntimeError(f"server for {model} did not become ready")

  return Server(port, log_path, proc)


def _stop_server(server: Server) -> None:
  server.proc.terminate()
  with contextlib.suppress(subprocess.TimeoutExpired):
    server.proc.wait(timeout=10)
  if server.proc.poll() is None:
    server.proc.kill()


@pytest.fixture(scope="module")
def native_server():
  """A running demo server backed by a native-audio Live model."""
  server = _start_server(MODEL, "native-audio")
  yield server
  _stop_server(server)


# ---------------------------------------------------------------------------
# Event helpers
# ---------------------------------------------------------------------------


async def _drain_turn(ws, timeout: float = TURN_TIMEOUT) -> list[dict]:
  """Collect events until ``turnComplete`` (or the timeout expires)."""
  events: list[dict] = []
  deadline = time.monotonic() + timeout
  while True:
    remaining = deadline - time.monotonic()
    if remaining <= 0:
      raise AssertionError(
          f"no turnComplete within {timeout}s; got {len(events)} events"
      )
    raw = await asyncio.wait_for(ws.recv(), timeout=remaining)
    event = json.loads(raw)
    events.append(event)
    if event.get("turnComplete"):
      return events


def _parts(events: list[dict]) -> list[dict]:
  out = []
  for event in events:
    for part in (event.get("content") or {}).get("parts") or []:
      out.append(part)
  return out


def _text(events: list[dict]) -> str:
  return "".join(p.get("text", "") for p in _parts(events))


def _b64_decode(data: str) -> bytes:
  """Decode the base64url-without-padding form Pydantic emits for bytes."""
  return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _audio_bytes(events: list[dict]) -> int:
  total = 0
  for part in _parts(events):
    inline = part.get("inlineData") or {}
    if str(inline.get("mimeType", "")).startswith("audio/"):
      total += len(_b64_decode(inline.get("data", "")))
  return total


def _transcript(events: list[dict], key: str) -> str:
  return "".join(
      (event.get(key) or {}).get("text") or "" for event in events
  ).strip()


def _reply(events: list[dict]) -> str:
  """Model reply as text, whichever modality it arrived in."""
  return (
      _text(events) + " " + _transcript(events, "outputTranscription")
  ).lower()


async def _send_text(ws, text: str) -> None:
  await ws.send(json.dumps({"type": "text", "text": text}))


# ---------------------------------------------------------------------------
# Media fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def spoken_pcm() -> bytes:
  """16 kHz mono LE16 PCM of a synthesized question, via macOS `say`."""
  if sys.platform != "darwin":
    pytest.skip("`say`/`afconvert` are macOS-only")
  ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
  aiff = ARTIFACT_DIR / "question.aiff"
  wav = ARTIFACT_DIR / "question.wav"
  subprocess.run(
      ["say", "-o", str(aiff), "What is the capital city of France?"],
      check=True,
  )
  subprocess.run(
      [
          "afconvert",
          "-f",
          "WAVE",
          "-d",
          "LEI16@16000",
          "-c",
          "1",
          str(aiff),
          str(wav),
      ],
      check=True,
  )
  with wave.open(str(wav)) as handle:
    assert handle.getframerate() == 16000
    assert handle.getnchannels() == 1
    assert handle.getsampwidth() == 2
    return handle.readframes(handle.getnframes())


@pytest.fixture(scope="session")
def blue_jpeg() -> bytes:
  """A solid-blue JPEG, generated with ffmpeg."""
  if not _which("ffmpeg"):
    pytest.skip("ffmpeg not available")
  ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
  path = ARTIFACT_DIR / "blue.jpg"
  subprocess.run(
      [
          "ffmpeg",
          "-y",
          "-loglevel",
          "error",
          "-f",
          "lavfi",
          "-i",
          "color=c=blue:s=320x240",
          "-frames:v",
          "1",
          str(path),
      ],
      check=True,
  )
  return path.read_bytes()


def _which(name: str) -> bool:
  import shutil

  return shutil.which(name) is not None


# ---------------------------------------------------------------------------
# T1 - HTTP surface
# ---------------------------------------------------------------------------


def test_t1_http_surface(native_server):
  root = httpx.get(native_server.http + "/", timeout=10)
  assert root.status_code == 200
  assert "<html" in root.text.lower()

  for asset in (
      "/static/js/app.js",
      "/static/js/audio-recorder.js",
      "/static/js/audio-player.js",
      "/static/js/pcm-recorder-processor.js",
      "/static/js/pcm-player-processor.js",
      "/static/css/style.css",
  ):
    resp = httpx.get(native_server.http + asset, timeout=10)
    assert resp.status_code == 200, asset


# ---------------------------------------------------------------------------
# T2 - text turn on the native-audio (AUDIO) branch
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_t2_text_turn_native_audio(native_server):
  url = f"{native_server.ws}/ws/t2-user/t2-session"
  async with websockets.connect(url, max_size=None) as ws:
    await _send_text(ws, "Say the word hello and nothing else.")
    events = await _drain_turn(ws)

  assert _audio_bytes(events) > 0, "expected inline audio on the AUDIO branch"
  assert _transcript(
      events, "outputTranscription"
  ), "expected outputTranscription"


# ---------------------------------------------------------------------------
# T3 - real speech in, transcription out
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_t3_audio_turn_native_audio(native_server, spoken_pcm):
  url = f"{native_server.ws}/ws/t3-user/t3-session"
  chunk = 640  # 20 ms of 16 kHz mono LE16
  async with websockets.connect(url, max_size=None) as ws:
    for offset in range(0, len(spoken_pcm), chunk):
      await ws.send(spoken_pcm[offset : offset + chunk])
      await asyncio.sleep(0.02)
    # Trailing silence so VAD sees end-of-speech.
    for _ in range(50):
      await ws.send(b"\x00" * chunk)
      await asyncio.sleep(0.02)
    events = await _drain_turn(ws)

  heard = _transcript(events, "inputTranscription").lower()
  assert heard, "expected inputTranscription for the spoken audio"
  assert "france" in heard or "capital" in heard, f"heard: {heard!r}"
  assert "paris" in _reply(events), f"reply: {_reply(events)!r}"


# ---------------------------------------------------------------------------
# T4 - image input
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_t4_image_turn(native_server, blue_jpeg):
  url = f"{native_server.ws}/ws/t4-user/t4-session"
  frame = json.dumps({
      "type": "image",
      "mimeType": "image/jpeg",
      "data": base64.b64encode(blue_jpeg).decode(),
  })
  async with websockets.connect(url, max_size=None) as ws:
    # Realtime blobs are streamed, not turn-scoped. Send a few frames the
    # way the camera UI does and let them reach the model before opening
    # a content turn.
    for _ in range(3):
      await ws.send(frame)
      await asyncio.sleep(0.3)
    await asyncio.sleep(2.0)
    await _send_text(
        ws, "What single color fills the image you can see right now?"
    )
    events = await _drain_turn(ws)

  assert "blue" in _reply(events), f"reply: {_reply(events)!r}"


# ---------------------------------------------------------------------------
# T5 - google_search tool invocation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_t5_google_search_tool(native_server):
  url = f"{native_server.ws}/ws/t5-user/t5-session"
  async with websockets.connect(url, max_size=None) as ws:
    await _send_text(
        ws, "Search the web and tell me who the current mayor of Tokyo is."
    )
    events = await _drain_turn(ws)

  blob = json.dumps(events)
  assert any(
      marker in blob
      for marker in (
          "executableCode",
          "functionCall",
          "webSearchQueries",
          "groundingChunks",
      )
  ), "expected evidence of a google_search invocation"


# ---------------------------------------------------------------------------
# T6 - proactivity / affective_dialog query parameters
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_t6_run_config_query_params(native_server):
  url = (
      f"{native_server.ws}/ws/t6-user/t6-session"
      "?proactivity=true&affective_dialog=true"
  )
  async with websockets.connect(url, max_size=None) as ws:
    await _send_text(ws, "Say the word ready and nothing else.")
    events = await _drain_turn(ws)

  assert _audio_bytes(events) > 0
  log = native_server.log()
  assert "proactivity=True, affective_dialog=True" in log
  assert "proactive_audio=True" in log


# ---------------------------------------------------------------------------
# T7 - reconnect onto the same session
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_t7_reconnect_same_session(native_server):
  session = "t7-session"
  url = f"{native_server.ws}/ws/t7-user/{session}"

  async with websockets.connect(url, max_size=None) as ws:
    await _send_text(ws, "Remember the number forty-two. Just say ok.")
    await _drain_turn(ws)

  await asyncio.sleep(1.0)

  async with websockets.connect(url, max_size=None) as ws:
    await _send_text(ws, "What number did I ask you to remember?")
    events = await _drain_turn(ws)

  reply = _reply(events)
  assert "42" in reply or "forty-two" in reply or "forty two" in reply, reply


# ---------------------------------------------------------------------------
# T8 - clean teardown
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_t8_clean_teardown(native_server):
  url = f"{native_server.ws}/ws/t8-user/t8-session"
  async with websockets.connect(url, max_size=None) as ws:
    await _send_text(ws, "Say the word bye and nothing else.")
    await _drain_turn(ws)
  await asyncio.sleep(2.0)

  log = native_server.log()
  assert "Closing live_request_queue" in log
  assert "Client disconnected, stopping upstream_task" in log
  # Errors raised by the demo itself. ADK 2.5.0's OpenTelemetry
  # instrumentation logs a benign "Failed to detach context" traceback when
  # the run_live() generator is closed, which is out of the demo's control.
  assert "Unexpected error in streaming tasks" not in log
  assert 'Cannot call "receive"' not in log
