# Gemini Live API Models - Comprehensive Report
**Report Date:** October 29, 2025  
**Report Type:** Live API Models Status  
**Platforms Covered:** Gemini API, Vertex AI

---

## Executive Summary

This report provides a comprehensive overview of all currently available models supporting Live API functionality across both Gemini API and Vertex AI platforms. Live API enables low-latency bidirectional voice and video interactions with natural, human-like voice conversations and the ability to interrupt model responses.

**Key Findings:**
- **2 Live API models** currently available for Gemini API
- **2 Live API models** currently available for Vertex AI
- All models support audio and video inputs with audio outputs
- Both platforms are in preview/experimental stages
- Deprecation scheduled for December 9, 2025 for older model versions

---

## Platform Comparison: Gemini API vs Vertex AI

| Feature | Gemini API | Vertex AI |
|---------|------------|-----------|
| **Number of Live API Models** | 2 (Gemini 2.5 & 2.0 Flash Live) | 2 (Gemini 2.5 & 2.0 Flash Live) |
| **Access Model** | API Key / OAuth | Google Cloud Project |
| **Deployment** | Managed Service | Managed Service (Global/Regional) |
| **Pricing Model** | Pay-per-use | Pay-per-use + Provisioned Throughput |
| **Regional Availability** | Global | Limited regions (us-central1 for 2.5) |
| **Model Versioning** | Preview versions | Preview versions with specific release dates |

---

## Gemini API - Live API Models

### 1. Gemini 2.5 Flash Live

#### Model Card

| Property | Details |
|----------|---------|
| **Platform** | Gemini API |
| **Model Code** | `gemini-2.5-flash-native-audio-preview-09-2025` |
| **Alternative Code** | `gemini-live-2.5-flash-preview` (deprecated Dec 9, 2025) |
| **Launch Stage** | Preview |
| **Latest Update** | September 2025 |
| **Knowledge Cutoff** | January 2025 |
| **Deprecation Date** | December 9, 2025 (for gemini-live-2.5-flash-preview) |

#### Supported Modalities

**Inputs:**
- Audio
- Video
- Text

**Outputs:**
- Audio
- Text

#### Token Limits

| Type | Limit |
|------|-------|
| **Input Token Limit** | 131,072 tokens |
| **Output Token Limit** | 8,192 tokens |

#### Capabilities

| Capability | Status |
|------------|--------|
| **Audio Generation** | ✓ Supported |
| **Live API** | ✓ Supported |
| **Function Calling** | ✓ Supported |
| **Search Grounding** | ✓ Supported |
| **Thinking** | ✓ Supported |
| **Batch API** | ✗ Not Supported |
| **Caching** | ✗ Not Supported |
| **Code Execution** | ✗ Not Supported |
| **Grounding with Google Maps** | ✗ Not Supported |
| **Image Generation** | ✗ Not Supported |
| **Structured Outputs** | ✗ Not Supported |
| **URL Context** | ✗ Not Supported |

---

### 2. Gemini 2.0 Flash Live

#### Model Card

| Property | Details |
|----------|---------|
| **Platform** | Gemini API |
| **Model Code** | `gemini-2.0-flash-live-001` |
| **Launch Stage** | Preview |
| **Latest Update** | April 2025 |
| **Knowledge Cutoff** | August 2024 |
| **Deprecation Date** | December 9, 2025 |

#### Supported Modalities

**Inputs:**
- Audio
- Video
- Text

**Outputs:**
- Audio
- Text

#### Token Limits

| Type | Limit |
|------|-------|
| **Input Token Limit** | 1,048,576 tokens (1M tokens) |
| **Output Token Limit** | 8,192 tokens |

#### Capabilities

| Capability | Status |
|------------|--------|
| **Audio Generation** | ✓ Supported |
| **Live API** | ✓ Supported |
| **Function Calling** | ✓ Supported |
| **Search Grounding** | ✓ Supported |
| **Code Execution** | ✓ Supported |
| **Structured Outputs** | ✓ Supported |
| **URL Context** | ✓ Supported |
| **Batch API** | ✗ Not Supported |
| **Caching** | ✗ Not Supported |
| **Grounding with Google Maps** | ✗ Not Supported |
| **Image Generation** | ✗ Not Supported |
| **Thinking** | ✗ Not Supported |

---

## Vertex AI - Live API Models

### 1. Gemini 2.5 Flash Live (Vertex AI)

#### Model Card

| Property | Details |
|----------|---------|
| **Platform** | Vertex AI |
| **Model Code** | `gemini-live-2.5-flash-preview-native-audio-09-2025` |
| **Launch Stage** | Public Preview |
| **Release Date** | September 18, 2025 |
| **Discontinuation Date** | TBD (Preview version) |

#### Supported Modalities

**Inputs:**
- Text
- Audio (Raw 16-bit PCM at 16kHz, little-endian)
- Video

**Outputs:**
- Text
- Audio (Raw 16-bit PCM at 24kHz, little-endian)

