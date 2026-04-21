"""
Preprocess GHOST-IoT wlan0 flow data into 15-minute snapshot frames.

Reads: data/ghost-iot/wlan0_ipv4_flows_db.csv
Writes:
  data/processed/session-01/manifest.json
  data/processed/session-01/frames/{0000.json, 0001.json, ...}

Each frame is a JSON snapshot of the home's WiFi state at a given 15-min window,
modeled after the Xfinity `wifi_status_report` schema:

  {
    "window_start": "2019-10-10T11:30:00Z",
    "window_end":   "2019-10-10T11:45:00Z",
    "gateway_mac": "13d35af5c06b",
    "devices": [
      {
        "mac": "d96b0fddf228",
        "label": "Device A",
        "online": true,
        "up_bytes_quarter": 12345,       # bytes device sent in this 15-min window
        "down_bytes_quarter": 67890,     # bytes device received
        "up_packets_quarter": 42,
        "down_packets_quarter": 100,
        "flows_quarter": 5,
        "protocols": ["HTTP", "DNS"]
      },
      ...
    ]
  }
"""

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

WINDOW_SIZE_S = 15 * 60  # 15 minutes
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "data" / "ghost-iot" / "wlan0_ipv4_flows_db.csv"
OUT = ROOT / "data" / "processed" / "session-01"


def load_flows():
    """Read flows and return list of parsed rows."""
    rows = []
    with SRC.open() as f:
        for row in csv.DictReader(f):
            mac_a = row["mac_a"].strip()
            mac_b = row["mac_b"].strip()
            ts_start = row["ts_start"].strip()
            ts_end = row["ts_end"].strip()
            if not (mac_a and mac_b and ts_start and ts_end):
                continue
            rows.append({
                "mac_a": mac_a,
                "mac_b": mac_b,
                "ts_start": float(ts_start),
                "ts_end": float(ts_end),
                "bytes_a": int(row["bytes_a"] or 0),
                "bytes_b": int(row["bytes_b"] or 0),
                "packets_a": int(row["packets_a"] or 0),
                "packets_b": int(row["packets_b"] or 0),
                "prot": row["prot"].strip() or "Unknown",
            })
    return rows


def identify_gateway(rows):
    """Gateway = MAC appearing as an endpoint in the most flows."""
    c = Counter()
    for r in rows:
        c[r["mac_a"]] += 1
        c[r["mac_b"]] += 1
    gateway, _ = c.most_common(1)[0]
    return gateway


def assign_labels(rows, gateway):
    """Deterministic Device A/B/C... labels for client MACs, ordered by flow count."""
    c = Counter()
    for r in rows:
        for mac in (r["mac_a"], r["mac_b"]):
            if mac != gateway:
                c[mac] += 1
    labels = {}
    for i, (mac, _) in enumerate(c.most_common()):
        labels[mac] = f"Device {chr(ord('A') + i)}"
    return labels


