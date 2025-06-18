# High-Level Architecture Implementation Memo

This document provides the actual code snippets for each flow in the ADK bidirectional streaming architecture diagram, showing how data moves between components in the real implementation.

## Architecture Flow Reference

Based on the high-level architecture diagram, here are the implementation details for each arrow/flow:

## 1. Client Layer ↔ Transport Layer

### Flow: `C1 <--> T1` (Bidirectional WebSocket Communication)

**Client Side (JavaScript Example):**
```javascript
// WebSocket connection to FastAPI
const ws = new WebSocket('ws://localhost:8000/run_live');

// Send audio data to server
function sendAudio(audioBlob) {
    const request = {
        blob: {
            mime_type: "audio/pcm", 
            data: arrayBufferToBase64(audioBlob)
        }
    };
    ws.send(JSON.stringify(request));
}

// Receive events from server
ws.onmessage = (event) => {
    const response = JSON.parse(event.data);
    handleServerResponse(response);
};
```

**Server Side (FastAPI):**
```python
# File: adk-python/src/google/adk/cli/fast_api.py (lines 852-918)
@app.websocket("/run_live")
async def agent_live_run(websocket: WebSocket, ...):
    await websocket.accept()
    
    # Bidirectional communication setup
    live_request_queue = LiveRequestQueue()
    
    async def process_messages():
        """Receive from client and forward to LiveRequestQueue"""
        async for data in websocket.iter_text():
            live_request_queue.send(LiveRequest.model_validate_json(data))
    
    async def forward_events():
        """Receive from Runner and forward to client"""
        async for event in runner.run_live(..., live_request_queue=live_request_queue):
            await websocket.send_text(event.model_dump_json(...))
```

## 2. Transport Layer → LiveRequestQueue

### Flow: `T1 -->|"live_request_queue.send()"| L1`

**Implementation:**
```python
# File: adk-python/src/google/adk/cli/fast_api.py (lines 892-897)
async def process_messages():
    async for data in websocket.iter_text():
        # Parse incoming WebSocket message
        live_request = LiveRequest.model_validate_json(data)
        
        # Send to LiveRequestQueue
        live_request_queue.send(live_request)
```

**LiveRequestQueue Implementation:**
```python
# File: adk-python/src/google/adk/agents/live_request_queue.py (lines 45-82)
class LiveRequestQueue:
    def send(self, req: LiveRequest) -> None:
        """Send a live request to the queue."""
        self._queue.put_nowait(req)
    
    def send_content(self, content: types.Content) -> None:
        """Send text content."""
        self.send(LiveRequest(content=content))
    
    def send_realtime(self, blob: types.Blob) -> None:
        """Send audio/video blob."""
        self.send(LiveRequest(blob=blob))
```

## 3. LiveRequestQueue → Runner

### Flow: `L1 -->|"runner.run_live(queue)"| L2`

**Implementation:**
```python
# File: adk-python/src/google/adk/cli/fast_api.py (lines 877-879)
runner = await _get_runner_async(app_name)

# Pass LiveRequestQueue to runner.run_live()
async for event in runner.run_live(
    user_id=user_id,
    session_id=session_id,
    live_request_queue=live_request_queue,  # Queue passed here
    run_config=run_config
):
    # Process events
```

**Runner.run_live() Method:**
```python
# File: adk-python/src/google/adk/runners.py (lines 247-328)
async def run_live(
    self,
    user_id: str,
    session_id: str,
    live_request_queue: LiveRequestQueue,
    run_config: Optional[RunConfig] = None,
) -> AsyncGenerator[Event, None]:
    
    # Create invocation context with the queue
    invocation_context = InvocationContext(
        # ... other parameters
        live_request_queue=live_request_queue,
    )
    
    # Delegate to agent
    async for event in invocation_context.agent.run_live(invocation_context):
        await self.session_service.append_event(session=session, event=event)
        yield event
```

## 4. Runner → Agent

### Flow: `L2 -->|"agent.run_live()"| L3`

