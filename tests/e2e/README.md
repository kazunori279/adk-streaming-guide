# End-to-end test procedures

This document provides step-by-step instructions for testing the ADK bidirectional streaming demo app using Chrome DevTools MCP server.

## 1. Environment setup

### Copy the demo code to a temporary directory

For testing purposes, we will copy the demo code to /tmp/demo directory and run the demo in it.

```bash
mkdir -p /tmp/demo
cp -r src/demo/* /tmp/demo
cd /tmp/demo
```

### Run the demo app

- Follow the instructions in /tmp/demo/README.md to run the app
- Monitor /tmp/demo/app/server.log to confirm that the server is successfully started.

## 2. End-to-End UI Testing with Chrome DevTools MCP

### Step 1: Navigate to the application

```yaml
mcp__chrome-devtools__navigate_page
url: http://localhost:8000
```

**Expected:** Page loads successfully

### Step 2: Take a snapshot to verify UI

```yaml
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

```yaml
mcp__chrome-devtools__fill
uid: <api-key-field-uid>
value: your_api_key_here
```

**For Vertex AI:**

```yaml
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

```yaml
mcp__chrome-devtools__click
uid: <connect-button-uid>
```

**Expected:**

- Status changes to "● Connected"
- Log shows: `[INFO] WebSocket connection established`
- Send button becomes enabled

### Step 5: Send a test message

```yaml
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

```yaml
mcp__chrome-devtools__take_screenshot
```

**Expected:** Screenshot showing streaming conversation with partial and complete events

### Step 7: Test graceful close

```yaml
mcp__chrome-devtools__click
uid: <close-button-uid>
```

**Expected:**

- Log shows: `[INFO] Sending graceful close signal`
- Connection closes cleanly

### Step 8: Check console for errors

```yaml
mcp__chrome-devtools__list_console_messages
```

**Expected:** No critical errors (warnings about development mode are acceptable)

### Step 9: Check server logs for errors

```bash
cat /tmp/demo/app/server.log | grep -i error
```

**Expected:** No critical errors (warnings about development mode are acceptable)

## 3. Test Cleanup

### 3.1 Stop the Server

```bash
# Find and kill the server process
pkill -f "uvicorn app.main"
```

**Expected output from run.sh cleanup:**

```text
Stopping server (PID: <process-id>)...
Server stopped
```

### 3.2 Clean Up Test Artifacts

```bash
rm -rf /tmp/demo
```

## 4. Test Report

Show a summary of the e2e test.
