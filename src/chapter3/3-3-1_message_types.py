#!/usr/bin/env python3
"""
Chapter 3.3.1: Message Types and Processing
Comprehensive demonstration of handling different message types in streaming contexts.
"""

import asyncio
import os
import base64
import time
from dotenv import load_dotenv

from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import InMemoryRunner
from google.adk.agents.run_config import RunConfig
from google.adk.tools import google_search
from google.genai.types import Content, Part, Blob

# Load environment variables
load_dotenv()

class MessageTypeProcessor:
    """Demonstrates comprehensive message type handling in streaming."""
    
    def __init__(self):
        self.agent = None
        self.runner = None
        self.message_stats = {
            'text_messages': 0,
            'blob_messages': 0,
            'control_signals': 0,
            'function_calls': 0,
            'total_events': 0
        }
        
    async def setup(self):
        """Set up agent with comprehensive message processing capabilities."""
        
        if not os.getenv("GOOGLE_API_KEY"):
            raise ValueError("GOOGLE_API_KEY required for message processing demo")
        
        # Create agent with tools for function call demonstrations
        self.agent = Agent(
            name="message_processor",
            model="gemini-2.0-flash",
            instruction="""You are an AI assistant demonstrating different message types and processing patterns.
            
            Your capabilities include:
            - Processing text content with rich formatting and context
            - Handling realtime blob data (audio, video, binary)
            - Managing control signals and conversation flow
            - Executing function calls and streaming intermediate results
            - Demonstrating interruption handling and turn completion
            
            For each type of input, acknowledge what you received and demonstrate
            your understanding of the message type and content.""",
            description="Message type processing demonstration agent",
            tools=[google_search]  # Include search for function call demos
        )
        
        self.runner = InMemoryRunner(agent=self.agent)
        print("✓ Message type processor setup complete")
    
    async def process_message_safely(self, event):
        """Type-safe message processing with comprehensive error handling."""
        
        self.message_stats['total_events'] += 1
        
        try:
            # Text content processing
            if hasattr(event, 'content') and event.content:
                await self._process_text_content(event.content)
                self.message_stats['text_messages'] += 1
            
            # Blob data processing
            if hasattr(event, 'blob') and event.blob:
                await self._process_blob_data(event.blob)
                self.message_stats['blob_messages'] += 1
            
            # Control signal processing
            if hasattr(event, 'interrupted') or hasattr(event, 'turn_complete'):
                await self._process_control_signal(event)
                self.message_stats['control_signals'] += 1
            
            # Function call processing
            if hasattr(event, 'function_call'):
                await self._process_function_call(event.function_call)
                self.message_stats['function_calls'] += 1
                
        except Exception as e:
            print(f"❌ Message processing error: {e}")
            await self._handle_processing_error(e)
    
    async def _process_text_content(self, content: Content):
        """Process text content with detailed analysis."""
        
        for part_idx, part in enumerate(content.parts):
            if hasattr(part, 'text') and part.text:
                text_length = len(part.text)
                word_count = len(part.text.split())
                
                print(f"   📝 Text part {part_idx + 1}: {text_length} chars, {word_count} words")
                print(f"      Content: {part.text[:100]}{'...' if text_length > 100 else ''}")
    
    async def _process_blob_data(self, blob: Blob):
        """Process blob data with format analysis."""
        
        print(f"   📦 Blob data: {blob.mime_type}")
        print(f"      Size: {len(blob.data)} characters (base64)")
        
        # Analyze blob type
        if blob.mime_type.startswith('audio/'):
            print(f"      Type: Audio stream")
        elif blob.mime_type.startswith('video/'):
            print(f"      Type: Video stream")
        else:
            print(f"      Type: Binary data")
    
    async def _process_control_signal(self, event):
        """Process control signals and flow management."""
        
        if hasattr(event, 'interrupted') and event.interrupted:
            print(f"   ⚠️ Interruption signal detected")
        
        if hasattr(event, 'turn_complete') and event.turn_complete:
            print(f"   ✅ Turn completion signal")
        
        if hasattr(event, 'partial'):
            status = "partial" if event.partial else "complete"
            print(f"   📊 Response status: {status}")
    
    async def _process_function_call(self, function_call):
        """Process function calls with streaming results."""
        
        print(f"   🔧 Function call: {function_call.name}")
        print(f"      Arguments: {function_call.arguments}")
        
        # Simulate streaming function execution
        for i in range(3):
            await asyncio.sleep(0.5)
            print(f"      ⚙️ Function progress: step {i + 1}")
        
        print(f"      ✅ Function execution complete")
    
    async def _handle_processing_error(self, error):
        """Handle processing errors gracefully."""
        
        print(f"   🔧 Error recovery: {type(error).__name__}")
        print(f"   📋 Continuing with next message...")

