---
name: embedding-upload
description: Run an Embedding Lens by uploading a CSV file for server-side processing. Use when you want to upload a file and get embeddings without local streaming.
argument-hint: [csv-file-path]
---

# Embedding Lens — Upload File (Server-Side Processing)

Generate a script that uploads a CSV file to the Archetype AI platform and extracts embeddings server-side. The server reads the file directly — no local streaming loop required. Supports both Python and JavaScript/Web.

## Frontend Architecture

Decompose the UI into components. See `@rules/frontend-architecture` for conventions.

### Recommended decomposition

| UI Area | Component | Pattern/Primitives | Key Props |
|---------|-----------|-------------------|-----------|
| File upload | `DataInput.svelte` | BackgroundCard, Button, Input | `onselect`, `status` |
| Scatter plot | Reuse ScatterChart pattern | BackgroundCard, Chart | `data[]`, `categories` |
| Progress | `StreamProgress.svelte` | BackgroundCard, Progress | `current`, `total` |

- Use `@skills/create-dashboard` for the page layout
- Extract upload and session logic into `$lib/api/embeddings.js`

---

## Python Implementation

### Requirements

- `archetypeai` Python package
- Environment variables: `ATAI_API_KEY`, optionally `ATAI_API_ENDPOINT`

### Architecture

Uses `create_and_run_lens` with YAML config. After the session is created, upload the data CSV and configure a `csv_file_reader` input stream for server-side reading.

#### 1. API Client Setup

```python
from archetypeai.api_client import ArchetypeAI
import os

api_key = os.getenv("ATAI_API_KEY")
api_endpoint = os.getenv("ATAI_API_ENDPOINT", ArchetypeAI.get_default_endpoint())
client = ArchetypeAI(api_key, api_endpoint=api_endpoint)
```

#### 2. Lens YAML Configuration

```yaml
lens_name: Embedding Lens
lens_config:
  model_pipeline:
    - processor_name: lens_timeseries_embedding_processor
      processor_config: {}
  model_parameters:
    model_name: OmegaEncoder
    model_version: OmegaEncoder::omega_embeddings_01
    normalize_input: true
    buffer_size: {window_size}
    csv_configs:
      timestamp_column: timestamp
      data_columns: ['a1', 'a2', 'a3', 'a4']
      window_size: {window_size}
      step_size: {step_size}
  output_streams:
    - stream_type: server_sent_events_writer
```

#### 3. Event Builders

```python
def build_input_event(file_id, window_size, step_size):
    return {
        "type": "input_stream.set",
        "event_data": {
            "stream_type": "csv_file_reader",
            "stream_config": {
                "file_id": file_id,
                "window_size": window_size,
                "step_size": step_size,
                "loop_recording": False,
                "output_format": ""
            }
        }
    }

def build_output_event():
    return {
        "type": "output_stream.set",
        "event_data": {
            "stream_type": "server_side_events_writer",
            "stream_config": {}
        }
    }
```

#### 4. Session Callback

```python
def session_callback(session_id, session_endpoint, client, args):
    print(f"Session created: {session_id}")

    # Upload the data CSV
    data_resp = client.files.local.upload(args["data_file_path"])
    data_file_id = data_resp["file_id"]

    # Tell server to read the uploaded CSV
    client.lens.sessions.process_event(
        session_id,
        build_input_event(data_file_id, args["window_size"], args["step_size"])
    )
    client.lens.sessions.process_event(
        session_id,
        build_output_event()
    )

    # Collect embeddings via SSE
    sse_reader = client.lens.sessions.create_sse_consumer(
        session_id, max_read_time_sec=args["max_run_time_sec"]
    )

    embeddings = []
    try:
        for event in sse_reader.read(block=True):
            if stop_flag:
                break
            if isinstance(event, dict) and event.get("type") == "inference.result":
                ed = event.get("event_data", {})
                embedding = ed.get("response")
                meta = ed.get("query_metadata", {})

                # Flatten 4×768 → 3072D
                if isinstance(embedding, list) and len(embedding) > 0:
                    if isinstance(embedding[0], list):
                        flat = [val for row in embedding for val in row]
                    else:
                        flat = embedding

                embeddings.append({
                    "window_index": len(embeddings),
                    "query_timestamp": meta.get("query_timestamp", "N/A"),
                    "read_index": meta.get("query_metadata", {}).get("read_index", "N/A"),
                    "embedding": flat,
                })
                print(f"[{len(embeddings)}] Embedding: {len(flat)}D")
    finally:
        sse_reader.close()
        print(f"Collected {len(embeddings)} embeddings. Stopped.")
```

