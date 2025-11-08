# ADK Change Review Report
**Generated**: 2025-11-08 09:28:02  
**Current ADK Version**: 1.18.0  
**Latest ADK Version**: 1.18.0  
**Status**: ✅ Up to date

## Executive Summary

The current documentation is tracking the latest ADK version (1.18.0). This review analyzes the changes introduced in version 1.18.0 (released 2025-11-05) to identify impacts on the bidirectional streaming guide and demo application.

### Key Findings

- **Critical Issues**: 1 (missing feature documentation)
- **Warnings**: 0 (no breaking changes affecting current docs)
- **Suggestions**: 2 (new features to consider documenting)

### Version Compatibility Status

✅ **Documentation is compatible** with ADK 1.18.0. No breaking changes affect the current bidirectional streaming guide or demo application.

## New Features in ADK 1.18.0

### Directly Relevant to Bidi-streaming

#### 1. Token Usage in Live Events (NEW FEATURE)

**Feature**: Add token usage to live events for bidi streaming  
**Commit**: [6e5c0eb](https://github.com/google/adk-python/commit/6e5c0eb6e0474f5b908eb9df20328e7da85ebed9)  
**Impact**: HIGH - This is a new feature that enhances the Live API events with usage metadata

**Description**: Live events now include token usage information, allowing applications to track token consumption in real-time during streaming sessions.

**Coverage in Docs**: ⚠️ **NOT DOCUMENTED**  
**Affected Parts**: Part 3 (Event Handling), Part 4 (Cost Controls)

**Source Code Evidence**:
```python
# From CHANGELOG.md line 58
* **[Live]**
  * Add token usage to live events for bidi streaming ([6e5c0eb](https://github.com/google/adk-python/commit/6e5c0eb6e0474f5b908eb9df20328e7da85ebed9))
```

**Current Documentation Gap**: Part 3 mentions `usage_metadata` in the Event class description (part3_run_live.md:133) but doesn't explain that this feature was added specifically for Live API events in version 1.18.0.

### Indirectly Relevant to Bidi-streaming

#### 2. Enhanced LiteLLM Token Tracking

**Feature**: Add support for extracting cache-related token counts from LiteLLM usage  
**Commit**: [4f85e86](https://github.com/google/adk-python/commit/4f85e86fc3915f0e67312a39fe22451968d4f1b1)

**Coverage**: Not applicable (LiteLLM is not used in the demo, guide focuses on native Live API)

#### 3. Code Interpreter Logging Enhancement

**Feature**: Expose the Python code run by the code interpreter in the logs  
**Commit**: [a2c6a8a](https://github.com/google/adk-python/commit/a2c6a8a85cf4f556e9dacfe46cf384d13d964208)

**Coverage**: Not applicable (code interpreter not covered in streaming guide)

#### 4. Debug Helper Method

**Feature**: Add run_debug() helper method for quick agent experimentation  
**Commit**: [0487eea](https://github.com/google/adk-python/commit/0487eea2abcd05d7efd123962d17b8c6c9a9d975)

**Coverage**: Not applicable (non-streaming feature)

### Not Relevant to Bidi-streaming

The following 1.18.0 features do not affect bidirectional streaming documentation:

- ADK Visual Agent Builder (UI feature)
- MCP prompts support via McpInstructionProvider
- LiteLLM model tracking and fallbacks
- ApigeeLlm model addition
- Vertex AI Express Mode enhancements
- Session database loading/upgrading
- BigQuery tools enhancements
- Evaluation features
- Observability enhancements

## Issues

### Critical Issues (Must Fix)

#### C1: Token Usage in Live Events Not Documented

**Problem**: ADK 1.18.0 added token usage metadata to Live API events, but this feature is not explained in the documentation.

**Target Documentation**: 
- `docs/part3_run_live.md` - Event Handling section
- `docs/part4_run_config.md` - Cost Controls section (if it exists, or should be added)

**Reason**: 
From CHANGELOG.md line 58:
```markdown
* **[Live]**
  * Add token usage to live events for bidi streaming ([6e5c0eb](https://github.com/google/adk-python/commit/6e5c0eb6e0474f5b908eb9df20328e7da85ebed9))
```

Part 3 briefly mentions `usage_metadata` in the Event class field list (line 133) but doesn't explain:
- That this was newly added for Live API in 1.18.0
- How to access and use token usage data in streaming sessions
- What specific token metrics are available (input tokens, output tokens, cached tokens, etc.)
- How this differs from non-streaming usage tracking

**Recommended Options**:

**O1**: Add a dedicated subsection in Part 3 about token usage tracking
```markdown
### Token Usage Tracking in Live Events (Since 1.18.0)

ADK 1.18.0 introduced token usage metadata for Live API events, enabling real-time monitoring of token consumption during streaming sessions.

**Accessing Token Usage**:
```python
async for event in runner.run_live(...):
    if event.usage_metadata:
        print(f"Input tokens: {event.usage_metadata.prompt_token_count}")
        print(f"Output tokens: {event.usage_metadata.candidates_token_count}")
        print(f"Total tokens: {event.usage_metadata.total_token_count}")
        
        # Cache-related metrics (if available)
        if hasattr(event.usage_metadata, 'cached_content_token_count'):
            print(f"Cached tokens: {event.usage_metadata.cached_content_token_count}")
```

**Use Cases**:
- Real-time cost monitoring during streaming sessions
- Implementing token-based rate limiting
- Tracking cache efficiency in resumed sessions
- Building usage dashboards for streaming applications
```

**O2**: Add a new section in Part 4 about Cost Controls with token usage
```markdown
## Cost Controls

### Token Usage Monitoring

ADK provides real-time token usage tracking through the `usage_metadata` field on events...
```

**O3**: Add both - brief mention in Part 3 with cross-reference to detailed cost control section in Part 4

### Warnings (Should Fix)

None identified. All changes in 1.18.0 are backward-compatible additions.

### Suggestions (Consider Improving)

#### S1: Mention ADK Visual Agent Builder for Development Workflow

**Problem**: The guide focuses on code-first agent development, but ADK 1.18.0 introduced a visual agent builder that could complement the development workflow.

**Target Documentation**: `docs/part1_intro.md` - Introduction or Development Tips section

**Reason**: From CHANGELOG.md lines 7-17:
```markdown
* **[ADK Visual Agent Builder]**
  * Core Features
    * Visual workflow designer for agent creation
    * Support for multiple agent types (LLM, Sequential, Parallel, Loop, Workflow)
    * Agent tool support with nested agent tools
    * Built-in and custom tool integration
    * Callback management for all ADK callback types
    * Assistant to help you build your agents with natural language
    * Save to test with chat interfaces as normal
    * Build and debug at the same time in adk web!
```

**Recommended Options**:

**O1**: Add a note in Part 1 about development tools:
```markdown
> 💡 **Development Tip**: ADK 1.18.0+ includes a visual agent builder (`adk web`) that can help you prototype agent configurations before implementing them in code. While this guide uses code-first examples, the visual builder can be useful for exploring agent architectures and tool integrations.
```

**O2**: Don't mention it - keep the guide focused on code-first approaches for production applications

#### S2: Cross-Reference Session Resumption with Token Usage

**Problem**: Part 4 covers session resumption but doesn't mention how token usage tracking works across resumed sessions.

**Target Documentation**: `docs/part4_run_config.md` - Session Resumption section

**Recommended Options**:

**O1**: Add a note in the Session Resumption section:
```markdown
> 💡 **Token Usage**: When using session resumption, token usage metadata in events reflects only the current connection's usage. To track cumulative token usage across all resumptions, you'll need to aggregate `usage_metadata` from events yourself. Context cache hits (available in `cache_metadata`) can significantly reduce token costs in resumed sessions.
```

## Cross-Documentation Consistency Report

### Part-by-Part Analysis

#### Part 1: Introduction (part1_intro.md)
**Status**: ✅ Consistent and up-to-date  
**Version-specific content**: None  
**Recommendations**: Consider S1 (Visual Agent Builder mention)

#### Part 2: LiveRequestQueue (part2_live_request_queue.md)
**Status**: ✅ Consistent and up-to-date  
**Version-specific content**: None  
**Recommendations**: None

#### Part 3: Event Handling (part3_run_live.md)
**Status**: ⚠️ Missing new feature documentation  
**Version-specific content**: Mentions `usage_metadata` but doesn't explain Live API token usage  
**Recommendations**: Add C1 (Token Usage section)

#### Part 4: RunConfig (part4_run_config.md)
**Status**: ✅ Consistent and up-to-date  
**Version-specific content**: None  
**Recommendations**: Consider adding cost controls section with token usage

#### Part 5: Audio and Video (part5_audio_and_video.md)
**Status**: ✅ Consistent and up-to-date  
**Version-specific content**: None  
**Recommendations**: None

### Demo Application (src/bidi-demo/)

**Status**: ✅ Compatible with ADK 1.18.0  
**Analysis**: The demo application doesn't use any deprecated features and remains fully functional with 1.18.0.

**Potential Enhancement**: Could add token usage monitoring to the WebSocket responses:
```python
# In downstream_task()
async for event in runner.run_live(...):
    event_json = event.model_dump_json(exclude_none=True, by_alias=True)
    
    # Optional: Log token usage for monitoring
    if event.usage_metadata:
        logger.debug(f"Token usage: {event.usage_metadata.total_token_count}")
    
    await websocket.send_text(event_json)
```

## Recommendations Summary

### Immediate Actions (Critical)

1. **Document Token Usage in Live Events** (C1)
   - Add dedicated section in Part 3 explaining how to access and use `usage_metadata`
   - Include code examples showing token tracking in streaming sessions
   - Consider adding cost control section in Part 4

### Optional Enhancements (Suggestions)

2. **Mention Visual Agent Builder** (S1)
   - Brief note in Part 1 about development workflow options
   - Keep focus on code-first approach

3. **Cross-reference Token Usage with Session Resumption** (S2)
   - Add note in Part 4 about token tracking across resumed sessions
   - Explain cache-related token savings

### Demo Application

4. **Add Token Usage Logging** (Optional)
   - Enhance demo to log token usage for educational purposes
   - Show how to monitor costs in production streaming applications

## Conclusion

The documentation is **mostly compatible** with ADK 1.18.0, with one critical gap: the new token usage feature for Live API events is not documented. This is the only significant update relevant to bidirectional streaming in this release.

All other changes in 1.18.0 (Visual Agent Builder, MCP prompts, LiteLLM enhancements, Vertex AI features, etc.) do not affect the core bidirectional streaming concepts covered in this guide.

### Next Steps

1. Add token usage documentation to Part 3 (Critical)
2. Consider adding a cost controls section to Part 4 (Recommended)
3. Optionally enhance demo with token usage logging (Nice to have)
4. Monitor future ADK releases for Live API-specific changes

---

**Report Generation Details**:
- Tool: change-reviewer agent
- Analysis Date: 2025-11-08
- ADK Versions Compared: 1.18.0 (current) vs 1.18.0 (latest)
- Documentation Files Analyzed: 5 parts + demo application
- CHANGELOG Lines Reviewed: 1154 lines (v1.18.0 through v1.0.0)
