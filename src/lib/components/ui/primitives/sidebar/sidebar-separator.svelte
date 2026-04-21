<script>
  import { Separator } from '@atai/ds-ui-svelte/atai/primitives/separator/index.js';
  import { cn } from '$lib/utils.js';
  let { ref = $bindable(null), class: className, ...restProps } = $props();
</script>

<Separator
  bind:ref
  data-slot="sidebar-separator"
  data-sidebar="separator"
  class={cn('bg-sidebar-border', className)}
  {...restProps}
/>