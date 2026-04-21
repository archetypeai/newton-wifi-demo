---
name: newton-machine-state-upload
description: Run a Machine State Lens by uploading a CSV file for server-side processing. Use when you want to upload a file and let the server handle streaming (no local streaming loop needed).
argument-hint: [csv-file-path]
---

# Newton Machine State Lens — Upload File (Server-Side Processing)

Generate a script that uploads a CSV file to the Archetype AI platform and runs Machine State classification server-side. Unlike the streaming approaches, this method lets the server read the file directly — no local streaming loop required. Supports both Python and JavaScript/Web.
1
> **Frontend architecture:** See `@rules/frontend-architecture` for component decomposition conventions. This skill already includes detailed frontend guidance in the "Row Synchronization" section below.

---

## Python Implementation

### Requirements

- `archetypeai` Python package
- Environment variables: `ATAI_API_KEY`, optionally `ATAI_API_ENDPOINT`

### Architecture

Uses `create_and_run_lens` with YAML config. After the lens session is created, the data file is uploaded and a `csv_file_reader` input stream tells the server to read it directly.

#### 1. API Client Setup

```python
from archetypeai.api_client import ArchetypeAI
import os

api_key = os.getenv("ATAI_API_KEY")
api_endpoint = os.getenv("ATAI_API_ENDPOINT", ArchetypeAI.get_default_endpoint())
client = ArchetypeAI(api_key, api_endpoint=api_endpoint)
```

#### 2. Upload N-Shot Example Files & Build YAML

```python
from pathlib import Path

input_n_shot = {}
for file_path in n_shot_file_paths:
    class_name = Path(file_path).stem.upper()
    resp = client.files.local.upload(file_path)
    input_n_shot[class_name] = resp["file_id"]
```

#### 3. Lens YAML Configuration

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
      HEALTHY: {healthy_file_id}
      BROKEN: {broken_file_id}
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

Build `input_n_shot` dynamically:

```python
n_shot_yaml_lines = []
for class_name, file_id in input_n_shot.items():
    n_shot_yaml_lines.append(f"      {class_name}: {file_id}")
n_shot_yaml = "\n".join(n_shot_yaml_lines)
```

#### 4. Event Builders for Server-Side File Reading

After the lens session is created, send these events to make the server read the uploaded CSV:

##### input_stream.set — Point server at the uploaded CSV

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
```

##### output_stream.set — Enable SSE output

```python
def build_output_event():
    return {
        "type": "output_stream.set",
        "event_data": {
            "stream_type": "server_side_events_writer",
            "stream_config": {}
        }
    }
```

#### 5. Session Callback

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

    # Listen for results via SSE
    sse_reader = client.lens.sessions.create_sse_consumer(
        session_id, max_read_time_sec=args["max_run_time_sec"]
    )

    try:
        for event in sse_reader.read(block=True):
            if stop_flag:
                break
            if isinstance(event, dict) and event.get("type") == "inference.result":
                ed = event.get("event_data", {})
                result = ed.get("response")
                meta = ed.get("query_metadata", {})
                ts = meta.get("query_timestamp", "N/A")
                if result is not None:
                    print(f"[{ts}] Predicted class: {result}")
    finally:
        sse_reader.close()
        print("Stopped.")
```

#### 6. Create and Run Lens

```python
client.lens.create_and_run_lens(
    yaml_config, session_callback,
    client=client, args=args
)
```

### CLI Arguments to Include

```
--api-key              API key (fallback to ATAI_API_KEY env var)
--api-endpoint         API endpoint (default from SDK)
--data-file            Path to CSV file to analyze (required)
--n-shot-files         Paths to n-shot example CSVs (required, nargs='+')
--window-size          Window size in samples (default: 100)
--step-size            Step size in samples (default: 100)
--max-run-time-sec     Max runtime (default: 600)
```

### Example Usage

```bash
python machine_state_upload.py \
  --data-file data.csv \
  --n-shot-files healthy.csv broken.csv

# With custom window size
python machine_state_upload.py \
  --data-file sensor_recording.csv \
  --n-shot-files normal.csv warning.csv critical.csv \
  --window-size 512 --step-size 256
```

