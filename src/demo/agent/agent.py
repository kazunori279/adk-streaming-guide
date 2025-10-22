# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Agent definition for the ADK streaming demo application."""

from google.adk import Agent
from google.adk.tools import google_search


def create_streaming_agent(model: str) -> Agent:
    """Create a streaming assistant agent with Google Search capability.

    Args:
        model: The model name to use for the agent (e.g., "gemini-2.0-flash-live-001")

    Returns:
        An Agent instance configured for streaming with Google Search.
    """
    return Agent(
        name="demo_assistant",
        model=model,
        instruction=(
            "You are a helpful assistant with access to Google Search. "
            "When you need current information or need to search for something, "
            "use the google_search tool. Respond concisely and clearly."
        ),
        description="Streaming assistant for Part 2 demo with Google Search capability.",
        tools=[google_search],
    )
