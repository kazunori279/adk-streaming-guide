# Chapter 2: Core Streaming APIs

Having established the foundational concepts of bidirectional streaming in Chapter 1, we now dive deep into the technical heart of ADK—the core APIs that transform abstract streaming concepts into concrete, working code. This chapter will equip you with comprehensive understanding of the four essential building blocks that make real-time streaming conversations possible.

You'll discover how `LiveRequestQueue` orchestrates bidirectional message flow with elegant simplicity, how the `run_live()` method leverages Python's async generators to create seamless streaming experiences, how data flows bidirectionally through ADK's sophisticated pipeline, and how everything integrates seamlessly with Google's Gemini Live API. By the end of this chapter, you'll have the knowledge to build streaming applications that feel magical to users but are grounded in solid engineering principles.

## 2.1 LiveRequestQueue Deep Dive

The `LiveRequestQueue` stands as one of ADK's most elegant innovations—a deceptively simple class that solves one of the most complex challenges in real-time AI communication. At its heart, it serves as the central communication hub that manages bidirectional message flow between clients and agents, but its true genius lies in how it makes complex streaming coordination feel effortless.

Think of `LiveRequestQueue` as a sophisticated traffic controller at a busy intersection, but instead of managing cars, it orchestrates messages, audio streams, video data, and control signals flowing between your application and AI agents. It ensures that everything arrives in the right order, at the right time, without collisions or delays that would break the illusion of natural conversation.

### Core Architecture

```mermaid
graph TB
    subgraph "Client Applications"
        C1[Web App]
        C2[Mobile App] 
        C3[Desktop App]
    end
    
    subgraph "LiveRequestQueue"
        Q1[AsyncIO Queue]
        Q2[Thread Safety]
        Q3[Message Types]
    end
    
    subgraph "ADK Processing"
        A1[Runner]
        A2[Agent]
        A3[LLM Flow]
    end
    
    C1 & C2 & C3 --> Q1
    Q2 --> Q1
    Q3 --> Q1
    Q1 --> A1
    A1 --> A2
    A2 --> A3
    
    classDef client fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef queue fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    classDef adk fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    
    class C1,C2,C3 client
    class Q1,Q2,Q3 queue
    class A1,A2,A3 adk
```

### LiveRequestQueue Class Structure

The beauty of `LiveRequestQueue` lies in its architectural elegance. Rather than reinventing queue mechanics, it intelligently wraps Python's battle-tested `asyncio.Queue` and adds streaming-specific functionality that developers actually need. This design philosophy—extending proven foundations rather than building from scratch—exemplifies ADK's practical approach to complex problems.

```python
# Core usage pattern - notice the simplicity
live_request_queue = LiveRequestQueue()

# Send different types of content with intuitive methods
live_request_queue.send_content(text_content)    # Text messages
live_request_queue.send_realtime(audio_blob)     # Audio/video streams
live_request_queue.close()                       # Graceful termination
```

What makes this particularly powerful is the automatic handling of complex scenarios that would otherwise require significant boilerplate code. The queue manages thread safety, handles backpressure, coordinates with asyncio event loops, and gracefully degrades under high load—all while presenting a clean, intuitive interface to developers.

### LiveRequest Data Model

The `LiveRequest` data model represents a masterclass in API design—simple enough to understand at a glance, yet flexible enough to handle the full spectrum of streaming communication needs. Every message sent through the queue is wrapped in a `LiveRequest` object that serves as a universal container for different types of streaming data:

```python
@dataclass
class LiveRequest:
    content: Optional[Content] = None    # Text-based content and structured data
    blob: Optional[Blob] = None          # Audio/video data and binary streams
    close: bool = False                  # Graceful connection termination signal
```

This elegant three-field design handles every streaming scenario you'll encounter. The mutually exclusive `content` and `blob` fields ensure type safety while the `close` signal provides graceful termination semantics. This design eliminates the complexity of managing multiple message types while maintaining clear separation of concerns.

