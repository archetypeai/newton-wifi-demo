---
paths:
  - '**/components/**/*.svelte'
  - '$lib/**/*.svelte'
  - '**/primitives/**/*.svelte'
  - '**/patterns/**/*.svelte'
---

# Component Authoring Rules

## Props Pattern

Every component should destructure props using `$props()` with this standard pattern:

```svelte
<script>
  import { cn } from '$lib/utils.js';

  let { ref = $bindable(null), class: className, children, ...restProps } = $props();
</script>
```

Key points:

- `ref = $bindable(null)` - enables parent to bind to DOM element
- `class: className` - rename to avoid reserved word conflict
- `children` - snippet for slot content
- `...restProps` - capture remaining props for spreading

## data-slot Attributes

Add `data-slot` to root elements for identification and styling hooks:

```svelte
<div bind:this={ref} data-slot="card" class={cn('bg-card ...', className)} {...restProps}>
  {@render children?.()}
</div>
```

This enables parent styling like `*:data-[slot=card]:p-4`.

## Class Merging with cn()

Always use `cn()` for class composition - never raw string concatenation:

```svelte
<!-- Correct -->
<div class={cn('bg-card text-card-foreground', className)}>

<!-- Wrong -->
<div class={`bg-card text-card-foreground ${className}`}>
```

`cn()` uses clsx + tailwind-merge to properly handle class conflicts.

## bits-ui Wrapper Pattern

When wrapping bits-ui primitives, import the primitive and wrap it:

```svelte
<script>
  import { Select as SelectPrimitive } from 'bits-ui';
  import { cn } from '$lib/utils.js';

  let { ref = $bindable(null), class: className, children, ...restProps } = $props();
</script>

<SelectPrimitive.Trigger
  bind:ref
  data-slot="select-trigger"
  class={cn('border-input bg-transparent ...', className)}
  {...restProps}
>
  {@render children?.()}
</SelectPrimitive.Trigger>
```

For the full primitives catalog with import paths, see `@skills/build-pattern`.

## tailwind-variants (tv)

Define variants in `<script module>` for reuse and export:

```svelte
<script module>
  import { cn } from '$lib/utils.js';
  import { tv } from 'tailwind-variants';

  export const buttonVariants = tv({
    base: 'inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors',
    variants: {
      variant: {
        default: 'bg-primary text-primary-foreground hover:bg-primary/90',
        destructive: 'bg-destructive text-white hover:bg-destructive/90',
        outline: 'border bg-background hover:bg-accent',
        secondary: 'bg-secondary text-secondary-foreground hover:bg-secondary/80',
        ghost: 'hover:bg-accent hover:text-accent-foreground',
        link: 'text-primary underline-offset-4 hover:underline'
      },
      size: {
        default: 'h-9 px-4 py-2',
        sm: 'h-8 px-3 rounded-md',
        lg: 'h-10 px-6 rounded-md',
        icon: 'size-9'
      }
    },
    defaultVariants: {
      variant: 'default',
      size: 'default'
    }
  });
</script>

<script>
  let { variant = 'default', size = 'default', class: className, ...restProps } = $props();
</script>

<button class={cn(buttonVariants({ variant, size }), className)} {...restProps}>
  {@render children?.()}
</button>
```

## Snippet Slots

Use `{@render}` for slot content:

```svelte
<!-- Default slot -->
{@render children?.()}

<!-- Named snippets (passed as props) -->
{#snippet icon()}
  <ChevronDown />
{/snippet}

<Button {icon}>Click me</Button>

<!-- In component, render the snippet prop -->
{@render icon?.()}
```

## restProps Spreading

Always spread `...restProps` on the root element to pass through attributes:

```svelte
<button
  bind:this={ref}
  data-slot="button"
  class={cn(buttonVariants({ variant, size }), className)}
  {type}
  {disabled}
  {...restProps}
>
  {@render children?.()}
</button>
```

## Conditional Rendering

Use standard Svelte `{#if}` blocks for conditional content:

```svelte
{#if href}
  <a bind:this={ref} data-slot="button" {href} {...restProps}>
    {@render children?.()}
  </a>
{:else}
  <button bind:this={ref} data-slot="button" {...restProps}>
    {@render children?.()}
  </button>
{/if}
```

## Icon Handling

Icons from Lucide use consistent sizing classes:

```svelte
<script>
  import ChevronDownIcon from '@lucide/svelte/icons/chevron-down';
</script>

<ChevronDownIcon class="size-4 opacity-50" />
```

Default icon sizing in buttons: `[&_svg:not([class*='size-'])]:size-4`

## Example: Complete Card Component

```svelte
<script>
  import { cn } from '$lib/utils.js';

  let { ref = $bindable(null), class: className, children, ...restProps } = $props();
</script>

<div
  bind:this={ref}
  data-slot="card"
  class={cn(
    'bg-card text-card-foreground flex flex-col gap-6 rounded-md border py-6 shadow-sm',
    className
  )}
  {...restProps}
>
  {@render children?.()}
</div>
```

## Example: Dialog Content with bits-ui

```svelte
<script>
  import { Dialog as DialogPrimitive } from 'bits-ui';
  import DialogPortal from './dialog-portal.svelte';
  import XIcon from '@lucide/svelte/icons/x';
  import * as Dialog from './index.js';
  import { cn } from '$lib/utils.js';

  let {
    ref = $bindable(null),
    class: className,
    portalProps,
    children,
    showCloseButton = true,
    ...restProps
  } = $props();
</script>

<DialogPortal {...portalProps}>
  <Dialog.Overlay />
  <DialogPrimitive.Content
    bind:ref
    data-slot="dialog-content"
    class={cn(
      'bg-background fixed top-[50%] left-[50%] z-50 w-full max-w-lg translate-x-[-50%] translate-y-[-50%] rounded-lg border p-6 shadow-lg',
      'data-[state=open]:animate-in data-[state=closed]:animate-out',
      className
    )}
    {...restProps}
  >
    {@render children?.()}
    {#if showCloseButton}
      <DialogPrimitive.Close class="absolute end-4 top-4 rounded-xs opacity-70 hover:opacity-100">
        <XIcon />
        <span class="sr-only">Close</span>
      </DialogPrimitive.Close>
    {/if}
  </DialogPrimitive.Content>
</DialogPortal>
```
