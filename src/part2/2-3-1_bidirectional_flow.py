#!/usr/bin/env python3
"""
Part 2.3.1: Bidirectional Data Flow Example
Demonstrates complete bidirectional streaming flow with real-time interaction.
"""

import asyncio
import os
import time
from dotenv import load_dotenv

from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import InMemoryRunner
from google.adk.agents.run_config import RunConfig
from google.genai.types import Content, Part

# Load environment variables
load_dotenv()

class StreamingConversationDemo:
    """Demonstrates bidirectional streaming conversation flow."""
    
    def __init__(self):
        self.agent = None
        self.runner = None
        self.live_request_queue = None
        self.conversation_active = False
        
    async def setup(self):
        """Set up the streaming agent and components."""
        
        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("GOOGLE_API_KEY not found. Please set it in your .env file")
        
        # Create conversational agent
        self.agent = Agent(
            name="conversation_agent",
            model="gemini-2.0-flash",
            instruction="""You are a helpful assistant in a real-time streaming conversation.
            - Respond naturally and conversationally
            - Keep initial responses brief but informative
            - Be ready to handle interruptions and follow-up questions
            - Show enthusiasm for interactive conversation""",
            description="Interactive streaming conversation agent"
        )
        
        self.runner = InMemoryRunner(agent=self.agent)
        self.live_request_queue = LiveRequestQueue()
        
        print("✓ Streaming conversation setup complete")
    
    async def start_conversation(self):
        """Start the bidirectional conversation flow."""
        
        run_config = RunConfig(
            response_modalities=["TEXT"],
            streaming_mode="SSE"
        )
        
        # Start the streaming session
        self.conversation_active = True
        
        print("🎯 Starting bidirectional streaming conversation...")
        print("📡 Agent is listening for messages...")
        
        # Process events from the conversation
        async for event in self.runner.run_live(
            user_id="demo_user",
            session_id=f"conversation_{int(time.time())}",
            live_request_queue=self.live_request_queue,
            run_config=run_config
        ):
            await self._handle_event(event)
            
            # Check if conversation should end
            if not self.conversation_active:
                break
    
    async def _handle_event(self, event):
        """Handle events from the streaming conversation."""
        
        # Process text responses
        if hasattr(event, 'content') and event.content:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    print(f"🤖 Agent: {part.text}")
        
        # Show streaming indicators
        if hasattr(event, 'partial') and event.partial:
            print("   📝 (partial response...)")
        
        if hasattr(event, 'turn_complete') and event.turn_complete:
            print("   ✅ (turn complete)")
        
        if hasattr(event, 'interrupted') and event.interrupted:
            print("   ⚠️  (interrupted)")
    
    def send_message(self, text: str):
        """Send a user message to the conversation."""
        content = Content(parts=[Part(text=text)])
        self.live_request_queue.send_content(content)
        print(f"👤 User: {text}")
    
    def end_conversation(self):
        """End the conversation gracefully."""
        self.live_request_queue.close()
        self.conversation_active = False
        print("🔚 Conversation ended")

async def simulate_interactive_conversation():
    """Simulate a realistic bidirectional conversation."""
    
    print("💬 Simulating Interactive Conversation")
    print("=" * 45)
    
    demo = StreamingConversationDemo()
    await demo.setup()
    
    # Create conversation simulation task
    async def conversation_simulation():
        """Simulate user input during the conversation."""
        
        # Initial greeting
        await asyncio.sleep(0.5)
        demo.send_message("Hello! I'm interested in learning about streaming AI.")
        
        # Follow-up questions with delays
        await asyncio.sleep(3)
        demo.send_message("What are the key benefits of bidirectional streaming?")
        
        await asyncio.sleep(4)
        demo.send_message("Can you give me a practical example?")
        
        # Simulate interruption
        await asyncio.sleep(2)
        demo.send_message("Actually, let me ask something different - how does it handle real-time audio?")
        
        await asyncio.sleep(3)
        demo.send_message("Thank you! That was very helpful.")
        
        # End conversation
        await asyncio.sleep(2)
        demo.end_conversation()
    
    # Run conversation and simulation concurrently
    await asyncio.gather(
        demo.start_conversation(),
        conversation_simulation()
    )

