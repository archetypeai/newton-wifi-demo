# Accessibility Rules

## Screen Reader Support

Use `sr-only` for text that should be accessible but visually hidden:

```svelte
<button>
  <XIcon />
  <span class="sr-only">Close</span>
</button>
```

The `sr-only` class hides content visually while keeping it accessible to screen readers.

## aria-label

### Icon-Only Buttons

Always provide `aria-label` for buttons that only contain an icon:

```svelte
<!-- Correct -->
<Button size="icon" aria-label="Search">
  <SearchIcon />
</Button>

<!-- Wrong - no accessible name -->
<Button size="icon">
  <SearchIcon />
</Button>
```

### Interactive Groups

Provide `aria-label` for grouped interactive elements:

```svelte
<ButtonGroup.Root aria-label="Pagination">
  <Button variant="outline" size="icon-sm" aria-label="Previous page">
    <ChevronLeftIcon />
  </Button>
  <ButtonGroup.Text>Page 1 of 10</ButtonGroup.Text>
  <Button variant="outline" size="icon-sm" aria-label="Next page">
    <ChevronRightIcon />
  </Button>
</ButtonGroup.Root>
```

### Toggles

```svelte
<Toggle variant="outline" aria-label="Toggle bookmark">
  <BookmarkIcon />
</Toggle>
```

## aria-hidden

Use `aria-hidden="true"` for decorative elements that shouldn't be announced:

```svelte
<!-- Decorative icons next to text -->
<CardTitle>Sensor Status</CardTitle>
<Icon strokeWidth={1.25} class="text-muted-foreground size-6" aria-hidden="true" />

<!-- Icons in buttons WITH text labels -->
<Button>
  <PlusIcon aria-hidden="true" />
  Add Item
</Button>
```

Do NOT use `aria-hidden` on icon-only buttons - use `aria-label` instead.

## role Attributes

### Lists

```svelte
<div role="list" data-slot="item-group">
  {#each items as item}
    <div role="listitem">{item}</div>
  {/each}
</div>
```

### Groups

```svelte
<!-- Input groups -->
<div role="group" data-slot="input-group">
  <Input />
  <Button>Submit</Button>
</div>

<!-- Button groups -->
<div role="group" aria-label="Text formatting" data-slot="button-group">
  <Button>Bold</Button>
  <Button>Italic</Button>
</div>
```

### Status

```svelte
<!-- Spinners/loading indicators -->
<svg role="status" aria-label="Loading" class="animate-spin"> ... </svg>
```

## aria-invalid Styling

Components use `aria-invalid` for validation states. The styling pattern:

```svelte
<input
  class={cn(
    'border-input focus-visible:ring-ring/50',
    'aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40',
    'aria-invalid:border-destructive'
  )}
  aria-invalid={hasError}
/>
```

This applies to: inputs, textareas, selects, checkboxes, buttons, badges.

To trigger invalid styling, set `aria-invalid="true"`:

```svelte
<Input aria-invalid={errors.email ? true : undefined} />
```

## Focus Management

### Focus Ring Pattern

All interactive elements use this focus pattern:

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

Key points:

- `outline-none` removes default browser outline
- `focus-visible` only shows on keyboard focus (not mouse clicks)
- `ring-[3px]` provides visible focus indicator
- `ring-ring/50` uses semantic ring color at 50% opacity

### Disabled States

```svelte
<button
  class="disabled:pointer-events-none disabled:opacity-50"
  disabled={isDisabled}
>
```

For links styled as buttons (can't use `disabled` attribute):

```svelte
<a
  href={disabled ? undefined : href}
  aria-disabled={disabled}
  role={disabled ? 'button' : undefined}
  tabindex={disabled ? -1 : undefined}
  class="aria-disabled:pointer-events-none aria-disabled:opacity-50"
>
```

## Keyboard Navigation

### bits-ui Primitives

Most keyboard navigation is handled automatically by bits-ui:

- Dialog: Escape to close, focus trap
- Select: Arrow keys to navigate, Enter to select
- Command: Arrow keys, Enter, type to filter
- Popover: Escape to close

### Custom Components

For custom interactive elements, ensure:

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

Use semantic HTML elements instead of generic `<div>` wrappers:

```svelte
<!-- Before -->
<div class="header">...</div>
<div class="nav">...</div>
<div class="content">...</div>

<!-- After -->
<header>...</header>
<nav>...</nav>
<main id="main-content">...</main>
```

### Heading Hierarchy

Every page needs an `<h1>`. If the visual design doesn't include one, add it as screen-reader-only:

```svelte
<h1 class="sr-only">Dashboard</h1>
```

Never skip heading levels (e.g. `<h1>` → `<h3>`). Use the correct level for the document outline.

## Checklist

When building components, verify:

- [ ] Page has a skip-to-content link as the first focusable element
- [ ] Page uses semantic landmarks (`<main>`, `<header>`, `<nav>`)
- [ ] Page has an `<h1>` (visible or `sr-only`)
- [ ] Heading hierarchy doesn't skip levels
- [ ] Icon-only buttons have `aria-label`
- [ ] Decorative icons have `aria-hidden="true"`
- [ ] Interactive groups have `aria-label`
- [ ] Form inputs support `aria-invalid` styling
- [ ] Focus states are visible (`focus-visible:ring-*`)
- [ ] Disabled states prevent interaction and reduce opacity
- [ ] Loading states use `role="status"`
- [ ] Lists use `role="list"` and `role="listitem"`
