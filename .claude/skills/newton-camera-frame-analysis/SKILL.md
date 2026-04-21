---
name: newton-camera-frame-analysis
description: Live webcam frame analysis using Newton's vision model via model.query (request/response). Captures frames from a webcam as base64 JPEG and sends them to Newton. Use for live camera analysis, scene description, presence detection, or visual Q&A. NOT for video file uploads — use /activity-monitor-lens-on-video for that.
argument-hint: [question] [camera_index]
allowed-tools: Bash(python *), Read
---

# Newton Camera Frame Analysis (Live Webcam → base64 → model.query)

Capture live webcam frames, encode as base64 JPEG, and send to Newton's vision model via `model.query` (synchronous request/response). Supports Python (OpenCV) and JavaScript (getUserMedia + canvas).

## Frontend Architecture

Decompose the UI into components. See `@rules/frontend-architecture` for conventions.

### Recommended decomposition

| UI Area | Component | Pattern/Primitives | Key Props |
|---------|-----------|-------------------|-----------|
| Camera feed | `WebcamView.svelte` | Card, AspectRatio | `stream`, `status` |
| Status | `ConnectionStatus.svelte` | StatusBadge pattern | `status`, `label` |
| Results | Use FlatLogItem pattern in ScrollArea | FlatLogItem, ScrollArea | `status`, `message`, `detail` |

- Use `@skills/create-dashboard` for the page layout
- Extract webcam capture and API logic into `$lib/api/camera-analysis.js`

**This skill is for LIVE WEBCAM input only.** For analyzing uploaded video files, use `/activity-monitor-lens-on-video` instead.

| | This skill (camera-frame-analysis) | activity-monitor-lens-on-video |
|---|---|---|
| **Input** | Live webcam (base64 JPEG frames) | Uploaded video file |
| **Who captures frames** | Client (Python cv2 / JS canvas) | Server (`video_file_reader`) |
| **Event type** | `model.query` (request/response) | Server-driven, results via SSE |
| **Response** | Direct in POST response | Async via SSE stream |
| **Use case** | Real-time webcam Q&A | Batch video analysis |

---

## Model Parameters

| Parameter | Default | Notes |
|---|---|---|
| `model_version` | `Newton::c2_4_7b_251215a172f6d7` | Newton model ID |
| `template_name` | `image_qa_template_task` | Prompt template |
| `instruction` | *(user-provided)* | System prompt guiding output format |
| `focus` | *(user-provided)* | The question or what to look for |
| `max_new_tokens` | `512` | Max response length |
| `camera_buffer_size` | `1` | Single-frame buffer for webcam |
| `min_replicas` / `max_replicas` | `1` / `1` | Scaling config |

**IMPORTANT:** `instruction` and `focus` must be passed as parameters — not hardcoded. The values in the lens config (registration) and in each `model.query` event must be consistent. Pass the user's values into both.

---

## Python Implementation

### Requirements

- `archetypeai` Python package
- `opencv-python` (`cv2`), `Pillow`
- Environment variables: `ATAI_API_KEY` or `ARCHETYPE_API_KEY`

### Quick Start

```bash
export ATAI_API_KEY=your_key_here
python camera_frame_analysis.py "Describe what you see"

# Custom question
python camera_frame_analysis.py "Is anyone present?"

# Different camera
python camera_frame_analysis.py "Describe the scene" 1
```

### Parameters

- **question** (positional, optional): What to analyze (default: "Describe what you see")
- **camera_index** (positional, optional): Camera index (default: 0)

### How It Works

1. **Capture**: Opens webcam with OpenCV, reads a frame
2. **Encode**: Converts frame to base64 JPEG (BGR → RGB → PIL → JPEG → base64)
3. **Setup**: Registers Newton lens, creates session, waits for ready
4. **Initialize**: Sends `session.modify` to initialize the processor
5. **Query**: Sends base64 image as `model.query` event, gets response directly
6. **Cleanup**: Destroys session

### Webcam Capture → base64

```python
import cv2
import base64
import io
from PIL import Image

def capture_frame_base64(camera_index=0, jpeg_quality=80, resize=(640, 480)):
    """Capture a webcam frame and return as raw base64 JPEG string."""
    cap = cv2.VideoCapture(camera_index)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        raise RuntimeError(f"Failed to capture from camera {camera_index}")

    # Resize if needed
    h, w = frame.shape[:2]
    if (w, h) != resize:
        frame = cv2.resize(frame, resize)

    # BGR (OpenCV) → RGB → PIL → JPEG → base64
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_frame)

    buffer = io.BytesIO()
    pil_image.save(buffer, format="JPEG", quality=jpeg_quality)
    raw_base64 = base64.b64encode(buffer.getvalue()).decode()

    return raw_base64  # No "data:image/jpeg;base64," prefix
```

