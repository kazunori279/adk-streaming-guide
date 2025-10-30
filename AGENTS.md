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

### 2. Writing Style

#### 2.1 Voice and Tone

- **Active voice**: Prefer "ADK provides" over "ADK is provided"
- **Present tense**: Use "returns" not "will return" for describing behavior
- **Second person**: Address the reader as "you" for instructions
- **Conversational but precise**: Write as if explaining to a colleague, but maintain technical accuracy
- **Avoid unnecessary superlatives**: Let the technical capabilities speak for themselves
- **Be specific**: Instead of "fast," say "low-latency" or provide actual metrics when available

#### 2.2 Consistent Terminology

Use these terms consistently throughout all documentation:

- **"Live API"** - When referring to both Gemini Live API and Vertex AI Live API collectively
- **"Gemini Live API"** - When platform-specific (via Google AI Studio)
- **"Vertex AI Live API"** - When platform-specific (via Google Cloud)
- **"bidirectional streaming" or "bidi-streaming"** - Not "bi-directional"
- **"ADK"** - Not "the ADK" or "Google ADK" (unless first mention)

#### 2.3 Technical Explanations

- **Progressive disclosure**: Introduce simple concepts before complex ones
- **Concrete before abstract**: Show examples before deep technical details
- **Real-world context**: Connect technical features to practical use cases
- **Consistent metaphors**: If using analogies, ensure they're appropriate and consistent

#### 2.4 Cross-references and Links

**Internal links format:**
```markdown
[Part 4: Response Modalities](part4_run_config.md#response-modalities)
```

**Source references:**
```markdown
> 📖 **Source Reference**: [`file_name.py`](github-url)
```

**Demo references:**
```markdown
> 📖 **Demo Implementation**: Description at [`path`](../src/demo/path)
```

**Learn more:**
```markdown
> 💡 **Learn More**: [Description of related content]
```

**Rules:**
- Use relative links for internal docs
- Link text should be descriptive, not "here" or "click here"
- Provide context when linking: "See Part 4 for RunConfig details"

#### 2.5 Lists and Bullets

- **Sentence fragments**: Bullet points should start with capital letters and end without periods (unless multi-sentence)
- **Parallel construction**: All items in a list should follow the same grammatical structure
- **Consistent markers**: Use `-` for unordered lists, numbers for sequential steps
- **Bold list headers**: Use **bold** for list item headers followed by explanatory text

**Example:**
- **Audio transcription**: Enable automatic transcription of audio streams
- **Voice Activity Detection**: Real-time detection of when users are speaking
- **Session resumption**: Transparent reconnection without context loss

#### 2.6 Admonitions and Callouts

Use these consistently across all parts:

- **Source references**: `> 📖 **Source Reference:**` for linking to ADK source code
- **Demo references**: `> 📖 **Demo Implementation:**` for linking to demo code
- **Learn more**: `> 💡 **Learn More**:` for directing readers to related content
- **Important notes**: `> 📖 **Important Note:**` for critical information
- **Consistency**: Use the same emoji and format across all parts

### 3. Code Examples

#### 3.1 Code Snippet Captions

Use **context-driven captions** that describe what the code does. Avoid generic labels like "Practical Example" everywhere.

**Caption Patterns:**

**For configuration snippets:**
```markdown
**Configuration:**
**Basic Configuration:**
**Advanced Configuration:**
```

**For action/implementation snippets:**
```markdown
**Sending Audio Input:**
**Receiving Audio Output:**
**Processing Events:**
**Handling Errors:**
```

**For complete implementations:**
```markdown
**Implementation:**
**Complete Implementation:**
**Client-side VAD Implementation:**
```

**For usage demonstrations:**
```markdown
**Usage:**
**Basic Usage:**
**Example Usage:**
```

**For specific scenarios:**
```markdown
**Example:** (for general examples)
**Example - Customer Service Bot:** (for targeted scenarios)
```

**For default/alternative patterns:**
```markdown
**Default behavior (VAD enabled):**
**Disable automatic VAD:**
```

**Why this approach:**
- More informative - readers immediately know what the code demonstrates
- Consistent with technical documentation standards
- Reduces redundancy - "Practical Example" is redundant
- Easier to scan - action-oriented headers help readers find what they need
- Already partially used in the docs

#### 3.2 Code Block Formatting

