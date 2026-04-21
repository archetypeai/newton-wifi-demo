---
name: newton-direct-query
description: Simple direct query to Newton model using the /query API endpoint. Test API connectivity, run text queries, or post-process results from other lenses. No lens registration or session needed.
argument-hint: [query]
allowed-tools: Bash(python *), Read
---

# Newton Direct Query (Newton /query endpoint)

Send a text query directly to Newton via `POST /v0.5/query`. No lens registration, no session, no SSE — just a simple request/response. Use for API testing, text Q&A, or post-processing results from other lenses.

## Frontend Architecture

| UI Area | Component | Pattern/Primitives | Key Props |
|---------|-----------|-------------------|-----------|
| Query input | `QueryInput.svelte` | BackgroundCard, Input, Button | `onsubmit`, `loading` |
| Response | `QueryResponse.svelte` | BackgroundCard | `response`, `loading` |

- Use `@skills/create-dashboard` for the page layout

---

## API Endpoint

```
POST https://api.u1.archetypeai.app/v0.5/query
Authorization: Bearer {apiKey}
Content-Type: application/json
```

## Request Body

```json
{
  "query": "Your question or prompt here",
  "system_prompt": "System-level instruction",
  "instruction_prompt": "System-level instruction",
  "file_ids": [],
  "model": "Newton::c2_4_7b_251215a172f6d7",
  "max_new_tokens": 1024,
  "sanitize": false
}
```

| Field | Type | Description |
|---|---|---|
| `query` | string | The user prompt / question (required) |
| `system_prompt` | string | System-level instruction guiding the model |
| `instruction_prompt` | string | Same as `system_prompt` — set both to the same value |
| `file_ids` | string[] | File IDs to include as context (empty for text-only) |
| `model` | string | Model ID (default: `Newton::c2_4_7b_251215a172f6d7`) |
| `max_new_tokens` | number | Max response length (default: 1024) |
| `sanitize` | boolean | Whether to sanitize input (default: false) |

**IMPORTANT:** The body uses `model` (not `model_version`) and `system_prompt` + `instruction_prompt` (not `instruction`). Both `system_prompt` and `instruction_prompt` should be set to the same value.

## Response Structure

```json
{
  "response": {
    "response": ["The model's answer text here"]
  }
}
```

Extract the text using this priority chain:
1. `data.response.response[0]` (most common)
2. `data.response[0]` (fallback)
3. `data.response` as string (fallback)
4. `data.text` (fallback)

---

## Web / JavaScript Implementation

Uses a config object pattern with `systemPrompt` (optional, defaults to `''`) and `fileIds` (optional, defaults to `[]`). Timeout is 120s since Newton queries can be slow for long prompts.

```javascript
/**
 * @param {Object} config
 * @param {string} config.apiKey
 * @param {string} config.query - The user prompt to send
 * @param {string} [config.systemPrompt=''] - Optional system/instruction prompt
 * @param {string[]} [config.fileIds=[]] - Optional file IDs to include as context
 * @param {number} [config.maxNewTokens=1024]
 * @returns {Promise<string>} The model's text response
 */
async function runDirectQuery(config) {
  const { apiKey, query, systemPrompt = '', fileIds = [], maxNewTokens = 1024 } = config

  const response = await fetch('https://api.u1.archetypeai.app/v0.5/query', {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      system_prompt: systemPrompt,
      instruction_prompt: systemPrompt,
      file_ids: fileIds,
      model: 'Newton::c2_4_7b_251215a172f6d7',
      max_new_tokens: maxNewTokens,
      sanitize: false,
    }),
    signal: AbortSignal.timeout(120000),
  })

  if (!response.ok) {
    const errorBody = await response.json().catch(() => ({}))
    throw new Error(`Query failed: ${response.status} - ${JSON.stringify(errorBody)}`)
  }

  const data = await response.json()

  // Extract response text — nested response.response[0] is most common
  if (data.response?.response && Array.isArray(data.response.response)) {
    return data.response.response[0] || ''
  }
  if (data.response && Array.isArray(data.response)) {
    return data.response[0] || ''
  }
  if (data.response && typeof data.response === 'string') {
    return data.response
  }
  if (data.text) {
    return data.text
  }

  return JSON.stringify(data)
}

// Usage
const answer = await runDirectQuery({
  apiKey,
  query: 'What is the capital of France?',
  systemPrompt: 'Answer the question concisely.',
})
console.log(answer) // "Paris"

// With file context
const summary = await runDirectQuery({
  apiKey,
  query: 'Summarize the sensor data patterns.',
  systemPrompt: 'You are a sensor data analyst.',
  fileIds: ['file-abc123'],
})
```

---

## Python Implementation

```python
import os
import requests

API_URL = "https://api.u1.archetypeai.app/v0.5/query"

def query_newton(query: str, system_prompt: str, api_key: str, max_new_tokens: int = 1024) -> str:
    """Send a direct text query to Newton."""
    response = requests.post(
        API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "query": query,
            "system_prompt": system_prompt,
            "instruction_prompt": system_prompt,
            "file_ids": [],
            "model": "Newton::c2_4_7b_251215a172f6d7",
            "max_new_tokens": max_new_tokens,
            "sanitize": False,
        },
        timeout=60,
    )
    response.raise_for_status()
    data = response.json()

    # Extract response text (multiple possible shapes)
    resp = data.get("response")
    if isinstance(resp, dict) and isinstance(resp.get("response"), list):
        return resp["response"][0] or ""
    if isinstance(resp, list):
        return resp[0] or ""
    if isinstance(resp, str):
        return resp
    if data.get("text"):
        return data["text"]

    return str(data)


# Usage
api_key = os.getenv("ATAI_API_KEY") or os.getenv("ARCHETYPE_API_KEY")
answer = query_newton(
    "What is the capital of France?",
    "Answer the question concisely.",
    api_key,
)
print(answer)  # "Paris"
```

---

## Use Cases

- **API connectivity testing**: Verify your API key works
- **Quick text Q&A**: Get answers without lens/session setup
- **Post-processing**: Send results from other lenses (activity monitor, machine state) to Newton for summarization or comparison
- **Debugging**: Verify the `/query` endpoint behavior

## Troubleshooting

- **"Failed to fetch"**: Check the request body format — use `model` (not `model_version`), `system_prompt` + `instruction_prompt` (not `instruction`), and `query` (not `focus`)
- **Empty response**: Check the response extraction chain — the text is typically in `data.response.response[0]`
- **Authentication error**: Verify API key is correct and has the `Bearer ` prefix
- **Timeout**: Newton queries can take 10-30s for long prompts; use a 60s timeout
