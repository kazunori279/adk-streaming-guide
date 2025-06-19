#!/usr/bin/env python3
"""
Part 2.4.1: Gemini Live API Integration
Demonstrates direct integration with Gemini Live API through ADK streaming components.
"""

import asyncio
import os
import base64
from dotenv import load_dotenv

from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import InMemoryRunner
from google.adk.agents.run_config import RunConfig
from google.genai.types import Content, Part, Blob

# Load environment variables
load_dotenv()

class GeminiIntegrationDemo:
    """Demonstrates Gemini Live API integration features."""
    
    def __init__(self):
        self.agent = None
        self.runner = None
        
    async def setup(self):
        """Set up Gemini-optimized streaming agent."""
        
        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("GOOGLE_API_KEY required for Gemini Live API integration")
        
        # Create agent optimized for Gemini Live API
        self.agent = Agent(
            name="gemini_live_demo",
            model="gemini-2.0-flash",  # Gemini Live API model
            instruction="""You are demonstrating Gemini Live API capabilities:
            - Respond to text and audio inputs
            - Show awareness of streaming context
            - Demonstrate real-time conversation abilities
            - Handle interruptions gracefully""",
            description="Gemini Live API integration demo agent"
        )
        
        self.runner = InMemoryRunner(agent=self.agent)
        print("✓ Gemini Live API agent setup complete")

async def demonstrate_text_streaming():
    """Show text-based streaming with Gemini Live API."""
    
    print("📝 Text Streaming with Gemini Live API")
    print("=" * 45)
    
    demo = GeminiIntegrationDemo()
    await demo.setup()
    
    live_request_queue = LiveRequestQueue()
    
    # Configure for text streaming
    run_config = RunConfig(
        response_modalities=["TEXT"],
        streaming_mode="SSE"
    )
    
    # Send conversation starter
    greeting = Content(parts=[Part(text="Hello! Can you demonstrate your real-time streaming capabilities?")])
    live_request_queue.send_content(greeting)
    
    # Follow up with a complex question
    await asyncio.sleep(0.1)
    complex_question = Content(parts=[Part(text="Explain how bidirectional streaming works in simple terms.")])
    live_request_queue.send_content(complex_question)
    
    live_request_queue.close()
    
    print("🚀 Starting Gemini Live API text streaming...")
    
    chunk_count = 0
    total_text = ""
    
    async for event in demo.runner.run_live(
        user_id="gemini_text_user",
        session_id="gemini_text_session",
        live_request_queue=live_request_queue,
        run_config=run_config
    ):
        # Track streaming chunks
        if hasattr(event, 'content') and event.content:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    chunk_count += 1
                    chunk_text = part.text
                    total_text += chunk_text
                    
                    # Show streaming behavior
                    print(f"📄 Chunk {chunk_count}: {chunk_text[:60]}{'...' if len(chunk_text) > 60 else ''}")
        
        # Show event metadata
        if hasattr(event, 'partial'):
            print(f"   Partial response: {event.partial}")
        if hasattr(event, 'turn_complete') and event.turn_complete:
            print("   ✅ Turn completed")
            break
    
    print(f"\n📊 Received {chunk_count} text chunks, {len(total_text)} total characters")

async def demonstrate_multimodal_support():
    """Show multimodal input handling with Gemini Live API."""
    
    print("\n🎭 Multimodal Support Demo")
    print("=" * 35)
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Skipping - GOOGLE_API_KEY not found")
        return
    
    demo = GeminiIntegrationDemo()
    await demo.setup()
    
    live_request_queue = LiveRequestQueue()
    
    # Configure for multimodal streaming
    run_config = RunConfig(
        response_modalities=["TEXT", "AUDIO"],
        streaming_mode="SSE"
    )
    
    print("📤 Sending multimodal inputs:")
    
    # 1. Text input
    text_input = Content(parts=[Part(text="I'm going to send you different types of input")])
    live_request_queue.send_content(text_input)
    print("   ✓ Sent text content")
    
    # 2. Simulated audio input
    fake_audio_data = b"simulated_pcm_audio_data_for_demo"
    audio_blob = Blob(
        mime_type="audio/pcm",
        data=base64.b64encode(fake_audio_data).decode()
    )
    live_request_queue.send_realtime(audio_blob)
    print("   ✓ Sent audio blob (simulated)")
    
    # 3. Follow-up text
    followup = Content(parts=[Part(text="How did you handle those different input types?")])
    live_request_queue.send_content(followup)
    print("   ✓ Sent follow-up question")
    
    live_request_queue.close()
    
    print("\n🔄 Processing multimodal conversation:")
    
    response_count = 0
    async for event in demo.runner.run_live(
        user_id="multimodal_user",
        session_id="multimodal_session",
        live_request_queue=live_request_queue,
        run_config=run_config
    ):
        if hasattr(event, 'content') and event.content:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    response_count += 1
                    print(f"   [{response_count}] {part.text}")
        
        # Limit output for demo
        if response_count >= 5:
            break
    
    print(f"✅ Processed multimodal conversation with {response_count} responses")

