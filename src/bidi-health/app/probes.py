"""Pure async probe functions: text and audio.

Each opens a WebSocket to the target ADK bidi app, exchanges one turn, and
returns a `ProbeResult`. Routes in main.py wrap these into HTTP responses.
"""

import asyncio
import json
import logging
import uuid
from dataclasses import dataclass
from urllib.parse import urlencode

import httpx
import websockets
from config import AppConfig, Defaults

logger = logging.getLogger(__name__)

# Audio streaming constants — Live API input format
AUDIO_SAMPLE_RATE = 16000
AUDIO_BYTES_PER_SAMPLE = 2  # 16-bit
AUDIO_CHUNK_MS = 100
AUDIO_CHUNK_BYTES = AUDIO_SAMPLE_RATE * AUDIO_BYTES_PER_SAMPLE * AUDIO_CHUNK_MS // 1000
AUDIO_TRAILING_SILENCE_MS = 1500  # let automatic VAD detect end-of-speech

HTTP_OK = 200


@dataclass
class ProbeResult:
    ok: bool
    transcript: str | None = None
    input_transcription: str | None = None
    output_transcription: str | None = None
    error: str | None = None


class _TranscriptIdleClock:
    """Time since the last transcription, for apps that never end a turn.

    The simultaneous translation model marks no end of turn — neither
    `turnComplete` nor `finished=true` ever arrives — so the probe has to
    decide for itself when the answer is over. A gap between *frames* is no
    use: that model streams output audio continuously, silence included, so
    frames never stop. The transcript does go quiet, so that is what this
    watches. With `idle` None the clock never expires and the probe relies on
    the ordinary end-of-turn markers.
    """

    def __init__(self, idle: float | None):
        self.idle = idle
        self._last = asyncio.get_running_loop().time()

    def touch(self) -> None:
        """Record a transcription frame, restarting the quiet window."""
        self._last = asyncio.get_running_loop().time()

    def remaining(self) -> float | None:
        if self.idle is None:
            return None
        return self._last + self.idle - asyncio.get_running_loop().time()


async def _frames(ws, clock: "_TranscriptIdleClock"):
    """Yield WebSocket frames until the connection closes or `clock` expires.

    Otherwise behaves like `async for message in ws`: a clean close ends the
    iteration, an abnormal one raises.
    """
    while True:
        timeout = clock.remaining()
        if timeout is not None and timeout <= 0:
            return
        try:
            yield await asyncio.wait_for(ws.recv(), timeout=timeout)
        except asyncio.TimeoutError:
            return
        except websockets.exceptions.ConnectionClosedOK:
            return


def _ws_url_for(app: AppConfig, prefix: str) -> str:
    user_id = "uptime-check"
    session_id = f"{prefix}-{uuid.uuid4().hex[:12]}"
    url = f"{app.ws_url}/ws/{user_id}/{session_id}"
    if app.ws_query_params:
        url = f"{url}?{urlencode(app.ws_query_params)}"
    return url


async def text_probe(app: AppConfig, defaults: Defaults) -> ProbeResult:
    """Send a text query, drain events until turn_complete, return transcript.

    Collects from both `content.parts[].text` (half-cascade models) and
    `outputTranscription.text` (native-audio models) so the same probe works
    against either modality. Retries once on abrupt WebSocket close — the
    upstream commonly drops the connection without a close frame when it
    can't open a Live API session (e.g. transient RESOURCE_EXHAUSTED).
    """
    timeout = app.effective_text_timeout(defaults)
    transcript_parts: list[str] = []

    for attempt in range(2):
        transcript_parts.clear()
        ws_url = _ws_url_for(app, "health")

        async def _check():
            async with websockets.connect(ws_url) as ws:
                if app.setup_message:
                    await ws.send(app.setup_message)
                await ws.send(json.dumps({"type": "text", "text": app.query}))
                async for message in ws:
                    event = json.loads(message)

                    content = event.get("content")
                    if content and content.get("parts"):
                        for part in content["parts"]:
                            if part.get("text"):
                                transcript_parts.append(part["text"])

                    ot = event.get("outputTranscription")
                    if ot and ot.get("text"):
                        transcript_parts[:] = [ot["text"]]

                    if event.get("turnComplete") or (ot and ot.get("finished")):
                        break

        try:
            await asyncio.wait_for(_check(), timeout=timeout)
            break
        except asyncio.TimeoutError:
            return ProbeResult(ok=False, error="Model response timed out")
        except websockets.exceptions.ConnectionClosed as e:
            if attempt == 0:
                logger.warning(
                    "text_probe %s closed early (%s); retrying once",
                    app.name,
                    e,
                )
                await asyncio.sleep(2)
                continue
            return ProbeResult(ok=False, error=str(e))
        except Exception as e:
            return ProbeResult(ok=False, error=str(e))

    transcript = "".join(transcript_parts)
    if not transcript:
        return ProbeResult(ok=False, error="No transcript received")
    return ProbeResult(ok=True, transcript=transcript)


