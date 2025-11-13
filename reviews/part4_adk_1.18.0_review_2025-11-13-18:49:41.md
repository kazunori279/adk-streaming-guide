# Part 4 ADK v1.18.0 Compatibility Review

**Review Date**: 2025-11-13 18:49:41
**ADK Version**: v1.18.0
**Documentation File**: `docs/part4_run_config.md`
**Reviewer**: Claude Code with google-adk skill

## Executive Summary

Part 4 (RunConfig Configuration) requires updates to address one **Critical** issue related to a deprecated parameter. The documentation currently uses `save_live_audio` which has been deprecated in ADK v1.18.0 in favor of `save_live_blob`. Additionally, ADK v1.18.0 added token usage metadata to live events, which is not documented in Part 4 but may be relevant for production deployments.

### Summary Statistics

- **Critical Issues**: 1 (deprecated parameter documentation)
- **Warnings**: 0
- **Suggestions**: 2 (token usage documentation, migration note)

---

## Critical Issues

### C1: `save_live_audio` Deprecated - Update Required

**Severity**: Critical
**Impact**: Users following current documentation will see deprecation warnings

**Finding**:

In ADK v1.18.0, the `save_live_audio` parameter has been deprecated in favor of `save_live_blob`. This change was introduced in commit `0ab79b95` with the message:

> "fix: Deprecate save_live_audio in favor of save_live_blob and fix audio event saving"

**Current ADK Source** (run_config.py:107-117):

```python
save_live_blob: bool = False
"""Saves live video and audio data to session and artifact service."""

save_live_audio: bool = Field(
    default=False,
    deprecated=True,
    description=(
        'DEPRECATED: Use save_live_blob instead. If set to True, it saves'
        ' live video and audio data to session and artifact service.'
    ),
)
```

**Model Validator** (run_config.py:132-145):

```python
@model_validator(mode='before')
@classmethod
def check_for_deprecated_save_live_audio(cls, data: Any) -> Any:
  """If save_live_audio is passed, use it to set save_live_blob."""
  if isinstance(data, dict) and 'save_live_audio' in data:
    warnings.warn(
        'The `save_live_audio` config is deprecated and will be removed in a'
        ' future release. Please use `save_live_blob` instead.',
        DeprecationWarning,
        stacklevel=2,
    )
    if data['save_live_audio']:
      data['save_live_blob'] = True
  return data
```

**Current Documentation Issues**:

1. **Quick Reference Table** (part4_run_config.md:22):
   - Lists `save_live_audio` without deprecation notice

2. **Code Examples** (part4_run_config.md:786):
   ```python
   save_live_audio=True,  # Default: False
   ```

3. **Section Title** (part4_run_config.md:810):
   - Section titled "### save_live_audio" should reference `save_live_blob`

4. **Cross-reference in Part 3** (part3_run_live.md:147):
   - References `RunConfig.save_live_model_audio_to_session = True` (incorrect parameter name)
   - Links to `[Part 4: save_live_audio](part4_run_config.md#save_live_audio)`

**Recommended Action**:

**Option 1: Update to New Parameter (RECOMMENDED)**

Replace all instances of `save_live_audio` with `save_live_blob` throughout the documentation:

1. **Update Quick Reference Table** (line 22):
   ```markdown
   | **save_live_blob** | bool | Persist audio/video streams | Both | [Details](#save_live_blob) |
   ```

2. **Update Section Title** (line 810):
   ```markdown
   ### save_live_blob
   ```

