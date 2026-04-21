---
name: apply-ds
description: Apply DS tokens, components, and patterns to an existing demo initialized with ds-cli init.
allowed-tools: Read, Edit, Grep, Bash
---

# Applying the Design System to a Demo

This skill assumes `npx @archetypeai/ds-cli init` has already been run. The project has tokens, Tailwind v4, shadcn-svelte, and DS components installed. The goal is to migrate the demo's existing UI to use DS primitives and semantic tokens.

## Steps

1. Audit for non-DS patterns
2. Replace raw colors with semantic tokens
3. Replace native elements with DS components
4. Apply layout patterns
5. Set up linting and formatting
6. Verify

## Step 1: Audit for Non-DS Patterns

Run the `scripts/audit.sh` script located in this skill's directory from the project root. The script scans all `.svelte` files and reports:

- **Raw Tailwind colors** — utilities like `bg-gray-100`, `text-blue-500`, `border-red-300` that should be semantic tokens
- **Native HTML elements** — `<button>`, `<input>`, `<table>`, `<select>`, `<textarea>`, `<dialog>`, `<hr>` that have DS component equivalents
- **Hardcoded colors** — inline `color:`, `background:`, `background-color:`, `border-color:` style values
- **Class concatenation** — string templates or `+` concatenation on class attributes instead of `cn()`

Review the output to prioritize what to migrate.

## Step 2: Replace Raw Colors with Semantic Tokens

Replace raw Tailwind color utilities with semantic equivalents throughout `.svelte` files:

| Raw Tailwind | Semantic Token |
| --- | --- |
| `bg-white` | `bg-background` |
| `bg-black` | `bg-foreground` |
| `text-black` | `text-foreground` |
| `text-white` | `text-background` |
| `bg-gray-50`, `bg-gray-100` | `bg-muted` |
| `text-gray-500`, `text-gray-600` | `text-muted-foreground` |
| `bg-gray-200`, `bg-gray-300` | `bg-accent` |
| `border-gray-200`, `border-gray-300` | `border-border` |
| `bg-slate-900`, `bg-gray-900` | `bg-primary` |
| `text-slate-900`, `text-gray-900` | `text-primary` |
| `bg-red-*` | `bg-destructive` |
| `text-red-*` | `text-destructive` |
| `bg-green-*` | `bg-atai-good` |
| `text-green-*` | `text-atai-good` |
| `bg-yellow-*` | `bg-atai-warning` |
| `text-yellow-*` | `text-atai-warning` |
| `bg-blue-*` | `bg-atai-neutral` |
| `text-blue-*` | `text-atai-neutral` |

Use judgement — not every raw color maps 1:1. Context matters:

- A `bg-gray-100` card background → `bg-card` or `bg-muted`
- A `bg-gray-100` hover state → `bg-accent`
- A `text-gray-400` placeholder → `text-muted-foreground`
- A `border-gray-200` divider → `border-border`

Leave non-color utilities (`p-4`, `flex`, `rounded-lg`, etc.) unchanged.

## Step 3: Replace Native Elements with DS Components

Swap native HTML elements for their DS component equivalents. Add imports as needed.

| Native Element | DS Component | Import From |
| --- | --- | --- |
| `<button>` | `<Button>` | `$lib/components/ui/primitives/button` |
| `<input>` | `<Input>` | `$lib/components/ui/primitives/input` |
| `<textarea>` | `<Textarea>` | `$lib/components/ui/primitives/textarea` |
| `<select>` | `<Select.Root>` + `<Select.Trigger>` + `<Select.Content>` + `<Select.Item>` | `$lib/components/ui/primitives/select` |
| `<table>` | `<Table.Root>` + `<Table.Header>` + `<Table.Row>` + `<Table.Head>` + `<Table.Body>` + `<Table.Cell>` | `$lib/components/ui/primitives/table` |
| `<dialog>` | `<Dialog.Root>` + `<Dialog.Content>` + `<Dialog.Header>` + `<Dialog.Title>` | `$lib/components/ui/primitives/dialog` |
| `<hr>` | `<Separator>` | `$lib/components/ui/primitives/separator` |
| `<label>` | `<Label>` | `$lib/components/ui/primitives/label` |
| `<a>` (styled as button) | `<Button variant="link">` or `<Button>` with `href` | `$lib/components/ui/primitives/button` |

For each replacement:

1. Add the import to the `<script>` block
2. Replace the element and map attributes (`class` → `class`, `onclick` → `onclick`, etc.)
3. Use `cn()` from `$lib/utils.js` for merging classes — never raw concatenation
4. Map native variants: e.g. a small styled button → `<Button size="sm">`, a ghost-styled button → `<Button variant="ghost">`

## Step 4: Apply Layout Patterns

Identify structural opportunities to use DS composition patterns:

- **Cards** — wrap content sections in `<Card.Root>` / `<Card.Header>` / `<Card.Content>` instead of raw `<div>` with border/shadow classes
- **Separators** — replace `<hr>` or border-bottom hacks with `<Separator>`
- **Badges** — replace styled `<span>` status indicators with `<Badge>`
- **Skeleton** — replace loading placeholders with `<Skeleton>`
- **Scroll Area** — replace overflow containers with `<ScrollArea>`
- **Tooltips** — replace `title` attributes with `<Tooltip.Root>` / `<Tooltip.Trigger>` / `<Tooltip.Content>`

Import primitives from `$lib/components/ui/primitives/` and patterns from `$lib/components/ui/patterns/` as needed.

## Step 5: Lint and Format

Run linting and formatting to clean up the migrated code:

```bash
npm run lint:fix && npm run format
```

See `@rules/linting.md` for details.

## Step 6: Verify

Confirm the design system is properly applied:

- [ ] No raw Tailwind color utilities in `.svelte` files (re-run the audit script)
- [ ] Native elements replaced with DS components where appropriate
- [ ] All component imports resolve to `$lib/components/ui/primitives/` or `$lib/components/ui/patterns/`
- [ ] `cn()` used for class merging — no string concatenation
- [ ] Linting passes: `npm run lint && npm run format:check`
- [ ] App builds without errors: `npm run build`
- [ ] App runs correctly: `npm run dev`
