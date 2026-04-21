---
name: newton-machine-state-from-file
description: Run a Machine State Lens by streaming sensor data from a CSV file. Use when analyzing time-series CSV data for machine state classification, anomaly detection, or n-shot state recognition from files.
argument-hint: [csv-file-path]
---

# Newton Machine State Lens — Stream from CSV File

Generate a script that streams time-series data from a CSV file to the Archetype AI Machine State Lens for n-shot state classification. Supports both Python and JavaScript/Web.

## Frontend Architecture

Decompose the UI into components. See `@rules/frontend-architecture` for conventions.

### Recommended decomposition

| UI Area | Component | Pattern/Primitives | Key Props |
|---------|-----------|-------------------|-----------|
| File input | `DataInput.svelte` | BackgroundCard, Button, Input | `onselect`, `status` |
| Classification | `StateDisplay.svelte` | BackgroundCard, Badge | `currentState`, `confidence` |
| Time series | Reuse SensorChart pattern | BackgroundCard, Chart | `data[]`, `signals` |
| Results | Use FlatLogItem pattern in ScrollArea | FlatLogItem, ScrollArea | `status`, `message`, `detail` |

- Use `@skills/create-dashboard` for the page layout
- Extract streaming and session logic into `$lib/api/machine-state.js`

---

## Python Implementation

### Requirements

- `archetypeai` Python package
- `pandas`, `numpy`
- Environment variables: `ATAI_API_KEY`, optionally `ATAI_API_ENDPOINT`

### Architecture

The script must follow this exact pattern:

#### 1. API Client Setup

```python
from archetypeai.api_client import ArchetypeAI
import os

api_key = os.getenv("ATAI_API_KEY")
api_endpoint = os.getenv("ATAI_API_ENDPOINT", ArchetypeAI.get_default_endpoint())
client = ArchetypeAI(api_key, api_endpoint=api_endpoint)
```

#### 2. Upload N-Shot Example Files

Upload one CSV per class. The file ID returned is used in the lens YAML config.

```python
# Upload example files for each class
# Class name is typically derived from filename stem
resp = client.files.local.upload("path/to/healthy.csv")
healthy_id = resp["file_id"]

resp = client.files.local.upload("path/to/broken.csv")
broken_id = resp["file_id"]
```

#### 3. Lens YAML Configuration

Build the YAML config string dynamically, inserting file IDs:

```yaml
lens_name: Machine State Lens
lens_config:
  model_pipeline:
    - processor_name: lens_timeseries_state_processor
      processor_config: {}
  model_parameters:
    model_name: OmegaEncoder
    model_version: OmegaEncoder::omega_embeddings_01
    normalize_input: true
    buffer_size: {window_size}
    input_n_shot:
      NORMAL: {healthy_file_id}
      WARNING: {broken_file_id}
    csv_configs:
      timestamp_column: timestamp
      data_columns: ['a1', 'a2', 'a3', 'a4']
      window_size: {window_size}
      step_size: {step_size}
    knn_configs:
      n_neighbors: 5
      metric: manhattan
      weights: distance
      algorithm: ball_tree
      normalize_embeddings: false
  output_streams:
    - stream_type: server_sent_events_writer
```

**Important**: `input_n_shot` keys become the predicted class labels. Users can define any number of classes (not just two).

#### 4. Session Callback Pattern

```python
def session_callback(session_id, session_endpoint, client, args):
    # Create SSE consumer FIRST
    sse_reader = client.lens.sessions.create_sse_consumer(
        session_id, max_read_time_sec=args["max_run_time_sec"]
    )

    # Load CSV with pandas
    df = pd.read_csv(args["file_path"])
    columns = ["a1", "a2", "a3", "a4"]  # or user-specified columns
    data = df[columns].values.T.tolist()  # Transpose: [channels][samples]

    # Stream data in windows
    total_samples = len(df)
    start = 0
    counter = 0
    while start < total_samples:
        end = start + window_size
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
        start += step_size
        counter += 1

    # Listen for results
    for event in sse_reader.read(block=True):
        etype = event.get("type")
        if etype == "inference.result":
            result = event["event_data"].get("response")
            meta = event["event_data"].get("query_metadata", {})
            print(f"[{meta.get('query_timestamp', 'N/A')}] Predicted: {result}")
        elif etype == "session.modify.result":
            cls = event["event_data"].get("query_metadata", {}).get("class_name")
            print(f"[TRAINING] Processed class: {cls}")
```

#### 5. Create and Run Lens

```python
client.lens.create_and_run_lens(
    yaml_config, session_callback,
    client=client, args=args
)
```

### CLI Arguments to Include

```
--api-key            API key (fallback to ATAI_API_KEY env var)
--api-endpoint       API endpoint (default from SDK)
--file-path          Path to CSV file to analyze (required)
--n-shot-files       Paths to n-shot example CSVs (required, nargs='+')
--window-size        Window size in samples (default: 100)
--step-size-n-shot   Step size for training data (default: 100)
--step-size-inference Step size for inference stream (default: 100)
--max-run-time-sec   Max runtime in seconds (default: 500)
```

