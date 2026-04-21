import { json } from '@sveltejs/kit';
import { runQuery } from '$lib/server/newton.js';

const SYSTEM_PROMPT = [
	'You are a home WiFi gateway analyst. For each device in the snapshot, INFER',
	'whether it is online and classify its activity. The online/offline state is',
	"NOT provided — you must derive it from the per-device traffic evidence.",
	'',
	'Output ONE line per device in this EXACT format:',
	'',
	'DEVICE_LABEL: VERDICT | CONFIDENCE | REASON',
	'',
	'Where:',
	'- VERDICT is exactly one of: online_active, online_idle, offline',
	'  · online_active = flows present + >10 KB traffic + user-interactive protocols (HTTPS/HTTP/streaming)',
	'  · online_idle   = flows present but only background chatter (DNS/mDNS/NTP/DHCP) and minimal bytes',
	'  · offline       = no flows observed in the window',
	'- CONFIDENCE is a decimal 0.0–1.0',
	'- REASON is a short phrase (no pipe characters, under 120 chars)',
	'',
	'Output one line per device, IN THE EXACT ORDER they appear in the snapshot.',
	'No preamble. No trailing commentary. No markdown. No code fences.'
].join('\n');

const USER_PROMPT_PREFIX =
	'Classify each device in this WiFi snapshot (online state has been withheld — infer it).\n\nSnapshot (JSON):\n';

/**
 * Strip the `online` field from every device so Newton has to infer it.
 * Everything else (bytes, packets, flows, protocols) stays.
 */
function redactOnline(frame) {
	return {
		...frame,
		devices: frame.devices.map((d) => {
			// eslint-disable-next-line no-unused-vars
			const { online: _online, ...rest } = d;
			return rest;
		})
	};
}

const LINE_RE =
	/^\s*(Device\s+[A-Z]+)\s*:\s*(online_active|online_idle|offline)\s*\|\s*([\d.]+)\s*\|\s*(.+?)\s*$/i;

function parsePredictions(text, frame) {
	const labels = new Set(frame.devices.map((d) => d.label));
	const out = new Map();

	for (const rawLine of text.split('\n')) {
		const m = rawLine.match(LINE_RE);
		if (!m) continue;
		const label = m[1].replace(/\s+/g, ' ').trim();
		if (!labels.has(label)) continue;
		out.set(label, {
			label,
			verdict: m[2].toLowerCase(),
			confidence: Math.max(0, Math.min(1, Number(m[3]))),
			reason: m[4].trim()
		});
	}

	// Guarantee every device has an entry (fallback: "unknown")
	return frame.devices.map(
		(d) =>
			out.get(d.label) ?? {
				label: d.label,
				verdict: 'unknown',
				confidence: 0,
				reason: 'Newton did not return a verdict for this device'
			}
	);
}

export async function POST({ request }) {
	try {
		const { frame } = await request.json();
		if (!frame) {
			return json({ error: 'Missing frame' }, { status: 400 });
		}

		const raw = await runQuery({
			query: USER_PROMPT_PREFIX + JSON.stringify(redactOnline(frame)),
			systemPrompt: SYSTEM_PROMPT,
			maxNewTokens: 512
		});

		const predictions = parsePredictions(raw, frame);
		return json({ predictions, raw, timestamp: Date.now() });
	} catch (err) {
		return json({ error: err.message }, { status: 500 });
	}
}
