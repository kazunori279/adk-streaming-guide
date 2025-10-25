# ADK Bidirectional Streaming Guide

A comprehensive technical guide to building real-time, bidirectional streaming AI applications using Google's [Agent Development Kit (ADK)](https://google.github.io/adk-docs/).

## Overview

This repository provides in-depth documentation and working examples for implementing bidirectional streaming conversations with ADK. It covers the complete architecture—from basic concepts to advanced features like multimodal interactions, voice activity detection, session resumption, and proactive AI responses.

**What you'll learn:**
- How ADK's streaming architecture eliminates the complexity of building real-time AI communication
- Using `LiveRequestQueue` for unified message processing (text, audio, control signals)
- Leveraging `run_live()` for async generator-based event streaming
- Configuring `RunConfig` for multimodal I/O, transcription, VAD, and proactivity
- Handling streaming events, interruptions, and turn completion
- Working with both Gemini Live API (Google AI Studio) and Vertex AI Live API (Google Cloud)

## Documentation Structure

### Core Documentation (docs/)

The documentation is organized into focused parts that build progressively:

1. **[part1_intro.md](docs/part1_intro.md)** - Introduction to ADK Bidi-streaming
   - What is bidirectional streaming
   - ADK streaming architecture overview
   - Event handling architecture and value proposition
   - Concepts we will learn (preview of advanced topics)
   - Demo app walkthrough

2. **[part2_live_request_queue.md](docs/part2_live_request_queue.md)** - Unified Message Processing with LiveRequestQueue
   - LiveRequest structure and message types
   - `send_content()` vs `send_realtime()` methods
   - Async queue management (sync producers, async consumers)
   - Concurrency patterns and best practices

3. **[part3_run_live.md](docs/part3_run_live.md)** - The run_live() Method
   - Method signature and async generator pattern
   - InvocationContext: execution state container
   - Lifecycle and scope management
   - Tool and callback developer access patterns

4. **[part4_run_config.md](docs/part4_run_config.md)** - Understanding RunConfig
   - Model compatibility (Gemini Live API vs Vertex AI Live API)
   - Feature support matrix and session limits
   - Multimodal I/O configuration
   - Audio transcription, VAD, proactivity, affective dialog
   - Session resumption and cost controls
   - Compositional function calling (experimental)

5. **[part5_audio_and_video.md](docs/part5_audio_and_video.md)** - Audio and Video
   - Multimodal input handling
   - Audio and video processing
   - Format specifications

6. **[part6_events.md](docs/part6_events.md)** - Understanding Events
   - Event emission pipeline and types
   - Concurrent processing model
   - Handling interruptions and turn completion
   - Connection lifecycle and backpressure

### Demo Application (src/demo/)

Working FastAPI application demonstrating bidirectional streaming:
- WebSocket-based real-time communication
- Support for both text and audio modalities
- Configurable transcription, VAD, and proactivity
- SSE (Server-Sent Events) endpoint for one-shot streaming

See [src/demo/README.md](src/demo/README.md) for setup and usage instructions.

## Testing

### End-to-End Testing

The repository includes comprehensive end-to-end tests for the demo application using Chrome DevTools MCP server. These tests verify:

- WebSocket connectivity and message streaming
- UI interactions and state management
- Event handling (partial responses, turn completion, interruptions)
- Graceful connection closure
- Error handling and console output

**Running E2E Tests:**

See [tests/e2e/README.md](tests/e2e/README.md) for detailed test procedures including:
- Environment setup and server configuration
- Step-by-step test scenarios with expected outcomes
- Chrome DevTools MCP integration for automated browser testing
- Test cleanup and reporting

The e2e tests provide a practical way to validate that the bidirectional streaming implementation works correctly across the full stack—from WebSocket communication to AI response streaming.

## Tech Writing Guidelines

### Voice and Tone

- **Be conversational but precise**: Write as if explaining to a colleague, but maintain technical accuracy
- **Use active voice**: "ADK provides" not "is provided by ADK"
- **Avoid unnecessary superlatives**: Let the technical capabilities speak for themselves
- **Be specific**: Instead of "fast," say "low-latency" or provide actual metrics when available

### Content Structure