**Language tags:**
- Always specify language: ```python, ```bash, ```json, ```javascript, ```mermaid
- No code blocks without language specification

**Indentation:**
- Use 4 spaces for Python (not tabs)
- Maintain consistent indentation throughout

**Line length:**
- Prefer breaking lines at 80-88 characters for readability
- Break long lines at logical points

#### 3.3 Code Example Structure

Each code example should include:

1. **Caption**: Context-driven header describing what the code does
2. **Brief introduction** (optional): One sentence explaining the example
3. **Complete code block**: Runnable code (or clearly marked pseudo-code)
4. **Explanation**: Key points explained after the code
5. **Variations** (if applicable): Alternative approaches with pros/cons

**Example:**

```markdown
**Sending Audio Input:**

```python
from google.genai.types import Blob

live_request_queue.send_realtime(
    Blob(data=audio_bytes, mime_type="audio/pcm;rate=16000")
)
```

The `send_realtime()` method sends audio data to the model...
```

#### 3.4 Code Consistency

**Import statements:**
- Show imports when first introducing a concept
- Don't repeat imports in every example in the same section

**Variable naming:**
- Use descriptive names: `live_request_queue` not `lrq`
- Follow Python conventions: `snake_case` for variables/functions, `PascalCase` for classes

**Type hints:**
- Include type hints in function signatures when helpful for understanding

**Error handling:**
- Show error handling in production-like examples
- Omit in minimal examples for clarity

#### 3.5 Code Example Types

Distinguish between:

**Minimal examples:**
- Simplest possible demonstration of a concept
- Focus on the core idea
- Omit error handling and edge cases

**Production-like examples:**
- Include error handling, logging, edge cases
- Show real-world patterns
- More complete and robust

**Anti-patterns:**
- Clearly marked with ❌ and ✅
- Explain what NOT to do
- Always show correct alternative

**Format for anti-patterns:**
```python
# ❌ INCORRECT: Don't do this
bad_example()

# ✅ CORRECT: Do this instead
good_example()
```

#### 3.6 Code Comments and Documentation

The documentation uses code comments strategically based on the example's purpose. Follow this consistent standard across all parts:

**1. Teaching Examples (Introductory/Concept-focused)**

Use detailed explanatory comments to teach concepts. These examples prioritize education over brevity:

```python
# Phase 1: Application initialization (once at startup)
agent = Agent(
    model="gemini-2.0-flash-live-001",
    tools=[google_search],  # Tools the agent can use
    instruction="You are a helpful assistant."
)

# Phase 2: Session initialization (once per streaming session)
run_config = RunConfig(
    streaming_mode=StreamingMode.BIDI,  # Bidirectional streaming
    response_modalities=["TEXT"]  # Text-only responses
)
```

**When to use:**
- First introduction of a concept in a part
- Complex multi-step processes (like the FastAPI example in Part 1)
- Examples showing complete workflows
- When explaining architectural patterns

**Characteristics:**
- Comments explain "why" and provide context
- Phase labels organize multi-step processes
- Inline comments clarify non-obvious parameters
- Section headers demarcate major steps

**2. Production-like Examples (Minimal Comments)**

Use minimal or no comments when the code is self-documenting. These examples show production patterns:

```python
session = await session_service.get_session(
    app_name="my-streaming-app",
    user_id="user123",
    session_id="session456"
)
if not session:
    await session_service.create_session(
        app_name="my-streaming-app",
        user_id="user123",
        session_id="session456"
    )
```

**When to use:**
- Straightforward API usage examples
- Code demonstrating patterns already explained in text
- After a concept has been introduced with detailed comments
- Simple configuration examples

**Characteristics:**
- Let descriptive variable/function names speak for themselves
- No redundant comments (avoid `# Send content` when code says `send_content()`)
- Code structure provides clarity

**3. Complex Logic (Always Comment)**

Always add comments for non-obvious logic, especially async patterns and edge cases:

```python
async def upstream_task():
    """Receive messages from client and forward to model."""
    try:
        async for message in websocket.iter_text():
            data = json.loads(message)

            # Convert WebSocket message to LiveRequest format
            content = types.Content(parts=[types.Part(text=data["text"])])
            live_request_queue.send_content(content)
    except asyncio.CancelledError:
        # Graceful shutdown on cancellation
        pass
```

**When to use:**
- Async/await patterns that aren't obvious
- Error handling with specific recovery strategies
- Edge cases or gotchas
- Performance-critical sections

**Characteristics:**
- Explains the "why" behind non-obvious decisions
- Clarifies timing or ordering requirements
- Documents error handling rationale

**4. Anti-pattern Examples**

Clearly mark incorrect vs correct approaches:

