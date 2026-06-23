"""Generic uptime probe for ADK-based bidi WebSocket apps.

Reads apps.yaml at startup, preloads TTS for every probe phrase, exposes:

    GET /health                       - service liveness
    GET /apps                         - list configured app names
    GET /check/{app}/live             - text probe
    GET /check/{app}/live/audio       - audio probe (TTS PCM upload)

See README.md for config schema and Cloud Run deploy instructions.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from config import AppsConfig, load_apps_config
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from probes import ProbeResult, audio_probe, text_probe
from tts import synthesize_query

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    config_path = os.getenv("APPS_CONFIG", "apps.yaml")
    cfg = load_apps_config(config_path)
    logger.info(
        "Loaded %d apps from %s: %s",
        len(cfg.apps),
        config_path,
        [a.name for a in cfg.apps],
    )
    app.state.cfg = cfg

    # Preload TTS at startup for the (audio query, effective voice) each audio
    # probe will use. Fails fast if TTS auth is broken instead of failing on
    # the first probe. The cache dedupes shared (query, voice) tuples.
    for a in cfg.apps:
        await asyncio.to_thread(
            synthesize_query,
            a.effective_audio_query(),
            a.effective_tts_voice(cfg.defaults),
        )

    yield


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    """Service liveness — does not probe upstream apps."""
    return {"status": "ok"}


@app.get("/apps")
async def list_apps(request: Request):
    cfg: AppsConfig = request.app.state.cfg
    return {
        "apps": [
            {"name": a.name, "ws_url": a.ws_url, "query": a.query}
            for a in cfg.apps
        ]
    }


def _resolve_app(request: Request, app_name: str):
    cfg: AppsConfig = request.app.state.cfg
    app_cfg = cfg.get(app_name)
    if not app_cfg:
        raise HTTPException(status_code=404, detail=f"Unknown app: {app_name}")
    return cfg, app_cfg


def _to_response(result: ProbeResult) -> JSONResponse | dict:
    if result.ok:
        body: dict = {"status": "ok"}
        if result.transcript is not None:
            body["transcript"] = result.transcript
        if result.input_transcription is not None:
            body["inputTranscription"] = result.input_transcription
        if result.output_transcription is not None:
            body["outputTranscription"] = result.output_transcription
        return body

    body = {"status": "error", "error": result.error}
    if result.input_transcription is not None:
        body["inputTranscription"] = result.input_transcription
    if result.output_transcription is not None:
        body["outputTranscription"] = result.output_transcription
    return JSONResponse(status_code=503, content=body)


@app.get("/check/{app_name}/live")
async def check_live(request: Request, app_name: str):
    cfg, app_cfg = _resolve_app(request, app_name)
    if not app_cfg.text_probe_enabled:
        return {
            "status": "skipped",
            "reason": "text probe disabled for this app",
        }
    result = await text_probe(app_cfg, cfg.defaults)
    return _to_response(result)


@app.get("/check/{app_name}/live/audio")
async def check_live_audio(request: Request, app_name: str):
    cfg, app_cfg = _resolve_app(request, app_name)
    pcm = synthesize_query(
        app_cfg.effective_audio_query(),
        app_cfg.effective_tts_voice(cfg.defaults),
    )
    result = await audio_probe(app_cfg, cfg.defaults, pcm)
    return _to_response(result)
