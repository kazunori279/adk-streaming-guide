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

## Document and code style guide

See [STYLES.md](STYLES.md) for the documenting and coding style guide for this project.

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

## Documentation Guidelines

This section provides comprehensive guidelines for maintaining consistency across all documentation. These rules apply to all contributors, AI agents, and reviewers working on this project.

### 1. Structure and Organization

#### 1.1 Section Hierarchy

**Heading Levels:**
- Part title: `# Part N: Title`
- Major sections: `## Section Title`
- Subsections: `### Subsection Title`
- Sub-subsections: `#### Detail Title`

**Rules:**
- Maximum nesting depth: 4 levels (####)
- Never skip heading levels (don't go from `##` to `####`)
- Similar content types across parts should use the same heading levels
- Use sentence case for headers: "Understanding events" not "Understanding Events"
- Make headers descriptive: tell readers what they'll learn

#### 1.2 Section Ordering

Each part should follow this standard structure where applicable:

1. **Introduction paragraph(s)**: Brief overview of the part's topic
2. **Core concepts**: Main technical content organized by subsections
3. **Code examples**: Practical demonstrations with explanations
4. **Best practices**: Guidelines and recommendations (if applicable)
5. **Common pitfalls**: Warnings and cautions (if applicable)
6. **Cross-references**: Links to related parts or sections

#### 1.3 Consistent Section Types

**Note boxes:**
```markdown
!!! note "Title"

    Note content here
```

**Warnings:**
```markdown
!!! warning "Title"

    Warning content here
```

**Code blocks:**
- All code examples must have language tags: ```python, ```bash, ```mermaid, ```json

**Diagrams:**
- Use Mermaid consistently for sequence flows and architecture diagrams
## Contributing

Contributions are welcome! When contributing:

1. **Follow the documentation guidelines above**
2. **Test all code examples** in your local environment
3. **Update related sections** if your changes affect multiple parts
4. **Verify links** to official documentation are current
5. **Check for consistency** with existing documentation style
6. **Run through the review checklist** before submitting

### File Naming Conventions

- Use lowercase with underscores: `part1_intro.md`
- Use descriptive names: `streaming_app.py` not `app.py`
- Keep draft/experimental content in `docs/drafts/`
- Review reports: `docs/reviews/docs_review_report_<target>_<yyyymmdd-hhmmss>.md`

### Commit Message Format

Follow conventional commits:

```
type(scope): brief description

- Detailed change 1
- Detailed change 2

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

**Types:** `feat`, `fix`, `docs`, `refactor`, `chore`

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