async def demonstrate_text_content_processing():
    """Show comprehensive text content message handling."""
    
    print("📝 Text Content Processing Demo")
    print("=" * 40)
    
    processor = MessageTypeProcessor()
    await processor.setup()
    
    live_request_queue = LiveRequestQueue()
    
    # Send various text content types
    text_examples = [
        "Simple text message",
        "Multi-word message with various punctuation marks! Questions? Answers.",
        "Longer message that demonstrates how the system handles more complex text content with multiple sentences and varied structure, including technical terms and concepts.",
        "Message with special characters: émojis 🎉, símbolos ©, and nümerics 123"
    ]
    
    print("📤 Sending different text content types:")
    
    for idx, text in enumerate(text_examples, 1):
        content = Content(parts=[Part(text=text)])
        live_request_queue.send_content(content)
        print(f"   [{idx}] {text[:50]}{'...' if len(text) > 50 else ''}")
    
    live_request_queue.close()
    
    print("\n🔄 Processing text messages:")
    
    async for event in processor.runner.run_live(
        user_id="text_user",
        session_id="text_session",
        live_request_queue=live_request_queue,
        run_config=RunConfig(response_modalities=["TEXT"])
    ):
        await processor.process_message_safely(event)
        
        # Show agent responses
        if hasattr(event, 'content') and event.content:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    response_preview = part.text[:80] + "..." if len(part.text) > 80 else part.text
                    print(f"   🤖 Agent: {response_preview}")
        
        # Stop after processing several messages
        if processor.message_stats['total_events'] >= 10:
            break
    
    print(f"✅ Processed {processor.message_stats['text_messages']} text messages")

async def demonstrate_blob_data_processing():
    """Show realtime blob message handling."""
    
    print("\n📦 Blob Data Processing Demo")
    print("=" * 35)
    
    processor = MessageTypeProcessor()
    await processor.setup()
    
    live_request_queue = LiveRequestQueue()
    
    # Create different blob types
    blob_examples = [
        {
            "data": b"simulated_audio_pcm_data_for_demo",
            "mime_type": "audio/pcm",
            "description": "PCM Audio"
        },
        {
            "data": b"simulated_video_webm_data_for_demo",
            "mime_type": "video/webm", 
            "description": "WebM Video"
        },
        {
            "data": b"binary_data_example_for_processing",
            "mime_type": "application/octet-stream",
            "description": "Binary Data"
        }
    ]
    
    print("📤 Sending different blob types:")
    
    # Send introduction
    intro = Content(parts=[Part(text="I'm going to send you different types of blob data for processing.")])
    live_request_queue.send_content(intro)
    
    for blob_info in blob_examples:
        # Create blob
        encoded_data = base64.b64encode(blob_info["data"]).decode()
        blob = Blob(
            mime_type=blob_info["mime_type"],
            data=encoded_data
        )
        
        live_request_queue.send_realtime(blob)
        print(f"   📦 {blob_info['description']}: {blob_info['mime_type']}")
    
    # Send conclusion
    conclusion = Content(parts=[Part(text="How did you handle those different blob types?")])
    live_request_queue.send_content(conclusion)
    
    live_request_queue.close()
    
    print("\n🔄 Processing blob messages:")
    
    async for event in processor.runner.run_live(
        user_id="blob_user",
        session_id="blob_session",
        live_request_queue=live_request_queue,
        run_config=RunConfig(response_modalities=["TEXT"])
    ):
        await processor.process_message_safely(event)
        
        # Show agent acknowledgments
        if hasattr(event, 'content') and event.content:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    print(f"   🤖 Agent: {part.text}")
        
        # Stop after reasonable processing
        if processor.message_stats['total_events'] >= 8:
            break
    
    print(f"✅ Processed {processor.message_stats['blob_messages']} blob messages")

