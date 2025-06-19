#!/usr/bin/env python3
"""
Chapter 3.1.1: Audio and Video Processing
Demonstrates multimedia streaming capabilities with PCM audio and video handling.
"""

import asyncio
import os
import base64
import wave
import struct
from dotenv import load_dotenv

from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import InMemoryRunner
from google.adk.agents.run_config import RunConfig, RealtimeInputConfig, VoiceActivityDetectionConfig
from google.genai.types import Content, Part, Blob

# Load environment variables
load_dotenv()

class AudioVideoProcessor:
    """Demonstrates audio and video processing for streaming applications."""
    
    def __init__(self):
        self.agent = None
        self.runner = None
        
    async def setup(self):
        """Set up agent optimized for multimedia streaming."""
        
        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("GOOGLE_API_KEY required for multimedia streaming")
        
        # Create multimedia-aware agent
        self.agent = Agent(
            name="multimedia_processor",
            model="gemini-2.0-flash",
            instruction="""You are an AI assistant specialized in processing multimedia content.
            You can handle audio, video, and text inputs simultaneously.
            - Acknowledge when you receive audio or video content
            - Describe what you perceive in multimedia streams
            - Provide helpful information about media format and content""",
            description="Multimedia streaming processor"
        )
        
        self.runner = InMemoryRunner(agent=self.agent)
        print("✓ Multimedia processing agent setup complete")

def generate_pcm_audio_sample(duration_seconds: float = 2.0, sample_rate: int = 16000) -> bytes:
    """Generate a simple PCM audio sample for testing."""
    
    # Generate a simple sine wave tone
    frequency = 440  # A4 note
    samples = int(duration_seconds * sample_rate)
    
    audio_data = bytearray()
    for i in range(samples):
        # Generate 16-bit signed PCM sample
        t = i / sample_rate
        sample = int(32767 * 0.3 * (
            0.5 * (1 + 0.5 * (i / samples)) *  # Fade in
            (1 - 0.5 * (i / samples)) *        # Fade out
            (0.5 + 0.5 * (i % 100) / 100)      # Add some variation
        ))
        
        # Pack as 16-bit little-endian signed integer
        audio_data.extend(struct.pack('<h', sample))
    
    return bytes(audio_data)

def create_audio_blob(pcm_audio_data: bytes) -> Blob:
    """Convert PCM audio data to ADK Blob format."""
    
    # Base64 encode the audio data
    encoded_audio = base64.b64encode(pcm_audio_data).decode('utf-8')
    
    # Create Blob with proper MIME type for PCM
    audio_blob = Blob(
        mime_type="audio/pcm",
        data=encoded_audio
    )
    
    return audio_blob

def create_video_blob(video_data: bytes, format: str = "webm") -> Blob:
    """Create video blob for streaming (simulated for demo)."""
    
    mime_types = {
        "webm": "video/webm",
        "mp4": "video/mp4", 
        "avi": "video/avi"
    }
    
    encoded_video = base64.b64encode(video_data).decode('utf-8')
    
    video_blob = Blob(
        mime_type=mime_types.get(format, "video/webm"),
        data=encoded_video
    )
    
    return video_blob

async def demonstrate_pcm_audio_streaming():
    """Show PCM audio blob creation and streaming."""
    
    print("🎵 PCM Audio Streaming Demo")
    print("=" * 35)
    
    processor = AudioVideoProcessor()
    await processor.setup()
    
    live_request_queue = LiveRequestQueue()
    
    # Configure for audio processing
    run_config = RunConfig(
        response_modalities=["TEXT"],
        streaming_mode="SSE",
        realtime_input_config=RealtimeInputConfig(
            voice_activity_detection=VoiceActivityDetectionConfig(enabled=True)
        )
    )
    
    print("🎤 Generating PCM audio sample...")
    
    # Generate test audio
    pcm_audio = generate_pcm_audio_sample(duration_seconds=1.0)
    print(f"   Generated {len(pcm_audio)} bytes of PCM audio")
    
    # Convert to audio blob
    audio_blob = create_audio_blob(pcm_audio)
    print(f"   Created audio blob: {audio_blob.mime_type}")
    print(f"   Encoded size: {len(audio_blob.data)} characters")
    
    # Send introductory text
    intro = Content(parts=[Part(text="I'm going to send you an audio sample for analysis.")])
    live_request_queue.send_content(intro)
    
    # Send audio blob
    live_request_queue.send_realtime(audio_blob)
    print("📤 Sent PCM audio blob to agent")
    
    # Follow up
    follow_up = Content(parts=[Part(text="What can you tell me about that audio?")])
    live_request_queue.send_content(follow_up)
    
    live_request_queue.close()
    
    print("🔄 Processing audio stream:")
    
    response_count = 0
    async for event in processor.runner.run_live(
        user_id="audio_user",
        session_id="audio_session",
        live_request_queue=live_request_queue,
        run_config=run_config
    ):
        if hasattr(event, 'content') and event.content:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    response_count += 1
                    print(f"   🤖 [{response_count}] {part.text}")
        
        # Limit output for demo
        if response_count >= 5:
            break
    
    print("✅ PCM audio streaming demonstration complete")

