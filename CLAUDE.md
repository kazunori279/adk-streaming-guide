# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **bidirectional streaming programming guide** for Google's Agent Development Kit (ADK) Python library. The project contains a comprehensive documentation guide demonstrating ADK's streaming capabilities:

- **Complete ADK Codebase Analysis** - Deep understanding of LiveRequestQueue, run_live(), and Gemini Live API integration
- **MkDocs Programming Guide** - Progressive parts from basics to production deployment
- **Working Code Examples** - Practical demonstrations organized by part and section
- **Architecture Documentation** - Verified diagrams and implementation details

**Repository**: Private GitHub repository at https://github.com/kazsato/streamdoc-0618.git

## Development Commands

### Documentation Development
```bash
# Test code examples
python src/part1/1-3-1_environment_setup.py
python src/part2/2-1-1_live_request_queue.py

# View documentation locally (if MkDocs format)
mkdocs serve  # Future consideration for web publishing
```

### Testing Your Streaming Project
```bash
# Use playground directory for testing streaming project setup
cd playground

# Create your streaming project following Chapter 1.3 setup
mkdir your-streaming-project
cd your-streaming-project

# Follow the setup instructions from docs/part1.md
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
pip install --upgrade google-adk==1.3.0
export SSL_CERT_FILE=$(python -m certifi)

# Create .env file with your API keys
# Test with working examples from ../src/part*/
```

### Git Workflow
```bash
# Check status and commit changes
git status
git add .
git commit -m "descriptive commit message"
git push

# Create private GitHub repository (already done)
gh repo create streamdoc-0618 --private
```

### Environment Setup
```bash
# Required environment variables
echo "GOOGLE_API_KEY=your_gemini_api_key" > .env

# Install ADK package
pip install google-adk

# Test installation
python src/part1/1-3-1_environment_setup.py
```

## ADK Streaming Architecture

### Core Streaming Components (Verified against codebase)
- **LiveRequestQueue**: Central bidirectional communication hub managing message flow between clients and agents
- **run_live()**: Async generator method enabling streaming conversations with real-time event processing
- **GeminiLlmConnection**: Bridge between ADK abstractions and Gemini Live API capabilities
- **Event Processing**: Real-time handling of streaming responses, interruptions, and turn completion

### Data Flow Architecture (Verified)
```mermaid
graph TB
    subgraph "Application" 
        C1[Web / Mobile] --> T1[Transport Layer (e.g. FastAPI)]
    end
    
    subgraph "ADK"
        T1 -->|live_request_queue.send()| L1[LiveRequestQueue]
        L1 -->|runner.run_live(queue)| L2[Runner]
        L2 -->|agent.run_live()| L3[Agent]
        L3 -->|_llm_flow.run_live()| L4[LLM Flow]
        L4 -->|llm.connect()| G1[GeminiLlmConnection]
        G1 <--> G2[Gemini Live API]
    end
```

### Key Streaming Features
- **Bidirectional Communication**: Real-time two-way data flow with interruption support
- **Multimodal Support**: Simultaneous text, audio, and video processing
- **Low Latency**: Millisecond response times through streaming protocols
- **Event-Driven Processing**: Async generator pattern for memory-efficient streaming

## Key Development Patterns

### Streaming Agent Setup
```python
from google.adk.agents import Agent, LiveRequestQueue
from google.adk.runners import InMemoryRunner
from google.adk.agents.run_config import RunConfig
from google.genai.types import Content, Part

# Create streaming-optimized agent
agent = Agent(
    name="streaming_agent",
    model="gemini-2.0-flash",  # Gemini Live API model
    instruction="Your streaming agent behavior",
    tools=[google_search]  # Optional tools
)

# Set up streaming components
runner = InMemoryRunner(agent=agent)
live_request_queue = LiveRequestQueue()

# Configure streaming settings
run_config = RunConfig(
    response_modalities=["TEXT", "AUDIO"],
    streaming_mode="SSE"
)
```

### Basic Streaming Flow
```python
# Send content to the queue
content = Content(parts=[Part(text="Hello, streaming AI!")])
live_request_queue.send_content(content)
live_request_queue.close()

# Process streaming responses
async for event in runner.run_live(
    user_id="user_123",
    session_id="session_456",
    live_request_queue=live_request_queue,
    run_config=run_config
):
    # Handle streaming events
    if hasattr(event, 'content') and event.content:
        for part in event.content.parts:
            if hasattr(part, 'text') and part.text:
                print(f"Agent: {part.text}")
```

## Documentation Development Practices

