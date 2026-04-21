---
name: embedding-from-file
description: Run an Embedding Lens by streaming sensor data from a CSV file. Use when extracting embeddings from time-series CSV data for visualization, clustering, dimensionality reduction, or similarity analysis.
argument-hint: [csv-file-path]
---

# Embedding Lens — Stream from CSV File

Generate a script that streams time-series data from a CSV file to the Archetype AI Embedding Lens and collects embedding vectors. Supports both Python and JavaScript/Web.

## Frontend Architecture

Decompose the UI into components. See `@rules/frontend-architecture` for conventions.

### Recommended decomposition

| UI Area | Component | Pattern/Primitives | Key Props |
|---------|-----------|-------------------|-----------|
| File input | `DataInput.svelte` | BackgroundCard, Button, Input | `onselect`, `status` |
| Scatter plot | Reuse ScatterChart pattern | BackgroundCard, Chart | `data[]`, `categories` |
| Progress | `StreamProgress.svelte` | BackgroundCard, Progress | `current`, `total` |

- Use `@skills/create-dashboard` for the page layout
- Extract streaming and session logic into `$lib/api/embeddings.js`

---

## Python Implementation

### Requirements

- `archetypeai` Python package
- `pandas`, `numpy`
- Environment variables: `ATAI_API_KEY`, optionally `ATAI_API_ENDPOINT`

### Architecture

#### 1. API Client Setup

```python
from archetypeai.api_client import ArchetypeAI
import os

api_key = os.getenv("ATAI_API_KEY")
api_endpoint = os.getenv("ATAI_API_ENDPOINT", ArchetypeAI.get_default_endpoint())
client = ArchetypeAI(api_key, api_endpoint=api_endpoint)
```

#### 2. Lens YAML Configuration

The embedding lens uses `lens_timeseries_embedding_processor` — no n-shot files or KNN config needed.

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

**Key difference from Machine State Lens**: No `input_n_shot`, no `knn_configs`. The processor outputs raw embedding vectors instead of class predictions.

#### 3. Session Callback — Stream Windows

```python
def session_callback(session_id, session_endpoint, client, args):
    sse_reader = client.lens.sessions.create_sse_consumer(
        session_id, max_read_time_sec=args["max_run_time_sec"]
    )

    # Load CSV with pandas
    df = pd.read_csv(args["file_path"])
    columns = ["a1", "a2", "a3", "a4"]
    data = df[columns].values.T.tolist()  # Transpose: [channels][samples]

    # Stream data in windows
    total_samples = len(df)
    start = 0
    counter = 0
    while start < total_samples:
        end = start + args["window_size"]
        chunk = [series[start:end] for series in data]

        payload = {
            "type": "session.update",
            "event_data": {
                "type": "data.json",
                "event_data": {
                    "sensor_data": chunk,
                    "sensor_metadata": {
                        "sensor_timestamp": time.time(),
                        "sensor_id": f"streamed_sensor_{counter}"
                    }
                }
            }
        }
        client.lens.sessions.process_event(session_id, payload)
        start += args["step_size"]
        counter += 1

    # Collect embeddings
    embeddings = []
    for event in sse_reader.read(block=True):
        if stop_flag:
            break
        etype = event.get("type")
        if etype == "inference.result":
            ed = event.get("event_data", {})
            embedding = ed.get("response")
            meta = ed.get("query_metadata", {})

            # Flatten 4×768 to 3072D vector
            if isinstance(embedding, list) and len(embedding) > 0:
                if isinstance(embedding[0], list):
                    flat = [val for row in embedding for val in row]
                else:
                    flat = embedding

            embeddings.append({
                "window_index": len(embeddings),
                "query_timestamp": meta.get("query_timestamp", "N/A"),
                "embedding": flat,
            })
            print(f"[{len(embeddings)}] Embedding: {len(flat)}D")

    sse_reader.close()
    return embeddings
```

#### 4. Create and Run Lens

```python
client.lens.create_and_run_lens(
    yaml_config, session_callback,
    client=client, args=args
)
```

### Embedding Response Structure

The `inference.result` response contains:
- `response`: nested list of shape `(4, 768)` — one 768D vector per input channel
- Flatten to `3072D` by concatenating: `[a1_768D, a2_768D, a3_768D, a4_768D]`
- `query_metadata.query_timestamp`: timestamp of the window
- `query_metadata.sensor_id`: sensor identifier
- `query_metadata.read_index`: window position in the data

### Saving Embeddings to CSV

```python
import csv

with open(output_file, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['window_index', 'query_timestamp', 'analysis_timestamp',
                     'read_index', 'window_size', 'step_size', 'embedding_vector'])

    for emb in embeddings:
        writer.writerow([
            emb["window_index"],
            emb["query_timestamp"],
            datetime.now().isoformat(),
            emb.get("read_index", "N/A"),
            args["window_size"],
            args["step_size"],
            str(emb["embedding"]),
        ])
```

