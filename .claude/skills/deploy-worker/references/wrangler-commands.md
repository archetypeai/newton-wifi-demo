# Wrangler Command Reference

Full reference for wrangler CLI commands. Only load this when you need detailed command syntax beyond what's in SKILL.md.

## Core Commands

| Task                      | Command                     |
| ------------------------- | --------------------------- |
| Start local dev server    | `wrangler dev`              |
| Deploy to Cloudflare      | `wrangler deploy`           |
| Deploy dry run            | `wrangler deploy --dry-run` |
| Generate TypeScript types | `wrangler types`            |
| Validate configuration    | `wrangler check`            |
| View live logs            | `wrangler tail`             |
| Delete Worker             | `wrangler delete`           |
| Auth status               | `wrangler whoami`           |

## Local Development

```bash
# Local mode (default) - uses local storage simulation
wrangler dev

# With specific environment
wrangler dev --env staging

# Custom port
wrangler dev --port 8787

# Live reload for HTML changes
wrangler dev --live-reload

# Test scheduled/cron handlers
wrangler dev --test-scheduled
# Then visit: http://localhost:8787/__scheduled
```

### Local Secrets

Create `.dev.vars` for local development secrets:

```
API_KEY=local-dev-key
DATABASE_URL=postgres://localhost:5432/dev
```

## Deployment

```bash
# Deploy to production
wrangler deploy

# Deploy specific environment
wrangler deploy --env staging

# Dry run (validate without deploying)
wrangler deploy --dry-run

# Keep dashboard-set variables
wrangler deploy --keep-vars

# Minify code
wrangler deploy --minify
```

### Manage Secrets

```bash
# Set secret interactively
wrangler secret put API_KEY

# Set from stdin
echo "secret-value" | wrangler secret put API_KEY

# List secrets
wrangler secret list

# Delete secret
wrangler secret delete API_KEY

# Bulk secrets from JSON file
wrangler secret bulk secrets.json
```

### Versions and Rollback

```bash
# List recent versions
wrangler versions list

# Rollback to previous version
wrangler rollback

# Rollback to specific version
wrangler rollback <VERSION_ID>
```

## KV (Key-Value Store)

```bash
# Create namespace
wrangler kv namespace create MY_KV

# List namespaces
wrangler kv namespace list

# Put/get/delete values
wrangler kv key put --namespace-id <ID> "key" "value"
wrangler kv key get --namespace-id <ID> "key"
wrangler kv key delete --namespace-id <ID> "key"

# Bulk put from JSON
wrangler kv bulk put --namespace-id <ID> data.json
```

Config binding:

```jsonc
{ "kv_namespaces": [{ "binding": "CACHE", "id": "<NAMESPACE_ID>" }] }
```

## R2 (Object Storage)

```bash
# Create bucket
wrangler r2 bucket create my-bucket

# Upload/download/delete objects
wrangler r2 object put my-bucket/path/file.txt --file ./local-file.txt
wrangler r2 object get my-bucket/path/file.txt
wrangler r2 object delete my-bucket/path/file.txt
```

Config binding:

```jsonc
{ "r2_buckets": [{ "binding": "ASSETS", "bucket_name": "my-bucket" }] }
```

## D1 (SQL Database)

```bash
# Create database
wrangler d1 create my-database

# Execute SQL
wrangler d1 execute my-database --remote --command "SELECT * FROM users"
wrangler d1 execute my-database --remote --file ./schema.sql

# Migrations
wrangler d1 migrations create my-database create_users_table
wrangler d1 migrations apply my-database --remote

# Export
wrangler d1 export my-database --remote --output backup.sql
```

Config binding:

```jsonc
{ "d1_databases": [{ "binding": "DB", "database_name": "my-db", "database_id": "<DB_ID>" }] }
```

## Vectorize

```bash
wrangler vectorize create my-index --dimensions 768 --metric cosine
wrangler vectorize insert my-index --file vectors.ndjson
wrangler vectorize query my-index --vector "[0.1, 0.2, ...]" --top-k 10
```

Config binding:

```jsonc
{ "vectorize": [{ "binding": "INDEX", "index_name": "my-index" }] }
```

## Hyperdrive

```bash
wrangler hyperdrive create my-hyperdrive \
  --connection-string "postgres://user:pass@host:5432/database"
```

Config binding:

```jsonc
{
  "compatibility_flags": ["nodejs_compat_v2"],
  "hyperdrive": [{ "binding": "HYPERDRIVE", "id": "<HYPERDRIVE_ID>" }]
}
```

## Workers AI

Config binding:

```jsonc
{ "ai": { "binding": "AI" } }
```

Workers AI always runs remotely and incurs usage charges even in local dev.

## Queues

```bash
wrangler queues create my-queue
wrangler queues consumer add my-queue my-worker
```

Config binding:

```jsonc
{
  "queues": {
    "producers": [{ "binding": "MY_QUEUE", "queue": "my-queue" }],
    "consumers": [{ "queue": "my-queue", "max_batch_size": 10 }]
  }
}
```

## Containers

```bash
wrangler containers build -t my-app:latest . --push
wrangler containers list
```

## Workflows

```bash
wrangler workflows trigger my-workflow --params '{"key": "value"}'
wrangler workflows instances list my-workflow
```

Config binding:

```jsonc
{ "workflows": [{ "binding": "MY_WORKFLOW", "name": "my-workflow", "class_name": "MyWorkflow" }] }
```

## Pipelines

```bash
wrangler pipelines create my-pipeline --r2 my-bucket
```

Config binding:

```jsonc
{ "pipelines": [{ "binding": "MY_PIPELINE", "pipeline": "my-pipeline" }] }
```

## Secrets Store

```bash
wrangler secrets-store store create my-store
wrangler secrets-store secret put <STORE_ID> my-secret
```

Config binding:

```jsonc
{
  "secrets_store_secrets": [
    { "binding": "MY_SECRET", "store_id": "<STORE_ID>", "secret_name": "my-secret" }
  ]
}
```

## Pages (Frontend Deployment)

```bash
wrangler pages project create my-site
wrangler pages deploy ./dist
wrangler pages deploy ./dist --branch main
wrangler pages deployment list --project-name my-site
```

## Observability

```bash
# Stream live logs
wrangler tail
wrangler tail --status error
wrangler tail --search "error"
wrangler tail --format json
```

Config:

```jsonc
{ "observability": { "enabled": true, "head_sampling_rate": 1 } }
```

## Testing with Vitest

```bash
npm install -D @cloudflare/vitest-pool-workers vitest
```

`vitest.config.ts`:

```typescript
import { defineWorkersConfig } from '@cloudflare/vitest-pool-workers/config';

export default defineWorkersConfig({
  test: {
    poolOptions: {
      workers: {
        wrangler: { configPath: './wrangler.jsonc' }
      }
    }
  }
});
```

## Troubleshooting

| Issue                           | Solution                                   |
| ------------------------------- | ------------------------------------------ |
| `command not found: wrangler`   | `npm install -D wrangler`                  |
| Auth errors                     | `wrangler login`                           |
| Config validation errors        | `wrangler check`                           |
| Type errors after config change | `wrangler types`                           |
| Local storage not persisting    | Check `.wrangler/state` directory          |
| Binding undefined in Worker     | Verify binding name matches config exactly |
