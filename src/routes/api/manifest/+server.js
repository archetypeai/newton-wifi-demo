import { json, error } from '@sveltejs/kit';
import { readFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const MANIFEST_PATH = resolve('data/processed/session-01/manifest.json');

export async function GET() {
	try {
		const raw = await readFile(MANIFEST_PATH, 'utf-8');
		return json(JSON.parse(raw));
	} catch (err) {
		throw error(
			500,
			`Failed to load manifest at ${MANIFEST_PATH}. Run \`python3 scripts/preprocess.py\` first. (${err.message})`
		);
	}
}