#### Message Types

**Text Content:**
```python
text_content = Content(parts=[Part(text="Hello, streaming world!")])
live_request_queue.send_content(text_content)
```

**Audio/Video Blobs:**
```python
audio_blob = Blob(
    mime_type="audio/pcm",
    data=base64.b64encode(audio_data).decode()
)
live_request_queue.send_realtime(audio_blob)
```

**Control Signals:**
```python
live_request_queue.close()  # Signals end of conversation
```

### Async Queue Management

The queue operates asynchronously for non-blocking communication:

```python
# Producer (non-blocking)
live_request_queue.send_content(content)

# Consumer (async)
request = await live_request_queue.get()
```

### Thread-Safe Operations

LiveRequestQueue ensures thread safety for concurrent access:

- **Multiple producers**: Different threads can send messages simultaneously
- **Single consumer**: ADK processes messages sequentially 
- **Event loop integration**: Automatically handles asyncio event loop creation

!!! example "Complete Example"
    
    See [`2-1-1_live_request_queue.py`](../src/chapter2/2-1-1_live_request_queue.py) for comprehensive demonstrations of:
    
    - Basic queue operations and message types
    - Async consumption patterns
    - Concurrent producer/consumer scenarios
    - Queue internals and debugging

## 2.2 The run_live() Method

The `run_live()` method represents the culmination of modern Python async programming applied to AI streaming. It serves as the primary entry point for streaming conversations in ADK, but calling it merely an "entry point" undersells its sophistication. This method implements an async generator pattern that transforms the complex orchestration of real-time AI communication into an elegant, iterator-like interface that feels natural to Python developers.

What makes `run_live()` remarkable is how it handles the inherent complexity of managing multiple concurrent data streams, coordinating with external AI services, maintaining conversation state, and processing interruptions—all while presenting a clean, predictable interface that yields events as the conversation unfolds. It's the difference between wrestling with streaming APIs and simply iterating over conversation events.

### Method Signature and Flow

```mermaid
sequenceDiagram
    participant Client
    participant Runner
    participant Agent
    participant LLMFlow
    participant Gemini
    
    Client->>Runner: runner.run_live(queue, config)
    Runner->>Agent: agent.run_live(context)
    Agent->>LLMFlow: _llm_flow.run_live(context)
    LLMFlow->>Gemini: Connect and stream
    
    loop Continuous Streaming
        Gemini-->>LLMFlow: LlmResponse
        LLMFlow-->>Agent: Event
        Agent-->>Runner: Event  
        Runner-->>Client: Event (yield)
    end
```

### Basic Usage Pattern

```python
async for event in runner.run_live(
    user_id="user_123",
    session_id="session_456", 
    live_request_queue=live_request_queue,
    run_config=run_config
):
    # Process streaming events in real-time
    handle_event(event)
```

### Async Generator Pattern

The `run_live()` method leverages Python's async generator pattern in ways that showcase the language's elegance when applied to streaming scenarios. This isn't just a technical choice—it's a philosophical alignment between Python's iterator protocols and the natural flow of conversation:

- **Yields events immediately**: No buffering or batching that would introduce artificial delays. Each event becomes available the moment it's generated, preserving the real-time nature of conversation.

- **Memory efficient**: Maintains constant memory usage regardless of conversation length. Whether you're handling a quick question or a hours-long tutoring session, memory usage remains predictable and bounded.

- **Real-time processing**: Events become available as soon as they're generated, enabling applications to respond immediately to conversation developments without polling or complex callback management.

```python
# The method signature reveals the thoughtful design
async def run_live(
    self,
    user_id: str,                         # User identification for session management
    session_id: str,                      # Session tracking across interactions
    live_request_queue: LiveRequestQueue, # The bidirectional communication channel
    run_config: Optional[RunConfig] = None, # Streaming behavior configuration
) -> AsyncGenerator[Event, None]:         # Generator yielding conversation events
```