---

## Web / JavaScript Implementation

Uses direct `fetch` calls to the Archetype AI REST API. The simplest of the three approaches on web — just upload files and let the server handle everything. Based on the working pattern from `test-stream/src/lib/atai-client.ts`.

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
  formData.append('file', file) // File from <input type="file">

  const response = await fetch(`${API_ENDPOINT}/files`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${apiKey}` },
    body: formData,
  })
  const result = await response.json()
  nShotMap[className.toUpperCase()] = result.file_id
}
```

### Step 2: Upload the data CSV

```typescript
const dataFormData = new FormData()
dataFormData.append('file', dataFile)

const dataResponse = await fetch(`${API_ENDPOINT}/files`, {
  method: 'POST',
  headers: { Authorization: `Bearer ${apiKey}` },
  body: dataFormData,
})
const dataUpload = await dataResponse.json()
const dataFileId = dataUpload.file_id
```

### Step 3: Register lens, create session, wait for ready

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
      input_n_shot: nShotMap,
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

// Register lens — NOTE: body wraps config as { lens_config: config }
const registeredLens = await apiPost<{ lens_id: string }>(
  '/lens/register', apiKey, { lens_config: lensConfig }
)
const lensId = registeredLens.lens_id

// Create session
const session = await apiPost<{ session_id: string; session_endpoint: string }>(
  '/lens/sessions/create', apiKey, { lens_id: lensId }
)
const sessionId = session.session_id

await apiPost('/lens/delete', apiKey, { lens_id: lensId })

// Wait for session to be ready
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

### Step 4: Tell server to read the uploaded CSV

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

### Step 5: Consume SSE results

```typescript
import { fetchEventSource } from '@microsoft/fetch-event-source'

const abortController = new AbortController()

fetchEventSource(`${API_ENDPOINT}/lens/sessions/consumer/${sessionId}`, {
  headers: { Authorization: `Bearer ${apiKey}` },
  signal: abortController.signal,
  onmessage(event) {
    const parsed = JSON.parse(event.data)

    if (parsed.type === 'inference.result') {
      const result = parsed.event_data.response
      const meta = parsed.event_data.query_metadata
      const ts = meta?.query_timestamp ?? 'N/A'
      console.log(`[${ts}] Predicted class: ${result}`)
    }

    if (parsed.type === 'sse.stream.end') {
      console.log('Analysis complete')
      abortController.abort()
    }
  },
})
```

### Step 6: Cleanup

```typescript
abortController.abort()
await apiPost('/lens/sessions/destroy', apiKey, { session_id: sessionId })
```

### Web Lifecycle Summary

```
1. Upload n-shot CSVs         ->  POST /files  (FormData, one per class)
2. Upload data CSV            ->  POST /files  (FormData)
3. Register lens              ->  POST /lens/register  { lens_config: config }
4. Create session             ->  POST /lens/sessions/create  { lens_id }
5. Wait for ready             ->  POST /lens/sessions/events/process  { session_id, event: { type: 'session.status' } }
6. (Optional) Delete lens     ->  POST /lens/delete  { lens_id }
7. Set input stream           ->  POST /lens/sessions/events/process  { session_id, event: { type: 'input_stream.set', ... } }
8. Set output stream          ->  POST /lens/sessions/events/process  { session_id, event: { type: 'output_stream.set', ... } }
9. Consume SSE results        ->  GET /lens/sessions/consumer/{sessionId}
10. Destroy session           ->  POST /lens/sessions/destroy  { session_id }
```

---

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
file_stem = Path(args["data_file_path"]).stem
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
results_file = results_dir / f"{file_stem}_{timestamp}.csv"

# Write CSV header
with open(results_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['read_index', 'predicted_class', 'confidence_scores',
                     'file_id', 'window_size', 'total_rows'])

# Inside the SSE event loop, when handling inference.result:
if isinstance(event, dict) and event.get("type") == "inference.result":
    ed = event.get("event_data", {})
    result = ed.get("response")
    meta = ed.get("query_metadata", {})
    query_meta = meta.get("query_metadata", {})

    predicted_class = result[0] if isinstance(result, list) and len(result) > 0 else "unknown"
    raw_votes = result[1] if isinstance(result, list) and len(result) > 1 else {}

    # Normalize KNN votes to percentages (votes are out of n_neighbors, default 5)
    total_votes = sum(raw_votes.values()) if raw_votes else 1
    confidence_scores = {k: round(v / total_votes * 100, 1) for k, v in raw_votes.items()}

    read_index = query_meta.get("read_index", "N/A")
    file_id = query_meta.get("file_id", "N/A")
    window_size_val = query_meta.get("window_size", "N/A")
    total_rows = query_meta.get("total_rows", "N/A")

    print(f"[{read_index}] Predicted: {predicted_class} | Confidence: {confidence_scores}")

    with open(results_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([read_index, predicted_class, str(confidence_scores),
                         file_id, window_size_val, total_rows])
```

**Row synchronization note**: Each result's `read_index` and `window_size` map directly to CSV row numbers (`[read_index, read_index + window_size)`). When building a UI on top of the Python backend, forward these fields to the frontend for chart-to-result synchronization. See the "Row Synchronization" section below for the full web pattern.

### Response Structure

The `inference.result` response contains:
- `response[0]`: predicted class name (string, e.g. `"HEALTHY"`)
- `response[1]`: KNN vote counts dict (e.g. `{"HEALTHY": 3, "BROKEN": 2}`) — these are raw votes out of `n_neighbors` (default 5), **not percentages**. Normalize by dividing each value by the total votes to get percentages (e.g. 3/5 = 60%, 2/5 = 40%)
- `query_metadata.query_metadata.read_index`: window position in the file
- `query_metadata.query_metadata.file_id`: the file being analyzed
- `query_metadata.query_metadata.window_size`: window size used
- `query_metadata.query_metadata.total_rows`: total rows in the file

### Web/JS — Results Array + CSV Download

```typescript
interface PredictionResult {
  readIndex: number
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

  // Normalize KNN votes to percentages (votes are out of n_neighbors, default 5)
  const rawVotes: Record<string, number> = Array.isArray(result) && result.length > 1 ? result[1] : {}
  const totalVotes = Object.values(rawVotes).reduce((sum, v) => sum + v, 0) || 1
  const confidenceScores: Record<string, number> = {}
  for (const [cls, votes] of Object.entries(rawVotes)) {
    confidenceScores[cls] = Math.round((votes / totalVotes) * 1000) / 10 // e.g. 60.0
  }

  const prediction: PredictionResult = {
    readIndex: queryMeta.read_index ?? 0,
    predictedClass: Array.isArray(result) && result.length > 0 ? result[0] : 'unknown',
    confidenceScores,
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

## Row Synchronization — Linking Results to Raw Data (Web)

Every `inference.result` from the API includes `query_metadata.query_metadata.read_index` and `query_metadata.query_metadata.window_size`. This tells you exactly which CSV rows `[read_index, read_index + window_size)` each classification covers. Use this to synchronize the results list with a line chart of the raw data.

### Architecture Overview

```
CSV File (user upload)
  ├─ Sent to API for classification (existing flow)
  └─ Parsed client-side for visualization
       ↓
  ┌─────────────────────────────────────┐
  │  Line Chart (all CSV data columns)  │
  │  ██████░░░░░░░░░░░░░░░░░░░░░░░░░░  │  ← highlight rect on selected result
  └─────────────────────────────────────┘
       ↑ click result sets activeResult
  ┌─────────────────────────────────────┐
  │  Results List (clickable rows)      │
  │  [0-99]   HEALTHY  ██████████ 0.95  │
  │  [100-199] BROKEN  ████░░░░░░ 0.40  │  ← click to highlight on chart
  └─────────────────────────────────────┘
```

### Step 1: Parse the CSV client-side on upload

When the user selects the data CSV file, parse it locally to feed the chart. This happens alongside the existing file upload to the API.

```typescript
interface CsvRow {
  [column: string]: number
}

function parseCsv(file: File): Promise<CsvRow[]> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const text = e.target?.result as string
      const lines = text.trim().split('\n')
      const headers = lines[0].split(',').map(h => h.trim())
      const rows = lines.slice(1).map(line => {
        const values = line.split(',')
        const row: CsvRow = {}
        headers.forEach((h, i) => {
          row[h] = parseFloat(values[i])
        })
        return row
      })
      resolve(rows)
    }
    reader.onerror = reject
    reader.readAsText(file)
  })
}

// Usage: parse when user selects file
const csvData = await parseCsv(dataFile)
```

### Step 2: Class color mapping

Assign consistent colors to each predicted class. Both the results list and chart highlight use these colors.

**Important (Svelte 5):** Do NOT use a `$state` object with imperative mutation inside a getter — this causes `state_unsafe_mutation` errors when called from templates or `$derived`. Instead, use `$derived.by()` to compute the color map reactively from the detections array:

```javascript
// Color palette — use 600-weight design tokens for light mode visibility
const CLASS_COLORS = [
  'var(--color-atai-screen-green-600)',
  'var(--color-atai-fire-red-600)',
  'var(--color-atai-sunshine-yellow-600)',
  'var(--chart-4)',
  'var(--chart-5)',
  'var(--chart-1)'
];

// Compute color map reactively from detections (no mutation)
let classColorMap = $derived.by(() => {
  const map = {};
  let idx = 0;
  for (const d of detections) {
    if (!map[d.predictedClass]) {
      map[d.predictedClass] = CLASS_COLORS[idx % CLASS_COLORS.length];
      idx++;
    }
    for (const cls of Object.keys(d.confidenceScores)) {
      if (!map[cls]) {
        map[cls] = CLASS_COLORS[idx % CLASS_COLORS.length];
        idx++;
      }
    }
  }
  return map;
});

function getClassColor(className) {
  return classColorMap[className] || CLASS_COLORS[0];
}
```

**Light mode note:** Avoid `--atai-good` (88% lightness) and `--atai-warning` (94% lightness) — they're invisible on white backgrounds. Use the 600-weight variants (`--color-atai-screen-green-600`, `--color-atai-fire-red-600`, `--color-atai-sunshine-yellow-600`) which have ~63% lightness.

### Step 3: Reactive state for selected result

```typescript
// Svelte 5 runes
let selectedResult: PredictionResult | null = $state(null)

// Or Svelte store
import { writable } from 'svelte/store'
const selectedResult = writable<PredictionResult | null>(null)
```

### Step 4: Line chart with D3 + highlight overlay

Render the raw CSV data as a multi-line chart. When `selectedResult` is set, draw a colored rectangle overlay for the row range `[readIndex, readIndex + windowSize)`.

```typescript
import * as d3 from 'd3'

function drawChart(
  container: HTMLElement,
  csvData: CsvRow[],
  dataColumns: string[],
  selectedResult: PredictionResult | null
) {
  const width = container.clientWidth
  const height = 300
  const margin = { top: 20, right: 30, bottom: 40, left: 60 }
  const innerW = width - margin.left - margin.right
  const innerH = height - margin.top - margin.bottom

  // Clear previous
  d3.select(container).selectAll('*').remove()

  const svg = d3.select(container)
    .append('svg')
    .attr('width', width)
    .attr('height', height)

  const g = svg.append('g')
    .attr('transform', `translate(${margin.left},${margin.top})`)

  // Scales
  const xScale = d3.scaleLinear()
    .domain([0, csvData.length - 1])
    .range([0, innerW])

  const allValues = csvData.flatMap(row => dataColumns.map(col => row[col]))
  const yScale = d3.scaleLinear()
    .domain([d3.min(allValues)!, d3.max(allValues)!])
    .range([innerH, 0])
    .nice()

  // Axes
  g.append('g')
    .attr('transform', `translate(0,${innerH})`)
    .call(d3.axisBottom(xScale).ticks(10))

  g.append('g')
    .call(d3.axisLeft(yScale).ticks(6))

  // Line colors for data columns
  const lineColors = ['#ff4444', '#44ff44', '#4444ff', '#ff44ff', '#ffaa00', '#00aaff']

  // Draw lines
  dataColumns.forEach((col, i) => {
    const line = d3.line<CsvRow>()
      .x((_, idx) => xScale(idx))
      .y(d => yScale(d[col]))

    g.append('path')
      .datum(csvData)
      .attr('fill', 'none')
      .attr('stroke', lineColors[i % lineColors.length])
      .attr('stroke-width', 1)
      .attr('d', line)
  })

  // Highlight selected result's row range
  if (selectedResult) {
    const startX = xScale(selectedResult.readIndex)
    const endX = xScale(selectedResult.readIndex + selectedResult.windowSize)
    const color = getClassColor(selectedResult.predictedClass)

    g.append('rect')
      .attr('x', startX)
      .attr('y', 0)
      .attr('width', endX - startX)
      .attr('height', innerH)
      .attr('fill', color)
      .attr('fill-opacity', 0.2)
      .attr('stroke', color)
      .attr('stroke-width', 1.5)
      .attr('stroke-opacity', 0.6)

    // Label at top of highlight
    g.append('text')
      .attr('x', startX + 4)
      .attr('y', 14)
      .attr('fill', color)
      .attr('font-size', '11px')
      .attr('font-weight', 'bold')
      .text(`${selectedResult.predictedClass} [${selectedResult.readIndex}–${selectedResult.readIndex + selectedResult.windowSize}]`)
  }
}
```

### Step 4b: SensorChart overlay alternative (layerchart)

If using the SensorChart pattern (layerchart) instead of raw D3, use an absolute-positioned div overlay rather than drawing into the SVG. SensorChart manages its own SVG, so you overlay a highlight div on top.

**Critical:** Use `[data-slot="chart"] svg` selector to find the layerchart SVG — a plain `querySelector('svg')` will match lucide icon SVGs (24×24) in CardHeader instead, producing wrong dimensions.

```svelte
<script>
  let chartWrapperRef = $state(null);
  let highlightRect = $state(null);

  $effect(() => {
    const _sel = selectedDetection;
    const _len = chartData.length;
    if (!_sel || !chartWrapperRef || _len === 0) {
      highlightRect = null;
      return;
    }

    // IMPORTANT: target [data-slot="chart"] to skip icon SVGs
    const svg = chartWrapperRef.querySelector('[data-slot="chart"] svg');
    if (!svg) { highlightRect = null; return; }

    const svgRect = svg.getBoundingClientRect();
    const wrapperRect = chartWrapperRef.getBoundingClientRect();

    // SensorChart uses padding={{ left: 20, bottom: 15 }}
    const paddingLeft = 20;
    const paddingBottom = 15;
    const plotLeft = svgRect.left - wrapperRect.left + paddingLeft;
    const plotWidth = svgRect.width - paddingLeft;
    const plotTop = svgRect.top - wrapperRect.top;
    const plotHeight = svgRect.height - paddingBottom;

    const startFrac = _sel.readIndex / _len;
    const widthFrac = _sel.windowSize / _len;

    highlightRect = {
      left: plotLeft + startFrac * plotWidth,
      width: widthFrac * plotWidth,
      top: plotTop,
      height: plotHeight
    };
  });
</script>

<!-- Wrapper with relative positioning for overlay -->
<div bind:this={chartWrapperRef} class="relative">
  <SensorChart
    title="SENSOR DATA"
    data={chartData}
    signals={{ a1: 'A1', a2: 'A2', a3: 'A3', a4: 'A4' }}
    xKey="timestamp"
    yMin={yMin}
    yMax={yMax}
  />
  {#if highlightRect}
    <div
      class="pointer-events-none absolute rounded-sm border-2"
      style="
        left: {highlightRect.left}px;
        top: {highlightRect.top}px;
        width: {highlightRect.width}px;
        height: {highlightRect.height}px;
        background-color: color-mix(in srgb, {getClassColor(selectedDetection.predictedClass)} 20%, transparent);
        border-color: {getClassColor(selectedDetection.predictedClass)};
      "
    ></div>
  {/if}
</div>
```

**Key details:**
- `[data-slot="chart"]` is set by `Chart.Container` (see `chart-container.svelte`)
- SensorChart padding constants: `left: 20`, `bottom: 15` — match `padding={{ left: 20, bottom: 15 }}` in SensorChart
- The overlay is `pointer-events-none` so it doesn't block chart interactions
- `color-mix` creates a translucent fill from the class color

### Step 5: Clickable results list

Each result row is clickable. Clicking sets `selectedResult`, which triggers the chart to redraw with the highlight.

**Important:** Do not use `result.readIndex` as the `{#each}` key — `readIndex` values can repeat when `step_size < window_size` (overlapping windows). Use the array index `i` instead.

```svelte
<div class="results-list">
  {#each results as result, i (i)}
    <button
      class="result-row"
      class:selected={selectedResult === result}
      onclick={() => selectedResult = result}
      style="border-left: 4px solid {getClassColor(result.predictedClass)}"
    >
      <span class="row-range">[{result.readIndex}–{result.readIndex + result.windowSize}]</span>
      <span class="class-name">{result.predictedClass}</span>
      <span class="confidence">
        {#each Object.entries(result.confidenceScores) as [cls, pct] (cls)}
          <span style="color: {getClassColor(cls)}">{cls}: {pct}%</span>
        {/each}
      </span>
    </button>
  {/each}
</div>
```

### Step 6: Wire chart + results together

In the page component, reactively redraw the chart when `selectedResult` changes:

```svelte
<script lang="ts">
  let chartContainer: HTMLElement
  let csvData: CsvRow[] = $state([])
  let results: PredictionResult[] = $state([])
  let selectedResult: PredictionResult | null = $state(null)
  const dataColumns = ['a1', 'a2', 'a3', 'a4'] // from csv_configs

  // Redraw chart when data or selection changes
  $effect(() => {
    if (chartContainer && csvData.length > 0) {
      drawChart(chartContainer, csvData, dataColumns, selectedResult)
    }
  })
</script>

<!-- Chart -->
<div bind:this={chartContainer} class="w-full h-[300px]"></div>

<!-- Results list -->
<!-- ... clickable results from Step 5 ... -->
```

### Row Range Mapping — How It Works

Each API result contains the exact row range it classified:

```
query_metadata.query_metadata = {
  "read_index": 200,    // start row in CSV
  "window_size": 100,   // number of rows in this window
  "total_rows": 6090    // total rows in the file
}
```

- **Start row**: `read_index` (0-based)
- **End row**: `read_index + window_size` (exclusive)
- **No proportional mapping needed** — the indices map directly to CSV row numbers

This is simpler than the embeddings demo's approach (which uses proportional mapping between datasets). Here, the API gives you exact row positions.

---

## Key Differences from Streaming Approaches

| | Upload (this skill) | Stream from File | Stream from Sensor |
|---|---|---|---|
| Data reading | Server-side `csv_file_reader` | Local pandas/JS + windowed push | Local sensor + buffered push |
| Lens creation | YAML config via `create_and_run_lens` / `registerLens` | Same | Same |
| Data delivery | Upload file, server reads it | Local code streams windows | Local code buffers + streams |
| Local processing | None (just upload) | Window slicing + streaming | Sensor acquisition + buffering |
| Best for | Batch analysis of existing data | Controlled local streaming | Real-time from hardware |

## CSV Format Expected

```csv
timestamp,a1,a2,a3,a4
1700000000.0,100,200,300,374
```

- Column names are configurable via `csv_configs.data_columns`
- N-shot files and data file must share the same column structure
- `a4` is typically the magnitude: sqrt(a1² + a2² + a3²)

## Key Implementation Notes

- Default `window_size` and `step_size`: **100**
- N-shot class names derived from filename stems (e.g., `healthy.csv` → `HEALTHY`)
- No local streaming loop needed — the server reads the file via `csv_file_reader`
- Python: `signal.SIGINT` for graceful shutdown, always use `try/finally` for `sse_reader`
- Web: `AbortController` for SSE cancellation, destroy session on unmount
- On web, this is the simplest approach — just file uploads and SSE consumption, no sensor APIs needed

## Graceful Shutdown

```python
import signal

stop_flag = False
def _sigint(sig, frame):
    global stop_flag
    stop_flag = True

signal.signal(signal.SIGINT, _sigint)
```

Always wrap the SSE reader in a `try/finally` to ensure `sse_reader.close()` is called.