#### Token Limits

| Type | Limit |
|------|-------|
| **Maximum Input Tokens** | 128K |
| **Maximum Output Tokens** | 64K |
| **Context Window** | 32K (default), upgradable to 128K |

#### Regional Availability

| Region Type | Regions |
|-------------|---------|
| **Model Availability** | United States |
| **Specific Regions** | us-central1 |

#### Usage Types

- Dynamic Shared Quota
- Provisioned Throughput
- Up to 1000 concurrent sessions

---

### 2. Gemini 2.0 Flash Live (Vertex AI)

#### Model Card

| Property | Details |
|----------|---------|
| **Platform** | Vertex AI |
| **Model Code** | `gemini-2.0-flash-live-preview-04-09` |
| **Launch Stage** | Public Preview |
| **Release Date** | April 9, 2025 |
| **Knowledge Cutoff** | June 2024 |

#### Supported Modalities

**Inputs:**
- Audio
- Video

**Outputs:**
- Audio

#### Token Limits

| Type | Limit |
|------|-------|
| **Maximum Input Tokens** | 32,768 tokens |
| **Maximum Output Tokens** | 8,192 tokens (default) |

#### Media Limits

| Media Type | Limit |
|------------|-------|
| **Maximum Video Length (with audio)** | ~45 minutes |
| **Maximum Video Length (without audio)** | ~1 hour |
| **Maximum Videos per Prompt** | 10 |
| **Maximum Audio Length per Prompt** | ~8.4 hours (up to 1M tokens) |
| **Maximum Audio Files per Prompt** | 1 |

#### Regional Availability

| Region Type | Regions |
|-------------|---------|
| **Model Availability** | Global |
| **Specific Regions** | global (with dynamic shared quota & Provisioned Throughput) |

---

## Key Feature Comparison

### Gemini 2.5 Flash Live vs 2.0 Flash Live

| Feature | Gemini 2.5 Flash Live | Gemini 2.0 Flash Live |
|---------|----------------------|----------------------|
| **Input Token Limit (Gemini API)** | 131K | 1M |
| **Output Token Limit** | 8K | 8K |
| **Knowledge Cutoff** | Jan 2025 | Aug 2024 |
| **Code Execution** | ✗ | ✓ |
| **Structured Outputs** | ✗ | ✓ |
| **URL Context** | ✗ | ✓ |
| **Thinking** | ✓ | ✗ |
| **Latest Update** | Sept 2025 | April 2025 |

---

## Platform-Specific Differences

### Gemini API Features
- **Simpler Authentication:** API Key or OAuth
- **Broader Access:** Available globally without regional restrictions
- **Version Aliases:** Support for both specific versions and preview aliases
- **Faster Updates:** More frequent model updates and iterations

### Vertex AI Features
- **Enterprise Integration:** Native GCP integration
- **Provisioned Throughput:** Dedicated capacity options
- **Data Residency:** Data residency controls at rest
- **Regional Deployment:** Choose specific regions for compliance
- **Security Controls:** Enhanced enterprise security features
- **Concurrent Sessions:** Support for up to 1000 concurrent sessions

---

## Availability & Access Requirements

### Gemini API
- **Access:** API key from Google AI Studio or OAuth
- **Regions:** Global availability
- **Restrictions:** None reported
- **Pricing:** Pay-per-use based on token consumption

### Vertex AI
- **Access:** Google Cloud Project with Vertex AI API enabled
- **Regions:** 
  - Gemini 2.5 Flash Live: us-central1
  - Gemini 2.0 Flash Live: global
- **Requirements:** 
  - Active GCP billing account
  - Vertex AI API enabled
  - Appropriate IAM permissions
- **Pricing:** Pay-per-use + optional Provisioned Throughput

---

## Recent Updates & Changes

### September 2025
- **Gemini 2.5 Flash Live** released on Gemini API
- Model code: `gemini-2.5-flash-native-audio-preview-09-2025`
- Vertex AI version: `gemini-live-2.5-flash-preview-native-audio-09-2025`
- Added Thinking capability
- Knowledge cutoff updated to January 2025

### April 2025
- **Gemini 2.0 Flash Live** updated
- Vertex AI model code: `gemini-2.0-flash-live-preview-04-09`
- Enhanced with structured outputs and URL context

### Upcoming Changes
- **December 9, 2025:** Deprecation of older model versions
  - `gemini-live-2.5-flash-preview` (to be replaced by `gemini-2.5-flash-native-audio-preview-09-2025`)
  - `gemini-2.0-flash-live-001`

---

## Technical Specifications

### Audio Requirements

#### Gemini API
- Input format: Standard audio formats supported
- Output format: Audio generation supported

#### Vertex AI
- **Input Audio Format:** Raw 16-bit PCM audio at 16kHz, little-endian
- **Output Audio Format:** Raw 16-bit PCM audio at 24kHz, little-endian

