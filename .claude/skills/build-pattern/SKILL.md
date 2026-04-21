---
name: build-pattern
description: Creates composite UI patterns by assembling design system primitives. Use when building reusable components that combine multiple primitives (Card, Button, Input, etc.), creating dashboard widgets, form groups, sensor cards, data displays, or any complex component from existing design system primitives. Also use when the user asks to create a "component" or "widget" that should follow design system conventions.
---

# Building Patterns

Patterns are composite components assembled from design system primitives.

## Decision: Pattern vs Extension

**Before building, fetch `https://design-system.archetypeai.workers.dev/r/patterns.json` and check if an existing pattern covers the use case — even partially. Use or extend it rather than creating a new one.**

**Build a pattern when:**

- Combining 3+ primitives into a reusable unit
- The combination will be used in multiple places
- The component has its own props/state logic

**Extend a primitive instead when:**

- Adding variants to a single primitive
- Customizing styling without composition

## Pattern Structure

```svelte
<script>
  import { cn } from '$lib/utils.js';
  import { Card, CardHeader, CardTitle, CardContent } from '$lib/components/ui/primitives/card/index.js';
  import { Button } from '$lib/components/ui/primitives/button/index.js';

  let { title, class: className, children, ...restProps } = $props();
</script>

<Card class={cn('p-4', className)} {...restProps}>
  <CardHeader>
    <CardTitle>{title}</CardTitle>
  </CardHeader>
  <CardContent>
    {@render children?.()}
  </CardContent>
</Card>
```

## Key Conventions

### Props Pattern

Always use this structure:

```javascript
let {
  ref = $bindable(null), // optional DOM reference
  class: className, // rename to avoid reserved word
  children, // snippet for slot content
  ...restProps // pass-through attributes
} = $props();
```

### Class Merging

Always use `cn()` for classes:

```svelte
<div class={cn('bg-card p-4', className)}>
```

Never concatenate strings directly.

### Spreading restProps

Always spread on the root element:

```svelte
<Card class={cn('p-4', className)} {...restProps}>
```

This ensures aria attributes, data attributes, and event handlers pass through.

### Rendering Children

Use `{@render}` for slot content:

```svelte
{@render children?.()}
```

## Available Primitives

Import primitives from `$lib/components/ui/primitives/` and patterns from `$lib/components/ui/patterns/`. Before building, list these directories to discover all installed components.

### Layout & Structure

- **card** - Card, CardHeader, CardTitle, CardContent, CardFooter, CardAction, CardDescription
- **separator** - Separator
- **resizable** - ResizablePane, ResizablePaneGroup, ResizableHandle
- **scroll-area** - ScrollArea
- **aspect-ratio** - AspectRatio
- **skeleton** - Skeleton
- **collapsible** - Collapsible.Root, Collapsible.Trigger, Collapsible.Content

### Forms & Inputs

- **button** - Button (with variants via `buttonVariants`)
- **input** - Input
- **textarea** - Textarea
- **label** - Label
- **checkbox** - Checkbox
- **switch** - Switch
- **select** - Select.Root, Select.Trigger, Select.Content, Select.Item
- **native-select** - NativeSelect
- **radio-group** - RadioGroup.Root, RadioGroup.Item
- **slider** - Slider
- **toggle** - Toggle
- **toggle-group** - ToggleGroup.Root, ToggleGroup.Item
- **input-otp** - InputOTP
- **input-group** - InputGroup
- **field** - Field, FieldSet, FieldGroup, FieldLabel, FieldDescription, FieldError, FieldContent

### Data Display

- **table** - Table, TableHeader, TableBody, TableRow, TableCell, TableHead, TableFooter, TableCaption
- **data-table** - createSvelteTable, FlexRender
- **chart** - Chart.Container, Chart.Tooltip
- **badge** - Badge
- **avatar** - Avatar, AvatarImage, AvatarFallback
- **kbd** - Kbd
- **empty** - Empty, EmptyHeader, EmptyMedia, EmptyTitle, EmptyDescription, EmptyContent
- **item** - Item, ItemGroup, ItemHeader, ItemContent, ItemTitle, ItemDescription, ItemActions, ItemMedia
- **spinner** - Spinner
- **progress** - Progress
- **carousel** - Carousel

