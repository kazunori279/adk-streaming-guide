# Gemini Live API Models Report

**Report Target:** Live API Models  
**Report Date:** 2025-10-29 19:53:26  
**Data Sources:**
- https://ai.google.dev/gemini-api/docs/models
- https://docs.cloud.google.com/vertex-ai/generative-ai/docs/model-reference/multimodal-live

---

## Executive Summary

This report documents all models that support the Live API capability across both Gemini API and Vertex AI platforms as of October 2025. A total of 4 Live API-supported models have been identified:

- **Gemini API:** 3 models (all in public preview)
- **Vertex AI:** 1 model (in public preview)

All identified Gemini API models are currently scheduled for deprecation on December 09, 2025.

---

## Model Cards

### 1. Gemini 2.0 Flash Live (Gemini API)

**Platform:** Gemini API

**Model Name:** `gemini-2.0-flash-live-001`

**Launch Stage:** Public preview

**Release Date:** April 2025

**Discontinuation Date:** December 09, 2025

**Supported Inputs:** Audio, video, and text

**Supported Outputs:** Text, and audio

**Maximum Input Tokens:** 1,048,576 (1M tokens)

**Maximum Output Tokens:** 8,192 (8K tokens)

**Context Window:** 1,048,576 tokens (1M)

**Capabilities:**
- Live API
- Function calling
- System instructions
- Grounding with Google Search

**Usage Types:** Not specified

**Notes:** Second generation small workhorse model with 1 million token context window. Supports multimodal inputs including audio and video with bidirectional audio output.

---

### 2. Gemini 2.5 Flash Native Audio (Gemini API)

**Platform:** Gemini API

**Model Name:** `gemini-2.5-flash-native-audio-preview-09-2025`

**Launch Stage:** Public preview

**Release Date:** September 2025

**Discontinuation Date:** December 09, 2025

**Supported Inputs:** Audio, video, text

**Supported Outputs:** Audio and text

**Maximum Input Tokens:** 8,192 (8K tokens)

**Maximum Output Tokens:** 16,384 (16K tokens)

**Context Window:** Not specified (default based on input tokens)

**Capabilities:**
- Live API
- Function calling
- System instructions
- Grounding with Google Search

**Usage Types:** Not specified

**Notes:** Native audio processing with multimodal inputs. Part of the Gemini 2.5 Flash family with enhanced audio capabilities.

---

### 3. Gemini Live 2.5 Flash Preview (Gemini API)

**Platform:** Gemini API

**Model Name:** `gemini-live-2.5-flash-preview`

**Launch Stage:** Public preview

**Release Date:** May 2025

**Discontinuation Date:** December 09, 2025

**Supported Inputs:** Text

**Supported Outputs:** Audio

**Maximum Input Tokens:** 8,192 (8K tokens)

**Maximum Output Tokens:** 16,384 (16K tokens)

**Context Window:** Not specified (default based on input tokens)

**Capabilities:**
- Live API
- Function calling
- System instructions
- Grounding with Google Search

**Usage Types:** Not specified

**Notes:** Text-to-speech focused Live API model with audio-only output. Specialized for conversational audio generation.

---

### 4. Gemini 2.0 Flash Live Preview (Vertex AI)

**Platform:** Vertex AI

**Model Name:** `gemini-2.0-flash-live-preview-04-09`

**Launch Stage:** Public preview

**Release Date:** Not specified in documentation

**Discontinuation Date:** Not specified in documentation

**Supported Inputs:** Audio, video, and text (inferred from platform capabilities)

**Supported Outputs:** Text and audio (inferred from platform capabilities)

**Maximum Input Tokens:** Not specified in documentation

**Maximum Output Tokens:** Not specified in documentation

**Context Window:** Not specified in documentation

**Capabilities:**
- Live API
- Function calling (supported on Vertex AI platform)
- System instructions (supported on Vertex AI platform)
- Grounding with Google Search (supported on Vertex AI platform)

**Usage Types:**
- Supports concurrent sessions
- Integrates with Vertex AI Provisioned Throughput

**Notes:** Vertex AI version of the Gemini 2.0 Flash Live model. The documentation references this model primarily in code examples. Detailed specifications may align with the Gemini API version but are not explicitly documented in the reviewed pages.

---

## Platform Comparison

### Gemini API vs Vertex AI

| Feature | Gemini API | Vertex AI |
|---------|------------|-----------|
| Number of Live API Models | 3 | 1 |
| Model Family Coverage | 2.0 Flash, 2.5 Flash | 2.0 Flash |
| Documentation Detail | Comprehensive | Limited |
| Deprecation Timeline | Clearly stated (Dec 2025) | Not specified |
| Token Limit Transparency | Fully documented | Not documented |
| Enterprise Features | Standard | Enhanced (Provisioned Throughput) |

---

## Key Findings

### 1. Model Availability
- All Live API models are currently in **public preview** stage
- No stable/GA Live API models are available as of this report date
- All Gemini API Live models have a short deprecation window (approximately 2-3 months from release)

### 2. Token Limits
- **Gemini 2.0 Flash Live** offers the largest context window at 1M tokens
- **Gemini 2.5 Flash** variants have smaller context windows (8K input)
- Output tokens are consistently limited to 8K-16K across models

### 3. Multimodal Support
- Most Live API models support audio and video inputs
- Audio output is a key feature across all Live API models
- One model (gemini-live-2.5-flash-preview) is specialized for text-to-audio only

### 4. Capabilities
- All models support core Live API features
- Function calling is standard across all models
- System instructions are supported for customization
- Grounding with Google Search is available for enhanced responses

### 5. Documentation Gaps
- Vertex AI documentation lacks detailed specifications for token limits
- Usage type information (RPM, TPM, concurrent sessions) is not clearly documented
- Some models appear only in code examples without full specification sheets

---

## Recommendations

### For Developers

1. **Plan for Model Transitions:** With all Gemini API models scheduled for deprecation in December 2025, plan for model migrations or prepare to use successor models.

2. **Choose Based on Use Case:**
   - For maximum context: Use `gemini-2.0-flash-live-001` (1M tokens)
   - For native audio processing: Use `gemini-2.5-flash-native-audio-preview-09-2025`
   - For text-to-speech only: Use `gemini-live-2.5-flash-preview`

3. **Platform Selection:**
   - Use Gemini API for development and prototyping with clear documentation
   - Use Vertex AI for enterprise deployments requiring provisioned throughput

### For Product Planning

1. **Monitor for Successor Models:** Given the short preview windows, watch for stable releases or next-generation Live API models
2. **Implement Version Flexibility:** Design applications to easily switch between model versions
3. **Test Across Platforms:** Evaluate both Gemini API and Vertex AI versions for production requirements

---

## Appendix

### Data Collection Methodology

This report was generated by:
1. Fetching official documentation from Google AI and Google Cloud
2. Parsing HTML content to extract model specifications
3. Cross-referencing information across multiple documentation pages
4. Validating token limits, capabilities, and deprecation dates

### Limitations

- Some Vertex AI specifications are inferred based on platform capabilities rather than explicit documentation
- Usage limits (RPM, TPM, concurrent sessions) were not clearly documented and are not included
- Additional models may exist in private preview or limited availability not reflected in public documentation

### Last Updated

2025-10-29 19:53:26

---

**Report Generated by:** Claude Code Research Agent  
**Version:** 1.0
