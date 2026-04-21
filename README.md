# Newton WiFi Demo

A replay-style demo that asks **"is anyone home?"** from real residential WiFi device-telemetry, powered by [Newton](https://www.archetypeai.dev/).

The app walks through a real 10-day smart-home WiFi capture one window at a time. Each window is a JSON snapshot of every device seen by the home gateway — which MACs were online, how much they sent and received, and which protocols they spoke. Newton reads the snapshot and returns both an overall occupancy verdict and a per-device classification, side-by-side with ground truth.

## Two playback modes

- **15-min** — aggregated 15-minute snapshots matching the cadence of a Comcast-style `wifi_status_report`. Auto-advance through the 61 windows with any device activity, or scrub the full 962-window session.
- **Realtime** — rolling window whose width tracks the analysis cadence (1 s / 2 s / 5 s / 10 s / 30 s). Newton fires on a wall-clock tick, reasoning over a fresh, non-overlapping slice each call.

## Data attribution

This demo uses the **GHOST-IoT** dataset by Anagnostopoulos, Spathoulas, Viaño, and Augusto-Gonzalez (2020), released under the MDPI open-access license.

> Anagnostopoulos, M.; Spathoulas, G.; Viaño, B.; Augusto-Gonzalez, J. **Tracing Your Smart-Home Devices Conversations: A Real World IoT Traffic Data-Set.** *Sensors* 2020, 20, 6600. [https://doi.org/10.3390/s20226600](https://doi.org/10.3390/s20226600)

- **Repository:** https://github.com/gspathoulas/ghost-iot-dataset
- **License:** academic use per the publication; see the upstream repo for specifics
- **Capture:** real smart-home deployment, multiple network interfaces, Oct 10 – 20, 2019
- **This demo uses:** only the WiFi interface (`wlan0_ipv4_flows_db.csv`)

MACs in the dataset are anonymized. We label the 9 WiFi clients as `Device A` … `Device I` in descending order of flow count. Newton reasons purely from traffic patterns — no device-type labels are given to the model.

The GHOST project was funded by the EU Horizon 2020 programme.

## Features

- **Ground Truth vs Newton** comparison card — per-device ground-truth state next to Newton's classification (`ACTIVE` / `IDLE` / `OFFLINE`) with match/mismatch badges
- **Newton Occupancy Analysis** — rolling log of per-window verdicts (`OCCUPIED` / `LIKELY_OCCUPIED` / `AMBIGUOUS` / `LIKELY_EMPTY` / `EMPTY`) with the reason Newton gave
- **Ask Newton** — interactive chat with follow-up questions; each message is tagged with the window it was about so paused conversations don't get confused with later state
- **Skip gaps** — auto-jump the playhead through long quiet stretches
- **Stale-prediction guard** — per-device Newton output is tagged with its source frame; if the displayed frame advances faster than Newton can respond, the Newton column shows a loading skeleton instead of stale text

## Stack

- **SvelteKit** with Svelte 5 runes
- **Archetype AI Design System** — semantic tokens, primitives, patterns
- **Newton `/v0.5/query` API** — JSON snapshot sent as text in the prompt; three separate endpoints (15-min analyze, realtime analyze, per-device predict) each with a purpose-built system prompt
- **Python** preprocessing (one-time) to reshape GHOST-IoT flows into snapshot frames + an event stream

## Setup

### 1. Install JS dependencies

```bash
npm install
```

### 2. Fetch and preprocess the dataset

```bash
# Clone GHOST-IoT into data/ghost-iot (the path the preprocessor expects)
mkdir -p data
git clone https://github.com/gspathoulas/ghost-iot-dataset.git data/ghost-iot

# Extract the compressed CSVs (requires unrar — `brew install rar` on macOS)
cd data/ghost-iot && unrar x data.rar && cd ../..

# Aggregate into 15-min snapshot frames + flat event stream
python3 scripts/preprocess.py
```

This writes:
- `data/processed/session-01/manifest.json` — session metadata, device inventory, per-window activity, highlight list
- `data/processed/session-01/frames/{0000..0961}.json` — one JSON per 15-min window
- `data/processed/session-01/events.jsonl` — flat per-flow event stream (used by Realtime mode)

### 3. Configure API credentials

Create `.env`:

```
ATAI_API_KEY=your_api_key_here
ATAI_API_ENDPOINT=https://api.u1.archetypeai.app/
```

### 4. Run

```bash
npm run dev
```

Open `http://localhost:5173`, then click **Play** to begin.

## Architecture

```
src/
├── routes/
│   ├── +page.svelte                      # Dashboard orchestrator
│   └── api/
│       ├── analyze/+server.js            # 15-min occupancy verdict (Newton /v0.5/query)
│       ├── analyze-realtime/+server.js   # Rolling-window occupancy verdict
│       ├── predict-devices/+server.js    # Per-device ACTIVE/IDLE/OFFLINE
│       ├── manifest/+server.js           # GET processed session manifest
│       ├── frame/[index]/+server.js      # GET single frame by index
│       └── events/+server.js             # GET full event stream (realtime mode)
├── lib/
│   ├── server/newton.js                  # Server-side Newton /query client
│   ├── api/newton.js                     # Client-side fetch wrappers
│   └── components/ui/custom/
│       ├── comparison-grid.svelte        # Ground Truth vs Newton row-by-row
│       ├── analysis-log.svelte           # Rolling occupancy verdict history
│       └── chat-panel.svelte             # Interactive Q&A with Newton

scripts/
└── preprocess.py                         # GHOST-IoT wlan0 flows → frames + events

data/                                     # git-ignored
├── ghost-iot/                            # raw dataset (after clone + unrar)
└── processed/session-01/                 # manifest.json, frames/, events.jsonl
```

## How it works

1. On load, the client fetches `manifest.json`. In realtime mode, it additionally fetches the full `events.jsonl`.
2. **15-min mode:** picking a window loads its pre-built frame from `frames/NNNN.json`. The page POSTs the frame to `/api/analyze` and `/api/predict-devices` in parallel; the first returns a window-level verdict, the second returns per-device classifications.
3. **Realtime mode:** the client maintains a `rollingFrame` derived — events from `playhead − windowSec` to `playhead`, aggregated per device, with the same shape as a 15-min frame but `_window` field names. Every tick (configurable 1–30 s wall time), the current rolling frame is sent to `/api/analyze-realtime` and `/api/predict-devices`.
4. Newton's responses are parsed client-side: the occupancy verdict via regex on the word list, per-device classifications via a strict line-based format the prompt asks for.
5. Results render in the `ComparisonGrid` (per-device) and `AnalysisLog` (per-window history). Predictions are tagged with their source frame so stale answers don't pollute a newly-advanced view.

## Customer context

This demo is modeled after the per-device telemetry Comcast gateways already emit (`wifi_status_report`) — a periodic JSON block listing every connected device with online state, RSSI, and traffic counters. GHOST-IoT doesn't include RSSI, device-type metadata, or set-top-box interaction events, so those fields are absent from this demo. The narrative: *"Newton reasons about occupancy from the data your gateway already produces — no new sensors, no wearables, no cameras."*

## Acknowledgements

- **Data:** [GHOST-IoT dataset](https://github.com/gspathoulas/ghost-iot-dataset) — Anagnostopoulos et al., *Sensors* 2020. Funded by EU Horizon 2020.
- **Model:** [Newton](https://www.archetypeai.dev/) (C2.4 7B) via Archetype AI's Query API.