```python
# ❌ INCORRECT: Don't reuse LiveRequestQueue across sessions
queue = LiveRequestQueue()
await runner.run_live(..., live_request_queue=queue)
await runner.run_live(..., live_request_queue=queue)  # BUG!

# ✅ CORRECT: Create fresh queue for each session
queue1 = LiveRequestQueue()
await runner.run_live(..., live_request_queue=queue1)

queue2 = LiveRequestQueue()  # New queue for new session
await runner.run_live(..., live_request_queue=queue2)
```

**When to use:**
- Demonstrating common mistakes
- Showing what NOT to do alongside correct approach
- Security or safety considerations

**Characteristics:**
- Use ❌ and ✅ markers consistently
- Include brief explanation of why it's wrong
- Always show correct alternative

**General Guidelines for Comments:**

- **Avoid redundant comments**: Don't comment obvious code
  ```python
  # ❌ BAD: Redundant
  live_request_queue.send_content(content)  # Send content

  # ✅ GOOD: No comment needed (self-documenting)
  live_request_queue.send_content(content)
  ```

- **Comment "why" not "what"**: The code shows what; comments explain why
  ```python
  # ❌ BAD: States the obvious
  queue.close()  # Close the queue

  # ✅ GOOD: Explains the reason
  queue.close()  # Ensure graceful termination before cleanup
  ```

- **Use inline comments sparingly**: Prefer explanatory text before/after code blocks
- **Consistency within examples**: All examples in the same section should use similar commenting density
- **Progressive detail reduction**: Use detailed comments in Part 1, lighter comments in later parts as readers gain familiarity

**Checklist for Code Comments:**

- [ ] Teaching examples have explanatory comments for all non-obvious steps
- [ ] Production examples avoid redundant comments
- [ ] Complex async/await patterns are explained
- [ ] Anti-patterns are clearly marked with ❌/✅
- [ ] Comments explain "why" not "what"
- [ ] Comment density is consistent within each part
- [ ] No TODO, FIXME, or placeholder comments in documentation

### 4. Table Formatting

#### 4.1 Column Alignment

Consistent table formatting improves readability. Follow these alignment rules:

**Text columns:** Left-align (use `---` or `|---|`)
- Model names, descriptions, notes, explanations
- Any column containing paragraphs or sentences

**Status/Symbol columns:** Center-align (use `:---:` or `|:---:|`)
- Columns containing only checkmarks (✅/❌)
- Single-character or symbol-only columns
- Boolean indicators

**Numeric columns:** Right-align (use `---:` or `|---:|`)
- Numbers, percentages, counts
- Measurements and statistics

**Example of correct alignment:**

```markdown
| Feature | Status | Count | Description |
|---------|:------:|------:|-------------|
| Audio   | ✅     |   100 | All text here is left-aligned |
| Video   | ❌     |    50 | Status centered, count right-aligned |
```

#### 4.2 Header Formatting

- All table headers should use **bold** text: `| **Feature** | **Status** |`
- Headers should be concise and descriptive
- Use title case for headers

#### 4.3 Cell Content

- Use code formatting for code terms: `` `response_modalities` ``
- Use line breaks (`<br>`) sparingly, only when necessary for readability
- Keep cell content concise - tables should be scannable

#### 4.4 Table Consistency Across Parts

- All tables across all parts should follow the same alignment rules
- Similar table types (e.g., feature matrices, comparison tables) should use the same structure
- Platform comparison tables should use consistent column ordering

### 5. Formatting Standards

#### 5.1 Code Blocks

- Always specify language for syntax highlighting
- Use `python` for Python code, `bash` for shell commands, `mermaid` for diagrams
- Keep code blocks focused—break up large examples with explanatory text

#### 5.2 Diagrams

- Use Mermaid for sequence diagrams and architecture diagrams
- Keep diagrams simple and focused on one concept
- Add explanatory text after complex diagrams

#### 5.3 Emphasis

**Bold** for important terms:
- Use on first mention of key concepts
- Example: The **LiveRequestQueue** handles message processing

**Code formatting** for technical terms:
- Class names: `LiveRequestQueue`
- Method names: `run_live()`
- Parameter names: `response_modalities`
- File names: `streaming_app.py`

**Italics** - use sparingly:
- Only for subtle emphasis
- Avoid overuse

### 6. Platform Coverage

#### 6.1 API References

- Always link to official documentation when mentioning features
- Provide source code references for ADK internals
- Format references consistently:

```markdown
> 📖 **Source Reference**: [`file_name.py`](https://github.com/google/adk-python/blob/main/path/to/file.py)
```

#### 6.2 Version-Specific Information

- Include disclaimers for preview features or model availability
- Reference official docs for latest information
- Format warnings consistently:

```markdown
!!! warning "Model Availability Disclaimer"

    Model availability and capabilities are subject to change...
```

