import { json, error } from '@sveltejs/kit';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const FRAMES_DIR = resolve('data/processed/session-01/frames');

export async function GET({ params }) {
	const idx = Number(params.index);
	if (!Number.isInteger(idx) || idx < 0) {
		throw error(400, 'Invalid frame index');
	}
	const name = String(idx).padStart(4, '0') + '.json';
	try {
		const raw = await readFile(resolve(FRAMES_DIR, name), 'utf-8');
		return json(JSON.parse(raw));
	} catch (err) {
		throw error(404, `Frame ${name} not found (${err.message})`);
	}
}