---

## Web / JavaScript Implementation

Uses direct `fetch` calls to the Archetype AI REST API. Based on the working pattern from `test-stream/src/lib/atai-client.ts`.

### Requirements

- `@microsoft/fetch-event-source` for SSE consumption

### API Reference

| Operation | Method | Endpoint | Body |
|-----------|--------|----------|------|
| Upload file | POST | `/files` | `FormData` |
| Register lens | POST | `/lens/register` | `{ lens_config: config }` |
| Delete lens | POST | `/lens/delete` | `{ lens_id }` |
| Create session | POST | `/lens/sessions/create` | `{ lens_id }` |
| Process event | POST | `/lens/sessions/events/process` | `{ session_id, event }` |
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

### Step 1: Upload n-shot CSV files

```typescript
const nShotMap: Record<string, string> = {}

for (const { file, className } of nShotFiles) {
  const formData = new FormData()
  formData.append('file', file) // File object from <input type="file">

  const response = await fetch(`${API_ENDPOINT}/files`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${apiKey}` },
    body: formData,
  })
  const result = await response.json()
  nShotMap[className.toUpperCase()] = result.file_id
}
```

### Step 2: Build the lens config

```typescript
const windowSize = 100
const stepSize = 100

const lensConfig = {
  lens_name: 'machine_state_lens',
  lens_config: {
    model_pipeline: [
      { processor_name: 'lens_timeseries_state_processor', processor_config: {} },
    ],
    model_parameters: {
      model_name: 'OmegaEncoder',
      model_version: 'OmegaEncoder::omega_embeddings_01',
      normalize_input: true,
      buffer_size: windowSize,
      input_n_shot: nShotMap, // { HEALTHY: 'file_id', BROKEN: 'file_id' }
      csv_configs: {
        timestamp_column: 'timestamp',
        data_columns: ['a1', 'a2', 'a3', 'a4'],
        window_size: windowSize,
        step_size: stepSize,
      },
      knn_configs: {
        n_neighbors: 5,
        metric: 'manhattan',
        weights: 'distance',
        algorithm: 'ball_tree',
        normalize_embeddings: false,
      },
    },
    output_streams: [
      { stream_type: 'server_sent_events_writer' },
    ],
  },
}
```

### Step 3: Register lens, create session, wait for ready

```typescript
// Register lens — NOTE: body must wrap config as { lens_config: config }
const registeredLens = await apiPost<{ lens_id: string }>(
  '/lens/register', apiKey, { lens_config: lensConfig }
)
const lensId = registeredLens.lens_id

// Create session
const session = await apiPost<{ session_id: string; session_endpoint: string }>(
  '/lens/sessions/create', apiKey, { lens_id: lensId }
)
const sessionId = session.session_id

// Optionally delete the lens definition (session keeps running independently)
await apiPost('/lens/delete', apiKey, { lens_id: lensId })

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
if (!isReady) throw new Error('Session failed to start')
```

### Step 4: Stream CSV data in windows

Parse the CSV client-side and send windowed chunks via `POST /lens/sessions/events/process`:

```typescript
// Parse CSV (using PapaParse or similar)
const rows = parsedCsv.data // array of { timestamp, a1, a2, a3, a4 }
const columns = ['a1', 'a2', 'a3', 'a4']

let start = 0
let counter = 0

