"""Google Search Agent definition for ADK Bidi-streaming demo."""

import os
from google.adk.agents import Agent
from google.adk.tools import google_search


# Default models for Live API with native audio support:
# - Gemini Live API: gemini-2.5-flash-native-audio-preview-09-2025
# - Vertex AI Live API: gemini-live-2.5-flash-preview-native-audio-09-2025
agent = Agent(
    name="google_search_agent",
    model=os.getenv("DEMO_AGENT_MODEL", "gemini-2.5-flash-native-audio-preview-09-2025"),
    tools=[google_search],
    instruction="You are a helpful assistant that can search the web."
)