### Full Python Example

```python
import os
import time
from archetypeai.api_client import ArchetypeAI

api_key = os.getenv("ATAI_API_KEY")
client = ArchetypeAI(api_key)

# --- User-provided values (NOT hardcoded) ---
instruction = "Answer the following question about the image:"
focus = "Describe what you see in this image."

def build_lens_config(instruction: str, focus: str) -> dict:
    """Build lens config with user-provided instruction and focus."""
    return {
        "lens_name": "camera-frame-capture-lens",
        "lens_config": {
            "model_pipeline": [
                {"processor_name": "lens_camera_processor", "processor_config": {}}
            ],
            "model_parameters": {
                "model_version": "Newton::c2_4_7b_251215a172f6d7",
                "template_name": "image_qa_template_task",
                "instruction": instruction,
                "focus": focus,
                "max_new_tokens": 512,
                "camera_buffer_size": 1,
                "min_replicas": 1,
                "max_replicas": 1,
            },
        },
    }

def build_query_event(raw_base64: str, instruction: str, focus: str) -> dict:
    """Build model.query event with the SAME instruction and focus as the lens config."""
    return {
        "type": "model.query",
        "event_data": {
            "model_version": "Newton::c2_4_7b_251215a172f6d7",
            "template_name": "image_qa_template_task",
            "instruction": instruction,
            "focus": focus,
            "max_new_tokens": 512,
            "data": [{"type": "base64_img", "base64_img": raw_base64}],
        },
    }

# 1. Register lens (pass user's instruction + focus)
lens_config = build_lens_config(instruction, focus)
lens = client.lens.register(lens_config)
lens_id = lens["lens_id"]

# 2. Create session
session = client.lens.sessions.create(lens_id)
session_id = session["session_id"]

# 3. Wait for session ready
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

# 4. Initialize processor (REQUIRED)
client.lens.sessions.process_event(session_id, {
    "type": "session.modify",
    "event_data": {"camera_buffer_size": 1}
})

# 5. Capture frame and send as model.query (same instruction + focus)
raw_base64 = capture_frame_base64(camera_index=0)
event = build_query_event(raw_base64, instruction, focus)

response = client.lens.sessions.process_event(session_id, event)

if response.get("type") == "model.query.response":
    result = response["event_data"]["response"]
    if isinstance(result, list):
        result = result[0]
    print(f"Answer: {result}")

# 6. Cleanup
client.lens.sessions.destroy(session_id)
```

---

## Web / JavaScript Implementation

Uses direct `fetch` calls to the Archetype AI REST API.

### Requirements

- Browser with `getUserMedia` support (webcam access)
- HTTPS (required for camera access, except `localhost`)

### API Reference

| Operation | Method | Endpoint | Body |
|-----------|--------|----------|------|
| List lenses | GET | `/lens/metadata` | — |
| Register lens | POST | `/lens/register` | `{ lens_config: config }` |
| Delete lens | POST | `/lens/delete` | `{ lens_id }` |
| Create session | POST | `/lens/sessions/create` | `{ lens_id }` |
| Process event | POST | `/lens/sessions/events/process` | `{ session_id, event }` |
| Destroy session | POST | `/lens/sessions/destroy` | `{ session_id }` |

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

### Step 1: Find or create the lens (clean up stale lenses)

A stale lens from a previous run causes `"Input stream is unhealthy!"` errors. Always check for an existing lens with the same name and delete it before registering a fresh one.

**Pass the user's `instruction` and `focus` into the lens config** — do not hardcode them.

```typescript
const LENS_NAME = 'camera-frame-capture-lens'

// --- User-provided values (NOT hardcoded) ---
const instruction = 'Answer the following question about the image:'
const focus = 'Describe what you see in this image.'

function buildLensConfig(instruction: string, focus: string) {
  return {
    lens_name: LENS_NAME,
    lens_config: {
      model_pipeline: [
        { processor_name: 'lens_camera_processor', processor_config: {} },
      ],
      model_parameters: {
        model_version: 'Newton::c2_4_7b_251215a172f6d7',
        template_name: 'image_qa_template_task',
        instruction,
        focus,
        max_new_tokens: 512,
        camera_buffer_size: 1,
        min_replicas: 1,
        max_replicas: 1,
      },
    },
  }
}

// Delete any existing lens with the same name to avoid stale state
const existingLenses = await apiGet<Array<{ lens_id: string; lens_name: string }>>(
  '/lens/metadata', apiKey
)
const staleLens = existingLenses.find(l => l.lens_name === LENS_NAME)
if (staleLens) {
  console.log('Deleting stale lens:', staleLens.lens_id)
  await apiPost('/lens/delete', apiKey, { lens_id: staleLens.lens_id })
}

// Register fresh lens with user's instruction + focus
const lensConfig = buildLensConfig(instruction, focus)
const registeredLens = await apiPost<{ lens_id: string }>(
  '/lens/register', apiKey, { lens_config: lensConfig }
)
const lensId = registeredLens.lens_id
```

