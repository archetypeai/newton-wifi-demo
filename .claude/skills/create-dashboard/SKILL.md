---
name: create-dashboard
description: Scaffolds a full-viewport dashboard layout with no scrolling, a branded menubar with the Archetype AI logo, and panel-based content areas. Use when creating a dashboard UI, building a full-screen layout, setting up a monitoring view, creating a control panel, or when the user asks for a "dashboard", "full-screen layout", "no-scroll UI", or "panel layout".
---

# Creating a Dashboard

Scaffold a full-viewport dashboard with a branded menubar and panel-based content.

> **Note:** This is one layout option for demos. If the user's request doesn't clearly map to a dashboard, consider the best-fit layout for their use case.

## Discovering Components

Before building, check which components are installed in the project:

1. List `$lib/components/ui/primitives/` and `$lib/components/ui/patterns/` to discover available primitives and patterns (each in a kebab-case subdirectory with `index.js`)
2. Only use components that actually exist in the project
3. If a required component is missing, ask the user to install it (via `npx shadcn-svelte@latest add`) or build it (via `@skills/build-pattern`)
4. **Never inline raw markup as a substitute for a missing component**

The dashboard requires at minimum: `Menubar`, `Button`. For card-based layouts: `Card`.

## Layout Requirements

Dashboards fill the entire viewport with no scrolling:

- `h-screen w-screen` — full viewport dimensions
- `overflow-hidden` — prevent any scrolling
- Grid layout: `grid grid-rows-[auto_1fr]` so the Menubar takes its natural height and content fills the rest

## Card Grid Defaults

Unless the user explicitly asks for a different layout:

- **Equal-width columns** — use `grid-cols-2`, `grid-cols-3`, etc. Never mix fixed and fluid widths for card grids (e.g., don't use `grid-cols-[300px_1fr]` for cards — that's for sidebar layouts only)
- **Cards fill available height** — cards must stretch to fill their grid cell or flex container. Add `max-h-full` to constrain content. For asymmetric layouts (stacked cards in one column, full-height card in another), use a flex column with `flex-1` on the card that should grow
- **Consistent spacing** — always use `gap-4` between cards and `p-4` padding around the grid

## Menubar

Use the `Menubar` pattern. It renders a branded `<header>` with the Archetype AI Logo on the left and a partner logo placeholder. Pass action content as children. The Menubar includes a built-in dark mode toggle on the far right that detects system preference and defaults to dark. To disable it, pass `darkToggle={false}`.

**Every dashboard Menubar must include a "Send Report" button.** Additional actions can be appended alongside it.

```svelte
<script>
  import Menubar from '$lib/components/ui/patterns/menubar/index.js';
  import { Button } from '$lib/components/ui/primitives/button/index.js';
</script>

<Menubar>
  <!-- these children are additive examples — append to existing children, don't replace them, if there are no children, add them -->
  <Button variant="link" class="text-muted-foreground">Send Report</Button>
</Menubar>
```

For co-branding, pass a `partnerLogo` snippet to replace the default placeholder:

```svelte
<Menubar>
  {#snippet partnerLogo()}
    <img src="/partner-logo.svg" alt="Partner" class="h-6" />
  {/snippet}
  <!-- additive example — append to existing children, don't replace them  -->
  <Button variant="link" class="text-muted-foreground">Send Report</Button>
</Menubar>
```

## Preservation Rules

- **Never rewrite or replace** the Menubar component file in `$lib/components/ui/`
- **Never modify installed primitives/patterns** in `$lib/components/ui/` — those are design system files
- When a Menubar already has children (buttons, actions), **append** new actions alongside existing ones — do not replace them
- When a page already has content, **integrate alongside** existing markup — do not overwrite the file

## Full Layout

```svelte
<script>
  import Menubar from '$lib/components/ui/patterns/menubar/index.js';
  import { Button } from '$lib/components/ui/primitives/button/index.js';
</script>

<div class="bg-background grid h-screen w-screen grid-rows-[auto_1fr] overflow-hidden">
  <Menubar>
    <Button variant="link" class="text-muted-foreground">Send Report</Button>
  </Menubar>

  <main class="overflow-hidden">
    <!-- panels go here -->
  </main>
</div>
```

## Panel Layouts

### Two Columns (Sidebar + Main)

```svelte
<main class="grid grid-cols-[300px_1fr] overflow-hidden">
  <aside class="border-border overflow-y-auto border-r p-4">
    <!-- sidebar content -->
  </aside>
  <section class="overflow-hidden p-4">
    <!-- main content -->
  </section>
</main>
```

