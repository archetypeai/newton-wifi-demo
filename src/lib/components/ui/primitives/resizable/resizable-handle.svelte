<script>
  import { PaneResizer as HandlePrimitive } from 'paneforge';
  import { cn } from '$lib/utils.js';
  import GripVerticalIcon from '@lucide/svelte/icons/grip-vertical';

  let { ref = $bindable(null), class: className, withHandle = false, ...restProps } = $props();
</script>

<HandlePrimitive
  bind:ref
  data-slot="resizable-handle"
  class={cn(
    'bg-border focus-visible:ring-ring relative flex w-px items-center justify-center after:absolute after:inset-y-0 after:left-1/2 after:w-1 after:-translate-x-1/2 focus-visible:ring-1 focus-visible:ring-offset-1 focus-visible:outline-none data-[direction=vertical]:h-px data-[direction=vertical]:w-full data-[direction=vertical]:after:left-0 data-[direction=vertical]:after:h-1 data-[direction=vertical]:after:w-full data-[direction=vertical]:after:translate-x-0 data-[direction=vertical]:after:-translate-y-1/2 [&[data-direction=vertical]>button]:h-4',
    className
  )}
  {...restProps}
>
  {#if withHandle}
    <button class="bg-border z-10 flex h-4 w-3 items-center justify-center rounded-xs border">
      <GripVerticalIcon class="h-2.5 w-2.5" />
    </button>
  {/if}
</HandlePrimitive>