### Step 2: Create session and wait for ready

```typescript
const session = await apiPost<{ session_id: string; session_endpoint: string }>(
  '/lens/sessions/create', apiKey, { lens_id: lensId }
)
const sessionId = session.session_id

// Wait for session to be ready (poll until status = running)
async function waitForSessionReady(sessionId: string, maxWaitMs = 30000): Promise<boolean> {
  const start = Date.now()
  while (Date.now() - start < maxWaitMs) {
    const status = await apiPost<{ session_status: string }>(
      '/lens/sessions/events/process', apiKey,
      { session_id: sessionId, event: { type: 'session.status' } },
      10000
    )
    if (status.session_status === 'LensSessionStatus.SESSION_STATUS_RUNNING' ||
        status.session_status === '3') {
      return true
    }
    if (status.session_status === 'LensSessionStatus.SESSION_STATUS_FAILED' ||
        status.session_status === '6') {
      return false
    }
    await new Promise(r => setTimeout(r, 500))
  }
  return false
}

const isReady = await waitForSessionReady(sessionId)
if (!isReady) throw new Error('Session failed to initialize')
```

### Step 3: Initialize the processor (REQUIRED for lens_camera_processor)

This sends a `session.modify` event that triggers `update_lens_params()` which initializes `video_narrator_memory`. **Without this step, inference will fail.**

```typescript
await apiPost('/lens/sessions/events/process', apiKey, {
  session_id: sessionId,
  event: {
    type: 'session.modify',
    event_data: {
      camera_buffer_size: 1,
    },
  },
}, 30000) // 30s timeout for initialization
```

### Step 4: Start webcam and capture frames as base64

#### 4a. Create a video element

```html
<!-- Visible preview (optional) -->
<video id="webcam" autoplay playsinline muted></video>

<!-- Or create it in JS (no visible preview) -->
```

```typescript
// Option A: Reference an existing <video> element
const video = document.getElementById('webcam') as HTMLVideoElement

// Option B: Create a hidden video element in JS
const video = document.createElement('video')
video.autoplay = true
video.playsInline = true  // Required for iOS
video.muted = true
```

#### 4b. Request camera access and start the stream

```typescript
async function startCamera(
  preferredWidth = 640,
  preferredHeight = 480,
  facingMode: 'user' | 'environment' = 'user',  // 'user' = front, 'environment' = back
): Promise<MediaStream> {
  const stream = await navigator.mediaDevices.getUserMedia({
    video: {
      width: { ideal: preferredWidth },
      height: { ideal: preferredHeight },
      facingMode,
    },
    audio: false,
  })

  video.srcObject = stream

  // Wait until video is actually playing and has dimensions
  await new Promise<void>((resolve) => {
    video.onloadedmetadata = () => {
      video.play()
      resolve()
    }
  })

  console.log(`Camera started: ${video.videoWidth}x${video.videoHeight}`)
  return stream
}

const stream = await startCamera()
```

**Permission notes:**
- Browser will show a permission prompt on first call
- HTTPS is **required** (except `localhost`)
- On mobile, `facingMode: 'environment'` selects the rear camera

#### 4c. Capture a frame as base64 JPEG

The flow is: **video element → canvas → toDataURL → base64 string**.

```typescript
function captureFrame(quality = 0.8): string | null {
  if (!video.videoWidth || !video.videoHeight) return null

  const canvas = document.createElement('canvas')
  canvas.width = video.videoWidth
  canvas.height = video.videoHeight

  const ctx = canvas.getContext('2d')
  if (!ctx) return null

  // Draw current video frame onto canvas
  ctx.drawImage(video, 0, 0)

  // Convert to base64 JPEG — returns "data:image/jpeg;base64,/9j/4AAQ..."
  return canvas.toDataURL('image/jpeg', quality)
}
```

**Quality vs size tradeoffs:**
| Quality | ~Size (640x480) | Use case |
|---------|-----------------|----------|
| `0.5` | ~20-30 KB | Fast continuous streaming |
| `0.8` | ~40-60 KB | Good balance (recommended) |
| `1.0` | ~80-120 KB | Maximum detail |

#### 4d. Strip the data URI prefix before sending to the API

The API expects **raw base64**, not the `data:image/jpeg;base64,` prefix that `toDataURL` produces.

```typescript
function captureFrameRaw(quality = 0.8): string | null {
  const dataUri = captureFrame(quality)
  if (!dataUri) return null

  // Strip "data:image/jpeg;base64," prefix → raw base64
  return dataUri.replace(/^data:image\/\w+;base64,/, '')
}
```