**Implementation:**
```python
# File: adk-python/src/google/adk/runners.py (lines 320-328)
async for event in invocation_context.agent.run_live(invocation_context):
    # Save event to session
    await self.session_service.append_event(session=session, event=event)
    yield event
```

**Agent.run_live() Method:**
```python
# File: adk-python/src/google/adk/agents/llm_agent.py (lines 278-286)
async def run_live(self, parent_context: InvocationContext) -> AsyncGenerator[Event, None]:
    """Run the agent in live mode with bidirectional streaming."""
    invocation_context = parent_context.create_child(agent=self)
    
    async for event in self._run_live_impl(invocation_context):
        yield event

async def _run_live_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
    """Delegate to LLM Flow."""
    async for event in self._llm_flow.run_live(ctx):
        self.__maybe_save_output_to_state(event)
        yield event
```

## 5. Agent → LLM Flow

### Flow: `L3 -->|"_llm_flow.run_live()"| L4`

**Implementation:**
```python
# File: adk-python/src/google/adk/agents/llm_agent.py (lines 281-286)
async for event in self._llm_flow.run_live(ctx):
    self.__maybe_save_output_to_state(event)
    yield event
```

**LLM Flow run_live() Method:**
```python
# File: adk-python/src/google/adk/flows/llm_flows/base_llm_flow.py (lines 151-175)
async def run_live(self, invocation_context: InvocationContext) -> AsyncGenerator[Event, None]:
    """Run live streaming conversation."""
    
    # Prepare LLM request
    llm_request = self._prepare_llm_request(invocation_context, streaming=True)
    
    # Get LLM instance
    llm = self._get_llm(invocation_context)
    
    # Establish connection and start bidirectional streaming
    async with llm.connect(llm_request) as llm_connection:
        await llm_connection.send_history(llm_request.contents)
        
        # Create concurrent tasks
        send_task = asyncio.create_task(
            self._send_to_model(llm_connection, invocation_context)
        )
        
        # Process responses
        async for event in self._receive_from_model(
            llm_connection, event_id, invocation_context, llm_request
        ):
            yield event
```

## 6. LLM Flow ↔ GeminiLlmConnection

### Flow: `L4 <-->|"llm.connect()"| G1`

**Connection Establishment:**
```python
# File: adk-python/src/google/adk/flows/llm_flows/base_llm_flow.py (lines 165-175)
async with llm.connect(llm_request) as llm_connection:
    # Send conversation history
    await llm_connection.send_history(llm_request.contents)
    
    # Start bidirectional communication
    send_task = asyncio.create_task(
        self._send_to_model(llm_connection, invocation_context)
    )
```

**Sending to Model:**
```python
# File: adk-python/src/google/adk/flows/llm_flows/base_llm_flow.py (lines 276-320)
async def _send_to_model(
    self, llm_connection: BaseLlmConnection, invocation_context: InvocationContext
) -> None:
    """Send data from LiveRequestQueue to LLM."""
    live_request_queue = invocation_context.live_request_queue
    
    while True:
        # Get request from queue
        live_request = await live_request_queue.get()
        
        if live_request.close:
            break
        elif live_request.content:
            # Send text content
            await llm_connection.send_content(live_request.content)
        elif live_request.blob:
            # Send audio/video blob
            await llm_connection.send_realtime(live_request.blob)
```

## 7. GeminiLlmConnection ↔ Gemini Live API

### Flow: `G1 <--> G2`

**GeminiLlmConnection Implementation:**
```python
# File: adk-python/src/google/adk/models/gemini_llm_connection.py

class GeminiLlmConnection(BaseLlmConnection):
    def __init__(self, gemini_session: live.AsyncSession):
        self._gemini_session = gemini_session
    
    async def send_content(self, content: types.Content) -> None:
        """Send text content to Gemini Live API."""
        await self._gemini_session.send(content)
    
    async def send_realtime(self, blob: types.Blob) -> None:
        """Send audio/video to Gemini Live API."""
        await self._gemini_session.send(blob)
    
    async def receive(self) -> AsyncGenerator[LlmResponse, None]:
        """Receive responses from Gemini Live API."""
        async for message in self._gemini_session.receive():
            # Process different message types
            if message.server_content and message.server_content.model_turn:
                # Convert to LlmResponse
                yield LlmResponse(
                    content=content,
                    interrupted=message.server_content.interrupted,
                    turn_complete=message.server_content.turn_complete
                )
```