async def demonstrate_function_call_streaming():
    """Show function call processing in streaming contexts."""
    
    print("\n🔧 Function Call Streaming Demo")
    print("=" * 40)
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Skipping - GOOGLE_API_KEY not found")
        return
    
    processor = MessageTypeProcessor()
    await processor.setup()
    
    live_request_queue = LiveRequestQueue()
    
    # Send function call trigger message
    function_request = Content(parts=[Part(text="Please search for information about 'bidirectional streaming' to help explain the concept.")])
    live_request_queue.send_content(function_request)
    live_request_queue.close()
    
    print("🔍 Triggering function call through conversation:")
    print("   📤 Request: Search for 'bidirectional streaming'")
    
    print("\n🔄 Processing function call stream:")
    
    function_detected = False
    response_count = 0
    
    async for event in processor.runner.run_live(
        user_id="function_user",
        session_id="function_session",
        live_request_queue=live_request_queue,
        run_config=RunConfig(response_modalities=["TEXT"])
    ):
        await processor.process_message_safely(event)
        
        # Detect function calls
        if hasattr(event, 'function_call') or 'search' in str(event).lower():
            function_detected = True
            print("   🎯 Function call detected in event stream")
        
        # Show responses
        if hasattr(event, 'content') and event.content:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    response_count += 1
                    preview = part.text[:100] + "..." if len(part.text) > 100 else part.text
                    print(f"   🤖 [{response_count}] {preview}")
        
        # Stop after sufficient processing
        if response_count >= 5:
            break
    
    status = "detected" if function_detected else "not explicitly detected"
    print(f"✅ Function call processing complete - function {status}")

async def demonstrate_control_signal_handling():
    """Show control signal processing and conversation management."""
    
    print("\n⚠️ Control Signal Handling Demo")
    print("=" * 40)
    
    processor = MessageTypeProcessor()
    await processor.setup()
    
    live_request_queue = LiveRequestQueue()
    
    # Simulate conversation with various control signals
    messages = [
        "Start a conversation about AI",
        "Actually, let me interrupt - tell me about streaming instead",
        "Thank you, that's all I needed"
    ]
    
    print("🎭 Simulating conversation with control signals:")
    
    for msg_idx, message in enumerate(messages, 1):
        content = Content(parts=[Part(text=message)])
        live_request_queue.send_content(content)
        print(f"   [{msg_idx}] {message}")
        
        # Add delay to simulate interruption timing
        if msg_idx == 2:
            await asyncio.sleep(0.5)
    
    live_request_queue.close()
    
    print("\n🔄 Processing with control signal detection:")
    
    turn_completions = 0
    interruptions = 0
    
    async for event in processor.runner.run_live(
        user_id="control_user",
        session_id="control_session",
        live_request_queue=live_request_queue,
        run_config=RunConfig(response_modalities=["TEXT"])
    ):
        await processor.process_message_safely(event)
        
        # Track control signals
        if hasattr(event, 'turn_complete') and event.turn_complete:
            turn_completions += 1
            print(f"   🏁 Turn completion #{turn_completions}")
        
        if hasattr(event, 'interrupted') and event.interrupted:
            interruptions += 1
            print(f"   ⚠️ Interruption #{interruptions}")
        
        # Show agent responses
        if hasattr(event, 'content') and event.content:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    print(f"   🤖 {part.text[:60]}...")
        
        # Stop after processing control flow
        if turn_completions >= 2:
            break
    
    print(f"✅ Control signals: {turn_completions} completions, {interruptions} interruptions")