#### Headers
- Use sentence case for headers: "Understanding events" not "Understanding Events"
- Keep header hierarchy logical: never skip levels (don't go from `##` to `####`)
- Use descriptive headers that tell readers what they'll learn

#### Code Examples
- **Always provide context**: Explain what the code does before showing it
- **Use complete, runnable examples**: When possible, show full working code
- **Add inline comments**: Explain non-obvious logic
- **Follow the pattern**: Conceptual explanation → Code example → Practical notes

```python
# Good: Complete example with context
# Send user message to start a conversation turn
content = Content(parts=[Part(text="Hello, AI assistant!")])
live_request_queue.send_content(content)
```

#### Lists
- Use **bold** for list item headers followed by explanatory text
- Keep list items parallel in structure
- Use numbered lists for sequential steps, bullet points for unordered items

**Example:**
- **Audio transcription**: Enable automatic transcription of audio streams
- **Voice Activity Detection**: Real-time detection of when users are speaking
- **Session resumption**: Transparent reconnection without context loss

### Technical Accuracy

#### API References
- Always link to official documentation when mentioning features
- Provide source code references for ADK internals
- Format references consistently:

```markdown
> 📖 **Source Reference**: [`file_name.py`](https://github.com/google/adk-python/blob/main/path/to/file.py)
```

#### Version-Specific Information
- Include disclaimers for preview features or model availability
- Reference official docs for latest information
- Format warnings consistently:

```markdown
**⚠️ Disclaimer:** Model availability and capabilities are subject to change.
```

#### Platform Coverage
- **Always mention both APIs**: When discussing features, cover both Gemini Live API and Vertex AI Live API
- **Specify platform differences**: Clearly indicate when features differ between platforms
- **Use consistent naming**:
  - "Gemini Live API" (via Google AI Studio)
  - "Vertex AI Live API" (via Google Cloud)

### Formatting Standards

#### Code Blocks
- Always specify language for syntax highlighting
- Use `python` for Python code, `bash` for shell commands, `mermaid` for diagrams
- Keep code blocks focused—break up large examples with explanatory text

#### Tables
- Use tables for comparison and reference information
- Keep cells concise—use bullet points within cells if needed
- Always include headers

#### Diagrams
- Use Mermaid for sequence diagrams and architecture diagrams
- Keep diagrams simple and focused on one concept
- Add explanatory text after complex diagrams

#### Emphasis
- Use **bold** for important terms on first mention
- Use `code formatting` for:
  - Class names: `LiveRequestQueue`
  - Method names: `run_live()`
  - Parameter names: `response_modalities`
  - File names: `streaming_app.py`
- Use _italics_ sparingly, only for subtle emphasis

### Content Organization

#### Progressive Disclosure
- Start with high-level concepts, then dive into details
- Use subsections to organize complex topics
- Provide "Common Use Cases" or "Practical Examples" sections

#### Cross-References
- Link to related sections within the guide
- Use relative links for internal documentation: `[Part 2](part2_live_request_queue.md)`
- Provide context when linking: "See [Part 4](part4_run_config.md) for RunConfig details"

#### Code Samples from Demo App
- Reference real code from `src/demo/streaming_app.py` when possible
- Use annotations to indicate source:

```markdown
**Sample Code (from src/demo/streaming_app.py):**
```

### Writing Checklist

Before submitting documentation:

- [ ] All code examples are tested and working
- [ ] Both Gemini Live API and Vertex AI Live API are mentioned where relevant
- [ ] Technical terms are defined on first use
- [ ] Links to official documentation are current
- [ ] Source references are provided for ADK internals
- [ ] Headers follow logical hierarchy (no skipped levels)
- [ ] Code blocks have language specifications
- [ ] Tables and diagrams render correctly
- [ ] No orphaned subsections (every `###` has a `##` parent)

## Contributing

Contributions are welcome! When contributing:

1. **Follow the tech writing guidelines above**
2. **Test all code examples** in your local environment
3. **Update related sections** if your changes affect multiple parts
4. **Verify links** to official documentation are current
5. **Check for consistency** with existing documentation style

### File Naming Conventions
- Use lowercase with underscores: `part1_intro.md`
- Use descriptive names: `streaming_app.py` not `app.py`
- Keep draft/experimental content in `docs/drafts/`

### Commit Message Format
Follow conventional commits:
```
type(scope): brief description

- Detailed change 1
- Detailed change 2

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

Types: `feat`, `fix`, `docs`, `refactor`, `chore`

## Resources

### Official Documentation
- [ADK Documentation](https://google.github.io/adk-docs/)
- [Gemini Live API](https://ai.google.dev/gemini-api/docs/live)
- [Vertex AI Live API](https://cloud.google.com/vertex-ai/generative-ai/docs/live-api)

### Related Projects
- [ADK Python Repository](https://github.com/google/adk-python)
- [Google AI Studio](https://aistudio.google.com/)

## License

[Specify your license here]

## Authors

Kazunori Sato ([@kazunori279](https://github.com/kazunori279))

With assistance from Claude Code for technical writing and documentation structure.
