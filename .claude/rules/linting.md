# Linting & Formatting

## Commands

| Command                | Description                      |
| ---------------------- | -------------------------------- |
| `npm run lint`         | Check for linting errors         |
| `npm run lint:fix`     | Auto-fix linting errors          |
| `npm run format`       | Format all files with Prettier   |
| `npm run format:check` | Check formatting without changes |

## Stack

- **ESLint** - Flat config (v9+) with `eslint-plugin-svelte`
- **Prettier** - Code formatting
- **prettier-plugin-svelte** - Svelte file formatting
- **prettier-plugin-tailwindcss** - Auto-sorts Tailwind classes

## Workflow

Run linting and formatting before committing:

```bash
npm run lint:fix && npm run format
```

Or check without auto-fixing:

```bash
npm run lint && npm run format:check
```