3. **Update Section Content** (line 810-843):
   ```markdown
   ### save_live_blob

   This parameter controls whether audio and video streams are persisted to ADK's session and artifact services for debugging, compliance, and quality assurance purposes.

   > **Note**: This parameter replaces the deprecated `save_live_audio` parameter introduced in earlier ADK versions. If you're migrating from ADK versions prior to v1.18.0, replace `save_live_audio=True` with `save_live_blob=True`.

   **Important scope limitation:** Currently, **only audio is persisted** by ADK's implementation. Video streams are not yet stored by default, even when video input is used in the session.

   When enabled, ADK persists audio streams to:

   - **[Session service](https://google.github.io/adk-docs/sessions/)**: Conversation history includes audio references
   - **[Artifact service](https://google.github.io/adk-docs/artifacts/)**: Audio files stored with unique IDs
   ```

4. **Update Code Examples**:
   ```python
   run_config = RunConfig(
       # Limit total LLM calls per invocation
       max_llm_calls=500,

       # Save audio artifacts for debugging/compliance
       save_live_blob=True,  # Default: False

       # Attach custom metadata to events
       custom_metadata={"user_tier": "premium", "session_type": "support"},

       # Enable compositional function calling (experimental)
       support_cfc=True  # Default: False (Gemini 2.x models only)
   )
   ```

5. **Update Cross-reference in Part 3** (part3_run_live.md:147):
   ```markdown
   > 💡 **Audio Persistence**: To save audio conversations to the ADK `Session` for review or resumption, enable `RunConfig.save_live_blob = True`. This persists audio streams to artifacts. See [Part 4: save_live_blob](part4_run_config.md#save_live_blob) for configuration details.
   ```

**Option 2: Document Both with Deprecation Notice**

Keep `save_live_audio` section but add prominent deprecation warning, then add `save_live_blob` as the new recommended approach.

---

## Warnings

No warnings identified. The documentation is generally accurate for ADK v1.18.0 aside from the critical deprecation issue above.

---

## Suggestions

### S1: Document Token Usage Metadata for Live Events

**Context**:

ADK v1.18.0 added token usage metadata to live streaming events (commit `6e5c0eb6`):

> "feat: Add token usage to live events for bidi streaming
> Populate the usage_metadata field for live events with the metadata provided by the Gemini live API."

**Current State**:

Part 4 does not mention that Live API events now include `usage_metadata` for tracking token consumption during bidirectional streaming sessions.

**Recommendation**:

Add a new section or note documenting this feature, particularly useful for:
- Cost monitoring in production
- Quota management
- Session analytics
- Debugging token consumption patterns

**Suggested Location**:

Add a subsection under "Miscellaneous Controls" or create a new section titled "Monitoring and Observability" that covers:
- Token usage metadata in live events
- How to access usage data from events
- Use cases for production monitoring

**Example Content**:

```markdown
### Token Usage Tracking in Live Events

**New in ADK v1.18.0**: Live streaming events now include token usage metadata, allowing you to track token consumption in real-time during bidirectional streaming sessions.

**Accessing usage metadata:**

```python
async for event in runner.run_live(
    session=session,
    live_request_queue=queue,
    run_config=run_config
):
    if hasattr(event, 'usage_metadata') and event.usage_metadata:
        print(f"Tokens used: {event.usage_metadata}")
        # Track cumulative usage, costs, quotas, etc.
```

**Use cases:**
- **Cost monitoring**: Track token consumption per session for billing
- **Quota management**: Monitor usage against platform limits
- **Analytics**: Analyze conversation efficiency and token patterns
- **Debugging**: Identify unexpectedly high token usage
```

### S2: Add Migration Note for Users Upgrading from Earlier Versions

**Context**:

Users upgrading from ADK versions prior to v1.18.0 may have existing code using `save_live_audio`. While ADK handles this gracefully with deprecation warnings, clear migration guidance would improve the upgrade experience.

**Recommendation**:

Add a migration note at the top of Part 4 or in the `save_live_blob` section:

```markdown
> **Migration Note for ADK v1.18.0+**: If you're upgrading from earlier ADK versions, update `save_live_audio=True` to `save_live_blob=True` in your `RunConfig`. The old parameter still works but will show deprecation warnings and will be removed in a future release.
```

---

## Detailed Analysis by Section