def window_index(ts, session_start):
    return int((ts - session_start) // WINDOW_SIZE_S)


def aggregate_windows(rows, gateway, labels):
    """Bucket flows into 15-min windows, per-client."""
    session_start = min(r["ts_start"] for r in rows)
    session_end = max(r["ts_end"] for r in rows)
    n_windows = int((session_end - session_start) // WINDOW_SIZE_S) + 1

    # windows[w][mac] = {up_bytes, down_bytes, up_packets, down_packets, flows, prots}
    windows = [defaultdict(lambda: {
        "up_bytes": 0,
        "down_bytes": 0,
        "up_packets": 0,
        "down_packets": 0,
        "flows": 0,
        "prots": set(),
    }) for _ in range(n_windows)]

    for r in rows:
        # Determine the client MAC and the direction
        if r["mac_a"] == gateway:
            client = r["mac_b"]
            up_bytes, down_bytes = r["bytes_b"], r["bytes_a"]
            up_packets, down_packets = r["packets_b"], r["packets_a"]
        elif r["mac_b"] == gateway:
            client = r["mac_a"]
            up_bytes, down_bytes = r["bytes_a"], r["bytes_b"]
            up_packets, down_packets = r["packets_a"], r["packets_b"]
        else:
            # Peer-to-peer flow (no gateway endpoint) — attribute to mac_a as client
            client = r["mac_a"]
            up_bytes, down_bytes = r["bytes_a"], r["bytes_b"]
            up_packets, down_packets = r["packets_a"], r["packets_b"]

        if client not in labels:
            continue

        w = window_index(r["ts_start"], session_start)
        if 0 <= w < n_windows:
            b = windows[w][client]
            b["up_bytes"] += up_bytes
            b["down_bytes"] += down_bytes
            b["up_packets"] += up_packets
            b["down_packets"] += down_packets
            b["flows"] += 1
            b["prots"].add(r["prot"])

    return windows, session_start, session_end


def write_frames(windows, session_start, gateway, labels):
    frames_dir = OUT / "frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    all_clients = sorted(labels.keys(), key=lambda m: labels[m])
    frame_files = []

    for i, window in enumerate(windows):
        ws = session_start + i * WINDOW_SIZE_S
        we = ws + WINDOW_SIZE_S

        devices = []
        for mac in all_clients:
            b = window.get(mac)
            if b is None:
                devices.append({
                    "mac": mac,
                    "label": labels[mac],
                    "online": False,
                    "up_bytes_quarter": 0,
                    "down_bytes_quarter": 0,
                    "up_packets_quarter": 0,
                    "down_packets_quarter": 0,
                    "flows_quarter": 0,
                    "protocols": [],
                })
            else:
                devices.append({
                    "mac": mac,
                    "label": labels[mac],
                    "online": True,
                    "up_bytes_quarter": b["up_bytes"],
                    "down_bytes_quarter": b["down_bytes"],
                    "up_packets_quarter": b["up_packets"],
                    "down_packets_quarter": b["down_packets"],
                    "flows_quarter": b["flows"],
                    "protocols": sorted(b["prots"]),
                })

        frame = {
            "window_index": i,
            "window_start": datetime.fromtimestamp(ws, tz=timezone.utc).isoformat(),
            "window_end": datetime.fromtimestamp(we, tz=timezone.utc).isoformat(),
            "window_start_epoch": ws,
            "gateway_mac": gateway,
            "devices": devices,
        }

        name = f"{i:04d}.json"
        (frames_dir / name).write_text(json.dumps(frame, indent=2))
        frame_files.append(f"frames/{name}")

    return frame_files


def write_manifest(frame_files, session_start, session_end, gateway, labels, windows):
    # Per-device totals across the session
    client_totals = defaultdict(lambda: {"online_windows": 0, "total_flows": 0, "total_bytes": 0})
    for w in windows:
        for mac, b in w.items():
            client_totals[mac]["online_windows"] += 1
            client_totals[mac]["total_flows"] += b["flows"]
            client_totals[mac]["total_bytes"] += b["up_bytes"] + b["down_bytes"]

    devices = []
    for mac in sorted(labels.keys(), key=lambda m: labels[m]):
        t = client_totals[mac]
        devices.append({
            "mac": mac,
            "label": labels[mac],
            "online_windows": t["online_windows"],
            "total_flows": t["total_flows"],
            "total_bytes": t["total_bytes"],
        })

    # Per-window activity summary (for timeline navigation in the UI)
    activity = []
    active_indices = []
    for i, w in enumerate(windows):
        n_online = sum(1 for b in w.values() if b["flows"] > 0)
        total_bytes = sum(b["up_bytes"] + b["down_bytes"] for b in w.values())
        activity.append({
            "window_index": i,
            "n_online": n_online,
            "total_bytes": total_bytes,
        })
        if n_online > 0:
            active_indices.append(i)

    # Highlight indices: every active window plus 2 windows of context on each side.
    highlight_set = set()
    for idx in active_indices:
        for j in range(max(0, idx - 2), min(len(windows), idx + 3)):
            highlight_set.add(j)
    highlights = sorted(highlight_set)

    manifest = {
        "dataset": "GHOST-IoT wlan0 flows",
        "source_paper": "https://doi.org/10.3390/s20226600",
        "session_start": datetime.fromtimestamp(session_start, tz=timezone.utc).isoformat(),
        "session_end": datetime.fromtimestamp(session_end, tz=timezone.utc).isoformat(),
        "session_start_epoch": session_start,
        "session_end_epoch": session_end,
        "window_size_s": WINDOW_SIZE_S,
        "n_windows": len(frame_files),
        "gateway_mac": gateway,
        "devices": devices,
        "activity": activity,
        "highlights": highlights,
        "frames": frame_files,
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def write_events(rows, gateway, labels, session_start):
    """Emit per-flow event stream, sorted by ts_start, one JSON per line."""
    events = []
    for r in rows:
        # Determine client + direction
        if r["mac_a"] == gateway:
            client, up_b, down_b, up_p, down_p = (
                r["mac_b"], r["bytes_b"], r["bytes_a"], r["packets_b"], r["packets_a"]
            )
        elif r["mac_b"] == gateway:
            client, up_b, down_b, up_p, down_p = (
                r["mac_a"], r["bytes_a"], r["bytes_b"], r["packets_a"], r["packets_b"]
            )
        else:
            client, up_b, down_b, up_p, down_p = (
                r["mac_a"], r["bytes_a"], r["bytes_b"], r["packets_a"], r["packets_b"]
            )

        if client not in labels:
            continue

        events.append({
            "t": round(r["ts_start"] - session_start, 3),  # seconds since session start
            "t_end": round(r["ts_end"] - session_start, 3),
            "ts_start": r["ts_start"],
            "ts_end": r["ts_end"],
            "mac": client,
            "label": labels[client],
            "protocol": r["prot"],
            "up_bytes": up_b,
            "down_bytes": down_b,
            "up_packets": up_p,
            "down_packets": down_p,
        })

    events.sort(key=lambda e: e["ts_start"])

    path = OUT / "events.jsonl"
    with path.open("w") as f:
        for ev in events:
            f.write(json.dumps(ev) + "\n")

    return path, len(events)


def main():
    if not SRC.exists():
        raise SystemExit(f"Missing source file: {SRC}")

    print(f"Reading {SRC.name}...")
    rows = load_flows()
    print(f"  {len(rows)} flows")

    gateway = identify_gateway(rows)
    print(f"Gateway MAC: {gateway}")

    labels = assign_labels(rows, gateway)
    print(f"Clients: {len(labels)}")
    for mac, label in labels.items():
        print(f"  {label}: {mac}")

    print(f"\nAggregating into {WINDOW_SIZE_S // 60}-minute windows...")
    windows, session_start, session_end = aggregate_windows(rows, gateway, labels)
    duration_h = (session_end - session_start) / 3600
    print(f"  {len(windows)} windows across {duration_h:.1f} hours ({duration_h/24:.2f} days)")

    OUT.mkdir(parents=True, exist_ok=True)
    frame_files = write_frames(windows, session_start, gateway, labels)
    print(f"\nWrote {len(frame_files)} frames to {OUT / 'frames'}")

    manifest = write_manifest(frame_files, session_start, session_end, gateway, labels, windows)
    print(f"Wrote manifest: {OUT / 'manifest.json'}")

    events_path, n_events = write_events(rows, gateway, labels, session_start)
    print(f"Wrote {n_events} events: {events_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
