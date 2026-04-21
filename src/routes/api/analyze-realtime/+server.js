import { json } from '@sveltejs/kit';
import { runQuery } from '$lib/server/newton.js';

function buildSystemPrompt(windowSec) {
	return [
		`You are a home-occupancy inference AI analyzing a rolling ${windowSec}-second window of`,
		'WiFi device-telemetry from a residential gateway. Every MAC is anonymized — device',
		'types are not labeled. Reason from traffic patterns alone: active interactive',
		'sessions (HTTP/HTTPS/streaming) suggest a person is using a device; periodic',
		'low-byte background chatter (DNS, mDNS, NTP) is consistent with idle devices;',
		'multiple devices active in the same window increases the likelihood someone is',
		`home. This is a SHORT ${windowSec}-second window — byte counts and flow counts will be`,
		'correspondingly small; calibrate your confidence accordingly. Be concise,',
		'direct, and hedge only when the signal is genuinely ambiguous.'
	].join(' ');
}

function buildDefaultQuery(windowSec) {
	return (
		`Based on this rolling ${windowSec}-second snapshot of home WiFi device telemetry, is anyone home right now? ` +
		'Answer with one of: OCCUPIED, LIKELY_OCCUPIED, AMBIGUOUS, LIKELY_EMPTY, EMPTY. ' +
		`Then give a single-sentence reason citing specific device behavior (e.g. "Device B sent ~8 KB over HTTPS in the last ${windowSec}s").`
	);
}

function windowDurationSeconds(frame) {
	if (!frame?.window_start || !frame?.window_end) return 30;
	const ms = new Date(frame.window_end).getTime() - new Date(frame.window_start).getTime();
	return Math.max(1, Math.round(ms / 1000));
}

export async function POST({ request }) {
	try {
		const { frame, query } = await request.json();
		if (!frame) {
			return json({ error: 'Missing frame' }, { status: 400 });
		}

		const windowSec = windowDurationSeconds(frame);
		const userQuery =
			(query || buildDefaultQuery(windowSec)) +
			`\n\nSnapshot (JSON, ${windowSec}-second rolling window):\n` +
			JSON.stringify(frame);

		const analysis = await runQuery({
			query: userQuery,
			systemPrompt: buildSystemPrompt(windowSec),
			maxNewTokens: 400
		});

		return json({ analysis, timestamp: Date.now() });
	} catch (err) {
		return json({ error: err.message }, { status: 500 });
	}
}
