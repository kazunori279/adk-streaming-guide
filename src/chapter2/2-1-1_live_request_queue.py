#!/usr/bin/env python3
"""
Chapter 2.1.1: LiveRequestQueue Operations
Demonstrates the core functionality of LiveRequestQueue for bidirectional streaming.
"""

import asyncio
import base64
from google.adk.agents import LiveRequestQueue, LiveRequest
from google.genai.types import Content, Part, Blob

async def demonstrate_live_request_queue():
    """Demonstrate LiveRequestQueue operations and data flow."""
    
    print("🔄 LiveRequestQueue Operations Demo")
    print("=" * 50)
    
    # Create a LiveRequestQueue instance
    live_request_queue = LiveRequestQueue()
    print("✓ Created LiveRequestQueue instance")
    
    # 1. Sending Text Content
    print("\n📝 Sending Text Content:")
    text_content = Content(parts=[Part(text="Hello, streaming world!")])
    live_request_queue.send_content(text_content)
    print(f"   Sent: {text_content.parts[0].text}")
    
    # 2. Sending Audio Blob
    print("\n🎵 Sending Audio Blob:")
    # Simulate audio data (in real usage, this would be actual audio)
    fake_audio_data = b"fake_pcm_audio_data_here"
    audio_blob = Blob(
        mime_type="audio/pcm",
        data=base64.b64encode(fake_audio_data).decode()
    )
    live_request_queue.send_realtime(audio_blob)
    print(f"   Sent audio blob: {audio_blob.mime_type}, {len(audio_blob.data)} chars")
    
    # 3. Custom LiveRequest
    print("\n🔧 Sending Custom LiveRequest:")
    custom_request = LiveRequest(
        content=Content(parts=[Part(text="Custom message")]),
        close=False
    )
    live_request_queue.send(custom_request)
    print(f"   Sent custom request with content: {custom_request.content.parts[0].text}")
    
    # 4. Close Signal
    print("\n🔚 Sending Close Signal:")
    close_request = LiveRequest(close=True)
    live_request_queue.send(close_request)
    print("   Sent close signal")
    
    # 5. Consuming from Queue (async)
    print("\n📥 Consuming from Queue:")
    consumed_count = 0
    
    try:
        while consumed_count < 4:  # We sent 4 messages
            request = await asyncio.wait_for(live_request_queue.get(), timeout=1.0)
            consumed_count += 1
            
            if request.content:
                print(f"   [{consumed_count}] Content: {request.content.parts[0].text}")
            elif request.blob:
                print(f"   [{consumed_count}] Blob: {request.blob.mime_type}")
            elif request.close:
                print(f"   [{consumed_count}] Close signal received")
                break
                
    except asyncio.TimeoutError:
        print(f"   Timeout - consumed {consumed_count} messages")

def demonstrate_queue_internals():
    """Show the internal structure and properties of LiveRequestQueue."""
    
    print("\n🔍 LiveRequestQueue Internals")
    print("=" * 40)
    
    queue = LiveRequestQueue()
    
    # Show queue properties
    print(f"Queue type: {type(queue._queue).__name__}")
    print(f"Queue empty: {queue._queue.empty()}")
    print(f"Queue size: {queue._queue.qsize()}")
    
    # Add some items
    queue.send_content(Content(parts=[Part(text="Test message 1")]))
    queue.send_content(Content(parts=[Part(text="Test message 2")]))
    
    print(f"After adding 2 items:")
    print(f"  Queue empty: {queue._queue.empty()}")
    print(f"  Queue size: {queue._queue.qsize()}")

def demonstrate_message_types():
    """Demonstrate different types of messages that can be sent."""
    
    print("\n📋 Message Types Demo")
    print("=" * 30)
    
    queue = LiveRequestQueue()
    
    # 1. Text-only content
    text_content = Content(parts=[Part(text="Simple text message")])
    print(f"1. Text Content: {text_content.parts[0].text}")
    
    # 2. Multi-part content
    multi_content = Content(parts=[
        Part(text="Text part: "),
        Part(text="Another text part")
    ])
    print(f"2. Multi-part Content: {len(multi_content.parts)} parts")
    
    # 3. Audio blob
    audio_blob = Blob(
        mime_type="audio/pcm",
        data=base64.b64encode(b"audio_data").decode()
    )
    print(f"3. Audio Blob: {audio_blob.mime_type}")
    
    # 4. Video blob
    video_blob = Blob(
        mime_type="video/mp4",
        data=base64.b64encode(b"video_data").decode()
    )
    print(f"4. Video Blob: {video_blob.mime_type}")
    
    # Send all types
    queue.send_content(text_content)
    queue.send_content(multi_content)
    queue.send_realtime(audio_blob)
    queue.send_realtime(video_blob)
    
    print(f"✓ Sent {queue._queue.qsize()} messages to queue")

async def demonstrate_concurrent_access():
    """Demonstrate concurrent producers and consumers."""
    
    print("\n🔄 Concurrent Access Demo")
    print("=" * 35)
    
    queue = LiveRequestQueue()
    
    async def producer(name: str, count: int):
        """Simulate a producer sending messages."""
        for i in range(count):
            content = Content(parts=[Part(text=f"Message {i+1} from {name}")])
            queue.send_content(content)
            await asyncio.sleep(0.1)  # Simulate some processing time
        print(f"✓ {name} finished sending {count} messages")
    
    async def consumer(name: str):
        """Simulate a consumer reading messages."""
        consumed = 0
        while consumed < 6:  # Total messages from both producers
            try:
                request = await asyncio.wait_for(queue.get(), timeout=2.0)
                if request.content:
                    consumed += 1
                    print(f"   {name} received: {request.content.parts[0].text}")
            except asyncio.TimeoutError:
                print(f"   {name} timeout after {consumed} messages")
                break
    
    # Run concurrent producers and consumer
    await asyncio.gather(
        producer("Producer-A", 3),
        producer("Producer-B", 3),
        consumer("Consumer-1")
    )

async def main():
    """Run all demonstrations."""
    
    # Basic queue operations
    await demonstrate_live_request_queue()
    
    # Queue internals
    demonstrate_queue_internals()
    
    # Message types
    demonstrate_message_types()
    
    # Concurrent access
    await demonstrate_concurrent_access()
    
    print("\n🎉 LiveRequestQueue demonstration complete!")

if __name__ == "__main__":
    asyncio.run(main())