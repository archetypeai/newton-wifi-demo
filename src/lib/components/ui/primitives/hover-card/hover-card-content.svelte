<script>
  import { LinkPreview as HoverCardPrimitive } from 'bits-ui';
  import { cn } from '$lib/utils.js';
  import HoverCardPortal from './hover-card-portal.svelte';
  let {
    ref = $bindable(null),
    class: className,
    align = 'center',
    sideOffset = 4,
    portalProps,
    ...restProps
  } = $props();
</script>

<HoverCardPortal {...portalProps}>
  <HoverCardPrimitive.Content
    bind:ref
    data-slot="hover-card-content"
    {align}
    {sideOffset}
    class={cn(
      'bg-popover text-popover-foreground data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0 data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-end-2 data-[side=right]:slide-in-from-start-2 data-[side=top]:slide-in-from-bottom-2 z-50 mt-3 w-64 rounded-xs border p-4 shadow-md outline-hidden outline-none',
      className
    )}
    {...restProps}
  />
</HoverCardPortal>