## 8. GeminiLlmConnection → LLM Flow (Response Path)

### Flow: `G1 -->|"yield LlmResponse"| L4`

**Receiving from Model:**
```python
# File: adk-python/src/google/adk/flows/llm_flows/base_llm_flow.py (lines 210-274)
async def _receive_from_model(
    self, llm_connection: BaseLlmConnection, ...
) -> AsyncGenerator[Event, None]:
    """Receive LlmResponse and convert to Event."""
    
    async for llm_response in llm_connection.receive():
        # Create Event object
        event = Event.model_validate({
            "event_id": event_id,
            "author": self.agent_config.name,
            "invocation_id": invocation_context.invocation_id,
            **llm_response.model_dump(exclude_none=True),
        })
        
        # Post-process and yield Event
        async for processed_event in self._postprocess_live(event, invocation_context):
            yield processed_event
```

**Event Creation:**
```python
# File: adk-python/src/google/adk/flows/llm_flows/base_llm_flow.py (lines 620-635)
def _finalize_model_response_event(
    self, model_response_event: Event, llm_response: LlmResponse
) -> Event:
    """Convert LlmResponse to Event."""
    return Event.model_validate({
        **model_response_event.model_dump(exclude_none=True),
        **llm_response.model_dump(exclude_none=True),
    })
```

## 9. LLM Flow → Agent (Response Path)

### Flow: `L4 -->|"yield Event"| L3`

**Implementation:**
```python
# File: adk-python/src/google/adk/agents/llm_agent.py (lines 281-286)
async for event in self._llm_flow.run_live(ctx):
    # Optional state saving
    self.__maybe_save_output_to_state(event)
    
    # Pass through the same Event object
    yield event
```

## 10. Agent → Runner (Response Path)

### Flow: `L3 -->|"yield Event"| L2`

**Implementation:**
```python
# File: adk-python/src/google/adk/runners.py (lines 320-328)
async for event in invocation_context.agent.run_live(invocation_context):
    # Persist event to session
    if not event.partial:
        await self.session_service.append_event(session=session, event=event)
    
    # Pass through the same Event object
    yield event
```

## 11. Runner → Transport Layer (Response Path)

### Flow: `L2 -->|"yield Event"| T1`

**Implementation:**
```python
# File: adk-python/src/google/adk/cli/fast_api.py (lines 885-891)
async def forward_events():
    """Forward events from Runner to WebSocket client."""
    runner = await _get_runner_async(app_name)
    
    async for event in runner.run_live(
        user_id=user_id,
        session_id=session_id,
        live_request_queue=live_request_queue,
        run_config=run_config
    ):
        # Serialize Event to JSON and send via WebSocket
        await websocket.send_text(
            event.model_dump_json(exclude_none=True, by_alias=True)
        )
```

## Key Observations

### Object Transformations:
1. **WebSocket JSON** → **LiveRequest** (Transport Layer)
2. **LiveRequest** → **Content/Blob** (LiveRequestQueue)
3. **LlmResponse** → **Event** (LLM Flow) ← **Critical transformation point**
4. **Event** objects pass unchanged through Agent, Runner, Transport Layer

### Async Generator Chain:
- Each component yields data immediately for real-time streaming
- No buffering or batching - true streaming pipeline
- Memory efficient regardless of conversation length

### Bidirectional Flow:
- **Input**: Client → LiveRequestQueue → GeminiLlmConnection
- **Output**: GeminiLlmConnection → Event chain → Client
- **Concurrent**: Both flows operate simultaneously for real-time interaction

This architecture enables natural conversation with interruption capabilities while maintaining clean separation of concerns across all layers.