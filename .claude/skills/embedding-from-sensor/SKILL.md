---
name: embedding-from-sensor
description: Run an Embedding Lens by streaming real-time data from a physical sensor (BLE, USB, UDP, or recording playback). Use when extracting live embeddings from sensor hardware for real-time visualization or clustering.
argument-hint: [source-type]
---

# Embedding Lens — Stream from Sensor

Generate a script that streams real-time IMU sensor data to the Archetype AI Embedding Lens for live embedding extraction. Supports both Python and JavaScript/Web.

## Frontend Architecture

Decompose the UI into components. See `@rules/frontend-architecture` for conventions.

### Recommended decomposition

| UI Area | Component | Pattern/Primitives | Key Props |
|---------|-----------|-------------------|-----------|
| Sensor input | `DataInput.svelte` | BackgroundCard, Button, Input | `onselect`, `status` |
| Scatter plot | Reuse ScatterChart pattern | BackgroundCard, Chart | `data[]`, `categories` |
| Progress | `StreamProgress.svelte` | BackgroundCard, Progress | `current`, `total` |

- Use `@skills/create-dashboard` for the page layout
- Extract streaming and session logic into `$lib/api/embeddings.js`

---

## Python Implementation

### Requirements

- `archetypeai` Python package
- `numpy`
- `bleak` (for BLE sources)
- `pyserial` (for USB sources)
- Environment variables: `ATAI_API_KEY`, optionally `ATAI_API_ENDPOINT`

### Supported Source Types

| Source | Description | Extra args |
|--------|-------------|------------|
| `ble` | Bluetooth Low Energy IMU device | None (auto-discovers) |
| `usb` | USB serial IMU device | `--sensor-port` |
| `udp` | UDP relay (from BLE relay server) | `--udp-port` |
| `recording` | Replay a CSV recording | `--file-path` |

### Architecture

#### 1. API Client Setup

```python
from archetypeai.api_client import ArchetypeAI

client = ArchetypeAI(api_key, api_endpoint=api_endpoint)
```

#### 2. Lens YAML Config

No n-shot files or KNN config — just the embedding processor:

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

#### 3. ImuReceiver — Multi-Source Data Acquisition

Same `ImuReceiver` class as the machine state sensor skill:

```python
class ImuReceiver:
    def __init__(self, incoming_data, num_samples_per_packet=10,
                 num_sensor_packets_per_packets_out=10):
        self.packet_queue = queue.Queue()
        # ... source detection (recording/sensor/ble)

    def get_data(self):
        """Returns (packet_out, timestamp) or (None, None)"""
        if self.packet_queue.qsize() >= self.num_sensor_packets_per_packets_out:
            packets = [self.packet_queue.get()
                       for _ in range(self.num_sensor_packets_per_packets_out)]
            packet_out = np.vstack([p['data'] for p in packets]).tolist()
            return packet_out, packets[-1]['sensor_timestamp']
        return None, None
```

See the machine-state-from-sensor skill for full BLE/USB/UDP acquisition implementations.

#### 4. Real-Time Streaming with Buffering

```python
from collections import deque

data_buffer = deque(maxlen=window_size * 4)
embeddings = []

while not stop_event.is_set():
    packet_out, packet_timestamp = imu_receiver.get_data()

    if packet_out is not None:
        for row in packet_out[:, :3] if hasattr(packet_out, 'shape') else packet_out:
            ax, ay, az = int(row[0]), int(row[1]), int(row[2])
            a4 = int((ax*ax + ay*ay + az*az) ** 0.5)
            data_buffer.append((ax, ay, az, a4))

        if len(data_buffer) >= window_size:
            window_rows = list(data_buffer)[:window_size]

            a1 = [r[0] for r in window_rows]
            a2 = [r[1] for r in window_rows]
            a3 = [r[2] for r in window_rows]
            a4 = [r[3] for r in window_rows]

            payload = {
                "type": "session.update",
                "event_data": {
                    "type": "data.json",
                    "event_data": {
                        "sensor_data": [a1, a2, a3, a4],
                        "sensor_metadata": {
                            "sensor_timestamp": packet_timestamp,
                            "sensor_id": f"live_sensor_{counter}"
                        }
                    }
                }
            }
            client.lens.sessions.process_event(session_id, payload)

            # Advance by step_size
            for _ in range(min(step_size, len(data_buffer))):
                data_buffer.popleft()
```

#### 5. SSE Event Listening — Collect Embeddings

```python
sse_reader = client.lens.sessions.create_sse_consumer(
    session_id, max_read_time_sec=max_run_time_sec
)

for event in sse_reader.read(block=True):
    if event.get("type") == "inference.result":
        embedding = event["event_data"].get("response")

        # Flatten 4×768 → 3072D
        if isinstance(embedding, list) and len(embedding) > 0:
            if isinstance(embedding[0], list):
                flat = [val for row in embedding for val in row]
            else:
                flat = embedding

        embeddings.append(flat)
        print(f"Embedding {len(embeddings)}: {len(flat)}D")
```

