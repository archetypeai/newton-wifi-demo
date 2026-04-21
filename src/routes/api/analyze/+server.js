import { json } from '@sveltejs/kit';
import { runQuery } from '$lib/server/newton.js';
import { redactOnline } from '$lib/server/frame.js';

const SYSTEM_PROMPT = [
	'You are a home-occupancy inference AI analyzing a single 15-minute window of',
	'WiFi device-telemetry from a residential gateway. Every MAC is anonymized — device',
	'types are not labeled, and the per-device `online` flag has been withheld:',
	'infer online state from the flow/byte/protocol evidence. Reason from traffic',
	'patterns alone: active interactive sessions (HTTP/HTTPS/streaming) suggest a',
	'person is using a device; periodic low-byte background chatter (DNS, mDNS, NTP)',
	'is consistent with idle devices; multiple devices active in the same window',
	'increases the likelihood someone is home. Be concise, direct, and hedge only',
	'when the signal is genuinely ambiguous.'
].join(' ');

const DEFAULT_QUERY =
	'Based on this 15-minute snapshot of home WiFi device telemetry, is anyone home? ' +
	'Answer with one of: OCCUPIED, LIKELY_OCCUPIED, AMBIGUOUS, LIKELY_EMPTY, EMPTY. ' +
	'Then give a single-sentence reason citing specific device behavior (e.g. "Device B streamed ~500KB over HTTPS across 80 flows").';

export async function POST({ request }) {
	try {
		const { frame, query } = await request.json();
		if (!frame) {
			return json({ error: 'Missing frame' }, { status: 400 });
		}

		const userQuery =
			(query || DEFAULT_QUERY) + '\n\nSnapshot (JSON):\n' + JSON.stringify(redactOnline(frame));

		const analysis = await runQuery({
			query: userQuery,
			systemPrompt: SYSTEM_PROMPT,
			maxNewTokens: 400
		});

		return json({ analysis, timestamp: Date.now() });
	} catch (err) {
		return json({ error: err.message }, { status: 500 });
	}
}