async def demonstrate_interruption_handling():
    """Show how Gemini Live API handles interruptions."""
    
    print("\n⚠️  Interruption Handling Demo")
    print("=" * 35)
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Skipping - GOOGLE_API_KEY not found")
        return
    
    demo = GeminiIntegrationDemo()
    await demo.setup()
    
    live_request_queue = LiveRequestQueue()
    
    run_config = RunConfig(
        response_modalities=["TEXT"],
        streaming_mode="SSE"
    )
    
    async def simulate_interruption():
        """Simulate user interrupting the agent."""
        
        # Initial long question
        long_question = Content(parts=[Part(text="Please give me a very detailed explanation of machine learning, including history, algorithms, applications, and future trends.")])
        live_request_queue.send_content(long_question)
        print("📤 Sent long question to trigger extended response")
        
        # Wait a bit, then interrupt
        await asyncio.sleep(2)
        
        interruption = Content(parts=[Part(text="Actually, just tell me what machine learning is in one sentence.")])
        live_request_queue.send_content(interruption)
        print("⚠️  Sent interruption after 2 seconds")
        
        await asyncio.sleep(1)
        live_request_queue.close()
    
    async def process_with_interruption():
        """Process the conversation and handle interruption signals."""
        
        interrupted_detected = False
        response_after_interruption = False
        
        async for event in demo.runner.run_live(
            user_id="interruption_user",
            session_id="interruption_session",
            live_request_queue=live_request_queue,
            run_config=run_config
        ):
            # Check for interruption signals
            if hasattr(event, 'interrupted') and event.interrupted:
                interrupted_detected = True
                print("🔄 Interruption detected by Gemini Live API")
            
            # Process responses
            if hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        prefix = "📥 [AFTER INTERRUPTION]" if interrupted_detected and not response_after_interruption else "📥"
                        if interrupted_detected and not response_after_interruption:
                            response_after_interruption = True
                        print(f"{prefix} {part.text}")
            
            # Show turn completion
            if hasattr(event, 'turn_complete') and event.turn_complete:
                print("   ✅ Turn completed")
                if response_after_interruption:
                    break
    
    # Run interruption simulation
    await asyncio.gather(
        simulate_interruption(),
        process_with_interruption()
    )
    
    print("✅ Interruption handling demonstration complete")

async def demonstrate_streaming_metadata():
    """Show metadata and status information from Gemini Live API."""
    
    print("\n📊 Streaming Metadata Demo")
    print("=" * 30)
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Skipping - GOOGLE_API_KEY not found")
        return
    
    demo = GeminiIntegrationDemo()
    await demo.setup()
    
    live_request_queue = LiveRequestQueue()
    
    question = Content(parts=[Part(text="Explain quantum computing in three paragraphs.")])
    live_request_queue.send_content(question)
    live_request_queue.close()
    
    print("🔍 Analyzing streaming metadata from Gemini Live API:")
    
    metadata_collected = {
        'partial_events': 0,
        'complete_events': 0,
        'turn_complete_events': 0,
        'event_types': set(),
        'total_events': 0
    }
    
    async for event in demo.runner.run_live(
        user_id="metadata_user",
        session_id="metadata_session",
        live_request_queue=live_request_queue,
        run_config=RunConfig(response_modalities=["TEXT"])
    ):
        metadata_collected['total_events'] += 1
        metadata_collected['event_types'].add(type(event).__name__)
        
        # Analyze event properties
        if hasattr(event, 'partial') and event.partial:
            metadata_collected['partial_events'] += 1
            print(f"   📝 Partial event #{metadata_collected['total_events']}")
        
        if hasattr(event, 'partial') and not event.partial:
            metadata_collected['complete_events'] += 1
            print(f"   ✅ Complete event #{metadata_collected['total_events']}")
        
        if hasattr(event, 'turn_complete') and event.turn_complete:
            metadata_collected['turn_complete_events'] += 1
            print(f"   🏁 Turn complete event #{metadata_collected['total_events']}")
            break
        
        # Show additional metadata
        if hasattr(event, 'event_id'):
            print(f"      Event ID: {event.event_id}")
        if hasattr(event, 'author'):
            print(f"      Author: {event.author}")
    
    print(f"\n📈 Metadata Summary:")
    print(f"   Total events: {metadata_collected['total_events']}")
    print(f"   Partial events: {metadata_collected['partial_events']}")
    print(f"   Complete events: {metadata_collected['complete_events']}")
    print(f"   Turn complete events: {metadata_collected['turn_complete_events']}")
    print(f"   Event types: {', '.join(sorted(metadata_collected['event_types']))}")

async def main():
    """Run all Gemini Live API integration demonstrations."""
    
    print("🚀 Part 2.4.1: Gemini Live API Integration Demonstrations")
    print("=" * 70)
    
    try:
        # Text streaming
        await demonstrate_text_streaming()
        
        # Multimodal support
        await demonstrate_multimodal_support()
        
        # Interruption handling
        await demonstrate_interruption_handling()
        
        # Streaming metadata
        await demonstrate_streaming_metadata()
        
        print("\n🎉 All Gemini Live API integration demonstrations complete!")
        print("\nKey Features Demonstrated:")
        print("• Real-time text streaming with chunk-by-chunk delivery")
        print("• Multimodal input support (text + audio)")
        print("• Interruption detection and handling")
        print("• Rich metadata and event information")
        print("• Turn completion and conversation state management")
        
    except ValueError as e:
        print(f"❌ Setup Error: {e}")
        print("Please ensure GOOGLE_API_KEY is set in your .env file")
    except Exception as e:
        print(f"❌ Runtime Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())