while (start < rows.length) {
  const end = Math.min(start + windowSize, rows.length)
  const window = rows.slice(start, end)

  // Transpose to channel-first: [[a1_vals], [a2_vals], [a3_vals], [a4_vals]]
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

### Step 5: Consume SSE results

```typescript
import { fetchEventSource } from '@microsoft/fetch-event-source'

fetchEventSource(`${API_ENDPOINT}/lens/sessions/consumer/${sessionId}`, {
  headers: { Authorization: `Bearer ${apiKey}` },
  onmessage(event) {
    const parsed = JSON.parse(event.data)

    if (parsed.type === 'inference.result') {
      const result = parsed.event_data.response
      const meta = parsed.event_data.query_metadata
      console.log(`[${meta.query_timestamp ?? 'N/A'}] Predicted: ${result}`)
    }

    if (parsed.type === 'session.modify.result') {
      const cls = parsed.event_data?.query_metadata?.class_name
      console.log(`[TRAINING] Processed class: ${cls}`)
    }

    if (parsed.type === 'sse.stream.end') {
      console.log('Stream complete')
    }
  },
})
```

### Step 6: Cleanup

```typescript
await apiPost('/lens/sessions/destroy', apiKey, { session_id: sessionId })
```

### Web Lifecycle Summary

```
1. Upload n-shot CSVs    ->  POST /files  (FormData, one per class)
2. Register lens         ->  POST /lens/register  { lens_config: config }
3. Create session        ->  POST /lens/sessions/create  { lens_id }
4. Wait for ready        ->  POST /lens/sessions/events/process  { session_id, event: { type: 'session.status' } }
5. (Optional) Delete lens -> POST /lens/delete  { lens_id }
6. Stream windowed data  ->  POST /lens/sessions/events/process  { session_id, event }  (loop)
7. Consume SSE results   ->  GET /lens/sessions/consumer/{sessionId}
8. Destroy session       ->  POST /lens/sessions/destroy  { session_id }
```

---

## CSV Format Expected

```csv
timestamp,a1,a2,a3,a4
1700000000.0,100,200,300,374
1700000000.01,101,199,301,375
```

- `timestamp`: UNIX epoch float
- `a1, a2, a3`: Sensor axes (e.g., accelerometer x, y, z)
- `a4`: Magnitude (sqrt(a1² + a2² + a3²))
- Column names are configurable via `csv_configs.data_columns`

## Optional: Results Logging

Save predictions to a timestamped CSV for analysis or visualization.

### Python — Results CSV

```python
import csv
from pathlib import Path
from datetime import datetime

# Create results directory and timestamped filename
results_dir = Path("results")
results_dir.mkdir(exist_ok=True)
file_stem = Path(args["file_path"]).stem
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
results_file = results_dir / f"{file_stem}_{timestamp}.csv"

# Write CSV header
with open(results_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['read_index', 'predicted_class', 'confidence_scores',
                     'file_id', 'window_size', 'total_rows'])

# Inside the SSE event loop, when handling inference.result:
if etype == "inference.result":
    ed = event.get("event_data", {})
    result = ed.get("response")
    meta = ed.get("query_metadata", {})
    query_meta = meta.get("query_metadata", {})

    predicted_class = result[0] if isinstance(result, list) and len(result) > 0 else "unknown"
    confidence_scores = result[1] if isinstance(result, list) and len(result) > 1 else {}
    read_index = query_meta.get("read_index", "N/A")
    file_id = query_meta.get("file_id", "N/A")
    window_size = query_meta.get("window_size", "N/A")
    total_rows = query_meta.get("total_rows", "N/A")

    print(f"[{read_index}] Predicted: {predicted_class} | Scores: {confidence_scores}")

    with open(results_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([read_index, predicted_class, str(confidence_scores),
                         file_id, window_size, total_rows])
```

### Response Structure

The `inference.result` response contains:
- `response[0]`: predicted class name (string, e.g. `"HEALTHY"`)
- `response[1]`: confidence scores dict (e.g. `{"HEALTHY": 0.95, "BROKEN": 0.05}`)
- `query_metadata.query_metadata.read_index`: window position in the file
- `query_metadata.query_metadata.file_id`: the file being analyzed
- `query_metadata.query_metadata.window_size`: window size used
- `query_metadata.query_metadata.total_rows`: total rows in the file

### Web/JS — Results Array + CSV Download

```typescript
interface PredictionResult {
  readIndex: number | string
  predictedClass: string
  confidenceScores: Record<string, number>
  fileId: string
  windowSize: number
  totalRows: number
}

const results: PredictionResult[] = []

// Inside the SSE onmessage handler:
if (parsed.type === 'inference.result') {
  const result = parsed.event_data.response
  const meta = parsed.event_data.query_metadata
  const queryMeta = meta?.query_metadata ?? {}

  const prediction: PredictionResult = {
    readIndex: queryMeta.read_index ?? 'N/A',
    predictedClass: Array.isArray(result) && result.length > 0 ? result[0] : 'unknown',
    confidenceScores: Array.isArray(result) && result.length > 1 ? result[1] : {},
    fileId: queryMeta.file_id ?? 'N/A',
    windowSize: queryMeta.window_size ?? 0,
    totalRows: queryMeta.total_rows ?? 0,
  }

  results.push(prediction)
  console.log(`[${prediction.readIndex}] ${prediction.predictedClass}`, prediction.confidenceScores)
}

// Download results as CSV
function downloadResultsCsv(results: PredictionResult[], filename: string) {
  const header = 'read_index,predicted_class,confidence_scores,file_id,window_size,total_rows\n'
  const rows = results.map(r =>
    `${r.readIndex},${r.predictedClass},"${JSON.stringify(r.confidenceScores)}",${r.fileId},${r.windowSize},${r.totalRows}`
  ).join('\n')

  const blob = new Blob([header + rows], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
```

### CLI Flag

Add `--save-results` flag (default: `True`) to enable/disable results logging:

```
--save-results       Save predictions to CSV in results/ directory (default: True)
```

---

## Key Implementation Notes

- N-shot class names are derived from the filename stem (e.g., `healthy.csv` → class `HEALTHY`)
- The `data_columns` in `csv_configs` must match both the n-shot files and the data file
- `window_size` and `step_size` control the sliding window over the data
- Default `window_size` and `step_size`: **100**
- Use `signal.SIGINT` handler for graceful shutdown (Python) or `AbortController` (Web)
- Always close `sse_reader` in a `finally` block (Python) or destroy session on unmount (Web)
- The SSE reader emits `inference.result` for predictions and `session.modify.result` for training confirmations
