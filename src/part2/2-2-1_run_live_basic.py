#!/usr/bin/env python3
"""
Part 2.2.1: Basic run_live() Usage
Demonstrates the run_live() method and async generator pattern in ADK streaming.
"""

import asyncio
import os
from dotenv import load_dotenv

from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import InMemoryRunner
from google.adk.agents.run_config import RunConfig
from google.adk.tools import google_search
from google.genai.types import Content, Part

# Load environment variables
load_dotenv()

async def basic_run_live_demo():
    """Demonstrate basic run_live() usage with a simple agent."""
    
    print("🚀 Basic run_live() Demo")
    print("=" * 30)
    
    # Check for API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY not found in environment")
        print("Please set your Gemini API key in .env file")
        return
    
    # 1. Create a simple streaming agent
    agent = Agent(
        name="streaming_demo_agent",
        model="gemini-2.0-flash",
        instruction="You are a helpful assistant that responds to streaming conversations. Keep responses concise.",
        description="A basic agent for demonstrating run_live() functionality",
        tools=[google_search]  # Add search capability
    )
    print("✓ Created streaming agent")
    
    # 2. Create LiveRequestQueue for communication
    live_request_queue = LiveRequestQueue()
    print("✓ Created LiveRequestQueue")
    
    # 3. Create runner for agent execution
    runner = InMemoryRunner(agent=agent)
    print("✓ Created InMemoryRunner")
    
    # 4. Configure streaming settings
    run_config = RunConfig(
        response_modalities=["TEXT"],  # Text-only for this demo
        streaming_mode="SSE"  # Server-Sent Events mode
    )
    print("✓ Configured for text streaming")
    
    # 5. Start the run_live() session
    print("\n🎯 Starting run_live() session...")
    
    # Send a message to the queue
    user_message = Content(parts=[Part(text="Hello! Can you tell me about the weather today?")])
    live_request_queue.send_content(user_message)
    print(f"📤 Sent: {user_message.parts[0].text}")
    
    # Send close signal after the message
    live_request_queue.close()
    
    try:
        # Use run_live() to process the conversation
        event_count = 0
        async for event in runner.run_live(
            user_id="demo_user",
            session_id="demo_session_001",
            live_request_queue=live_request_queue,
            run_config=run_config
        ):
            event_count += 1
            
            # Process different event types
            if hasattr(event, 'content') and event.content:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        print(f"📥 Agent response: {part.text}")
            
            # Show event metadata
            print(f"   Event #{event_count}: {event.event_type if hasattr(event, 'event_type') else 'unknown'}")
            if hasattr(event, 'partial'):
                print(f"   Partial: {event.partial}")
            if hasattr(event, 'turn_complete'):
                print(f"   Turn complete: {event.turn_complete}")
            
            # Stop after reasonable number of events
            if event_count >= 10:
                print("   (Limiting to 10 events for demo)")
                break
                
    except Exception as e:
        print(f"❌ Error during run_live(): {e}")
        return
    
    print(f"\n✅ Completed run_live() session with {event_count} events")

async def demonstrate_async_generator_pattern():
    """Show how run_live() implements the async generator pattern."""
    
    print("\n🔄 Async Generator Pattern Demo")
    print("=" * 40)
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Skipping - GOOGLE_API_KEY not found")
        return
    
    # Simple agent setup
    agent = Agent(
        name="generator_demo",
        model="gemini-2.0-flash",
        instruction="Respond with exactly 3 short sentences, one at a time.",
    )
    
    runner = InMemoryRunner(agent=agent)
    live_request_queue = LiveRequestQueue()
    
    # Send message
    user_message = Content(parts=[Part(text="Tell me 3 facts about Python programming")])
    live_request_queue.send_content(user_message)
    live_request_queue.close()
    
    print("📊 Demonstrating async generator behavior:")
    print("   Each 'yield' from run_live() produces an Event object")
    
    start_time = asyncio.get_event_loop().time()
    
    async for event in runner.run_live(
        user_id="generator_user",
        session_id="generator_session",
        live_request_queue=live_request_queue,
        run_config=RunConfig(response_modalities=["TEXT"])
    ):
        current_time = asyncio.get_event_loop().time()
        elapsed = current_time - start_time
        
        print(f"   [{elapsed:.2f}s] Event yielded: {type(event).__name__}")
        
        # Show content if available
        if hasattr(event, 'content') and event.content:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    print(f"      Content: {part.text[:50]}...")
        
        # Break after a few events for demo
        if elapsed > 10:  # Stop after 10 seconds
            break
    
    print("   ✓ Async generator completed")

async def demonstrate_event_types():
    """Show different types of events yielded by run_live()."""
    
    print("\n📋 Event Types Demo")
    print("=" * 25)
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Skipping - GOOGLE_API_KEY not found")
        return
    
    # Agent with search tool to generate function call events
    agent = Agent(
        name="event_demo",
        model="gemini-2.0-flash",
        instruction="Use Google search to answer questions. Be concise.",
        tools=[google_search]
    )
    
    runner = InMemoryRunner(agent=agent)
    live_request_queue = LiveRequestQueue()
    
    # Send a question that will trigger tool use
    search_question = Content(parts=[Part(text="What's the latest news about artificial intelligence?")])
    live_request_queue.send_content(search_question)
    live_request_queue.close()
    
    print("🔍 Analyzing event types from run_live():")
    
    event_types = set()
    
    async for event in runner.run_live(
        user_id="event_user",
        session_id="event_session",
        live_request_queue=live_request_queue,
        run_config=RunConfig(response_modalities=["TEXT"])
    ):
        event_type = type(event).__name__
        event_types.add(event_type)
        
        print(f"   📄 {event_type}")
        
        # Show key attributes
        key_attrs = []
        if hasattr(event, 'partial') and event.partial is not None:
            key_attrs.append(f"partial={event.partial}")
        if hasattr(event, 'turn_complete') and event.turn_complete is not None:
            key_attrs.append(f"turn_complete={event.turn_complete}")
        if hasattr(event, 'interrupted') and event.interrupted is not None:
            key_attrs.append(f"interrupted={event.interrupted}")
        
        if key_attrs:
            print(f"      Attributes: {', '.join(key_attrs)}")
        
        # Stop after collecting several event types
        if len(event_types) >= 5:
            break
    
    print(f"\n   📊 Found {len(event_types)} event types: {', '.join(sorted(event_types))}")

async def main():
    """Run all demonstrations."""
    
    print("🎬 Part 2.2.1: run_live() Method Demonstrations")
    print("=" * 60)
    
    # Basic run_live usage
    await basic_run_live_demo()
    
    # Async generator pattern
    await demonstrate_async_generator_pattern()
    
    # Event types
    await demonstrate_event_types()
    
    print("\n🎉 All run_live() demonstrations complete!")
    print("\nKey Takeaways:")
    print("• run_live() is an async generator that yields Event objects")
    print("• It enables real-time streaming conversation processing")
    print("• Events contain content, metadata, and state information")
    print("• The method integrates LiveRequestQueue for bidirectional communication")

if __name__ == "__main__":
    asyncio.run(main())