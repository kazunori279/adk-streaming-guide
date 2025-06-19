#!/usr/bin/env python3
"""
Chapter 3.2.1: Your First Streaming Agent
Complete implementation of a "Hello World" streaming agent demonstrating all core concepts.
"""

import asyncio
import os
import time
from dotenv import load_dotenv

from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import InMemoryRunner
from google.adk.agents.run_config import RunConfig, RealtimeInputConfig, VoiceActivityDetectionConfig, AudioTranscriptionConfig
from google.genai.types import Content, Part

# Load environment variables
load_dotenv()

class HelloStreamingAgent:
    """Your first complete streaming agent implementation."""
    
    def __init__(self):
        self.agent = None
        self.runner = None
        self.conversation_active = False
        
    async def setup(self):
        """Set up the streaming agent with optimal configuration."""
        
        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("GOOGLE_API_KEY required for streaming agent")
        
        # Create agent optimized for streaming conversations
        self.agent = Agent(
            name="hello_streaming",
            model="gemini-2.0-flash",  # Gemini Live API model
            instruction="""You are a friendly streaming AI assistant demonstrating 
            real-time conversation capabilities. Your role is to:
            
            - Showcase natural, conversational responses
            - Demonstrate streaming features like real-time processing
            - Keep responses engaging but concise for good streaming experience
            - Show enthusiasm for interactive conversations
            - Help users understand how streaming works through practical examples
            
            Be helpful, informative, and showcase the magic of real-time AI conversation!""",
            description="First streaming agent for learning ADK streaming concepts"
        )
        
        self.runner = InMemoryRunner(agent=self.agent)
        print("✓ Hello Streaming Agent setup complete")
    
    def get_streaming_config(self, include_audio: bool = False) -> RunConfig:
        """Get optimized streaming configuration."""
        
        config_params = {
            "response_modalities": ["TEXT"],
            "streaming_mode": "SSE"
        }
        
        if include_audio:
            config_params["response_modalities"] = ["TEXT", "AUDIO"]
            config_params["realtime_input_config"] = RealtimeInputConfig(
                voice_activity_detection=VoiceActivityDetectionConfig(
                    enabled=True,
                    threshold=0.5
                )
            )
            config_params["input_audio_transcription"] = AudioTranscriptionConfig(enabled=True)
            config_params["output_audio_transcription"] = AudioTranscriptionConfig(enabled=True)
        
        return RunConfig(**config_params)
    
    async def start_conversation(self, welcome_message: str = "Hello! Welcome to streaming AI!"):
        """Start an interactive streaming conversation."""
        
        live_request_queue = LiveRequestQueue()
        run_config = self.get_streaming_config()
        
        # Send welcome message
        welcome = Content(parts=[Part(text=welcome_message)])
        live_request_queue.send_content(welcome)
        live_request_queue.close()
        
        print(f"🎯 Starting streaming conversation with: '{welcome_message}'")
        print("📡 Processing streaming response...")
        
        # Process streaming conversation
        response_count = 0
        async for event in self.runner.run_live(
            user_id="hello_user",
            session_id=f"hello_session_{int(time.time())}",
            live_request_queue=live_request_queue,
            run_config=run_config
        ):
            response_count += 1
            await self._process_event(event, response_count)
            
            # Stop after complete response
            if hasattr(event, 'turn_complete') and event.turn_complete:
                break
        
        print(f"✅ Conversation complete with {response_count} events")
    
    async def _process_event(self, event, event_number: int):
        """Process individual streaming events with detailed output."""
        
        # Show event metadata first
        print(f"   📋 Event #{event_number}: {type(event).__name__}")
        
        # Process content
        if hasattr(event, 'content') and event.content:
            for part_idx, part in enumerate(event.content.parts):
                if hasattr(part, 'text') and part.text:
                    # Show streaming text with formatting
                    text_preview = part.text[:80] + "..." if len(part.text) > 80 else part.text
                    print(f"      🤖 Text part {part_idx + 1}: {text_preview}")
        
        # Show streaming indicators
        if hasattr(event, 'partial'):
            status = "📝 (partial)" if event.partial else "✅ (complete)"
            print(f"      {status}")
        
        if hasattr(event, 'turn_complete') and event.turn_complete:
            print(f"      🏁 Turn completed")
        
        if hasattr(event, 'interrupted') and event.interrupted:
            print(f"      ⚠️ Interrupted")

class StreamingClient:
    """Simple client for testing streaming agent conversations."""
    
    def __init__(self, agent: HelloStreamingAgent):
        self.agent = agent
        self.conversation_count = 0
    
    async def send_message(self, message: str, show_details: bool = True):
        """Send a message to the streaming agent and process response."""
        
        self.conversation_count += 1
        
        live_request_queue = LiveRequestQueue()
        run_config = self.agent.get_streaming_config()
        
        # Send user message
        content = Content(parts=[Part(text=message)])
        live_request_queue.send_content(content)
        live_request_queue.close()
        
        print(f"\n💬 Conversation #{self.conversation_count}")
        print(f"👤 User: {message}")
        print("🔄 Agent processing...")
        
        # Track response details
        response_parts = []
        event_count = 0
        
        # Process response
        async for event in self.agent.runner.run_live(
            user_id="client_user",
            session_id=f"client_session_{self.conversation_count}",
            live_request_queue=live_request_queue,
            run_config=run_config
        ):
            event_count += 1
            
            if show_details:
                print(f"   📊 Event {event_count}: {type(event).__name__}")
            
            # Collect response text
            if hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        response_parts.append(part.text)
                        if not show_details:
                            print(f"🤖 Agent: {part.text}")
            
            # Stop at turn completion
            if hasattr(event, 'turn_complete') and event.turn_complete:
                if show_details:
                    print("   ✅ Response complete")
                break
        
        if show_details:
            full_response = "".join(response_parts)
            print(f"🤖 Complete Response: {full_response}")
            print(f"📈 Statistics: {event_count} events, {len(full_response)} characters")

