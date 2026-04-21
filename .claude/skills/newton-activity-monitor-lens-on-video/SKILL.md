---
name: newton-activity-monitor-lens-on-video
description: Analyze uploaded video files using Newton's activity monitor lens. Server reads the video via video_file_reader and streams results via SSE. Use for batch video analysis, activity detection, or temporal event extraction from video files. NOT for live webcam — use /camera-frame-analysis for that.
---

# Newtown Activity Monitor Lens on Video (Upload Video → Server-Side Processing → SSE)

Upload a video file to the Archetype AI platform and analyze it server-side using Newton's activity monitor lens. The server reads the video via `video_file_reader` and streams inference results back via SSE.

**This skill is for UPLOADED VIDEO FILES only.** For live webcam analysis, use `/camera-frame-analysis` instead.

| | This skill (activity-monitor-lens-on-video) | camera-frame-analysis |
|---|---|---|
| **Input** | Uploaded video file (mp4, etc.) | Live webcam (base64 JPEG frames) |
| **Who reads frames** | Server (`video_file_reader`) | Client (Python cv2 / JS canvas) |
| **Event type** | Server-driven processing | `model.query` (request/response) |
| **Response** | Async via SSE stream (`inference.result`) | Direct in POST response |
| **Use case** | Batch video analysis, post-hoc review | Real-time webcam Q&A |

---

## Step 0: Choose an implementation approach

Before writing any code, ask the user which approach they want:

| Approach | Best for | API key security | Requires |
|----------|----------|-------------------|----------|
| **Server Proxy (SvelteKit)** | SvelteKit apps, demos with MediaRecorder | Private (server-side only) | SvelteKit server routes, `ffmpeg-static` for MediaRecorder video conversion |
| **Plain JS (client-side)** | Quick prototypes, static sites | Exposed in client | Direct `fetch` calls, pre-recorded MP4 files only |
| **Python** | Backend scripts, batch processing, CLI tools | Private (server-side) | `archetypeai` Python package |

### Key considerations

- **MediaRecorder video (webcam recordings):** Chrome's `MediaRecorder` produces fragmented MP4 or WebM that the Archetype `video_file_reader` **cannot parse**. You MUST convert to proper MP4 (with moov atom) before uploading. The Server Proxy approach handles this automatically with `ffmpeg-static`. Plain JS does NOT support this — use pre-recorded MP4 files only.
- **CORS:** The Archetype AI API does not allow direct browser requests. The Server Proxy approach avoids this by routing all API calls through SvelteKit server routes. Plain JS will only work if CORS is not an issue (e.g., server-side Node.js scripts).
- **API key:** The Server Proxy approach keeps the API key in private server env vars. Plain JS exposes it to the browser.

---

## Default Model Parameters

| Parameter | Default | Description |
|---|---|---|
| `model_version` | `Newton::c2_4_7b_251215a172f6d7` | Newton model ID |
| `instruction` | *(your activity description prompt)* | What the model should output |
| `focus` | *(what to look for)* | Focus of analysis |
| `temporal_focus` | `5` | Temporal window in seconds |
| `max_new_tokens` | `512` | Max response length |
| `camera_buffer_size` | `5` | Frames to buffer before processing |
| `camera_buffer_step_size` | `5` | Step size for frame sampling |
| `memory_prompt_buffer_size` | `0` | Prior prompts to retain (0 = no memory) |

---

## API Reference

| Operation | Method | Endpoint | Body |
|-----------|--------|----------|------|
| Upload file | POST | `/files` | `FormData` |
| List lenses | GET | `/lens/metadata` | — |
| Register lens | POST | `/lens/register` | `{ lens_config: config }` |
| Delete lens | POST | `/lens/delete` | `{ lens_id }` |
| Create session | POST | `/lens/sessions/create` | `{ lens_id }` |
| Process event | POST | `/lens/sessions/events/process` | `{ session_id, event }` |
| Destroy session | POST | `/lens/sessions/destroy` | `{ session_id }` |
| SSE consumer | GET | `/lens/sessions/consumer/{sessionId}` | — |

