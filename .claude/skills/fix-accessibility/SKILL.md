---
name: fix-accessibility
description: Audits and fixes accessibility issues in projects using shadcn-svelte and the Archetype AI design system. Use when running an a11y audit, fixing WCAG violations, adding aria labels, improving keyboard navigation, fixing focus management, adding screen reader support, or when the user mentions "accessibility", "a11y", "aria", "screen reader", or "keyboard navigation".
---

# Fixing Accessibility

Audit and fix accessibility issues in projects built with the design system.

## Audit Process

Walk through the project in this order:

1. **Skip link** — verify the page has a skip-to-content link as the first focusable element. If missing, add `<a href="#main-content" class="sr-only focus:not-sr-only ...">Skip to content</a>` targeting `<main id="main-content">`.
2. **Landmarks** — verify the page uses semantic HTML landmarks: `<main>`, `<nav>`, `<header>`. Replace generic `<div>` wrappers with the correct landmark element.
3. **Heading hierarchy** — verify there is an `<h1>` on every page and headings don't skip levels (h1 → h3). Add `sr-only` headings where visual design omits them.
4. **Icon-only buttons** — search for `<Button size="icon"` and similar patterns, verify each has `aria-label`
5. **Decorative icons** — icons next to text labels should have `aria-hidden="true"`
6. **Form inputs** — verify `aria-invalid` support for error states
7. **Focus rings** — confirm all interactive elements have `focus-visible:ring-*` styles
8. **Disabled states** — check `disabled:pointer-events-none disabled:opacity-50`
9. **Lists and groups** — verify `role="list"`, `role="listitem"`, `role="group"` where appropriate
10. **Screen reader text** — add `sr-only` spans where visual context is missing
11. **Keyboard navigation** — tab through the entire UI, verify all controls are reachable
12. **Dialog focus traps** — open dialogs, confirm focus is trapped and Escape closes them

## Common Issues and Fixes

### Icon-Only Buttons Missing aria-label

```svelte
<!-- Before -->
<Button size="icon">
  <SearchIcon />
</Button>

<!-- After -->
<Button size="icon" aria-label="Search">
  <SearchIcon />
</Button>
```

### Decorative Icons Missing aria-hidden

Icons next to visible text labels are decorative and should be hidden from screen readers:

```svelte
<!-- Before -->
<Button>
  <PlusIcon />
  Add Item
</Button>

<!-- After -->
<Button>
  <PlusIcon aria-hidden="true" />
  Add Item
</Button>
```

### Inputs Missing aria-invalid

Form inputs should reflect validation state:

```svelte
<!-- Before -->
<Input class={errors.email ? 'border-destructive' : ''} />

<!-- After -->
<Input aria-invalid={errors.email ? true : undefined} />
```

The design system primitives already style `aria-invalid` with destructive border and ring colors — no extra classes needed.

### Missing Focus Ring Styles

Interactive elements must have visible focus indicators:

```svelte
<button
  class={cn(
    'outline-none',
    'focus-visible:border-ring',
    'focus-visible:ring-ring/50',
    'focus-visible:ring-[3px]'
  )}
>
```

Design system primitives include these by default. Custom interactive elements must add them manually.

### Disabled States Not Preventing Interaction

```svelte
<!-- For native elements -->
<button
  class="disabled:pointer-events-none disabled:opacity-50"
  disabled={isDisabled}
>

<!-- For links styled as buttons -->
<a
  href={disabled ? undefined : href}
  aria-disabled={disabled}
  tabindex={disabled ? -1 : undefined}
  class="aria-disabled:pointer-events-none aria-disabled:opacity-50"
>
```

### Missing Roles on Lists and Groups

```svelte
<!-- Lists -->
<div role="list">
  {#each items as item}
    <div role="listitem">{item}</div>
  {/each}
</div>

<!-- Button groups -->
<div role="group" aria-label="Text formatting">
  <Button>Bold</Button>
  <Button>Italic</Button>
</div>

<!-- Loading indicators -->
<svg role="status" aria-label="Loading" class="animate-spin">...</svg>
```

### Missing Screen Reader Text

Add visually hidden text where icons or visual cues carry meaning:

```svelte
<button>
  <XIcon />
  <span class="sr-only">Close</span>
</button>
```

## Page Structure

### Skip Link

Every page should have a skip link as the first focusable element:

```svelte
<a
  href="#main-content"
  class="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:rounded-md focus:bg-background focus:px-4 focus:py-2 focus:text-foreground focus:ring-2 focus:ring-ring"
>
  Skip to content
</a>

<main id="main-content">
  <!-- page content -->
</main>
```

### Semantic Landmarks

```svelte
<!-- Before -->
<div class="header">...</div>
<div class="content">...</div>

<!-- After -->
<header>...</header>
<main id="main-content">...</main>
```

### Heading Hierarchy

Every page needs an `<h1>`. If the visual design doesn't include one, add it as screen-reader-only:

```svelte
<h1 class="sr-only">Dashboard</h1>
```

Never skip heading levels (e.g. `<h1>` → `<h3>`). Use the correct level for the document outline.

## Keyboard Navigation for Custom Elements

When building custom interactive elements (not using bits-ui primitives), ensure keyboard support:

```svelte
<div
  role="button"
  tabindex="0"
  onkeydown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  }}
  onclick={handleClick}
>
```

## Dialog and Popover Focus Traps

bits-ui handles focus trapping automatically for Dialog, Popover, Command, and Select. Verify:

- Focus moves into the dialog when opened
- Tab cycles within the dialog (does not escape)
- Escape closes the dialog
- Focus returns to the trigger element after close

If focus trapping is broken, check that the bits-ui primitive is used correctly and not wrapped in a way that breaks the DOM structure.

## Verification Checklist

After fixing, walk through the project and confirm:

- [ ] Page has a skip-to-content link as the first focusable element
- [ ] Page uses `<main>` landmark with `id="main-content"`
- [ ] Page has an `<h1>` (visible or `sr-only`)
- [ ] Heading hierarchy doesn't skip levels
- [ ] All icon-only buttons have `aria-label`
- [ ] All decorative icons have `aria-hidden="true"`
- [ ] Form inputs support `aria-invalid` styling
- [ ] All interactive elements have visible focus rings
- [ ] Disabled states prevent interaction and reduce opacity
- [ ] Loading indicators use `role="status"`
- [ ] Lists use `role="list"` and `role="listitem"`
- [ ] Groups use `role="group"` with `aria-label`
- [ ] Tab navigation reaches all interactive elements
- [ ] Dialogs trap focus and close with Escape

## Reference

See `@rules/accessibility.md` for the complete accessibility rules and patterns.