### Content Creation Methodology
- **Chapter Structure**: Progressive complexity from basics to production deployment
- **Code Examples**: Organized in `/src/` with part/section numbering (e.g., `2-1-1_live_request_queue.py`)
- **Architecture Diagrams**: Mermaid diagrams with verified flows against actual ADK implementation
- **Writing Style**: Engaging narrative with rich descriptive explanations, not just technical documentation
- **Verification Process**: All architecture flows and code snippets verified against actual ADK codebase

### Architecture Diagram Best Practices
1. **Verify Against Implementation**: Always check actual code before finalizing diagrams
2. **Use Method Names as Labels**: Add actual API calls like `runner.run_live(queue)` on arrows
3. **Color Coding**: External components vs ADK components for clarity
4. **Mermaid Syntax**: Use quotes for complex labels like `L3["run_live()"]` to avoid parse errors
5. **Component Accuracy**: Use exact naming from codebase (e.g., "GeminiLlmConnection", not "Gemini Connection")

### Code Example Standards
- **Working Examples**: All code examples must be executable and demonstrate real functionality
- **Error Handling**: Include proper exception handling and environment validation
- **Progressive Complexity**: Start simple, add features incrementally
- **Real-world Scenarios**: Examples should reflect actual use cases, not toy demonstrations

## Project File Structure

```
/
├── docs/                           # Main documentation parts
│   ├── part1.md                # Introduction to bidirectional streaming
│   ├── part2.md                # Core streaming APIs
│   └── high-level-architecture-memo.md  # Implementation details
├── src/                           # Working code examples
│   ├── part1/                  # Chapter 1 examples
│   │   ├── 1-3-1_environment_setup.py
│   │   └── 1-3-2_basic_imports.py
│   └── part2/                  # Chapter 2 examples
│       ├── 2-1-1_live_request_queue.py
│       ├── 2-2-1_run_live_basic.py
│       ├── 2-3-1_bidirectional_flow.py
│       └── 2-4-1_gemini_integration.py
├── streaming-guide-outline.md     # Complete guide structure
├── .env                          # Environment variables
├── README.md                     # Project overview
└── CLAUDE.md                     # This guidance file
```

## Environment Requirements

### Required Environment Variables
```bash
# Essential for Gemini Live API access
GOOGLE_API_KEY=your_gemini_api_key_here

# Optional for Google Cloud integration
GOOGLE_CLOUD_PROJECT=your_project_id
GOOGLE_CLOUD_LOCATION=us-central1
```

### Dependencies
```bash
pip install google-adk python-dotenv
```

## Instruction Verification Process

### Documentation Testing Standards

When creating or updating instructional content across any part, follow this verification methodology:

#### 1. **End-to-End Testing**

- Use the `playground/` directory for testing instructions from scratch
- Follow each documented step precisely without shortcuts or prior knowledge
- Test on clean environments to ensure reproducibility
- Verify cross-platform compatibility where applicable

#### 2. **Output Documentation**

- Capture and include actual command outputs in documentation
- Show users exactly what success looks like at each step
- Include both successful outputs and common error scenarios
- Use consistent formatting (checkmarks ✓, errors ❌, info ℹ️)

#### 3. **Validation Scripts**

- Create executable validation scripts for complex setup procedures
- Include comprehensive checks for all critical components
- Provide clear success/failure feedback with actionable next steps
- Display expected output examples within the scripts themselves

#### 4. **Documentation Synchronization**

- Keep instructions and validation scripts synchronized
- Update version numbers consistently across all materials
- Test complete workflows, not just individual components
- Maintain consistency in code examples and architecture references

### General Testing Workflow

```bash
# Generic pattern for testing any part instructions
cd playground
mkdir test-part-X-setup
cd test-part-X-setup

# Follow part instructions exactly as documented
# Document any discrepancies or improvements needed
# Update both instructions and validation scripts accordingly
```

### Quality Assurance Checklist

- [ ] Instructions tested on clean environment
- [ ] All code examples are executable
- [ ] Expected outputs documented and verified
- [ ] Error scenarios identified and documented
- [ ] Validation scripts work as intended
- [ ] Cross-references to other parts remain accurate

## Development Best Practices Established

1. **Architecture Verification**: Always verify diagrams against actual ADK implementation
2. **Progressive Documentation**: Build parts incrementally with working code examples
3. **Git Workflow**: Regular commits with descriptive messages, push to private repository
4. **Content Enhancement**: Focus on engaging, descriptive explanations rather than dry technical descriptions
5. **Code Organization**: Logical part/section structure that mirrors learning progression
6. **Working Examples**: Every code example must be executable and demonstrate real streaming functionality
7. **Instruction Verification**: Test all instructional content end-to-end with documented expected outputs