async def demonstrate_mixed_message_flow():
    """Show handling mixed message types in a single conversation."""
    
    print("\n🎭 Mixed Message Flow Demo")
    print("=" * 35)
    
    processor = MessageTypeProcessor()
    await processor.setup()
    
    live_request_queue = LiveRequestQueue()
    
    print("🌊 Sending mixed message types in sequence:")
    
    # 1. Text introduction
    intro = Content(parts=[Part(text="I'll send you different message types in sequence.")])
    live_request_queue.send_content(intro)
    print("   📝 Text: Introduction")
    
    # 2. Audio blob
    audio_data = b"simulated_audio_for_mixed_demo"
    audio_blob = Blob(
        mime_type="audio/pcm",
        data=base64.b64encode(audio_data).decode()
    )
    live_request_queue.send_realtime(audio_blob)
    print("   🎵 Blob: Audio data")
    
    # 3. Follow-up text
    follow_up = Content(parts=[Part(text="How did you handle that audio? Now here's a video.")])
    live_request_queue.send_content(follow_up)
    print("   📝 Text: Follow-up question")
    
    # 4. Video blob
    video_data = b"simulated_video_for_mixed_demo"
    video_blob = Blob(
        mime_type="video/webm",
        data=base64.b64encode(video_data).decode()
    )
    live_request_queue.send_realtime(video_blob)
    print("   🎬 Blob: Video data")
    
    # 5. Final text
    conclusion = Content(parts=[Part(text="That concludes the mixed message demonstration.")])
    live_request_queue.send_content(conclusion)
    print("   📝 Text: Conclusion")
    
    live_request_queue.close()
    
    print("\n🔄 Processing mixed message stream:")
    
    async for event in processor.runner.run_live(
        user_id="mixed_user",
        session_id="mixed_session",
        live_request_queue=live_request_queue,
        run_config=RunConfig(response_modalities=["TEXT"])
    ):
        await processor.process_message_safely(event)
        
        # Show responses
        if hasattr(event, 'content') and event.content:
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    print(f"   🤖 {part.text[:70]}...")
        
        # Stop after comprehensive processing
        if processor.message_stats['total_events'] >= 12:
            break
    
    print("✅ Mixed message flow processing complete")
    print(f"📊 Final statistics: {processor.message_stats}")

async def main():
    """Run all message type processing demonstrations."""
    
    print("📋 Chapter 3.3.1: Message Types and Processing Demonstrations")
    print("=" * 70)
    
    try:
        # Text content processing
        await demonstrate_text_content_processing()
        
        # Blob data processing
        await demonstrate_blob_data_processing()
        
        # Function call streaming
        await demonstrate_function_call_streaming()
        
        # Control signal handling
        await demonstrate_control_signal_handling()
        
        # Mixed message flow
        await demonstrate_mixed_message_flow()
        
        print("\n🎉 All message type processing demonstrations complete!")
        print("\nKey Processing Capabilities Demonstrated:")
        print("• Type-safe text content processing with detailed analysis")
        print("• Realtime blob data handling for audio, video, and binary content")
        print("• Function call detection and streaming execution")
        print("• Control signal management (interruptions, turn completion)")
        print("• Mixed message type handling in complex conversations")
        print("• Comprehensive error handling and recovery patterns")
        
        print("\n💡 Integration Insights:")
        print("• Each message type serves specific streaming communication needs")
        print("• Proper type checking prevents processing errors")
        print("• Control signals enable natural conversation flow management")
        print("• Mixed message flows enable rich multimodal interactions")
        
    except ValueError as e:
        print(f"❌ Setup Error: {e}")
        print("Please ensure GOOGLE_API_KEY is set in your .env file")
    except Exception as e:
        print(f"❌ Runtime Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())