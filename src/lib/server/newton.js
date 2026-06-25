import { ATAI_API_KEY, ATAI_API_ENDPOINT } from '$env/static/private';

const API_VERSION = 'v0.5';
// C 2.6 fusion checkpoint, per the atai-newton-fusion-model skill.
const MODEL = 'Newton::c2_6_8b_fp8_260424d7a55d5e';
const DEFAULT_TIMEOUT_MS = 60000;

function queryUrl() {
	const base = ATAI_API_ENDPOINT.replace(/\/$/, '');
	return `${base}/${API_VERSION}/query`;
}

/**
 * Send a text query to Newton's /query endpoint.
 *
 * @param {Object} args
 * @param {string} args.query - User prompt.
 * @param {string} [args.systemPrompt] - System / instruction prompt.
 * @param {number} [args.maxNewTokens=512]
 * @param {number} [args.timeoutMs=60000]
 * @returns {Promise<string>} The model's text response.
 */
export async function runQuery({
	query,
	systemPrompt = '',
	maxNewTokens = 512,
	timeoutMs = DEFAULT_TIMEOUT_MS
}) {
	const controller = new AbortController();
	const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

	try {
		const res = await fetch(queryUrl(), {
			method: 'POST',
			headers: {
				Authorization: `Bearer ${ATAI_API_KEY}`,
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({
				// The system turn goes in `instruction_prompt`. C 2.6 honors only this
				// field; the legacy `system_prompt` is inert on this checkpoint, so we
				// don't send it (per the atai-newton-fusion-model skill).
				query,
				instruction_prompt: systemPrompt,
				file_ids: [],
				model: MODEL,
				max_new_tokens: maxNewTokens
			}),
			signal: controller.signal
		});

		if (!res.ok) {
			const err = await res.json().catch(() => ({}));
			throw new Error(`Newton query failed: ${res.status} — ${JSON.stringify(err)}`);
		}

		const data = await res.json();

		if (data?.response?.response && Array.isArray(data.response.response)) {
			return data.response.response[0] || '';
		}
		if (Array.isArray(data?.response)) return data.response[0] || '';
		if (typeof data?.response === 'string') return data.response;
		if (data?.text) return data.text;
		return JSON.stringify(data);
	} finally {
		clearTimeout(timeoutId);
	}
}
