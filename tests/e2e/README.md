# End-to-end test procedures

This document provides step-by-step instructions for testing the ADK bidirectional streaming demo app using Chrome DevTools MCP server.

## 1. Environment Setup

- Create tmp directory under tests/e2e and copy src/demo/* to it.
- Change to the directory and execute run.sh


## 2. Verify Server is Running

- Monitor server.log and wait for the server start up.

## 3. End-to-End Testing with Chrome DevTools MCP

### Step 1: Navigate to the application

```
mcp__chrome-devtools__navigate_page
url: http://localhost:8000
```

**Expected:** Page loads successfully

### Step 2: Take a snapshot to verify UI

```
mcp__chrome-devtools__take_snapshot
```

**Expected elements:**

- Status indicator (should show "● Disconnected")
- API Backend radio buttons (Gemini API / Vertex AI)
- Credential input fields
- Model dropdown
- WebSocket URL field (pre-filled with `ws://localhost:8000/ws`)
- Message input field
- Connect/Disconnect buttons
- Send/Close buttons
- RunConfig checkboxes
- Log area

### Step 3: Configure credentials in the UI

Use tests/e2e/.env to copy appropriate values to the UI

**For Gemini API:**

```
mcp__chrome-devtools__fill
uid: <api-key-field-uid>
value: your_api_key_here
```

**For Vertex AI:**

```
mcp__chrome-devtools__click
uid: <vertex-radio-button-uid>

mcp__chrome-devtools__fill
uid: <gcp-project-field-uid>
value: your_project_id

mcp__chrome-devtools__fill
uid: <gcp-location-field-uid>
value: us-central1
```

### Step 4: Connect WebSocket

```
mcp__chrome-devtools__click
uid: <connect-button-uid>
```

**Expected:**

- Status changes to "● Connected"
- Log shows: `[INFO] WebSocket connection established`
- Send button becomes enabled

### Step 5: Send a test message

```
mcp__chrome-devtools__fill
uid: <message-input-uid>
value: Hello! Can you explain what ADK streaming is?

mcp__chrome-devtools__click
uid: <send-button-uid>
```

**Expected in log:**

1. `[SENT] Hello! Can you explain what ADK streaming is?`
2. `[PARTIAL]` events showing streaming text chunks
3. `[COMPLETE]` event with full response
4. `[TURN COMPLETE]` event marking end of response

### Step 6: Take screenshot of results

```
mcp__chrome-devtools__take_screenshot
```

**Expected:** Screenshot showing streaming conversation with partial and complete events

### Step 7: Test graceful close

```
mcp__chrome-devtools__click
uid: <close-button-uid>
```

**Expected:**

- Log shows: `[INFO] Sending graceful close signal`
- Connection closes cleanly

### Step 8: Check console for errors

```
mcp__chrome-devtools__list_console_messages
```

**Expected:** No critical errors (warnings about development mode are acceptable)

### Step 9: Check server.log for errors

**Expected:** No critical errors (warnings about development mode are acceptable)

## 4. Test Cleanup

### 4.1 Stop the Server

Kill the uvicorn server process

### 4.2 Clean Up Test Artifacts

Remove the /tmp directory

## 5. Test report

Show a summary of the e2e test.