async def demonstrate_basic_streaming():
    """Demonstrate basic streaming agent functionality."""
    
    print("👋 Basic Streaming Agent Demo")
    print("=" * 40)
    
    # Create and setup agent
    agent = HelloStreamingAgent()
    await agent.setup()
    
    # Start simple conversation
    await agent.start_conversation("Hello! I'm your streaming AI assistant. How can I help you today?")

async def demonstrate_interactive_conversation():
    """Show interactive conversation with multiple exchanges."""
    
    print("\n💬 Interactive Conversation Demo") 
    print("=" * 40)
    
    # Setup agent and client
    agent = HelloStreamingAgent()
    await agent.setup()
    
    client = StreamingClient(agent)
    
    # Series of interactive messages
    conversation_flow = [
        "Hi there! What is streaming AI?",
        "That's interesting! Can you give me a practical example?",
        "How does this compare to regular chatbots?",
        "What are the benefits for users?",
        "Thank you for the explanation!"
    ]
    
    print(f"🎯 Starting interactive conversation with {len(conversation_flow)} exchanges...")
    
    for message in conversation_flow:
        await client.send_message(message, show_details=False)
        await asyncio.sleep(1)  # Brief pause between messages
    
    print(f"✅ Interactive conversation complete!")

async def demonstrate_streaming_features():
    """Showcase specific streaming features and capabilities."""
    
    print("\n🚀 Streaming Features Demo")
    print("=" * 35)
    
    agent = HelloStreamingAgent()
    await agent.setup()
    
    client = StreamingClient(agent)
    
    # Feature demonstration messages
    feature_demos = [
        {
            "message": "Can you demonstrate real-time streaming by counting to 5 slowly?",
            "description": "Real-time response streaming"
        },
        {
            "message": "Tell me about the benefits of bidirectional communication",
            "description": "Bidirectional conversation flow"
        },
        {
            "message": "What makes streaming different from batch processing?",
            "description": "Streaming vs batch comparison"
        }
    ]
    
    for demo in feature_demos:
        print(f"\n🎯 Feature Demo: {demo['description']}")
        await client.send_message(demo['message'], show_details=True)
        await asyncio.sleep(2)

async def demonstrate_configuration_options():
    """Show different streaming configuration options."""
    
    print("\n⚙️ Configuration Options Demo")
    print("=" * 40)
    
    agent = HelloStreamingAgent()
    await agent.setup()
    
    print("📋 Available configuration options:")
    
    # Text-only configuration
    text_config = agent.get_streaming_config(include_audio=False)
    print(f"   📝 Text-only: {text_config.response_modalities}")
    
    # Multimodal configuration
    audio_config = agent.get_streaming_config(include_audio=True)
    print(f"   🎵 With audio: {audio_config.response_modalities}")
    print(f"   🎤 Voice detection: {audio_config.realtime_input_config.voice_activity_detection.enabled if audio_config.realtime_input_config else 'N/A'}")
    
    # Test with text configuration
    live_request_queue = LiveRequestQueue()
    
    test_message = Content(parts=[Part(text="Explain how configuration affects streaming performance")])
    live_request_queue.send_content(test_message)
    live_request_queue.close()
    
    print("🔧 Testing text-only configuration:")
    
    async for event in agent.runner.run_live(
        user_id="config_user",
        session_id="config_session",
        live_request_queue=live_request_queue,
        run_config=text_config
    ):
        if hasattr(event, 'content') and event.content:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    preview = part.text[:60] + "..." if len(part.text) > 60 else part.text
                    print(f"   🤖 {preview}")
        
        if hasattr(event, 'turn_complete') and event.turn_complete:
            break
    
    print("✅ Configuration demonstration complete")

async def main():
    """Run all Hello Streaming Agent demonstrations."""
    
    print("👋 Chapter 3.2.1: Hello Streaming Agent Demonstrations")
    print("=" * 65)
    
    try:
        # Basic streaming
        await demonstrate_basic_streaming()
        
        # Interactive conversation
        await demonstrate_interactive_conversation()
        
        # Streaming features
        await demonstrate_streaming_features()
        
        # Configuration options
        await demonstrate_configuration_options()
        
        print("\n🎉 All Hello Streaming Agent demonstrations complete!")
        print("\nKey Capabilities Demonstrated:")
        print("• Complete streaming agent setup and configuration")
        print("• Real-time conversation processing with detailed event tracking")
        print("• Interactive multi-turn conversations")
        print("• Client-server communication patterns")
        print("• Configurable streaming options (text-only vs multimodal)")
        print("• Event-driven response processing with metadata")
        
        print("\n💡 Next Steps:")
        print("• Try modifying the agent instructions for different personalities")
        print("• Experiment with different RunConfig settings")
        print("• Build upon this foundation for your own streaming applications")
        
    except ValueError as e:
        print(f"❌ Setup Error: {e}")
        print("Please ensure GOOGLE_API_KEY is set in your .env file")
    except Exception as e:
        print(f"❌ Runtime Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())