#### 5. Create and Run Lens

```python
client.lens.create_and_run_lens(
    yaml_config, session_callback,
    client=client, args=args
)
```

### CLI Arguments

```
--api-key              API key (fallback to ATAI_API_KEY env var)
--api-endpoint         API endpoint (default from SDK)
--data-file            Path to CSV file to analyze (required)
--window-size          Window size in samples (default: 100)
--step-size            Step size in samples (default: 100)
--max-run-time-sec     Max runtime (default: 600)
--output-file          Path to save embeddings CSV (optional)
```

---

## Web / JavaScript Implementation

Uses direct `fetch` calls to the Archetype AI REST API. The simplest embedding approach on web — just upload and collect results.

### API Reference

| Operation | Method | Endpoint | Body |
|-----------|--------|----------|------|
| Upload file | POST | `/files` | `FormData` |
| Register lens | POST | `/lens/register` | `{ lens_config: config }` |
| Create session | POST | `/lens/sessions/create` | `{ lens_id }` |
| Process event | POST | `/lens/sessions/events/process` | `{ session_id, event }` |
| Delete lens | POST | `/lens/delete` | `{ lens_id }` |
| Destroy session | POST | `/lens/sessions/destroy` | `{ session_id }` |
| SSE consumer | GET | `/lens/sessions/consumer/{sessionId}` | — |

### Helper: API fetch wrapper

```typescript
const API_ENDPOINT = 'https://api.u1.archetypeai.app/v0.5'

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

### Step 1: Upload the data CSV

```typescript
const dataFormData = new FormData()
dataFormData.append('file', dataFile) // File from <input type="file">

const dataResponse = await fetch(`${API_ENDPOINT}/files`, {
  method: 'POST',
  headers: { Authorization: `Bearer ${apiKey}` },
  body: dataFormData,
})
const dataUpload = await dataResponse.json()
const dataFileId = dataUpload.file_id
```

### Step 2: Register embedding lens and create session

```typescript
const windowSize = 100
const stepSize = 100

const lensConfig = {
  lens_name: 'embedding_lens',
  lens_config: {
    model_pipeline: [
      { processor_name: 'lens_timeseries_embedding_processor', processor_config: {} },
    ],
    model_parameters: {
      model_name: 'OmegaEncoder',
      model_version: 'OmegaEncoder::omega_embeddings_01',
      normalize_input: true,
      buffer_size: windowSize,
      csv_configs: {
        timestamp_column: 'timestamp',
        data_columns: ['a1', 'a2', 'a3', 'a4'],
        window_size: windowSize,
        step_size: stepSize,
      },
    },
    output_streams: [
      { stream_type: 'server_sent_events_writer' },
    ],
  },
}

const registeredLens = await apiPost<{ lens_id: string }>(
  '/lens/register', apiKey, { lens_config: lensConfig }
)
const lensId = registeredLens.lens_id

const session = await apiPost<{ session_id: string }>(
  '/lens/sessions/create', apiKey, { lens_id: lensId }
)
const sessionId = session.session_id

await apiPost('/lens/delete', apiKey, { lens_id: lensId })