### Three Columns

```svelte
<main class="grid grid-cols-[250px_1fr_300px] overflow-hidden">
  <aside class="border-border overflow-y-auto border-r p-4">
    <!-- left panel -->
  </aside>
  <section class="overflow-hidden p-4">
    <!-- center content -->
  </section>
  <aside class="border-border overflow-y-auto border-l p-4">
    <!-- right panel -->
  </aside>
</main>
```

### Grid of Cards (Equal)

```svelte
<main class="grid grid-cols-2 grid-rows-2 gap-4 overflow-hidden p-4">
  <Card class="max-h-full"><!-- panel 1 --></Card>
  <Card class="max-h-full"><!-- panel 2 --></Card>
  <Card class="max-h-full"><!-- panel 3 --></Card>
  <Card class="max-h-full"><!-- panel 4 --></Card>
</main>
```

### Asymmetric Cards (Stacked Left + Full-Height Right)

When one column has multiple cards and the other has a single tall card, use `grid-rows-subgrid` or nested flex columns. Cards must stretch to fill available height — never leave empty space at the bottom.

```svelte
<main class="grid grid-cols-[1fr_2fr] gap-4 overflow-hidden p-4">
  <!-- Left column: stacked cards that fill height -->
  <div class="flex flex-col gap-4 overflow-hidden">
    <Card class="max-h-full"><!-- input --></Card>
    <Card class="max-h-full"><!-- status --></Card>
    <Card class="max-h-full flex-1"><!-- summary (grows to fill remaining space) --></Card>
  </div>
  <!-- Right column: single card spanning full height -->
  <Card class="max-h-full overflow-hidden"><!-- log / results --></Card>
</main>
```

The `flex-1` on the last left-column card makes it grow to fill remaining vertical space. Adjust column ratio (`1fr_2fr`, `1fr_1fr`, etc.) to match content needs.

## Key Tailwind Classes

| Class                    | Purpose                                      |
| ------------------------ | -------------------------------------------- |
| `h-screen w-screen`      | Full viewport                                |
| `overflow-hidden`        | Prevent scrolling (apply to root and panels) |
| `grid-rows-[auto_1fr]`   | Menubar + fill content                       |
| `grid-cols-[300px_1fr]`  | Fixed sidebar + fluid main                   |
| `border-b border-border` | Semantic border for menubar                  |
| `bg-background`          | Themed background                            |

## Complete Example

```svelte
<!-- src/routes/+page.svelte -->
<script>
  import Menubar from '$lib/components/ui/patterns/menubar/index.js';
  import { Button } from '$lib/components/ui/primitives/button/index.js';
  import { Card, CardHeader, CardTitle, CardContent } from '$lib/components/ui/primitives/card/index.js';
</script>

<div
  class="bg-background text-foreground grid h-screen w-screen grid-rows-[auto_1fr] overflow-hidden"
>
  <Menubar>
    <Button variant="link" class="text-muted-foreground">Send Report</Button>
  </Menubar>

  <main class="grid grid-cols-2 grid-rows-2 gap-4 overflow-hidden p-4">
    <Card class="max-h-full">
      <CardHeader><CardTitle>Panel 1</CardTitle></CardHeader>
      <CardContent><!-- content --></CardContent>
    </Card>
    <Card class="max-h-full">
      <CardHeader><CardTitle>Panel 2</CardTitle></CardHeader>
      <CardContent><!-- content --></CardContent>
    </Card>
    <Card class="max-h-full">
      <CardHeader><CardTitle>Panel 3</CardTitle></CardHeader>
      <CardContent><!-- content --></CardContent>
    </Card>
    <Card class="max-h-full">
      <CardHeader><CardTitle>Panel 4</CardTitle></CardHeader>
      <CardContent><!-- content --></CardContent>
    </Card>
  </main>
</div>
```

## Populating Panels with Pattern Components

Panels should contain pattern components, not raw markup. Before building new components:

1. Fetch `https://design-system.archetypeai.workers.dev/r/patterns.json` to discover available patterns. Each has a `description` summarizing its purpose. If one fits, use it.
2. If no existing pattern fits, create one via `@skills/build-pattern`
3. Each panel should contain one primary component with clear props for data flow

This keeps dashboards composable and consistent with the design system.

## Reference

See `@rules/styling.md` for:

- Complete semantic token reference
- Tailwind v4 specifics and responsive patterns
