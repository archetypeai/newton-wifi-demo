import { json, error } from '@sveltejs/kit';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const EVENTS_PATH = resolve('data/processed/session-01/events.jsonl');

export async function GET() {
	try {
		const raw = await readFile(EVENTS_PATH, 'utf-8');
		const events = raw
			.split('\n')
			.filter((line) => line.trim())
			.map((line) => JSON.parse(line));
		return json({ events, count: events.length });
	} catch (err) {
		throw error(
			500,
			`Failed to load events at ${EVENTS_PATH}. Run \`python3 scripts/preprocess.py\` first. (${err.message})`
		);
	}
}