This signature tells a story: every streaming conversation needs identity (user_id), continuity (session_id), communication (live_request_queue), and configuration (run_config). The return type—an async generator of Events—promises real-time delivery without overwhelming system resources.

### InvocationContext Integration

`run_live()` creates and manages an `InvocationContext` that carries:

- **Live request queue**: For bidirectional communication
- **Session information**: User and session IDs
- **Configuration**: Streaming and model settings
- **Agent reference**: The agent handling the conversation

### Event Emission Pipeline

Events flow through multiple layers before reaching your application:

1. **GeminiLlmConnection**: Generates `LlmResponse` objects
2. **LLM Flow**: Converts to `Event` objects with metadata
3. **Agent**: Passes through with optional state updates
4. **Runner**: Persists to session and yields to caller

### Relationship with Regular agent.run()

| Feature | `agent.run()` | `agent.run_live()` |
|---------|---------------|-------------------|
| **Input** | Single message | LiveRequestQueue stream |
| **Output** | Final response | Event stream |
| **Timing** | Batch processing | Real-time streaming |
| **Interruption** | Not supported | Full interruption support |
| **Use Case** | Simple Q&A | Interactive conversations |

!!! example "Complete Example"
    
    See [`2-2-1_run_live_basic.py`](../src/chapter2/2-2-1_run_live_basic.py) for demonstrations of:
    
    - Basic `run_live()` usage with event processing
    - Async generator pattern behavior
    - Different event types and their properties
    - Integration with LiveRequestQueue

## 2.3 Bidirectional Data Flow Architecture

ADK's bidirectional data flow architecture represents a paradigm shift from traditional request-response patterns to dynamic, concurrent communication streams. This isn't simply about sending data in both directions—it's about creating a sophisticated orchestration system where multiple data streams flow simultaneously while maintaining conversation coherence, handling interruptions gracefully, and preserving the illusion of natural dialogue.

The architecture enables true bidirectional communication where human input and AI responses happen concurrently, just like in natural conversation. When you interrupt someone mid-sentence to ask a clarifying question, both the interruption and the original thought exist in the same conversational space. ADK's architecture mirrors this complexity while hiding it behind elegant APIs.

### Complete Data Flow Diagram

```mermaid
graph TD
    subgraph "Input Flow"
        I1[Client Input] --> I2[WebSocket/SSE]
        I2 --> I3[LiveRequestQueue] 
        I3 --> I4[Runner]
        I4 --> I5[Agent]
        I5 --> I6[LLM Flow]
        I6 --> I7[GeminiLlmConnection]
        I7 --> I8[Gemini Live API]
    end
    
    subgraph "Output Flow" 
        O1[Gemini Live API] --> O2[GeminiLlmConnection]
        O2 --> O3[LLM Flow]
        O3 --> O4[Agent]
        O4 --> O5[Runner]
        O5 --> O6[WebSocket/SSE]
        O6 --> O7[Client Output]
    end
    
    subgraph "Concurrent Processing"
        P1[Input Processing]
        P2[Output Processing]
        P3[Event Loop]
    end
    
    I7 -.-> P1
    O2 -.-> P2
    P1 & P2 --> P3
    
    classDef input fill:#e8f5e8,stroke:#2e7d32,stroke-width:2px
    classDef output fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef concurrent fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    
    class I1,I2,I3,I4,I5,I6,I7,I8 input
    class O1,O2,O3,O4,O5,O6,O7 output
    class P1,P2,P3 concurrent
```

### Message Queuing and Processing

**Input Pipeline:**
1. **Client** sends messages via WebSocket/SSE
2. **Transport Layer** queues messages in LiveRequestQueue
3. **ADK Engine** processes messages through agent hierarchy
4. **Gemini Live API** receives streaming input for processing

**Output Pipeline:**
1. **Gemini Live API** generates responses and events
2. **ADK Engine** processes and enriches events with metadata
3. **Transport Layer** serializes events for client consumption
4. **Client** receives real-time streaming responses