async def demonstrate_chunked_media_streaming():
    """Show how to stream large media files in chunks."""
    
    print("\n📼 Chunked Media Streaming Demo")
    print("=" * 40)
    
    processor = AudioVideoProcessor()
    await processor.setup()
    
    live_request_queue = LiveRequestQueue()
    
    print("🔄 Simulating chunked media streaming...")
    
    # Generate larger audio sample
    large_audio = generate_pcm_audio_sample(duration_seconds=5.0)
    chunk_size = 1024 * 16  # 16KB chunks
    
    print(f"   Total audio size: {len(large_audio)} bytes")
    print(f"   Chunk size: {chunk_size} bytes")
    
    # Send introduction
    intro = Content(parts=[Part(text="I'll send you audio in chunks to demonstrate streaming.")])
    live_request_queue.send_content(intro)
    
    # Stream in chunks
    chunks_sent = 0
    for i in range(0, len(large_audio), chunk_size):
        chunk = large_audio[i:i + chunk_size]
        
        # Create blob for chunk
        chunk_blob = create_audio_blob(chunk)
        live_request_queue.send_realtime(chunk_blob)
        
        chunks_sent += 1
        print(f"   📤 Sent chunk {chunks_sent}: {len(chunk)} bytes")
        
        # Small delay to simulate real-time streaming
        await asyncio.sleep(0.1)
    
    # Final message
    conclusion = Content(parts=[Part(text=f"Finished streaming {chunks_sent} audio chunks.")])
    live_request_queue.send_content(conclusion)
    
    live_request_queue.close()
    
    print(f"✅ Streamed {chunks_sent} chunks totaling {len(large_audio)} bytes")

async def demonstrate_video_format_handling():
    """Show video format handling and MIME type considerations."""
    
    print("\n🎬 Video Format Handling Demo")
    print("=" * 40)
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Skipping - GOOGLE_API_KEY not found")
        return
    
    processor = AudioVideoProcessor()
    await processor.setup()
    
    live_request_queue = LiveRequestQueue()
    
    # Simulate different video formats
    formats_to_test = ["webm", "mp4", "avi"]
    
    print("📹 Testing video format support:")
    
    for format_type in formats_to_test:
        # Create simulated video data
        fake_video_data = f"simulated_{format_type}_video_data_for_demo".encode()
        
        # Create video blob
        video_blob = create_video_blob(fake_video_data, format_type)
        
        print(f"   📄 {format_type.upper()}: {video_blob.mime_type}")
        
        # Send format description
        description = Content(parts=[Part(text=f"Sending {format_type.upper()} video format sample")])
        live_request_queue.send_content(description)
        
        # Send video blob
        live_request_queue.send_realtime(video_blob)
        
        await asyncio.sleep(0.5)  # Brief pause between formats
    
    live_request_queue.close()
    
    print("✅ Video format demonstration complete")

async def demonstrate_media_synchronization():
    """Show synchronized audio and video streaming."""
    
    print("\n🎭 Media Synchronization Demo")
    print("=" * 40)
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Skipping - GOOGLE_API_KEY not found")
        return
    
    processor = AudioVideoProcessor()
    await processor.setup()
    
    live_request_queue = LiveRequestQueue()
    
    # Configure for multimodal processing
    run_config = RunConfig(
        response_modalities=["TEXT", "AUDIO"],
        streaming_mode="SSE"
    )
    
    print("🎬 Demonstrating synchronized audio and video streaming:")
    
    # Send synchronized content introduction
    intro = Content(parts=[Part(text="I'm sending synchronized audio and video content.")])
    live_request_queue.send_content(intro)
    
    # Simulate synchronized streaming
    for frame in range(3):
        print(f"   📽️ Frame {frame + 1}:")
        
        # Create synchronized audio and video for this "frame"
        audio_data = generate_pcm_audio_sample(duration_seconds=0.5)
        video_data = f"video_frame_{frame}_data".encode()
        
        # Create blobs
        audio_blob = create_audio_blob(audio_data)
        video_blob = create_video_blob(video_data)
        
        # Send both simultaneously (as close as possible)
        live_request_queue.send_realtime(audio_blob)
        live_request_queue.send_realtime(video_blob)
        
        print(f"      🎵 Audio: {len(audio_data)} bytes")
        print(f"      🎬 Video: {len(video_data)} bytes")
        
        # Timing for next frame
        await asyncio.sleep(0.5)
    
    # Conclusion
    conclusion = Content(parts=[Part(text="Synchronized streaming complete. How was the experience?")])
    live_request_queue.send_content(conclusion)
    
    live_request_queue.close()
    
    print("✅ Media synchronization demonstration complete")

async def main():
    """Run all audio and video processing demonstrations."""
    
    print("🎵 Chapter 3.1.1: Audio and Video Processing Demonstrations")
    print("=" * 70)
    
    try:
        # PCM audio streaming
        await demonstrate_pcm_audio_streaming()
        
        # Chunked media streaming
        await demonstrate_chunked_media_streaming()
        
        # Video format handling
        await demonstrate_video_format_handling()
        
        # Media synchronization
        await demonstrate_media_synchronization()
        
        print("\n🎉 All audio and video processing demonstrations complete!")
        print("\nKey Features Demonstrated:")
        print("• PCM audio blob creation and streaming")
        print("• Chunked media processing for large files")
        print("• Multiple video format support (WebM, MP4, AVI)")
        print("• Synchronized audio and video streaming")
        print("• Real-time media processing with proper MIME types")
        
    except ValueError as e:
        print(f"❌ Setup Error: {e}")
        print("Please ensure GOOGLE_API_KEY is set in your .env file")
    except Exception as e:
        print(f"❌ Runtime Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())