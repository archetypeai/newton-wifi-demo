---
name: newton-machine-state-from-sensor
description: Run a Machine State Lens by streaming real-time data from a physical sensor (BLE, USB, UDP, or recording playback). Use when doing real-time machine state classification from live sensor hardware.
argument-hint: [source-type]
---

# Newton Machine State Lens — Stream from Sensor

Generate a script that streams real-time IMU sensor data to the Archetype AI Machine State Lens for live n-shot state classification. Supports both Python and JavaScript/Web.

## Frontend Architecture

Decompose the UI into components. See `@rules/frontend-architecture` for conventions.

### Recommended decomposition

| UI Area | Component | Pattern/Primitives | Key Props |
|---------|-----------|-------------------|-----------|
| Sensor input | `DataInput.svelte` | BackgroundCard, Button, Input | `onselect`, `status` |
| Classification | `StateDisplay.svelte` | BackgroundCard, Badge | `currentState`, `confidence` |
| Time series | Reuse SensorChart pattern | BackgroundCard, Chart | `data[]`, `signals` |
| Results | Use FlatLogItem pattern in ScrollArea | FlatLogItem, ScrollArea | `status`, `message`, `detail` |

- Use `@skills/create-dashboard` for the page layout
- Extract streaming and session logic into `$lib/api/machine-state.js`

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
| `usb` | USB serial IMU device | `--sensor-port` (default `/dev/tty.usbmodem1101`) |
| `udp` | UDP relay (from BLE relay server) | `--udp-port` (default `5556`) |
| `recording` | Replay a CSV recording | `--file-path` |

### Architecture

#### 1. API Client & N-Shot Setup

```python
from archetypeai.api_client import ArchetypeAI

client = ArchetypeAI(api_key, api_endpoint=api_endpoint)

# Upload n-shot files, derive class names from filenames
n_shot_files = {}
for file_path in args.n_shot_files:
    class_name = Path(file_path).stem.upper()
    resp = client.files.local.upload(file_path)
    n_shot_files[class_name] = resp["file_id"]
```

#### 2. Lens YAML Config

Same YAML structure as file-based, with dynamic `input_n_shot` built from uploaded files:

```python
n_shot_yaml_lines = []
for class_name, file_id in n_shot_files.items():
    n_shot_yaml_lines.append(f"      {class_name}: {file_id}")
n_shot_yaml = "\n".join(n_shot_yaml_lines)
```

Insert into the YAML template under `model_parameters.input_n_shot`.

#### 3. ImuReceiver — Multi-Source Data Acquisition

Create an `ImuReceiver` class that handles all source types with a unified interface:

```python
class ImuReceiver:
    def __init__(self, incoming_data, num_samples_per_packet=10,
                 num_sensor_packets_per_packets_out=10):
        self.packet_queue = queue.Queue()

        if 'recording' in incoming_data:
            self.source = 'recording'
            self.recording = incoming_data['recording']
        elif 'sensor' in incoming_data:
            self.source = 'sensor'
            self.port = incoming_data['sensor']
        elif 'ble' in incoming_data:
            self.source = 'ble'

    def get_data(self):
        """Returns (packet_out, timestamp) or (None, None)"""
        if self.packet_queue.qsize() >= self.num_sensor_packets_per_packets_out:
            packets = [self.packet_queue.get()
                       for _ in range(self.num_sensor_packets_per_packets_out)]
            packet_out = np.vstack([p['data'] for p in packets]).tolist()
            return packet_out, packets[-1]['sensor_timestamp']
        return None, None
```

##### BLE Acquisition (async)