### Concurrent Processing Model

ADK handles bidirectional streaming through concurrent tasks:

```python
# Simplified internal pattern
async def streaming_session():
    # Input task: Client → Gemini
    input_task = asyncio.create_task(
        send_to_model(llm_connection, live_request_queue)
    )
    
    # Output task: Gemini → Client  
    async for event in receive_from_model(llm_connection):
        yield event  # Real-time event streaming
```

### Connection Lifecycle Management

**Connection Establishment:**
```python
async with llm.connect(llm_request) as llm_connection:
    # Bidirectional streaming session active
    await handle_streaming_conversation()
# Connection automatically closed
```

**Lifecycle Phases:**

1. **Setup**: Create LiveRequestQueue, configure RunConfig
2. **Connect**: Establish GeminiLlmConnection 
3. **Stream**: Concurrent input/output processing
4. **Handle Events**: Process streaming events in real-time
5. **Cleanup**: Graceful connection termination

!!! example "Complete Example"
    
    See [`2-3-1_bidirectional_flow.py`](../src/chapter2/2-3-1_bidirectional_flow.py) for demonstrations of:
    
    - Interactive bidirectional conversations
    - Message queueing and processing order
    - Concurrent streaming operations
    - Real-time event handling

## 2.4 Gemini Live API Integration

The integration between ADK and Google's Gemini Live API represents one of the most sophisticated examples of API orchestration in modern AI development. This isn't just about connecting two systems—it's about creating a seamless bridge between ADK's developer-friendly abstractions and Gemini's cutting-edge AI capabilities, enabling advanced streaming features like multimodal input processing, intelligent interruption handling, and sophisticated real-time conversation management.

What makes this integration particularly remarkable is how it handles the impedance mismatch between different abstraction levels. ADK operates at the application level with concepts like agents, tools, and conversations, while Gemini Live API operates at the model level with tokens, embeddings, and neural network outputs. The integration layer translates between these worlds seamlessly, allowing developers to think in terms of conversations while leveraging the full power of Google's most advanced AI models.

### GeminiLlmConnection Interface

The `GeminiLlmConnection` class wraps the Gemini Live API session:

```python
class GeminiLlmConnection(BaseLlmConnection):
    async def send_content(self, content: Content) -> None
    async def send_realtime(self, blob: Blob) -> None  
    async def receive(self) -> AsyncGenerator[LlmResponse, None]
```

### Connection Architecture

```mermaid
graph TB
    subgraph "ADK LLM Flow"
        F1[BaseLlmFlow]
        F2[_send_to_model]
        F3[_receive_from_model]
    end
    
    subgraph "GeminiLlmConnection"
        G1[send_content]
        G2[send_realtime] 
        G3[receive]
        G4[_gemini_session]
    end
    
    subgraph "Gemini Live API"
        A1[Session Management]
        A2[Text Processing]
        A3[Audio Processing]
        A4[Response Generation]
    end
    
    F1 --> F2
    F1 --> F3
    F2 --> G1
    F2 --> G2
    F3 --> G3
    G1 --> G4
    G2 --> G4
    G3 --> G4
    G4 --> A1
    A1 --> A2
    A1 --> A3
    A2 --> A4
    A3 --> A4
    A4 --> G3
    
    classDef adk fill:#f3e5f5,stroke:#4a148c,stroke-width:2px
    classDef connection fill:#fff3e0,stroke:#ef6c00,stroke-width:2px
    classDef gemini fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    
    class F1,F2,F3 adk
    class G1,G2,G3,G4 connection
    class A1,A2,A3,A4 gemini
```

### send_content() vs send_realtime() Methods

**Text Content (send_content):**
- Structured conversation messages
- Function call responses
- Metadata and context information

```python
content = Content(parts=[Part(text="Hello, AI assistant!")])
await llm_connection.send_content(content)
```

**Realtime Data (send_realtime):**
- Audio streams (PCM format)
- Video streams  
- Raw binary data