---

## Frontend Architecture

Decompose the UI into components rather than building a monolithic `+page.svelte`. See `@rules/frontend-architecture` for full conventions.

### Recommended decomposition

| UI Area | Component | Composes (DS primitives) | Key Props |
|---------|-----------|--------------------------|-----------|
| Video input | `VideoUpload.svelte` (or reuse VideoPlayer pattern) | Card, Button | `onupload`, `status`, `videoUrl` |
| Status | `ProcessingStatus.svelte` | Card, Badge, Spinner | `status`, `message` |
| Summary | `AnalysisSummary.svelte` | Card | `title`, `summary` |
| Log | Use FlatLogItem pattern in ScrollArea | FlatLogItem, ScrollArea | `status`, `message`, `detail` |

### Layout and API logic

- Use `@skills/create-dashboard` as a layout starting point for dashboard-style UIs
- Extract SSE consumer, session management, and upload logic into `$lib/api/activity-monitor.js`
- `+page.svelte` orchestrates flow state (status, sessionId) and passes data to components via props

### What NOT to include unless requested

- Charts (SensorChart, ScatterChart) — only if the user asks for time-series visualization
- Complex data tables — only if the user needs tabular result inspection

---

## Approach A: Server Proxy (SvelteKit)

Routes all API calls through SvelteKit server routes. Converts MediaRecorder video to proper MP4 using `ffmpeg-static`. API key stays private on the server.

### Prerequisites

```bash
npm install ffmpeg-static
```

Add to `.env`:
```
ATAI_API_KEY=your-api-key
ATAI_API_ENDPOINT=https://api.u1.archetypeai.app/v0.5
```

### Server Route 1: Upload (`src/routes/api/upload/+server.js`)

Accepts a video blob, converts to proper MP4 via ffmpeg, then uploads to the Archetype API.

```javascript
import { json, error } from '@sveltejs/kit';
import { ATAI_API_KEY, ATAI_API_ENDPOINT } from '$env/static/private';
import { writeFile, unlink, readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { spawn } from 'node:child_process';
import ffmpegPath from 'ffmpeg-static';

function convertToMp4(inputPath, outputPath) {
  return new Promise((resolve, reject) => {
    const args = [
      '-i', inputPath,
      '-c:v', 'libx264', '-preset', 'ultrafast',
      '-movflags', '+faststart',
      '-an', '-y', outputPath
    ];
    const proc = spawn(ffmpegPath, args, { stdio: ['ignore', 'pipe', 'pipe'] });
    let stderr = '';
    proc.stderr.on('data', (d) => (stderr += d.toString()));
    proc.on('close', (code) => {
      if (code === 0) resolve();
      else reject(new Error(`ffmpeg exited with code ${code}: ${stderr.slice(-500)}`));
    });
    proc.on('error', reject);
  });
}

export async function POST({ request }) {
  const formData = await request.formData();
  const file = formData.get('file');
  if (!file) throw error(400, 'No file provided');

  const timestamp = Date.now();
  const inputPath = join(tmpdir(), `upload_input_${timestamp}`);
  const outputPath = join(tmpdir(), `upload_output_${timestamp}.mp4`);

  try {
    const buffer = Buffer.from(await file.arrayBuffer());
    await writeFile(inputPath, buffer);
    await convertToMp4(inputPath, outputPath);

    const convertedBuffer = await readFile(outputPath);
    const outputName = file.name.replace(/\.\w+$/, '.mp4');
    const convertedFile = new File([convertedBuffer], outputName, { type: 'video/mp4' });

    const uploadForm = new FormData();
    uploadForm.append('file', convertedFile);

    const response = await fetch(`${ATAI_API_ENDPOINT}/files`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${ATAI_API_KEY}` },
      body: uploadForm
    });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      throw error(response.status, `Upload failed: ${JSON.stringify(errorBody)}`);
    }

    return json(await response.json());
  } finally {
    await unlink(inputPath).catch(() => {});
    await unlink(outputPath).catch(() => {});
  }
}
```

### Server Route 2: Activity Monitor (`src/routes/api/activity-monitor/+server.js`)

Handles stale lens cleanup, lens registration, session creation, and session-ready polling — all server-side.

```javascript
import { json, error } from '@sveltejs/kit';
import { ATAI_API_KEY, ATAI_API_ENDPOINT } from '$env/static/private';

