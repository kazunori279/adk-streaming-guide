"""ADK bidirectional streaming session management.

Handles all ADK streaming API interactions including LiveRequestQueue,
Runner.run_live(), and session management.
"""
from __future__ import annotations

from typing import AsyncGenerator

from pydantic import BaseModel, Field, ValidationError
from google.adk import Runner
from google.adk.agents.live_request_queue import LiveRequest, LiveRequestQueue
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from .agent.agent import create_streaming_agent


APP_NAME = "adk-streaming-demo"
DEFAULT_USER_ID = "demo-user"
DEFAULT_SESSION_ID = "demo-session"
DEFAULT_MODEL = "gemini-2.0-flash-live-001"

# Simple in-memory session service for demo use
SESSION_SERVICE = InMemorySessionService()


class SessionParams(BaseModel):
    """Parameters for creating a streaming session."""

    # Session identity
    model: str = DEFAULT_MODEL
    user_id: str = DEFAULT_USER_ID
    session_id: str = DEFAULT_SESSION_ID

    # Streaming configuration
    text_only: bool = True
    enable_input_transcription: bool = Field(default=False, alias="in_transcription")
    enable_output_transcription: bool = Field(default=False, alias="out_transcription")
    enable_vad: bool = Field(default=False, alias="vad")
    enable_proactivity: bool = Field(default=False, alias="proactivity")
    enable_affective: bool = Field(default=False, alias="affective")
    enable_session_resumption: bool = Field(default=False, alias="resume")

    class Config:
        populate_by_name = True  # Allow both field name and alias


class StreamingSession:
    """Encapsulates all ADK streaming components for a single session."""

    def __init__(self, params: SessionParams):
        """Initialize streaming session with parameters.

        Args:
            params: Session parameters including model, user_id, session_id, and streaming config
        """
        self.user_id = params.user_id
        self.session_id = params.session_id
        self._live_request_queue = LiveRequestQueue()
        self._run_config = _create_run_config(params)
        self._runner = Runner(
            app_name=APP_NAME,
            agent=create_streaming_agent(params.model),
            session_service=SESSION_SERVICE,
        )

    def send_activity_start(self) -> None:
        """Signal the start of user activity."""
        # Convenience passthrough to LiveRequestQueue
        self._live_request_queue.send_activity_start()

    def send_activity_end(self) -> None:
        """Signal the end of user activity."""
        self._live_request_queue.send_activity_end()

    def send_request(self, request: LiveRequest) -> None:
        """Send a pre-constructed LiveRequest directly to the queue.

        Useful when the client sends a full LiveRequest JSON (e.g., activity, blob, close).
        """
        self._live_request_queue.send(request)

    def send_text(self, text: str) -> None:
        """Send a text message to the agent.

        Note: Do not emit activity_start/activity_end for text-only interactions.
        This avoids conflicts with automatic activity detection on the backend.
        Activity signals remain available via send_activity_start/send_activity_end
        for future voice workflows.
        """
        content = types.Content(parts=[types.Part(text=text)])
        self._live_request_queue.send_content(content)

    def close(self) -> None:
        """Send close signal to the agent."""
        self._live_request_queue.close()

    async def stream_events_as_json(
        self, initial_message: str | None = None
    ) -> AsyncGenerator[str, None]:
        """Stream events from the agent as JSON strings.

        Args:
            initial_message: Optional initial message to send when streaming starts

        Yields:
            JSON-serialized event strings
        """
        if initial_message:
            self.send_text(initial_message)

        async for event in self._runner.run_live(
            user_id=self.user_id,
            session_id=self.session_id,
            live_request_queue=self._live_request_queue,
            run_config=self._run_config,
        ):
            yield event.model_dump_json(exclude_none=True, by_alias=True)


async def get_or_create_session(user_id: str, session_id: str) -> None:
    """Get existing session or create a new one."""
    sess = await SESSION_SERVICE.get_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    if not sess:
        await SESSION_SERVICE.create_session(
            app_name=APP_NAME, user_id=user_id, session_id=session_id
        )


def _create_run_config(params: SessionParams) -> RunConfig:
    """Create a RunConfig from SessionParams.

    Args:
        params: Session parameters including streaming configuration

    Returns:
        RunConfig instance
    """
    response_modalities = ["TEXT"] if params.text_only else ["TEXT", "AUDIO"]
    rc = RunConfig(
        response_modalities=response_modalities,
        streaming_mode=StreamingMode.BIDI,
    )
    if params.enable_input_transcription:
        rc.input_audio_transcription = types.AudioTranscriptionConfig(enabled=True)
    if params.enable_output_transcription:
        rc.output_audio_transcription = types.AudioTranscriptionConfig(enabled=True)
    if params.enable_vad:
        rc.realtime_input_config = types.RealtimeInputConfig(
            voice_activity_detection=types.VoiceActivityDetectionConfig(enabled=True)
        )
    if params.enable_affective:
        rc.enable_affective_dialog = True
    if params.enable_proactivity:
        rc.proactivity = types.ProactivityConfig()
    if params.enable_session_resumption:
        rc.session_resumption = types.SessionResumptionConfig(transparent=True)
    return rc


def parse_message(data: str) -> tuple[LiveRequest | None, str | None, bool]:
    """Parse incoming message as LiveRequest, close signal, or plain text.

    Args:
        data: Raw message string (JSON or plain text)

    Returns:
        Tuple of (live_request, text_message, is_close_signal)
        - If full LiveRequest JSON: (LiveRequest, None, req.close)
        - If plain text: (None, text, False)
    """
    try:
        req = LiveRequest.model_validate_json(data)
        return req, None, bool(req.close)
    except ValidationError:
        # Treat as plain text
        return None, data, False
