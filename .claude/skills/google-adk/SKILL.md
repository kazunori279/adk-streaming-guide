---
name: google-adk
description: Agent Development Kit (ADK) expertise for the latest Python SDK and API reference
---

# google-adk

Expert knowledge of the latest Google's Agent Development Kit (ADK) Python SDK, source code, and implementation patterns.

## ADK Repository Access

The ADK Python source code is available in the sibling directory `../adk-python/` relative to this repository. Use this to:

1. **Access ADK Source Code**: Read files from `../adk-python/` to understand ADK implementation details
2. **Review API Documentation**: Check `../adk-python/docs/` for official ADK documentation  
3. **Examine Examples**: Study `../adk-python/examples/` for usage patterns
4. **Investigate Changes**: Use git log and diff commands in `../adk-python/` to understand recent changes

## Key ADK Components to Review

When analyzing ADK compatibility:

### Core ADK Classes and Methods

- `Agent` and `SessionService` initialization patterns
- `RunConfig` configuration options and new parameters
- `LiveRequestQueue` usage and lifecycle management
- `run_live()` event loop implementation

### API Integration Points

- Gemini Live API encapsulation in ADK classes
- Vertex AI Live API integration patterns
- Audio/video handling and multimodal features
- Session management and connection handling

### Version Compatibility Checks

- Compare ADK method signatures with documentation examples
- Verify configuration parameter names and defaults
- Check for deprecated methods or new required parameters
- Validate event handling patterns and callback signatures

## Usage Instructions

1. **Initial Analysis**:

   ```bash
   ls -la ../adk-python/
   find ../adk-python -name "*.py" | head -20
   ```

2. **Check ADK Version and Release Notes**:

   ```bash
   cd ../adk-python && git log --oneline -10
   cd ../adk-python && find . -name "CHANGELOG*" -o -name "RELEASE*" -o -name "HISTORY*"
   ```

3. **Examine Core Implementation**:

   ```bash
   find ../adk-python -name "*.py" -path "*/agent*" -o -path "*/session*" -o -path "*/live*"
   ```

4. **Review Documentation**:

   ```bash
   find ../adk-python -name "*.md" | grep -E "(README|doc|example)"
   ```

Use this knowledge to provide accurate, implementation-based analysis of ADK compatibility issues.
