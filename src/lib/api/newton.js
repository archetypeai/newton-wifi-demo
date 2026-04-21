/**
 * Client-side wrappers around the server's API endpoints.
 * The server handles the direct call to Newton /v0.5/query.
 */

/** Fetch the session manifest (device inventory, activity timeline, highlights, frame index). */
export async function loadManifest() {
	const res = await fetch('/api/manifest');
	if (!res.ok) throw new Error(`Failed to load manifest: ${res.status}`);
	return res.json();
}

/** Fetch a single frame by index. */
export async function loadFrame(index) {
	const res = await fetch(`/api/frame/${index}`);
	if (!res.ok) throw new Error(`Failed to load frame ${index}: ${res.status}`);
	return res.json();
}

/** Fetch the full per-flow event stream (sorted by ts_start). */
export async function loadEvents() {
	const res = await fetch('/api/events');
	if (!res.ok) throw new Error(`Failed to load events: ${res.status}`);
	return res.json();
}

/**
 * Ask Newton to classify each device in the snapshot.
 * Returns { predictions: [{label, verdict, confidence, reason}, ...], raw, timestamp }.
 */
export async function predictDevices(frame) {
	const res = await fetch('/api/predict-devices', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ frame })
	});
	if (!res.ok) {
		const err = await res.json().catch(() => ({}));
		throw new Error(err.error || 'Prediction failed');
	}
	return res.json();
}

/**
 * Send a 15-minute snapshot frame (JSON) to Newton for occupancy analysis.
 */
export async function analyze(frame, query) {
	return postFrame('/api/analyze', frame, query);
}

/**
 * Send a 30-second rolling-window frame (JSON) to Newton for occupancy analysis.
 * Uses a different system prompt tuned to the shorter window.
 */
export async function analyzeRealtime(frame, query) {
	return postFrame('/api/analyze-realtime', frame, query);
}

async function postFrame(url, frame, query) {
	const body = { frame };
	if (query) body.query = query;
	const res = await fetch(url, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(body)
	});
	if (!res.ok) {
		const err = await res.json().catch(() => ({}));
		throw new Error(err.error || 'Analysis failed');
	}
	return res.json();
}
