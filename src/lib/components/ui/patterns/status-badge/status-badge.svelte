<script>
  import { cn, clamp, healthTier } from '$lib/utils.js';
  import Badge from '$lib/components/ui/primitives/badge/index.js';
  import {
    Avatar,
    AvatarImage,
    AvatarFallback
  } from '$lib/components/ui/primitives/avatar/index.js';

  /**
   * @typedef {Object} Props
   * @property {string} [label="NW CONVEYOR D"] - status label text
   * @property {number} [percentage=80] - health percentage (0-100, clamped)
   * @property {string} [initial="d"] - fallback letter for avatar
   * @property {string} [image] - optional avatar image URL
   * @property {string} [class] - additional CSS classes
   */

  /** @type {Props} */
  let {
    label = 'NW CONVEYOR D',
    percentage = 80,
    initial = 'd',
    image,
    class: className,
    ...restProps
  } = $props();

  let clampedScore = $derived(clamp(percentage));
  let bgColor = $derived(healthTier(clampedScore));
</script>

<Badge
  variant="outline"
  class={cn(
    'bg-muted/80 grid w-50 grid-cols-[auto_1fr_auto] items-center gap-2 border px-2 py-0.5',
    className
  )}
  {...restProps}
>
  <!-- avatar with green/yellow/red background depending on percentage -->
  <Avatar class="-ml-1.5 flex size-9 shrink-0 items-center justify-center">
    {#if image}
      <AvatarImage src={image} alt={label} />
    {/if}
    <AvatarFallback
      class="{bgColor} flex items-center justify-center text-sm font-medium text-black/70"
    >
      {initial.toUpperCase()}
    </AvatarFallback>
  </Avatar>
  <!-- label text -->
  <span class="text-foreground min-w-0 truncate font-mono text-sm whitespace-nowrap uppercase">
    {label}
  </span>
  <!-- percentage -->
  <span class="text-foreground/70 font-mono text-sm whitespace-nowrap">
    {percentage}%
  </span>
</Badge>