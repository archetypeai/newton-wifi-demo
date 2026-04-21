---
name: deploy-worker
description: Deploys a SvelteKit project to Cloudflare Workers with CI/CD auto-deploy on merge to main. Use when deploying a project, setting up wrangler configuration, running a local worker dev server, managing secrets, configuring environments, or when the user mentions "deploy", "cloudflare", "worker", "wrangler", or "production".
---

# Deploying a Worker

Deploy SvelteKit projects built with the design system to Cloudflare Workers with GitHub Actions CI/CD that auto-deploys on merge to main.

## Prerequisites

```bash
wrangler --version  # Requires v4.x+
```

If not installed:

```bash
npm install -D wrangler@latest
```

Authenticate:

```bash
wrangler login
wrangler whoami  # Verify
```

## SvelteKit Adapter Setup

Install the Cloudflare adapter:

```bash
npm install -D @sveltejs/adapter-cloudflare
```

Update `svelte.config.js`:

```javascript
import adapter from '@sveltejs/adapter-cloudflare';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  kit: {
    adapter: adapter()
  }
};

export default config;
```

## Wrangler Configuration

Create `wrangler.jsonc` in the project root:

```jsonc
{
  "$schema": "./node_modules/wrangler/config-schema.json",
  "name": "my-app",
  "main": ".svelte-kit/cloudflare/_worker.js",
  "compatibility_date": "2026-01-01",
  "compatibility_flags": ["nodejs_compat_v2"],

  // Static assets from SvelteKit build
  "assets": {
    "directory": ".svelte-kit/cloudflare",
    "binding": "ASSETS"
  },

  // Environment variables
  "vars": {
    "ENVIRONMENT": "production"
  },

  // Environments
  "env": {
    "staging": {
      "name": "my-app-staging",
      "vars": { "ENVIRONMENT": "staging" }
    }
  }
}
```

> **Note**: Existing projects may use `wrangler.toml` instead of `wrangler.jsonc`. Both work, but JSONC is recommended for new projects as newer wrangler features are JSON-only.

## Build and Initial Deploy

```bash
# Build the SvelteKit app
npm run build

# Dry run first to validate
wrangler deploy --dry-run

# Deploy to Cloudflare
wrangler deploy
```

## CI/CD Auto-Deploy

Always set up GitHub Actions so the project auto-deploys when changes are merged into main.

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npm run build
      - run: npx wrangler deploy
        env:
          CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
```

Required secret: `CLOUDFLARE_API_TOKEN` with Workers permissions. Remind the user to add this to their GitHub repo under Settings > Secrets and variables > Actions.

If the user has a staging environment, extend the workflow:

```yaml
on:
  push:
    branches: [main, staging]

# In the deploy step:
- run: npx wrangler deploy ${{ github.ref_name == 'staging' && '--env staging' || '' }}
```

## Local Development

```bash
# SvelteKit dev server (preferred for development)
npm run dev

# Worker dev server (test Cloudflare-specific behavior)
npm run build && wrangler dev
```

Use `wrangler dev` when you need to test:

- Cloudflare bindings (KV, R2, D1)
- Worker-specific routing
- Production-like behavior

## Secrets

Never commit secrets to config. Use wrangler secrets for production and `.dev.vars` for local dev.

```bash
# Set a secret
wrangler secret put API_KEY

# List secrets
wrangler secret list
```

For local development, create `.dev.vars` (gitignored):

```
API_KEY=local-dev-key
```

## Environments

Deploy to staging or production:

```bash
# Deploy to staging
wrangler deploy --env staging

# Deploy to production (default)
wrangler deploy
```

## Observability

```bash
# Stream live logs
wrangler tail

# Filter by errors
wrangler tail --status error
```

Enable in config:

```jsonc
{
  "observability": {
    "enabled": true,
    "head_sampling_rate": 1
  }
}
```

## Rollback

```bash
# List recent versions
wrangler versions list

# Rollback to previous version
wrangler rollback
```

## Checklist

- [ ] `@sveltejs/adapter-cloudflare` installed
- [ ] `svelte.config.js` uses the Cloudflare adapter
- [ ] `wrangler.jsonc` exists with correct `name` and `compatibility_date`
- [ ] `npm run build` succeeds
- [ ] `wrangler deploy --dry-run` passes
- [ ] `.github/workflows/deploy.yml` created with auto-deploy on merge to main
- [ ] User reminded to set `CLOUDFLARE_API_TOKEN` in GitHub repo secrets
- [ ] Secrets set via `wrangler secret put` (not in config)
- [ ] `.dev.vars` gitignored

## Reference

See [references/wrangler-commands.md](references/wrangler-commands.md) for the full wrangler CLI reference including KV, R2, D1, Vectorize, Hyperdrive, Workers AI, Queues, Containers, Workflows, Pipelines, and Secrets Store commands.