This raw base64 string is what goes into the `model.query` event's `base64_img` field.

### Step 5: Send frames for analysis (model.query)

This uses **request/response — NOT SSE**. Each frame is sent as a `model.query` event and the response comes back directly in the POST response.

The `instruction` and `focus` in the `model.query` event **must match** the values used at lens registration. Pass them through — do not hardcode different values.

```typescript
function createModelQueryEvent(
  rawBase64Images: string[],  // Already stripped of data URI prefix
  instruction: string,         // Same as lens config
  focus: string,               // Same as lens config
  modelVersion = 'Newton::c2_4_7b_251215a172f6d7',
  templateName = 'image_qa_template_task',
  maxNewTokens = 512,
) {
  return {
    type: 'model.query' as const,
    event_data: {
      model_version: modelVersion,
      template_name: templateName,
      instruction,
      focus,
      max_new_tokens: maxNewTokens,
      data: rawBase64Images.map(img => ({
        type: 'base64_img',
        base64_img: img,
      })),
    },
  }
}

// Send a frame and get the response (uses the same instruction + focus from Step 1)
async function analyzeFrame(instruction: string, focus: string): Promise<string> {
  const frame = captureFrameRaw()  // Raw base64 (no data URI prefix)
  if (!frame) throw new Error('Failed to capture frame')

  const event = createModelQueryEvent([frame], instruction, focus)

  const response = await apiPost<{
    type: string
    event_data?: { response?: string | string[]; message?: string }
  }>(
    '/lens/sessions/events/process', apiKey,
    { session_id: sessionId, event },
    60000  // 60s timeout for model inference
  )

  // Extract text from response
  if (response.type === 'model.query.response' && response.event_data) {
    const text = response.event_data.response
    if (typeof text === 'string') return text
    if (Array.isArray(text)) return text.join('\n')
    return JSON.stringify(response.event_data)
  }

  return JSON.stringify(response)
}
```

### Step 6: Continuous capture loop

Send the first frame **immediately** after initialization — do not wait for the interval. The processor expects data promptly after `session.modify`.

```typescript
let isSending = false

async function captureAndSend() {
  if (isSending) {
    console.log('Previous request still in progress, skipping frame')
    return
  }

  isSending = true
  try {
    const result = await analyzeFrame(instruction, focus)
    console.log('Result:', result)
  } catch (error) {
    console.error('Frame analysis failed:', error)
  } finally {
    isSending = false
  }
}

// Send first frame immediately
captureAndSend()

// Then continue at 1 frame per second
const intervalId = setInterval(captureAndSend, 1000)
```

### Step 7: Cleanup

```typescript
// Stop capture loop
clearInterval(intervalId)

// Stop camera
stream.getTracks().forEach(track => track.stop())

// Destroy session
await apiPost('/lens/sessions/destroy', apiKey, { session_id: sessionId })
```

### Web Lifecycle Summary

```
1. List existing lenses  ->  GET  /lens/metadata
2. Delete stale lens     ->  POST /lens/delete  { lens_id }  (if same name exists)
3. Register fresh lens   ->  POST /lens/register  { lens_config: config }
4. Create session        ->  POST /lens/sessions/create  { lens_id }
5. Wait for ready        ->  POST /lens/sessions/events/process  (poll session.status)
6. Initialize processor  ->  POST /lens/sessions/events/process  { session_id, event: session.modify }
7. Start webcam          ->  navigator.mediaDevices.getUserMedia()
8. Send first frame NOW  ->  POST /lens/sessions/events/process  { session_id, event: model.query }
9. Capture loop (1fps)   ->  POST /lens/sessions/events/process  { session_id, event: model.query }
10. Stop camera          ->  stream.getTracks().forEach(t => t.stop())
11. Destroy session      ->  POST /lens/sessions/destroy  { session_id }
```

---

## Use Cases

- **Quick scene analysis**: Single frame description
- **Presence detection**: Check if someone is at their desk
- **Safety monitoring**: Verify safety equipment usage
- **Object identification**: Identify specific items in view
- **Continuous monitoring**: Stream frames with periodic analysis

## Troubleshooting

- **"Input stream is unhealthy!"**: Stale lens from previous run. Always delete existing lens before registering a new one (see Step 1).
- **Camera not found**: Try different camera indices (Python) or check browser permissions (Web)
- **API errors**: Verify API key is set correctly
- **Session fails**: Ensure `session.modify` (Step 3) is called before sending queries
- **Timeout on inference**: Model queries can take 10-30s; use 60s timeout
- **Frame too large**: Use JPEG encoding with quality 0.8 to reduce payload size
- **Requests overlap**: Gate with `isSending` flag to skip frames while previous request is in-flight