// Wait for session ready (same waitForSessionReady pattern)
async function waitForSessionReady(sessionId: string, maxWaitMs = 30000): Promise<boolean> {
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

await waitForSessionReady(sessionId)
```

### Step 3: Tell server to read the uploaded CSV

```typescript
// Set input stream to CSV file reader
await apiPost('/lens/sessions/events/process', apiKey, {
  session_id: sessionId,
  event: {
    type: 'input_stream.set',
    event_data: {
      stream_type: 'csv_file_reader',
      stream_config: {
        file_id: dataFileId,
        window_size: windowSize,
        step_size: stepSize,
        loop_recording: false,
        output_format: '',
      },
    },
  },
}, 10000)

// Enable SSE output
await apiPost('/lens/sessions/events/process', apiKey, {
  session_id: sessionId,
  event: {
    type: 'output_stream.set',
    event_data: {
      stream_type: 'server_side_events_writer',
      stream_config: {},
    },
  },
}, 10000)
```

### Step 4: Consume SSE embedding results

```typescript
import { fetchEventSource } from '@microsoft/fetch-event-source'

interface EmbeddingResult {
  windowIndex: number
  queryTimestamp: string
  readIndex: number | string
  embedding: number[]  // 3072D flattened
}

const embeddings: EmbeddingResult[] = []
const abortController = new AbortController()

fetchEventSource(`${API_ENDPOINT}/lens/sessions/consumer/${sessionId}`, {
  headers: { Authorization: `Bearer ${apiKey}` },
  signal: abortController.signal,
  onmessage(event) {
    const parsed = JSON.parse(event.data)

    if (parsed.type === 'inference.result') {
      const response = parsed.event_data.response
      const meta = parsed.event_data.query_metadata
      const queryMeta = meta?.query_metadata ?? {}

      const flat = Array.isArray(response[0]) ? response.flat() : response

      embeddings.push({
        windowIndex: embeddings.length,
        queryTimestamp: meta?.query_timestamp ?? 'N/A',
        readIndex: queryMeta.read_index ?? 'N/A',
        embedding: flat,
      })
      console.log(`[${embeddings.length}] Embedding: ${flat.length}D`)
    }

    if (parsed.type === 'sse.stream.end') {
      console.log(`Complete. ${embeddings.length} embeddings collected.`)
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

### Web Lifecycle Summary

```
1. Upload data CSV       ->  POST /files  (FormData)
2. Register lens         ->  POST /lens/register  { lens_config: config }
3. Create session        ->  POST /lens/sessions/create  { lens_id }
4. Wait for ready        ->  POST /lens/sessions/events/process  (poll)
5. Set input stream      ->  POST /lens/sessions/events/process  { session_id, event: input_stream.set }
6. Set output stream     ->  POST /lens/sessions/events/process  { session_id, event: output_stream.set }
7. Consume SSE results   ->  GET /lens/sessions/consumer/{sessionId}
8. Destroy session       ->  POST /lens/sessions/destroy  { session_id }
```

---

## Embedding Response Structure

The `inference.result` response contains:
- `response`: nested list `(4, 768)` — one 768D embedding per input channel
- Flatten to `3072D` by concatenating: `[a1_768D, a2_768D, a3_768D, a4_768D]`
- `query_metadata.query_timestamp`: timestamp
- `query_metadata.query_metadata.read_index`: window position in file
- `query_metadata.query_metadata.file_id`: the file being analyzed

## Key Differences from Streaming Approaches

| | Upload (this skill) | Stream from File | Stream from Sensor |
|---|---|---|---|
| Data reading | Server-side `csv_file_reader` | Local pandas/JS + windowed push | Local sensor + buffered push |
| Local processing | None (just upload) | Window slicing | Sensor acquisition + buffering |
| Best for | Batch embedding extraction | Controlled local streaming | Real-time from hardware |

## Key Implementation Notes

- Default `window_size` and `step_size`: **100**
- No n-shot files or KNN config — this is pure embedding extraction
- Embeddings are `(4, 768)` per window — flatten to `3072D` for downstream use
- Use UMAP/t-SNE for 2D/3D visualization
- Combine with machine state lens results for labeled embedding plots