async def demonstrate_message_queueing():
    """Show how messages are queued and processed in order."""
    
    print("\n📬 Message Queueing Demo")
    print("=" * 30)
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Skipping - GOOGLE_API_KEY not found")
        return
    
    # Quick setup
    agent = Agent(
        name="queue_demo",
        model="gemini-2.0-flash",
        instruction="Respond to each message with a brief acknowledgment and the message number you received."
    )
    
    runner = InMemoryRunner(agent=agent)
    live_request_queue = LiveRequestQueue()
    
    # Send multiple messages rapidly
    messages = [
        "Message 1: Hello",
        "Message 2: How are you?", 
        "Message 3: What's the weather like?",
        "Message 4: Tell me a joke",
        "Message 5: Goodbye"
    ]
    
    print("📤 Sending messages rapidly to queue:")
    for i, msg in enumerate(messages, 1):
        content = Content(parts=[Part(text=msg)])
        live_request_queue.send_content(content)
        print(f"   [{i}] Queued: {msg}")
    
    live_request_queue.close()
    
    print("\n📥 Processing queued messages:")
    
    response_count = 0
    async for event in runner.run_live(
        user_id="queue_user",
        session_id="queue_session",
        live_request_queue=live_request_queue,
        run_config=RunConfig(response_modalities=["TEXT"])
    ):
        if hasattr(event, 'content') and event.content:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    response_count += 1
                    print(f"   [{response_count}] Agent: {part.text}")
        
        # Stop after processing all messages
        if response_count >= len(messages):
            break
    
    print(f"✅ Processed {response_count} responses for {len(messages)} messages")

async def demonstrate_concurrent_streaming():
    """Show how streaming handles concurrent operations."""
    
    print("\n🔄 Concurrent Streaming Demo")
    print("=" * 35)
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Skipping - GOOGLE_API_KEY not found")
        return
    
    agent = Agent(
        name="concurrent_demo",
        model="gemini-2.0-flash",
        instruction="You are demonstrating concurrent streaming. Respond promptly to each input."
    )
    
    runner = InMemoryRunner(agent=agent)
    live_request_queue = LiveRequestQueue()
    
    # Track events for analysis
    events_received = []
    start_time = time.time()
    
    async def send_messages():
        """Send messages at intervals."""
        messages = [
            "First message",
            "Second message after delay",
            "Third message"
        ]
        
        for i, msg in enumerate(messages):
            await asyncio.sleep(1.5)  # Stagger messages
            content = Content(parts=[Part(text=msg)])
            live_request_queue.send_content(content)
            timestamp = time.time() - start_time
            print(f"📤 [{timestamp:.1f}s] Sent: {msg}")
        
        await asyncio.sleep(1)
        live_request_queue.close()
    
    async def process_responses():
        """Process streaming responses."""
        async for event in runner.run_live(
            user_id="concurrent_user",
            session_id="concurrent_session",
            live_request_queue=live_request_queue,
            run_config=RunConfig(response_modalities=["TEXT"])
        ):
            timestamp = time.time() - start_time
            events_received.append((timestamp, event))
            
            if hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        print(f"📥 [{timestamp:.1f}s] Agent: {part.text[:50]}...")
    
    # Run concurrently
    await asyncio.gather(
        send_messages(),
        process_responses()
    )
    
    print(f"📊 Received {len(events_received)} events over {time.time() - start_time:.1f} seconds")

async def main():
    """Run all bidirectional flow demonstrations."""
    
    print("🌊 Part 2.3.1: Bidirectional Data Flow Demonstrations")
    print("=" * 65)
    
    try:
        # Interactive conversation
        await simulate_interactive_conversation()
        
        # Message queueing
        await demonstrate_message_queueing()
        
        # Concurrent streaming
        await demonstrate_concurrent_streaming()
        
        print("\n🎉 All bidirectional flow demonstrations complete!")
        print("\nKey Insights:")
        print("• LiveRequestQueue enables real-time bidirectional communication")
        print("• Messages are processed in order while maintaining streaming responsiveness")
        print("• The system handles concurrent operations efficiently")
        print("• Events provide detailed metadata about the conversation state")
        
    except ValueError as e:
        print(f"❌ Setup Error: {e}")
    except Exception as e:
        print(f"❌ Runtime Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())