async def cuj_probe(app: AppConfig, defaults: Defaults) -> ProbeResult:
    """Drive one end-to-end CUJ against an ADK-workflow app's SSE endpoint.

    POSTs the objective to ``{http_url}/api/chat`` (form fields ``prompt`` and
    ``session_id``) and reads the Server-Sent Events stream until a
    ``WorkflowComplete`` event arrives. The probe succeeds if that event is
    seen without a terminal error frame.

    Besides health, this is a keep-warm call: driving a real CUJ exercises the
    full Control Room -> Planner -> Executor path, so backends that scale to
    zero (the demo's Agent Engine reasoning engines) stay hot between runs.

    Transient mid-run error frames (e.g. an executor's cold-start
    ``FAILED_PRECONDITION`` that the re-planner recovers from, pushed with
    ``name: "execution"``) are NOT failures — only a terminal ``name: "error"``
    frame or a missing ``WorkflowComplete`` is. The final status and report are
    returned as the transcript so a Cloud Monitoring matcher can require a
    specific word (e.g. ``SUCCESS``).

    Retries once on abrupt connection drops (transient upstream restart);
    timeouts are not retried — a cold/slow backend stays slow.
    """
    timeout = app.effective_cuj_timeout(defaults)
    url = f"{app.http_url}/api/chat"

    for attempt in range(2):
        session_id = f"health-cuj-{uuid.uuid4().hex[:12]}"
        # Mutated inside _check(); bound as defaults to avoid late-binding.
        state = {"complete": False, "status": None, "report": None, "error": None}

        async def _check(session_id=session_id, state=state):
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream(
                    "POST",
                    url,
                    data={"prompt": app.query, "session_id": session_id},
                ) as resp:
                    if resp.status_code != HTTP_OK:
                        body = (await resp.aread()).decode("utf-8", "replace")
                        state["error"] = f"HTTP {resp.status_code}: {body[:200]}"
                        return
                    async for line in resp.aiter_lines():
                        stripped = line.strip()
                        if not stripped.startswith("data:"):
                            continue
                        raw = stripped[len("data:") :].strip()
                        if not raw:
                            continue
                        try:
                            event = json.loads(raw)
                        except json.JSONDecodeError:
                            continue

                        # Terminal error event (not a transient executor blip,
                        # which is pushed with name "execution").
                        if event.get("name") == "error" or event.get("type") == "error":
                            state["error"] = str(
                                event.get("text") or event.get("message") or event
                            )[:300]

                        if event.get("event_type") == "WorkflowComplete":
                            out = event.get("output") or {}
                            state["complete"] = True
                            state["status"] = out.get("status")
                            state["report"] = out.get("report")
                            return

        try:
            await asyncio.wait_for(_check(), timeout=timeout)
        except asyncio.TimeoutError:
            return ProbeResult(ok=False, error="CUJ timed out")
        except (
            httpx.ConnectError,
            httpx.RemoteProtocolError,
            httpx.ReadError,
        ) as e:
            if attempt == 0:
                logger.warning(
                    "cuj_probe %s connection error (%s); retrying once",
                    app.name,
                    e,
                )
                await asyncio.sleep(2)
                continue
            return ProbeResult(ok=False, error=str(e))
        except Exception as e:
            return ProbeResult(ok=False, error=str(e))

        if state["complete"]:
            transcript = "\n".join(
                p for p in (state["status"], state["report"]) if p
            )
            return ProbeResult(ok=True, transcript=transcript or "WorkflowComplete")
        return ProbeResult(
            ok=False,
            error=state["error"] or "No WorkflowComplete event received",
        )

    return ProbeResult(ok=False, error="CUJ probe exhausted retries")