### CLI Arguments

```
--api-key              API key (fallback to ATAI_API_KEY env var)
--api-endpoint         API endpoint (default from SDK)
--file-path            Path to CSV file to analyze (required)
--window-size          Window size in samples (default: 100)
--step-size            Step size in samples (default: 100)
--max-run-time-sec     Max runtime in seconds (default: 500)
--output-file          Path to save embeddings CSV (optional)
```

---

## Web / JavaScript Implementation

Uses direct `fetch` calls to the Archetype AI REST API.

### API Reference

| Operation | Method | Endpoint | Body |
|-----------|--------|----------|------|
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

### Step 1: Build and register the embedding lens

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

// Register lens
const registeredLens = await apiPost<{ lens_id: string }>(
  '/lens/register', apiKey, { lens_config: lensConfig }
)
const lensId = registeredLens.lens_id

// Create session
const session = await apiPost<{ session_id: string }>(
  '/lens/sessions/create', apiKey, { lens_id: lensId }
)
const sessionId = session.session_id

await apiPost('/lens/delete', apiKey, { lens_id: lensId })

// Wait for session ready
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

### Step 2: Stream CSV data in windows

```typescript
// Parse CSV (PapaParse or similar)
const rows = parsedCsv.data
const columns = ['a1', 'a2', 'a3', 'a4']

let start = 0
let counter = 0

while (start < rows.length) {
  const end = Math.min(start + windowSize, rows.length)
  const window = rows.slice(start, end)

  const sensorData = columns.map(col =>
    window.map(row => Number(row[col]))
  )

  await apiPost('/lens/sessions/events/process', apiKey, {
    session_id: sessionId,
    event: {
      type: 'session.update',
      event_data: {
        type: 'data.json',
        event_data: {
          sensor_data: sensorData,
          sensor_metadata: {
            sensor_timestamp: Date.now() / 1000,
            sensor_id: `web_sensor_${counter}`,
          },
        },
      },
    },
  }, 10000)

  start += stepSize
  counter++
}
```

### Step 3: Consume SSE embedding results

```typescript
import { fetchEventSource } from '@microsoft/fetch-event-source'

interface EmbeddingResult {
  windowIndex: number
  queryTimestamp: string
  embedding: number[]  // 3072D flattened
}

const embeddings: EmbeddingResult[] = []

fetchEventSource(`${API_ENDPOINT}/lens/sessions/consumer/${sessionId}`, {
  headers: { Authorization: `Bearer ${apiKey}` },
  onmessage(event) {
    const parsed = JSON.parse(event.data)

    if (parsed.type === 'inference.result') {
      const response = parsed.event_data.response
      const meta = parsed.event_data.query_metadata

      // Flatten 4×768 → 3072D
      const flat = Array.isArray(response[0])
        ? response.flat()
        : response

      embeddings.push({
        windowIndex: embeddings.length,
        queryTimestamp: meta?.query_timestamp ?? 'N/A',
        embedding: flat,
      })
      console.log(`[${embeddings.length}] Embedding: ${flat.length}D`)
    }

    if (parsed.type === 'sse.stream.end') {
      console.log('Stream complete')
    }
  },
})
```

### Step 4: Cleanup

```typescript
await apiPost('/lens/sessions/destroy', apiKey, { session_id: sessionId })
```

### Web Lifecycle Summary

```
1. Register lens         ->  POST /lens/register  { lens_config: config }
2. Create session        ->  POST /lens/sessions/create  { lens_id }
3. Wait for ready        ->  POST /lens/sessions/events/process  (poll session.status)
4. (Optional) Delete lens -> POST /lens/delete  { lens_id }
5. Stream windowed data  ->  POST /lens/sessions/events/process  { session_id, event }  (loop)
6. Consume SSE results   ->  GET /lens/sessions/consumer/{sessionId}
7. Destroy session       ->  POST /lens/sessions/destroy  { session_id }
```

---

## CSV Format Expected

```csv
timestamp,a1,a2,a3,a4
1700000000.0,100,200,300,374
```

- Column names configurable via `csv_configs.data_columns`
- `a4` is typically magnitude: sqrt(a1² + a2² + a3²)

## Key Differences from Machine State Lens

| | Embedding Lens | Machine State Lens |
|---|---|---|
| Processor | `lens_timeseries_embedding_processor` | `lens_timeseries_state_processor` |
| N-shot files | Not needed | Required (one per class) |
| KNN config | Not needed | Required |
| Output | Raw embedding vectors (4×768 = 3072D) | Class predictions + confidence scores |
| Use case | Visualization, clustering, similarity | Classification, anomaly detection |