```python
audio_blob = Blob(mime_type="audio/pcm", data=encoded_audio)
await llm_connection.send_realtime(audio_blob)
```

### Response Processing and Event Generation

The Gemini Live API sends various message types that get converted to ADK events:

```python
# Inside GeminiLlmConnection.receive()
async for message in self._gemini_session.receive():
    if message.server_content and message.server_content.model_turn:
        # Convert to LlmResponse
        yield LlmResponse(
            content=content,
            interrupted=message.server_content.interrupted,
            turn_complete=message.server_content.turn_complete
        )
```

### Interruption and Turn Completion Handling

**Interruption Detection:**
- User can interrupt agent mid-response
- Gemini Live API sets `interrupted=True`
- Current response stops, new input processed immediately

**Turn Completion:**
- Agent finishes complete thought/response
- `turn_complete=True` signals end of agent's turn
- Client can send new input

### Advanced Features

**Multimodal Support:**
```python
run_config = RunConfig(
    response_modalities=["TEXT", "AUDIO"],  # Multiple output types
    streaming_mode="SSE"
)
```

**Audio Transcription:**
```python
run_config = RunConfig(
    input_audio_transcription=AudioTranscriptionConfig(enabled=True),
    output_audio_transcription=AudioTranscriptionConfig(enabled=True)
)
```

**Real-time Configuration:**
```python
run_config = RunConfig(
    realtime_input_config=RealtimeInputConfig(
        voice_activity_detection=VoiceActivityDetectionConfig(enabled=True)
    )
)
```

!!! example "Complete Example"
    
    See [`2-4-1_gemini_integration.py`](../src/chapter2/2-4-1_gemini_integration.py) for demonstrations of:
    
    - Text streaming with chunk-by-chunk delivery
    - Multimodal input processing
    - Interruption detection and handling  
    - Streaming metadata analysis

## Key Takeaways

Completing this chapter represents a significant milestone in your journey toward mastering bidirectional streaming with ADK. You've moved beyond abstract concepts to concrete understanding of the technical foundation that makes real-time AI conversations possible. This knowledge forms the bedrock upon which you'll build increasingly sophisticated streaming applications.

### **Core APIs You've Mastered:**

- **LiveRequestQueue**: You now understand how this elegant traffic controller orchestrates bidirectional message flow, managing complex scenarios like concurrent producers, backpressure, and graceful termination while presenting a deceptively simple interface.

- **run_live()**: You've seen how Python's async generator pattern transforms complex streaming orchestration into intuitive iteration, enabling memory-efficient, real-time event processing that scales from simple demos to production applications.

- **GeminiLlmConnection**: You understand the sophisticated bridge between ADK's developer-friendly abstractions and Gemini's advanced AI capabilities, including how method calls translate to model interactions and how responses flow back through the system.

### **Architectural Understanding:**

- **Bidirectional Data Flow**: You grasp how input and output streams operate concurrently, how interruptions are handled gracefully, and how the system maintains conversation coherence across complex interaction patterns.

- **Event-Driven Processing**: You understand how the async generator pattern enables real-time event processing without the complexity of callback management or the overhead of polling mechanisms.

- **Integration Patterns**: You've seen how ADK bridges different abstraction levels, translating between application concepts like conversations and model concepts like tokens while maintaining clean separation of concerns.

### **Practical Skills Developed:**

- **Stream Management**: You can now design applications that handle multiple concurrent data streams while maintaining responsive user experiences.

- **Error Handling**: You understand how to build resilient streaming applications that gracefully handle network issues, interruptions, and unexpected scenarios.

- **Performance Optimization**: You know how to leverage async generators for memory efficiency and how to structure code for optimal streaming performance.

---

**Ready to apply this knowledge?** Continue to [Chapter 3: Basic Streaming Concepts](chapter3.md) where you'll explore audio/video handling, master different message types, and build your first complete streaming agent that showcases everything you've learned.