### Overlays & Dialogs

- **dialog** - Dialog.Root, Dialog.Trigger, Dialog.Content, Dialog.Header, Dialog.Title, Dialog.Description, Dialog.Footer, Dialog.Close
- **alert-dialog** - AlertDialog.Root, AlertDialog.Trigger, AlertDialog.Content, AlertDialog.Header, AlertDialog.Title, AlertDialog.Description, AlertDialog.Footer, AlertDialog.Action, AlertDialog.Cancel
- **sheet** - Sheet.Root, Sheet.Trigger, Sheet.Content, Sheet.Header, Sheet.Title, Sheet.Description, Sheet.Footer, Sheet.Close
- **drawer** - Drawer.Root, Drawer.Trigger, Drawer.Content, Drawer.Header, Drawer.Title, Drawer.Description, Drawer.Footer, Drawer.Close
- **popover** - Popover.Root, Popover.Trigger, Popover.Content
- **hover-card** - HoverCard.Root, HoverCard.Trigger, HoverCard.Content
- **tooltip** - Tooltip.Root, Tooltip.Trigger, Tooltip.Content, Tooltip.Provider
- **command** - Command.Root, Command.Input, Command.List, Command.Item, Command.Group
- **sonner** - Toaster

### Navigation & Menus

- **tabs** - Tabs.Root, Tabs.List, Tabs.Trigger, Tabs.Content
- **accordion** - Accordion.Root, Accordion.Item, Accordion.Trigger, Accordion.Content
- **dropdown-menu** - DropdownMenu.Root, DropdownMenu.Trigger, DropdownMenu.Content, DropdownMenu.Item, DropdownMenu.Separator
- **context-menu** - ContextMenu.Root, ContextMenu.Trigger, ContextMenu.Content, ContextMenu.Item
- **menubar** - Menubar
- **navigation-menu** - NavigationMenu
- **breadcrumb** - Breadcrumb, BreadcrumbList, BreadcrumbItem, BreadcrumbLink, BreadcrumbSeparator, BreadcrumbPage
- **pagination** - Pagination
- **sidebar** - Sidebar, SidebarProvider, SidebarContent, SidebarGroup, SidebarGroupLabel, SidebarMenu, SidebarMenuItem, SidebarMenuButton, SidebarTrigger
- **button-group** - ButtonGroup, ButtonGroupText, ButtonGroupSeparator

### Date Picking

- **calendar** - Calendar
- **range-calendar** - RangeCalendar

### Feedback

- **alert** - Alert, AlertTitle, AlertDescription

## Example: Sensor Card Pattern

```svelte
<script>
  import { cn } from '$lib/utils.js';
  import { Card, CardHeader, CardTitle, CardContent } from '$lib/components/ui/primitives/card/index.js';
  import * as Chart from '$lib/components/ui/primitives/chart/index.js';

  let { title = 'SENSOR', icon: Icon, data = [], class: className, ...restProps } = $props();
</script>

<Card class={cn('p-4', className)} {...restProps}>
  <CardHeader class="flex flex-row items-center justify-between p-0">
    <CardTitle class="text-foreground font-mono text-base uppercase">
      {title}
    </CardTitle>
    {#if Icon}
      <Icon class="text-muted-foreground size-6" aria-hidden="true" />
    {/if}
  </CardHeader>
  <CardContent class="p-0">
    <Chart.Container config={{}} class="h-[220px] w-full">
      <!-- chart content -->
    </Chart.Container>
  </CardContent>
</Card>
```

## Detailed Conventions

See `@rules/components.md` for:

- bits-ui wrapper patterns
- tailwind-variants (tv) usage
- Conditional rendering patterns
- Icon handling