```python
async def acquire_ble(self, exception_holder):
    scanner = bleak.BleakScanner(
        detection_callback=self.detection_callback,
        service_uuids=[IMU_SERVICE_UUID]
    )
    await scanner.start()
    await asyncio.sleep(5)
    await scanner.stop()

    async with bleak.BleakClient(self.the_device) as client:
        await client.start_notify(IMU_CHARACTERISTIC_UUID, self.notify_callback)
        while client.is_connected:
            await asyncio.sleep(1)

def notify_callback(self, handle, data):
    samples = np.frombuffer(data, dtype=np.int16)
    header = samples[0]
    payload = samples[1:]
    imu = payload.reshape(-1, 3)  # (n, 3) — ax, ay, az
    self.packet_queue.put({"data": imu, "sensor_timestamp": time.time()})
```

##### USB Acquisition (threaded)

```python
def acquire_usb(self, exception_holder):
    port = serial.Serial(self.port, 115200, timeout=5.0)
    port.read(2)  # device ID
    port.write(bytearray([0x47]))  # Go signal

    while True:
        raw = port.read(self.num_samples_per_packet * 2)
        samples = list(array.array('h', raw))
        self.packet_queue.put({
            "data": np.array(samples),
            "sensor_timestamp": time.time()
        })
```

##### UDP Acquisition (threaded)

```python
class UdpImuReceiver:
    """Drop-in replacement for ImuReceiver using UDP relay data"""
    def __init__(self, port=5556):
        self.port = port
        self.packet_queue = queue.Queue()

    def _receive_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', self.port))
        sock.settimeout(0.5)

        while self.running:
            try:
                data, _ = sock.recvfrom(4096)
                packet = json.loads(data.decode('utf-8'))
                imu = np.array(packet['data'], dtype=np.int16)
                self.packet_queue.put({
                    "data": imu,
                    "sensor_timestamp": packet['timestamp']
                })
            except socket.timeout:
                continue
```

#### 4. Real-Time Streaming with Buffering

Use a `deque` to buffer incoming sensor data and stream windows to the API:

```python
from collections import deque

data_buffer = deque(maxlen=window_size * 2)

while not stop_event.is_set():
    packet_out, packet_timestamp = imu_receiver.get_data()

    if packet_out is not None:
        for row in packet_out:
            data_buffer.append((int(row[0]), int(row[1]), int(row[2])))

        if len(data_buffer) >= window_size:
            window_rows = list(data_buffer)[-window_size:]

            a1 = [r[0] for r in window_rows]
            a2 = [r[1] for r in window_rows]
            a3 = [r[2] for r in window_rows]
            a4 = [int((ax**2 + ay**2 + az**2) ** 0.5)
                  for ax, ay, az in window_rows]

            payload = {
                "type": "session.update",
                "event_data": {
                    "type": "data.json",
                    "event_data": {
                        "sensor_data": [a1, a2, a3, a4],
                        "sensor_metadata": {
                            "sensor_timestamp": packet_timestamp,
                            "sensor_id": f"imu_sensor_{counter}"
                        }
                    }
                }
            }
            client.lens.sessions.process_event(session_id, payload)

            # Advance by step_size
            for _ in range(min(step_size, len(data_buffer))):
                data_buffer.popleft()
```

#### 5. SSE Event Listening

```python
sse_reader = client.lens.sessions.create_sse_consumer(
    session_id, max_read_time_sec=max_run_time_sec
)

for event in sse_reader.read(block=True):
    if event.get("type") == "inference.result":
        result = event["event_data"].get("response")
        print(f"Predicted: {result}")
```

#### 6. Threading Model

```
Main Thread:  session_callback → starts SSE listener
Thread 1:     ImuReceiver (BLE async / USB serial / UDP socket)
Thread 2:     Streaming loop (buffer → API)
              Optional: CSV recording of session data
```

- BLE uses `asyncio.run()` in a daemon thread
- USB/recording use `threading.Thread(target=..., daemon=True)`
- Graceful shutdown via `signal.SIGINT` → `stop_event.set()`

#### 7. Optional: Record Session Data

Save streamed data to CSV for later replay or analysis:

```python
csv_filename = f"sessions/session_data_{timestamp}.csv"
writer.writerow(['timestamp', 'a1', 'a2', 'a3', 'a4'])

for ax, ay, az in window_rows:
    mag = int((ax**2 + ay**2 + az**2) ** 0.5)
    writer.writerow([time.time(), ax, ay, az, mag])
```

### CLI Arguments to Include

```
--api-key              API key (fallback to ATAI_API_KEY env var)
--api-endpoint         API endpoint (default from SDK)
--source-type          {ble, usb, recording, udp} (required)
--file-path            Recording file path (for recording mode)
--sensor-port          USB serial port (default: /dev/tty.usbmodem1101)
--udp-port             UDP relay port (default: 5556)
--n-shot-files         Paths to n-shot example CSVs (required, nargs='+')
--window-size          Window size in samples (default: 100)
--step-size-n-shot     Training step size (default: 100)
--step-size-inference  Inference step size (default: 100)
--max-run-time-sec     Max runtime (default: 500)
```

### Example Usage

```bash
# From UDP relay
python stream_from_sensor.py --source-type udp \
  --n-shot-files healthy.csv broken.csv

# From BLE device
python stream_from_sensor.py --source-type ble \
  --n-shot-files holding.csv walking.csv sitting.csv

# Replay a recording
python stream_from_sensor.py --source-type recording \
  --file-path data.csv --n-shot-files healthy.csv broken.csv
```

---

## Web / JavaScript Implementation

Uses direct `fetch` calls to the Archetype AI REST API with Web Bluetooth API or WebSocket for sensor data. Based on the working pattern from `test-stream/src/lib/atai-client.ts`.

### Requirements

- `@microsoft/fetch-event-source` for SSE consumption
- Web Bluetooth API (Chrome/Edge) for BLE sensors
- WebSocket support for UDP relay via WebSocket bridge

### Supported Web Source Types

| Source | Web API | Notes |
|--------|---------|-------|
| `ble` | Web Bluetooth API | Chrome/Edge only, requires HTTPS |
| `websocket` | WebSocket | Connect to a UDP-to-WebSocket bridge |
| `file` | File API | Replay a CSV recording from file input |

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
  formData.append('file', file)

  const response = await fetch(`${API_ENDPOINT}/files`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${apiKey}` },
    body: formData,
  })
  const result = await response.json()
  nShotMap[className.toUpperCase()] = result.file_id
}
```

### Step 2: Register lens, create session, wait for ready

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

### Step 3: Acquire sensor data (Web Bluetooth)

```typescript
const IMU_SERVICE = '0000fff0-0000-1000-8000-00805f9b34fb'
const IMU_CHARACTERISTIC = '0000fff1-0000-1000-8000-00805f9b34fb'

// Request BLE device (requires user gesture)
const device = await navigator.bluetooth.requestDevice({
  filters: [{ services: [IMU_SERVICE] }],
})
const server = await device.gatt.connect()
const service = await server.getPrimaryService(IMU_SERVICE)
const characteristic = await service.getCharacteristic(IMU_CHARACTERISTIC)

// Buffer for incoming samples
const dataBuffer: [number, number, number][] = []

characteristic.addEventListener('characteristicvaluechanged', (event) => {
  const value = (event.target as BluetoothRemoteGATTCharacteristic).value!
  const samples = new Int16Array(value.buffer)

  // Skip header byte, parse (ax, ay, az) triplets
  const payload = samples.slice(1)
  for (let i = 0; i + 2 < payload.length; i += 3) {
    dataBuffer.push([payload[i], payload[i + 1], payload[i + 2]])
  }
})

await characteristic.startNotifications()
```

### Step 4: Stream buffered data in windows

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
}, 200) // check every 200ms
```

### Step 5: Acquire sensor data (WebSocket bridge)

Alternative for UDP relay — connect to a WebSocket bridge that forwards UDP packets:

```typescript
const ws = new WebSocket('ws://localhost:8765')

