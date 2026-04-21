---
paths:
  - '**/*.css'
  - '**/*.svelte'
---

# Styling Rules

## Semantic Tokens

For the complete token reference including dark mode overrides, type scale (h1–h6, p, small), and spacing definitions, read `node_modules/@archetypeai/ds-lib-tokens/theme.css`.

Token naming pattern: `bg-{token}`, `text-{token}-foreground`, `border-{token}`.

Core tokens: `background`, `foreground`, `primary`, `secondary`, `muted`, `card`, `accent`, `destructive`, `border`, `input`, `ring`.

ATAI brand tokens: `atai-neutral`, `atai-good`, `atai-warning`, `atai-critical`.

Chart series: `--chart-1` through `--chart-5` (see `@rules/charts`).

## When to Use Semantic vs Standard Tailwind

### Use Semantic Tokens For:

```svelte
<!-- Themed colors that should change with light/dark mode -->
<div class="bg-background text-foreground">
<div class="bg-card border-border">
<button class="bg-primary text-primary-foreground">
<span class="text-muted-foreground">
```

### Use Standard Tailwind For:

```svelte
<!-- Spacing and sizing -->
<div class="p-4 gap-2 w-full h-screen">

<!-- Layout utilities -->
<div class="flex items-center justify-between">
<div class="grid grid-cols-2 gap-4">
<div class="absolute top-0 left-0">

<!-- One-off custom colors -->
<div class="bg-linear-to-r from-purple-500 to-pink-500">
<div class="text-amber-500">  <!-- specific non-themed color -->

<!-- Responsive breakpoints -->
<div class="sm:flex md:grid lg:hidden">

<!-- Animations and transitions -->
<div class="transition-all duration-200 ease-in-out">
```

## Dark Mode

Dark mode activates via `.dark` class on the root element:

```html
<html class="dark">
  ...
</html>
```

Semantic tokens automatically switch values in dark mode. No manual dark: prefixes needed for themed colors:

```svelte
<!-- This works in both light and dark mode automatically -->
<div class="bg-background text-foreground border-border">
```

For custom dark mode overrides, use the `dark:` prefix:

```svelte
<div class="bg-white dark:bg-slate-900">  <!-- custom dark override -->
```

For class merging with `cn()`, see `@rules/components`.

## CSS Import Order

In your global CSS file:

```css
@import '@archetypeai/ds-lib-fonts-internal';
@import '@archetypeai/ds-lib-tokens/theme.css';
@import 'tailwindcss';
@import 'tw-animate-css'; /* optional, for animations */
```

Order matters - tokens must come before Tailwind.

### Hide Scrollbars

Always add this rule to the root layout CSS (`src/app.css` or `src/routes/layout.css`) to hide visible scrollbars in ScrollArea components:

```css
[data-slot='scroll-area-scrollbar'] {
	display: none !important;
}
```

## Tailwind v4 Specifics

### @theme Directive

Custom theme values are defined with `@theme`:

```css
@theme {
  --font-sans: 'PP Neue Montreal', system-ui, sans-serif;
  --radius-md: var(--radius);
  --spacing-md: 0.75rem;
  --color-primary: var(--primary);
}
```

### CSS Variables in Classes

You can use CSS variables directly:

```svelte
<div style:--legend-color={seriesColor}>
  <span class="bg-(--legend-color)"> </span>
</div>
```

### No @apply in Components

Prefer Tailwind classes directly in markup. Use @apply only in base layer CSS:

```css
/* In theme.css - OK */
@layer base {
  body {
    @apply bg-background text-foreground;
  }
}
```

```svelte
<!-- In components - use classes directly -->
<div class="bg-background text-foreground">
```

## Common Patterns

For focus ring, disabled state, and data-state animation CSS patterns, see `@rules/accessibility`.

For icon sizing conventions, see `@rules/components`.
