<script>
  import { PaneGroup as PaneGroupPrimitive } from 'paneforge';
  import { cn } from '$lib/utils.js';

  let { ref = $bindable(null), class: className, children, ...restProps } = $props();
</script>

<PaneGroupPrimitive
  bind:ref
  data-slot="resizable-pane-group"
  class={cn('', className)}
  {...restProps}
>
  {@render children?.()}
</PaneGroupPrimitive>