async function apiGet(path) {
  const response = await fetch(`${ATAI_API_ENDPOINT}${path}`, {
    headers: { Authorization: `Bearer ${ATAI_API_KEY}` }
  });
  if (!response.ok) throw new Error(`API GET ${path} failed: ${response.status}`);
  return response.json();
}

async function apiPost(path, body, timeoutMs = 10000) {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${ATAI_API_ENDPOINT}${path}`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${ATAI_API_KEY}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(body),
      signal: controller.signal
    });
    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      throw new Error(`API POST ${path} failed: ${response.status} - ${JSON.stringify(errorBody)}`);
    }
    return response.json();
  } finally {
    clearTimeout(timeoutId);
  }
}

async function waitForSessionReady(sessionId, maxWaitMs = 60000) {
  const start = Date.now();
  while (Date.now() - start < maxWaitMs) {
    const status = await apiPost(
      '/lens/sessions/events/process',
      { session_id: sessionId, event: { type: 'session.status' } },
      10000
    );
    if (status.session_status === 'LensSessionStatus.SESSION_STATUS_RUNNING' ||
        status.session_status === '3') return true;
    if (status.session_status === 'LensSessionStatus.SESSION_STATUS_FAILED' ||
        status.session_status === '6') return false;
    await new Promise((r) => setTimeout(r, 500));
  }
  return false;
}

const LENS_NAME = 'activity-monitor-video-lens';

// POST: Create activity monitor session
export async function POST({ request }) {
  const { lensConfig } = await request.json();

  // Clean up ALL existing lenses to avoid stale state blocking new registrations
  try {
    const existing = await apiGet('/lens/metadata');
    if (Array.isArray(existing)) {
      for (const lens of existing) {
        await apiPost('/lens/delete', { lens_id: lens.lens_id }).catch(() => {});
      }
    }
  } catch { /* ignore cleanup errors */ }

  const registered = await apiPost('/lens/register', { lens_config: lensConfig });
  const lensId = registered.lens_id;

  const session = await apiPost('/lens/sessions/create', { lens_id: lensId });
  const sessionId = session.session_id;

  await apiPost('/lens/delete', { lens_id: lensId });

  const isReady = await waitForSessionReady(sessionId);
  if (!isReady) throw error(500, 'Session failed to start');

  return json({ sessionId });
}

// DELETE: Destroy a session
export async function DELETE({ request }) {
  const { sessionId } = await request.json();
  await apiPost('/lens/sessions/destroy', { session_id: sessionId });
  return json({ ok: true });
}
```

### Server Route 3: SSE Stream Proxy (`src/routes/api/activity-monitor/stream/[sessionId]/+server.js`)

```javascript
import { ATAI_API_KEY, ATAI_API_ENDPOINT } from '$env/static/private';

export async function GET({ params }) {
  const { sessionId } = params;

  const upstream = await fetch(
    `${ATAI_API_ENDPOINT}/lens/sessions/consumer/${sessionId}`,
    { headers: { Authorization: `Bearer ${ATAI_API_KEY}` } }
  );

  if (!upstream.ok) {
    return new Response('Failed to connect to SSE stream', { status: upstream.status });
  }

  return new Response(upstream.body, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive'
    }
  });
}
```

### Server Route 4: Direct Query Proxy (`src/routes/api/query/+server.js`)

```javascript
import { json, error } from '@sveltejs/kit';
import { ATAI_API_KEY, ATAI_API_ENDPOINT } from '$env/static/private';

export async function POST({ request }) {
  const { query, systemPrompt = '', maxNewTokens = 1024 } = await request.json();

  const response = await fetch(`${ATAI_API_ENDPOINT}/query`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${ATAI_API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      query,
      system_prompt: systemPrompt,
      instruction_prompt: systemPrompt,
      file_ids: [],
      model: 'Newton::c2_4_7b_251215a172f6d7',
      max_new_tokens: maxNewTokens,
      sanitize: false
    }),
    signal: AbortSignal.timeout(120000)
  });

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}));
    throw error(response.status, `Query failed: ${JSON.stringify(errorBody)}`);
  }

  const data = await response.json();
  let text = '';
  const r = data?.response;
  if (r?.response && Array.isArray(r.response)) text = r.response[0] || '';
  else if (Array.isArray(r)) text = r[0] || '';
  else if (typeof r === 'string') text = r;
  else if (data?.text) text = data.text;
  else text = JSON.stringify(data);

  return json({ text });
}
```

### Client-side usage (Svelte / JS)

The client calls the local server routes — no API key or endpoint needed:

```javascript
// 1. Upload video (server converts to proper MP4 automatically)
async function uploadVideo(blob) {
  const formData = new FormData();
  const ext = blob.type.includes('mp4') ? 'mp4' : 'webm';
  const timestamp = Date.now();
  formData.append('file', new File([blob], `recording_${timestamp}.${ext}`, { type: blob.type }));

  const res = await fetch('/api/upload', { method: 'POST', body: formData });
  if (!res.ok) throw new Error(`Upload failed: ${res.status}`);
  const result = await res.json();
  return result.file_id;
}

// 2. Create activity monitor session (server handles lens cleanup, registration, session polling)
async function createSession(lensConfig) {
  const res = await fetch('/api/activity-monitor', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ lensConfig })
  });
  if (!res.ok) throw new Error(`Session creation failed: ${res.status}`);
  const { sessionId } = await res.json();
  return sessionId;
}

// 3. Consume SSE results (proxied through server)
async function consumeSSE(sessionId, onResult) {
  const res = await fetch(`/api/activity-monitor/stream/${sessionId}`);
  if (!res.ok) throw new Error(`SSE stream failed: ${res.status}`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop();

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      try {
        const parsed = JSON.parse(line.slice(6));
        if (parsed.type === 'inference.result') {
          const text = parsed.event_data.response[0];
          const ts = parsed.event_data.query_metadata?.sensor_timestamp;
          onResult({ text, timestamp: ts });
        }
        if (parsed.type === 'sse.stream.end') return;
      } catch { /* skip malformed JSON */ }
    }
  }
}

// 4. Destroy session
async function destroySession(sessionId) {
  await fetch('/api/activity-monitor', {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sessionId })
  });
}

// 5. Direct query (for post-processing)
async function directQuery(systemPrompt, query) {
  const res = await fetch('/api/query', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, systemPrompt })
  });
  if (!res.ok) throw new Error(`Query failed: ${res.status}`);
  return res.json(); // { text: "..." }
}
```

### Server Proxy Lifecycle Summary

```
Client                          SvelteKit Server                  Archetype AI API
──────                          ───────────────                   ─────────────────
POST /api/upload          →     ffmpeg convert → POST /files  →   returns file_id
POST /api/activity-monitor →    GET /lens/metadata (cleanup)  →
                                POST /lens/register           →   returns lens_id
                                POST /lens/sessions/create    →   returns session_id
                                POST /lens/delete             →
                                poll session.status           →   SESSION_STATUS_RUNNING
                           ←    { sessionId }
GET /api/.../stream/:id    →    GET /lens/sessions/consumer/  →   SSE events proxied
                           ←    inference.result events
DELETE /api/activity-monitor →  POST /lens/sessions/destroy   →
```

---

## Approach B: Plain JS (client-side)

Direct `fetch` calls from the browser or Node.js. **Only works with pre-recorded MP4 files** (not MediaRecorder blobs). API key is exposed to the client. May hit CORS issues in the browser.

### Helpers: API wrappers

```typescript
const API_ENDPOINT = 'https://api.u1.archetypeai.app/v0.5'

async function apiGet<T>(path: string, apiKey: string): Promise<T> {
  const response = await fetch(`${API_ENDPOINT}${path}`, {
    method: 'GET',
    headers: { Authorization: `Bearer ${apiKey}` },
  })
  if (!response.ok) throw new Error(`API GET ${path} failed: ${response.status}`)
  return response.json()
}

async function apiPost<T>(path: string, apiKey: string, body: unknown, timeoutMs = 5000): Promise<T> {
  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs)

  try {
    const response = await fetch(`${API_ENDPOINT}${path}`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    })

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}))
      throw new Error(`API POST ${path} failed: ${response.status} - ${JSON.stringify(errorBody)}`)
    }

    return response.json()
  } finally {
    clearTimeout(timeoutId)
  }
}
```

### Step 1: Upload the video file

```typescript
const formData = new FormData()
formData.append('file', videoFile) // File object from <input type="file">

const uploadResponse = await fetch(`${API_ENDPOINT}/files`, {
  method: 'POST',
  headers: { Authorization: `Bearer ${apiKey}` },
  body: formData,
})
const uploadResult = await uploadResponse.json()
const fileId = uploadResult.file_id
```

### Step 2: Find or create the lens (clean up stale lenses)

```typescript
const LENS_NAME = 'activity-monitor-video-lens'

const lensConfig = {
  lens_name: LENS_NAME,
  lens_config: {
    model_pipeline: [
      { processor_name: 'lens_camera_processor', processor_config: {} },
    ],
    model_parameters: {
      model_version: 'Newton::c2_4_7b_251215a172f6d7',
      instruction: 'Describe the activity currently being performed in one concise sentence.',
      focus: 'Focus on the main person and their current action.',
      temporal_focus: 5,
      max_new_tokens: 512,
      camera_buffer_size: 5,
      camera_buffer_step_size: 5,
      memory_prompt_buffer_size: 0,
    },
    input_streams: [
      {
        stream_type: 'video_file_reader',
        stream_config: { file_id: fileId },
      },
    ],
    output_streams: [
      { stream_type: 'server_sent_events_writer' },
    ],
  },
}

// Delete ALL existing lenses to avoid stale state blocking new registrations
const existingLenses = await apiGet<Array<{ lens_id: string; lens_name: string }>>(
  '/lens/metadata', apiKey
)
if (Array.isArray(existingLenses)) {
  for (const lens of existingLenses) {
    await apiPost('/lens/delete', apiKey, { lens_id: lens.lens_id }).catch(() => {})
  }
}

// Register fresh lens
const registeredLens = await apiPost<{ lens_id: string }>(
  '/lens/register', apiKey, { lens_config: lensConfig }
)
const lensId = registeredLens.lens_id
```

### Step 3: Create session and wait for ready

```typescript
const session = await apiPost<{ session_id: string }>(
  '/lens/sessions/create', apiKey, { lens_id: lensId }
)
const sessionId = session.session_id

// Optionally delete the lens definition (the session keeps running independently)
await apiPost('/lens/delete', apiKey, { lens_id: lensId })

// Wait for session to be ready
async function waitForSessionReady(sessionId: string, maxWaitMs = 60000): Promise<boolean> {
  const start = Date.now()
  while (Date.now() - start < maxWaitMs) {
    const status = await apiPost<{ session_status: string }>(
      '/lens/sessions/events/process', apiKey,
      { session_id: sessionId, event: { type: 'session.status' } },
      10000
    )
    if (status.session_status === 'LensSessionStatus.SESSION_STATUS_RUNNING' ||
        status.session_status === '3') return true
    if (status.session_status === 'LensSessionStatus.SESSION_STATUS_FAILED' ||
        status.session_status === '6') return false
    await new Promise(r => setTimeout(r, 500))
  }
  return false
}

const isReady = await waitForSessionReady(sessionId)
if (!isReady) throw new Error('Session failed to initialize')
```

### Step 4: Consume SSE results

```typescript
import { fetchEventSource } from '@microsoft/fetch-event-source'

const results = []
const abortController = new AbortController()

fetchEventSource(`${API_ENDPOINT}/lens/sessions/consumer/${sessionId}`, {
  headers: { Authorization: `Bearer ${apiKey}` },
  signal: abortController.signal,
  onmessage(event) {
    const parsed = JSON.parse(event.data)

    if (parsed.type === 'inference.result') {
      const response = parsed.event_data.response
      const metadata = parsed.event_data.query_metadata
      const text = Array.isArray(response) ? response[0] : response
      const timestamp = metadata?.sensor_timestamp ?? 'N/A'

      results.push({ timestamp, frameIds: metadata?.frame_ids ?? [], response: text })
      console.log(`[${timestamp}] ${text}`)
    }

    if (parsed.type === 'sse.stream.end') {
      console.log(`Complete. ${results.length} results collected.`)
      abortController.abort()
    }
  },
})
```

### Step 5: Cleanup

```typescript
abortController.abort()
await apiPost('/lens/sessions/destroy', apiKey, { session_id: sessionId })
```

### Plain JS Lifecycle Summary

```
1. Upload video           ->  POST /files  (FormData)
2. List existing lenses   ->  GET  /lens/metadata
3. Delete stale lens      ->  POST /lens/delete  { lens_id }  (if same name exists)
4. Register lens          ->  POST /lens/register  { lens_config with video_file_reader }
5. Create session         ->  POST /lens/sessions/create  { lens_id }
6. Wait for ready         ->  POST /lens/sessions/events/process  (poll session.status)
7. Consume SSE results    ->  GET  /lens/sessions/consumer/{sessionId}
8. Destroy session        ->  POST /lens/sessions/destroy  { session_id }
```

---

## Approach C: Python

### Requirements

- `archetypeai` Python package
- Environment variables: `ATAI_API_KEY`, optionally `ATAI_API_ENDPOINT`

### Full Python Example

```python
import os
import time
from archetypeai.api_client import ArchetypeAI

api_key = os.getenv("ATAI_API_KEY")
api_endpoint = os.getenv("ATAI_API_ENDPOINT", ArchetypeAI.get_default_endpoint())
client = ArchetypeAI(api_key, api_endpoint=api_endpoint)

# 1. Upload the video file
upload_resp = client.files.local.upload("my_video.mp4")
file_id = upload_resp["file_id"]
print(f"Uploaded: {file_id}")

# 2. Lens config with video_file_reader input stream
lens_config = {
    "lens_name": "activity-monitor-video-lens",
    "lens_config": {
        "model_pipeline": [
            {"processor_name": "lens_camera_processor", "processor_config": {}}
        ],
        "model_parameters": {
            "model_version": "Newton::c2_4_7b_251215a172f6d7",
            "instruction": "Describe the activity currently being performed in one concise sentence.",
            "focus": "Focus on the main person and their current action.",
            "temporal_focus": 5,
            "max_new_tokens": 512,
            "camera_buffer_size": 5,
            "camera_buffer_step_size": 5,
            "memory_prompt_buffer_size": 0,
        },
        "input_streams": [
            {
                "stream_type": "video_file_reader",
                "stream_config": {"file_id": file_id},
            }
        ],
        "output_streams": [
            {"stream_type": "server_sent_events_writer"}
        ],
    },
}

# 3. Register lens
lens = client.lens.register(lens_config)
lens_id = lens["lens_id"]

# 4. Create session
session = client.lens.sessions.create(lens_id)
session_id = session["session_id"]

# Optionally delete the lens (session runs independently)
client.lens.delete(lens_id)

# 5. Wait for session ready
for _ in range(60):
    try:
        status = client.lens.sessions.process_event(
            session_id, {"type": "session.status"}
        )
        if status.get("session_status") in ["3", "LensSessionStatus.SESSION_STATUS_RUNNING"]:
            break
    except Exception:
        pass
    time.sleep(0.5)

# 6. Consume SSE results (server drives video processing)
sse_reader = client.lens.sessions.create_sse_consumer(
    session_id, max_read_time_sec=600
)

results = []
for event in sse_reader.read(block=True):
    if isinstance(event, dict) and event.get("type") == "inference.result":
        ed = event.get("event_data", {})
        response = ed.get("response", "")
        meta = ed.get("query_metadata", {})

        text = response[0] if isinstance(response, list) else response

        results.append({
            "timestamp": meta.get("sensor_timestamp", "N/A"),
            "frame_ids": meta.get("frame_ids", []),
            "response": text,
        })
        print(f"[{meta.get('sensor_timestamp', '?')}] {text}")

sse_reader.close()
print(f"Done. {len(results)} results collected.")

# 7. Cleanup
client.lens.sessions.destroy(session_id)
```

---

## SSE Event Types

| Event type | Description |
|---|---|
| `inference.result` | A model response with `response[]` text and `query_metadata` |
| `sse.stream.end` | The session has finished processing the entire video |

### `inference.result` payload

```json
{
  "type": "inference.result",
  "event_data": {
    "response": ["Person is stirring a pot on the stove."],
    "query_id": "qry-abc123",
    "query_metadata": {
      "sensor_timestamp": "00:02:15",
      "frame_ids": [270, 275, 280, 285, 290, 295, 300, 305]
    }
  }
}
```

- `sensor_timestamp`: position in the video (HH:MM:SS)
- `frame_ids`: the specific video frames the model analyzed
- `response`: array of model output strings (typically one element)

---

## Lens Configuration Reference

### Model Parameters

| Parameter | Description | Default |
|---|---|---|
| `model_version` | Newton model ID | `Newton::c2_4_7b_251215a172f6d7` |
| `instruction` | Main prompt guiding output format | *(user-defined)* |
| `focus` | What to look for in the video | *(user-defined)* |
| `temporal_focus` | Temporal window in seconds. Small (<5s) = fine-grained, large (>5s) = macro | `5` |
| `camera_buffer_size` | Number of frames to buffer before processing | `5` |
| `camera_buffer_step_size` | Step size for frame sampling from the buffer | `5` |
| `memory_prompt_buffer_size` | How many prior prompts to retain for context (0 = stateless) | `0` |
| `max_new_tokens` | Max tokens for model inference output | `512` |

### Input Stream Types

**Pre-recorded video file (this skill):**
```json
{ "stream_type": "video_file_reader", "stream_config": { "file_id": "<uploaded_file_id>" } }
```

**Live RTSP camera stream:**
```json
{ "stream_type": "rtsp_video_reader", "stream_config": { "rtsp_url": "rtsp://example.com:554/stream", "target_image_size": [360, 640], "target_frame_rate_hz": 1.0 } }
```

## Troubleshooting

- **"Input stream is unhealthy!" / "Failed to load video"**: The uploaded video is likely fragmented MP4 (from MediaRecorder) or WebM. The `video_file_reader` requires standard MP4 with moov atom. Use the Server Proxy approach which converts automatically via ffmpeg, or convert manually before uploading.
- **"Input stream is unhealthy!" (stale lens)**: Delete **ALL** existing lenses before registering a new one (not just name-matched). Stale lenses from previous sessions can block new registrations even with different names. All approaches above include aggressive lens cleanup via `GET /lens/metadata` → delete every lens.
- **CORS errors in browser**: The Archetype AI API does not support direct browser CORS. Use the Server Proxy approach or run from Node.js/Python server-side.
- **No SSE events**: Ensure the session reached `SESSION_STATUS_RUNNING` before connecting the SSE consumer. All approaches above include session-ready polling.
- **Session fails**: Check that `file_id` in `video_file_reader` config matches the uploaded file.
- **Video too long**: Use `max_run_time_sec` or adjust `temporal_focus` for faster processing.