### Live API Characteristics
- **Bidirectional Communication:** Real-time two-way audio/video streaming
- **Low Latency:** Optimized for real-time conversations
- **Interruption Support:** Users can interrupt model responses
- **Natural Conversations:** Human-like voice interactions
- **Multi-modal:** Simultaneous processing of audio, video, and text

---

## Use Cases

### Optimal Use Cases for Live API Models

1. **Voice Assistants**
   - Real-time conversational AI
   - Multi-turn dialogues
   - Natural interruption handling

2. **Customer Support**
   - Live video/audio support sessions
   - Screen sharing with audio commentary
   - Real-time troubleshooting

3. **Education & Training**
   - Interactive tutoring sessions
   - Live language learning
   - Video-based instruction with Q&A

4. **Accessibility**
   - Real-time transcription
   - Audio description generation
   - Voice-controlled interfaces

5. **Content Creation**
   - Live podcast generation
   - Video commentary
   - Interactive storytelling

---

## Migration Guidance

### Transitioning from Deprecated Models

For users currently using `gemini-live-2.5-flash-preview` or `gemini-2.0-flash-live-001`:

1. **Update Model Code** (Before December 9, 2025):
   - From: `gemini-live-2.5-flash-preview`
   - To: `gemini-2.5-flash-native-audio-preview-09-2025`

2. **Test Thoroughly:**
   - Verify audio format compatibility
   - Test function calling implementations
   - Validate grounding features

3. **Monitor Performance:**
   - Compare latency metrics
   - Assess response quality
   - Track token consumption

---

## Best Practices

### Choosing Between Platforms

**Choose Gemini API when:**
- Building consumer applications
- Need global deployment
- Prefer simpler authentication
- Want faster access to latest models

**Choose Vertex AI when:**
- Building enterprise applications
- Require data residency controls
- Need provisioned throughput
- Want GCP ecosystem integration
- Require enhanced security features

### Choosing Between Models

**Choose Gemini 2.5 Flash Live when:**
- Need latest knowledge cutoff (Jan 2025)
- Want Thinking capability
- Building newer applications
- Prefer latest model iterations

**Choose Gemini 2.0 Flash Live when:**
- Need 1M token input capacity (Gemini API)
- Require code execution
- Need structured outputs
- Want URL context support

---

## Resources & Documentation

### Official Documentation

**Gemini API:**
- Models Overview: https://ai.google.dev/gemini-api/docs/models
- Live API Guide: https://ai.google.dev/gemini-api/docs/live
- Live API Tools: https://ai.google.dev/gemini-api/docs/live-tools
- Live API Session: https://ai.google.dev/gemini-api/docs/live-session

**Vertex AI:**
- Multimodal Live API Reference: https://cloud.google.com/vertex-ai/generative-ai/docs/model-reference/multimodal-live
- Gemini 2.5 Flash Live API: https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/2-5-flash-live-api
- Gemini 2.0 Flash (Live API section): https://cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/2-0-flash#live-api

### Sample Applications
- WebSocket Demo App: https://github.com/GoogleCloudPlatform/generative-ai/tree/main/gemini/multimodal-live-api/websocket-demo-app
- Intro Colab: https://colab.research.google.com/github/GoogleCloudPlatform/generative-ai/blob/main/gemini/multimodal-live-api/intro_multimodal_live_api_genai_sdk.ipynb

---

## Limitations & Considerations

### Known Limitations

**All Live API Models:**
- No batch API support
- No caching support
- No image generation
- No Google Maps grounding

**Gemini 2.5 Flash Live:**
- No code execution
- No structured outputs
- No URL context
- Lower input token limit (131K vs 1M for 2.0)

**Gemini 2.0 Flash Live:**
- Older knowledge cutoff (Aug 2024)
- No Thinking capability

### Rate Limits
- Vertex AI: Up to 1000 concurrent sessions supported
- Gemini API: Standard rate limits apply (refer to documentation)

---

## Conclusion

Both Gemini API and Vertex AI offer robust Live API capabilities through their respective Gemini 2.5 and 2.0 Flash Live models. The choice between platforms and model versions depends on specific use case requirements, deployment preferences, and feature needs.

**Key Takeaways:**
1. **Gemini 2.5 Flash Live** provides the latest knowledge and Thinking capability
2. **Gemini 2.0 Flash Live** offers larger context windows and more advanced features like code execution
3. **Vertex AI** is better for enterprise deployments with compliance needs
4. **Gemini API** is better for rapid development and global deployment
5. All preview models are subject to deprecation - plan migrations accordingly

**Action Items:**
- Monitor for new model releases beyond the December 2025 deprecation dates
- Test applications with both model versions to determine optimal fit
- Plan migration from deprecated model versions
- Subscribe to official channels for updates on Live API capabilities

---

*Report generated on October 29, 2025*  
*Data sourced from official Google AI and Vertex AI documentation*  
*Model information accurate as of report generation date*