#### 6. Threading Model

```
Main Thread:  session_callback → starts SSE listener
Thread 1:     ImuReceiver (BLE async / USB serial / UDP socket)
Thread 2:     Streaming loop (buffer → API)
```

### Embedding Response Structure

- `response`: nested list `(4, 768)` — one 768D vector per channel (a1, a2, a3, a4)
- Flatten to `3072D` by concatenating rows
- `query_metadata.sensor_id`: which sensor window this came from

### CLI Arguments

```
--api-key              API key (fallback to ATAI_API_KEY env var)
--api-endpoint         API endpoint (default from SDK)
--source-type          {ble, usb, recording, udp} (required)
--file-path            Recording file path (for recording mode)
--sensor-port          USB serial port (default: /dev/tty.usbmodem1101)
--udp-port             UDP relay port (default: 5556)
--window-size          Window size in samples (default: 100)
--step-size            Step size in samples (default: 100)
--max-run-time-sec     Max runtime (default: 500)
--output-file          Path to save embeddings CSV (optional)
```

---

## Web / JavaScript Implementation

Uses direct `fetch` calls to the Archetype AI REST API with Web Bluetooth API or WebSocket for sensor data.

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

### Step 1: Register embedding lens and create session

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

// Wait for session ready (same waitForSessionReady as machine state skills)
```

### Step 2: Acquire sensor data (Web Bluetooth)

```typescript
const IMU_SERVICE = '0000fff0-0000-1000-8000-00805f9b34fb'
const IMU_CHARACTERISTIC = '0000fff1-0000-1000-8000-00805f9b34fb'

const device = await navigator.bluetooth.requestDevice({
  filters: [{ services: [IMU_SERVICE] }],
})
const server = await device.gatt.connect()
const service = await server.getPrimaryService(IMU_SERVICE)
const characteristic = await service.getCharacteristic(IMU_CHARACTERISTIC)

const dataBuffer: [number, number, number][] = []

characteristic.addEventListener('characteristicvaluechanged', (event) => {
  const value = (event.target as BluetoothRemoteGATTCharacteristic).value!
  const samples = new Int16Array(value.buffer)
  const payload = samples.slice(1)
  for (let i = 0; i + 2 < payload.length; i += 3) {
    dataBuffer.push([payload[i], payload[i + 1], payload[i + 2]])
  }
})

await characteristic.startNotifications()
```

### Step 3: Stream buffered data in windows

```typescript
let counter = 0

const streamLoop = setInterval(async () => {
  if (dataBuffer.length < windowSize) return

  const window = dataBuffer.splice(0, windowSize)

  const a1 = window.map(r => r[0])
  const a2 = window.map(r => r[1])
  const a3 = window.map(r => r[2])
  const a4 = window.map(([ax, ay, az]) =>
    Math.floor(Math.sqrt(ax * ax + ay * ay + az * az))
  )

  await apiPost('/lens/sessions/events/process', apiKey, {
    session_id: sessionId,
    event: {
      type: 'session.update',
      event_data: {
        type: 'data.json',
        event_data: {
          sensor_data: [a1, a2, a3, a4],
          sensor_metadata: {
            sensor_timestamp: Date.now() / 1000,
            sensor_id: `web_ble_sensor_${counter++}`,
          },
        },
      },
    },
  }, 10000)
}, 200)
```

### Step 4: Consume SSE embedding results

```typescript
import { fetchEventSource } from '@microsoft/fetch-event-source'

interface EmbeddingResult {
  windowIndex: number
  embedding: number[]
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
      const flat = Array.isArray(response[0]) ? response.flat() : response

      embeddings.push({
        windowIndex: embeddings.length,
        embedding: flat,
      })
      console.log(`Embedding ${embeddings.length}: ${flat.length}D`)
    }
  },
})
```

### Step 5: Cleanup

```typescript
clearInterval(streamLoop)
abortController.abort()
await device.gatt.disconnect()
await apiPost('/lens/sessions/destroy', apiKey, { session_id: sessionId })
```

### Web Lifecycle Summary

```
1. Register lens              ->  POST /lens/register  { lens_config: config }
2. Create session             ->  POST /lens/sessions/create  { lens_id }
3. Wait for ready             ->  POST /lens/sessions/events/process  (poll)
4. Connect sensor (BLE / WS)  ->  Web Bluetooth API or WebSocket
5. Buffer + stream windows    ->  POST /lens/sessions/events/process  (loop)
6. Consume SSE embeddings     ->  GET /lens/sessions/consumer/{sessionId}
7. Disconnect + destroy       ->  POST /lens/sessions/destroy  { session_id }
```

---

## Key Implementation Notes

- Default `window_size` and `step_size`: **100**
- Embeddings are `(4, 768)` per window — flatten to `3072D` for downstream use
- No n-shot files needed — this lens outputs raw embeddings, not classifications
- Use UMAP or t-SNE to reduce to 2D/3D for visualization
- Combine with machine state lens to overlay class labels on embedding plots