### Response Modalities (Lines 38-103)

**Status**: ✅ Accurate for ADK v1.18.0

- Parameter name matches source: `response_modalities`
- Default behavior correctly documented
- Transcription defaults correctly explained
- Source references are accurate

### StreamingMode: BIDI or SSE (Lines 105-259)

**Status**: ✅ Accurate for ADK v1.18.0

- `StreamingMode.BIDI` and `StreamingMode.SSE` correctly documented
- Protocol differences accurately explained
- Model compatibility information is correct
- Sequence diagrams match ADK implementation

### Live API Connections and Sessions (Lines 260-373)

**Status**: ✅ Accurate for ADK v1.18.0

- ADK Session vs Live API session distinction correctly explained
- Connection and session limits accurately documented
- Platform differences (Gemini vs Vertex AI) are correct
- Duration limits match official documentation

### Live API Session Resumption (Lines 374-507)

**Status**: ✅ Accurate for ADK v1.18.0

- `SessionResumptionConfig` usage is correct
- Transparent mode behavior accurately described
- ADK's automatic reconnection logic correctly explained
- Sequence diagram matches ADK implementation

### Live API Context Window Compression (Lines 509-618)

**Status**: ✅ Accurate for ADK v1.18.0

- `ContextWindowCompressionConfig` parameter is correct
- Configuration examples match ADK source
- Platform behavior accurately described
- Token threshold recommendations are reasonable

### Concurrent Live API Sessions and Quota Management (Lines 670-774)

**Status**: ✅ Accurate for ADK v1.18.0

- Quota limits are accurately documented
- Architectural patterns are sound
- Best practices align with ADK design

### Miscellaneous Controls (Lines 776-977)

**Status**: ⚠️ Requires update for `save_live_audio` deprecation

- ✅ `max_llm_calls` documentation is accurate
- ❌ `save_live_audio` needs update to `save_live_blob` (Critical issue C1)
- ✅ `custom_metadata` correctly documented (matches v1.18.0 addition)
- ✅ `support_cfc` documentation is accurate

---

## Verification Against ADK Source

**Files Reviewed**:
- `src/google/adk/agents/run_config.py` (v1.18.0)
- ADK CHANGELOG.md (v1.17.0 → v1.18.0)
- Commit `0ab79b95`: save_live_audio deprecation
- Commit `6e5c0eb6`: token usage for live events

**Key Changes in v1.18.0**:

1. ✅ `custom_metadata` parameter added - DOCUMENTED in Part 4
2. ❌ `save_live_audio` deprecated in favor of `save_live_blob` - NOT YET UPDATED
3. ⚠️ Token usage metadata in live events - NOT DOCUMENTED (suggestion)

---

## Action Items

### High Priority (Critical)

1. **C1: Update save_live_audio to save_live_blob**
   - Files: `docs/part4_run_config.md`, `docs/part3_run_live.md`
   - Update all references to use the new parameter name
   - Add deprecation notice for users migrating from earlier versions

### Medium Priority (Suggestions)

2. **S1: Document token usage metadata in live events**
   - File: `docs/part4_run_config.md`
   - Add section on monitoring and observability
   - Provide examples of accessing usage metadata

3. **S2: Add migration note for upgrading users**
   - File: `docs/part4_run_config.md`
   - Add prominent note about parameter rename
   - Include example of old → new syntax

---

## Conclusion

Part 4 documentation is generally accurate and comprehensive for ADK v1.18.0, with one critical update needed: replacing the deprecated `save_live_audio` parameter with `save_live_blob`. This is a straightforward find-and-replace operation with minimal impact on the documentation structure.

The two suggestions (token usage documentation and migration note) would enhance the documentation's value for production users and those upgrading from earlier ADK versions, but are not critical for correctness.

**Recommendation**: Prioritize fixing C1 immediately, then consider adding S1 and S2 in a follow-up update.