#### 6.3 Platform Differences

- **Always mention both APIs**: When discussing features, cover both Gemini Live API and Vertex AI Live API
- **Specify platform differences**: Clearly indicate when features differ between platforms
- **Use consistent naming**:
  - "Gemini Live API" (via Google AI Studio)
  - "Vertex AI Live API" (via Google Cloud)

### 7. Cross-Part Consistency

#### 7.1 Terminology Consistency

- Verify the same technical terms are used consistently across all parts
- Check that acronyms are defined on first use in each part
- Ensure consistent capitalization of product names and technical terms

#### 7.2 Navigation and Flow

- Each part should naturally lead to the next
- Cross-references should be bidirectional where appropriate
- Concepts introduced in earlier parts should not be re-explained in depth later

#### 7.3 Example Progression

- Code examples should increase in complexity across parts
- Earlier parts should use simpler examples
- Later parts can reference or build upon earlier examples

### 8. Content Organization

#### 8.1 Progressive Disclosure

- Start with high-level concepts, then dive into details
- Use subsections to organize complex topics
- Provide "Common Use Cases" or examples sections

#### 8.2 Cross-References

- Link to related sections within the guide
- Use relative links for internal documentation: `[Part 2](part2_live_request_queue.md)`
- Provide context when linking: "See Part 4 for RunConfig details"

#### 8.3 Code Samples from Demo App

- Reference real code from `src/demo/streaming_app.py` when possible
- Use annotations to indicate source:

```markdown
**Demo Implementation:**

From `src/demo/streaming_app.py`:

```python
# code here
```
```

## Documentation Review Process

### Review Checklist

Before submitting documentation, verify:

**Structure:**
- [ ] Headers follow logical hierarchy (no skipped levels)
- [ ] Maximum nesting depth is 4 levels (####)
- [ ] Similar content types use the same heading levels
- [ ] No orphaned subsections (every `###` has a `##` parent)

**Style:**
- [ ] Active voice used throughout
- [ ] Present tense for describing behavior
- [ ] Consistent terminology (Live API, ADK, bidi-streaming)
- [ ] Both platforms mentioned where relevant

**Code Examples:**
- [ ] All code examples are tested and working
- [ ] Code blocks have language specifications
- [ ] Captions use context-driven patterns
- [ ] Comments follow the appropriate pattern (teaching vs production)
- [ ] Import statements shown on first use
- [ ] Anti-patterns marked with ❌/✅

**Links and References:**
- [ ] All cross-references use relative links
- [ ] Link text is descriptive
- [ ] Source references formatted consistently
- [ ] Links to official documentation are current

**Tables:**
- [ ] Headers use bold text
- [ ] Column alignment follows rules (text left, symbols center, numbers right)
- [ ] Cell content is concise and scannable

**Technical Accuracy:**
- [ ] Technical terms defined on first use
- [ ] Source references provided for ADK internals
- [ ] Platform differences clearly indicated
- [ ] Version disclaimers included where appropriate

**Formatting:**
- [ ] Tables and diagrams render correctly
- [ ] Code formatting used for technical terms
- [ ] Admonitions use consistent emoji and format

### Review Report Format

When conducting formal reviews, organize findings into:

**Critical Issues (C1, C2, ...):**
- Must fix - severely impact readability or correctness
- Incorrect code examples
- Broken cross-references
- Major structural inconsistencies
- Incorrect technical information

**Warnings (W1, W2, ...):**
- Should fix - impact consistency and quality
- Minor style inconsistencies
- Missing cross-references
- Inconsistent terminology
- Formatting issues

**Suggestions (S1, S2, ...):**
- Consider improving - would enhance quality
- Opportunities for better examples
- Areas for clearer explanations
- Suggestions for additional content
- Minor wording improvements

**Issue Format:**

```markdown
**[Issue Number]: [Issue Title]**

- **Category**: Structure/Style/Code
- **Parts Affected**: part1, part3, etc.
- **Problem**: Clear description of the inconsistency or issue
- **Current State**:
  - Filename: line number(s)
  - Code/text snippet showing the issue
- **Expected State**: What it should look like for consistency
- **Recommendation**: Specific action to resolve
```

### Review Focus Areas

When reviewing, pay special attention to:

1. **First-time reader experience**: Does the documentation flow naturally?
2. **Code runability**: Can readers copy-paste examples and have them work?
3. **Cross-reference accuracy**: Do all links work and point to the right content?
4. **Technical accuracy**: Are all ADK APIs and patterns used correctly?
5. **Visual consistency**: Do diagrams, code blocks, and callouts follow the same patterns?

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
