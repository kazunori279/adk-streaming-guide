"""Pydantic models + YAML loader for the bidi-health apps config."""

import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator

_NAME_PATTERN = re.compile(r"^[a-z0-9-]+$")


class TtsVoiceConfig(BaseModel):
    language_code: str = "en-US"
    ssml_gender: Literal["NEUTRAL", "MALE", "FEMALE"] = "NEUTRAL"


class Defaults(BaseModel):
    text_timeout_seconds: int = 20
    audio_timeout_seconds: int = 30
    cuj_timeout_seconds: int = 60
    tts_voice: TtsVoiceConfig = Field(default_factory=TtsVoiceConfig)


class AppConfig(BaseModel):
    name: str
    # Which probe modality this app uses:
    #   "bidi" (default) — WebSocket text/audio probes against an ADK bidi app
    #     (requires ws_url). Exposed at /check/{name}/live[/audio].
    #   "cuj"           — HTTP probe that drives one end-to-end Critical User
    #     Journey against an ADK-workflow app's SSE endpoint (requires
    #     http_url). Exposed at /check/{name}/cuj. Doubles as a keep-warm call
    #     for backends that scale to zero (e.g. Agent Engine reasoning engines).
    probe_type: Literal["bidi", "cuj"] = "bidi"
    ws_url: str | None = None
    http_url: str | None = None
    query: str
    audio_query: str | None = None
    text_timeout_seconds: int | None = None
    audio_timeout_seconds: int | None = None
    cuj_timeout_seconds: int | None = None

    # Optional protocol knobs for ADK apps that vary slightly from bidi-demo:
    #
    # ws_query_params: appended to the WebSocket URL as ?k=v&... — for apps
    #   like adk-live-translator that select language pair via query string.
    # setup_message: a JSON text frame sent BEFORE any other payload — for
    #   apps that require a per-session setup handshake (e.g. translator's
    #   glossary message).
    # text_probe_enabled: set false for audio-only apps where text input is
    #   silently dropped server-side. The /check/{name}/live route returns
    #   200 {"status":"skipped"} instead of attempting a meaningless probe.
    # tts_voice: override the global default voice for this app's audio probe —
    #   for non-English apps that expect input in another language (e.g. a
    #   Japanese agent needs a ja-JP voice so its transcription recognizes the
    #   synthesized query).
    # audio_idle_exit_seconds: end the audio probe after this many seconds
    #   without a frame, instead of waiting for turnComplete / finished=true.
    #   Needed for apps whose model never marks the end of a turn — the
    #   simultaneous translation model (gemini-3.5-live-translate-preview)
    #   streams transcript chunks and sends neither signal.
    ws_query_params: dict[str, str] | None = None
    setup_message: str | None = None
    text_probe_enabled: bool = True
    tts_voice: TtsVoiceConfig | None = None
    audio_idle_exit_seconds: float | None = None

    @field_validator("name")
    @classmethod
    def _name_url_safe(cls, v: str) -> str:
        if not _NAME_PATTERN.fullmatch(v):
            raise ValueError(
                f"name must match {_NAME_PATTERN.pattern!r}, got {v!r}"
            )
        return v

    @field_validator("ws_url")
    @classmethod
    def _ws_url_scheme(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not (v.startswith("ws://") or v.startswith("wss://")):
            raise ValueError(
                f"ws_url must start with ws:// or wss://, got {v!r}"
            )
        return v.rstrip("/")

    @field_validator("http_url")
    @classmethod
    def _http_url_scheme(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError(
                f"http_url must start with http:// or https://, got {v!r}"
            )
        return v.rstrip("/")

    @model_validator(mode="after")
    def _url_matches_probe_type(self) -> "AppConfig":
        if self.probe_type == "bidi" and not self.ws_url:
            raise ValueError(
                f"{self.name!r}: probe_type 'bidi' requires ws_url"
            )
        if self.probe_type == "cuj" and not self.http_url:
            raise ValueError(
                f"{self.name!r}: probe_type 'cuj' requires http_url"
            )
        return self

    def effective_text_timeout(self, defaults: Defaults) -> int:
        return self.text_timeout_seconds or defaults.text_timeout_seconds

    def effective_audio_timeout(self, defaults: Defaults) -> int:
        return self.audio_timeout_seconds or defaults.audio_timeout_seconds

    def effective_cuj_timeout(self, defaults: Defaults) -> int:
        return self.cuj_timeout_seconds or defaults.cuj_timeout_seconds

    def effective_audio_query(self) -> str:
        return self.audio_query or self.query

    def effective_tts_voice(self, defaults: Defaults) -> "TtsVoiceConfig":
        return self.tts_voice or defaults.tts_voice


class AppsConfig(BaseModel):
    defaults: Defaults = Field(default_factory=Defaults)
    apps: list[AppConfig]

    @model_validator(mode="after")
    def _names_unique(self) -> "AppsConfig":
        names = [a.name for a in self.apps]
        if len(names) != len(set(names)):
            dupes = {n for n in names if names.count(n) > 1}
            raise ValueError(f"duplicate app names: {sorted(dupes)}")
        return self

    def get(self, name: str) -> AppConfig | None:
        return next((a for a in self.apps if a.name == name), None)


def load_apps_config(path: str | Path) -> AppsConfig:
    """Parse and validate apps.yaml at `path`."""
    raw = yaml.safe_load(Path(path).read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: top level must be a mapping")
    return AppsConfig.model_validate(raw)