ws.onmessage = (event) => {
  const packet = JSON.parse(event.data)
  // packet.data is [[ax, ay, az], ...] from UDP relay
  for (const [ax, ay, az] of packet.data) {
    dataBuffer.push([ax, ay, az])
  }
}
```

### Step 6: Consume SSE results

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
      console.log(`Predicted: ${result}`)
    }

    if (parsed.type === 'sse.stream.end') {
      console.log('Stream complete')
    }
  },
})
```

### Step 7: Cleanup

```typescript
clearInterval(streamLoop)
abortController.abort()
await device.gatt.disconnect()
await apiPost('/lens/sessions/destroy', apiKey, { session_id: sessionId })
```

### Web Lifecycle Summary

```
1. Upload n-shot CSVs        ->  POST /files  (FormData, one per class)
2. Register lens              ->  POST /lens/register  { lens_config: config }
3. Create session             ->  POST /lens/sessions/create  { lens_id }
4. Wait for ready             ->  POST /lens/sessions/events/process  { session_id, event: { type: 'session.status' } }
5. (Optional) Delete lens     ->  POST /lens/delete  { lens_id }
6. Connect sensor (BLE / WS)  ->  Web Bluetooth API or WebSocket
7. Buffer + stream windows    ->  POST /lens/sessions/events/process  { session_id, event }  (loop)
8. Consume SSE results        ->  GET /lens/sessions/consumer/{sessionId}
9. Disconnect + destroy       ->  POST /lens/sessions/destroy  { session_id }
```

---

## CSV Format Expected

```csv
timestamp,a1,a2,a3,a4
1700000000.0,100,200,300,374
```

- `timestamp`: UNIX epoch float
- `a1, a2, a3`: Sensor axes (e.g., accelerometer x, y, z)
- `a4`: Magnitude (sqrt(a1² + a2² + a3²))

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
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
results_file = results_dir / f"sensor_{args.source_type}_{timestamp}.csv"

# Write CSV header
with open(results_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['read_index', 'predicted_class', 'confidence_scores',
                     'file_id', 'window_size', 'total_rows'])

# Inside the SSE event loop, when handling inference.result:
if event.get("type") == "inference.result":
    ed = event.get("event_data", {})
    result = ed.get("response")
    meta = ed.get("query_metadata", {})
    query_meta = meta.get("query_metadata", {})

    predicted_class = result[0] if isinstance(result, list) and len(result) > 0 else "unknown"
    confidence_scores = result[1] if isinstance(result, list) and len(result) > 1 else {}
    read_index = query_meta.get("read_index", "N/A")
    file_id = query_meta.get("file_id", "N/A")
    window_size_val = query_meta.get("window_size", "N/A")
    total_rows = query_meta.get("total_rows", "N/A")

    print(f"[{read_index}] Predicted: {predicted_class} | Scores: {confidence_scores}")

    with open(results_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow([read_index, predicted_class, str(confidence_scores),
                         file_id, window_size_val, total_rows])
```

### Response Structure

The `inference.result` response contains:
- `response[0]`: predicted class name (string, e.g. `"HEALTHY"`)
- `response[1]`: confidence scores dict (e.g. `{"HEALTHY": 0.95, "BROKEN": 0.05}`)
- `query_metadata.query_metadata.read_index`: window position in the data
- `query_metadata.query_metadata.file_id`: reference file ID
- `query_metadata.query_metadata.window_size`: window size used
- `query_metadata.query_metadata.total_rows`: total rows processed

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

- Default `window_size` and `step_size`: **100**
- N-shot class names derived from filename stems (e.g., `healthy.csv` → `HEALTHY`)
- Python: `signal.SIGINT` for graceful shutdown
- Web: `AbortController` for SSE, `clearInterval` for stream loop, `gatt.disconnect()` for BLE
- Web Bluetooth requires HTTPS and a user gesture to initiate pairing
- For WebSocket bridge, run a small relay server that forwards UDP broadcast to WebSocket clients