async def audio_probe(app: AppConfig, defaults: Defaults, pcm: bytes) -> ProbeResult:
    """Stream pre-synthesized PCM as binary frames + trailing silence.

    Validates BOTH `inputTranscription` (Vertex transcribed what we sent) and
    `outputTranscription` (model produced an audio response). Retries once on
    abrupt WebSocket close — see text_probe for rationale.

    Four transcription patterns exist across models:

    1. Non-grounding apps (bidi-demo): cumulative partials → finished=true
       with full text → turnComplete.  Each partial replaces the previous.
    2. Grounding apps (grounding-demo): turnComplete fires FIRST with no
       output, then cumulative partials arrive late, ending with finished=true.
    3. Translator agent mode (gemini-3.1-flash-live-preview): incremental
       (non-cumulative) chunks → turnComplete.  finished=true is never sent.
    4. Translator simultaneous mode (gemini-3.5-live-translate-preview):
       incremental chunks and NOTHING else — neither finished=true nor
       turnComplete ever arrives, so the turn has no end marker.

    Strategy: append all partials (works for both cumulative and incremental)
    and exit on finished=true OR turnComplete — whichever comes first.
    For pattern 2, turnComplete arrives with no output yet, so we drain
    until finished=true or a 15s timeout.  Pattern 4 offers no marker to wait
    for, so those apps set `audio_idle_exit_seconds` and the probe ends once
    the transcript has been quiet that long — see `_TranscriptIdleClock`.
    """
    timeout = app.effective_audio_timeout(defaults)
    idle_exit = app.audio_idle_exit_seconds
    input_parts: list[str] = []
    output_parts: list[str] = []

    silence = b"\x00" * (
        AUDIO_SAMPLE_RATE * AUDIO_BYTES_PER_SAMPLE * AUDIO_TRAILING_SILENCE_MS // 1000
    )
    payload = pcm + silence

    for attempt in range(2):
        input_parts.clear()
        output_parts.clear()
        ws_url = _ws_url_for(app, "health-audio")

        async def _check():
            async with websockets.connect(ws_url) as ws:
                if app.setup_message:
                    await ws.send(app.setup_message)
                for offset in range(0, len(payload), AUDIO_CHUNK_BYTES):
                    await ws.send(payload[offset : offset + AUDIO_CHUNK_BYTES])
                    await asyncio.sleep(AUDIO_CHUNK_MS / 1000)

                # Started after the upload so the quiet window measures the
                # response, not the time spent streaming audio in.
                clock = _TranscriptIdleClock(idle_exit)

                async for message in _frames(ws, clock):
                    event = json.loads(message)

                    it = event.get("inputTranscription")
                    if it and it.get("text"):
                        input_parts.append(it["text"])
                        clock.touch()
                    ot = event.get("outputTranscription")
                    if ot and ot.get("text"):
                        output_parts.append(ot["text"])
                        clock.touch()

                    if ot and ot.get("finished") and output_parts:
                        break
                    if event.get("turnComplete") and output_parts:
                        break

                    if event.get("turnComplete") and not output_parts:
                        async def _drain():
                            async for msg in ws:
                                ev = json.loads(msg)
                                o = ev.get("outputTranscription")
                                if o and o.get("text"):
                                    output_parts.append(o["text"])
                                if o and o.get("finished") and output_parts:
                                    break
                        try:
                            await asyncio.wait_for(_drain(), timeout=15)
                        except asyncio.TimeoutError:
                            pass
                        break

        try:
            await asyncio.wait_for(_check(), timeout=timeout)
            break
        except asyncio.TimeoutError:
            return ProbeResult(
                ok=False,
                error="Audio probe timed out",
                input_transcription="".join(input_parts) or None,
                output_transcription="".join(output_parts) or None,
            )
        except websockets.exceptions.ConnectionClosed as e:
            if attempt == 0:
                logger.warning(
                    "audio_probe %s closed early (%s); retrying once",
                    app.name,
                    e,
                )
                await asyncio.sleep(2)
                continue
            return ProbeResult(ok=False, error=str(e))
        except Exception as e:
            return ProbeResult(ok=False, error=str(e))

    input_transcription = "".join(input_parts)
    output_transcription = "".join(output_parts)

    if not input_transcription:
        return ProbeResult(
            ok=False,
            error="No input transcription (audio not recognized)",
        )
    if not output_transcription:
        return ProbeResult(
            ok=False,
            error="No output transcription (model did not respond)",
            input_transcription=input_transcription,
        )

    return ProbeResult(
        ok=True,
        input_transcription=input_transcription,
        output_transcription=output_transcription,
    )
