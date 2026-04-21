---
paths:
  - '**/routes/**/*.svelte'
  - '**/+page.svelte'
  - '**/+layout.svelte'
---

# Frontend Architecture

When building a page that involves more than a simple static layout, decompose it into components rather than writing a monolithic `+page.svelte`.

## When to extract a component

Extract a component when a section of UI has:

- 3+ primitives composed together (Card + Badge + Button = a status card)
- Its own reactive state (`$state`, `$derived`)
- Potential for reuse across pages or skills

Common extraction candidates: media inputs, status displays, result/summary views, streaming logs, file upload flows.

## Gold-standard references

The project includes pattern components that demonstrate these conventions. Study them before building new ones:

- `$lib/components/ui/patterns/video-player/video-player.svelte` — media playback with controls, composes Card + AspectRatio + Button + Slider
- `$lib/components/ui/patterns/expandable-log/expandable-log.svelte` — streaming log display, composes Collapsible + Item + Badge
- `$lib/components/ui/patterns/status-badge/status-badge.svelte` — health indicator with derived state, composes Badge + Avatar
- `$lib/components/ui/patterns/healthscore-card/healthscore-card.svelte` — score card with derived state, composes Card sub-components
- `$lib/components/ui/patterns/menubar/menubar.svelte` — branded header with snippet slots

Check if an existing pattern fits before building a new one. Use `@skills/build-pattern` to create new patterns that follow these same conventions.

## Directory structure

```
$lib/components/ui/
  primitives/   — DS registry primitives (Card, Badge, Button, etc.)
  patterns/     — DS registry patterns (BackgroundCard, FlatLogItem, etc.)
  custom/       — Project-specific components not from the registry
```

Place custom components (ones you create for this project that are not installed from the registry) in `$lib/components/ui/custom/`. Never put custom components directly in `ui/` next to `primitives/` and `patterns/`.

## Component conventions

Follow `@rules/components` for the full conventions. The essentials:

- `let { class: className, ...restProps } = $props();`
- `cn()` for all class merging — never raw string concatenation
- `$derived` for computed state
- Spread `...restProps` on the root element
- Compose from DS primitives (Card, Badge, Button, etc.) — not raw HTML

## Page-level orchestration

`+page.svelte` is the orchestrator. It should:

- Own flow state (status, session IDs, error messages)
- Import and compose child components
- Pass data down via props
- Handle top-level layout (using `@skills/create-dashboard` for dashboard layouts)

Components should be presentational where possible — receive data via props, emit events up.

## API and streaming logic extraction

SSE consumers, fetch wrappers, polling loops, and data transforms belong in a utility file, not inline in components or pages:

```
src/lib/api/activity-monitor.js   — SSE + session management
src/lib/api/machine-state.js      — streaming + windowing
src/lib/api/embeddings.js         — upload + embedding extraction
```

This keeps components focused on rendering and makes API logic testable and reusable.

## Streaming UI

For skills that stream results (SSE, polling), prefer:

- Progressive rendering — show results as they arrive, don't wait for completion
- Live counters or progress indicators
- Auto-scrolling log views (reference ExpandableLog pattern)

## Override clause

If the user explicitly requests a single-file prototype, a minimal example, or specifies a different structure, follow their instruction. These guidelines apply to production-quality demos, not quick experiments.
