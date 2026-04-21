<script>
  import { Calendar as CalendarPrimitive } from 'bits-ui';
  import { cn } from '$lib/utils.js';

  let { ref = $bindable(null), class: className, ...restProps } = $props();
</script>

<CalendarPrimitive.Cell
  bind:ref
  class={cn(
    'relative size-(--cell-size) p-0 text-center text-sm focus-within:z-20 [&:first-child[data-selected]_[data-bits-day]]:rounded-s-xs [&:last-child[data-selected]_[data-bits-day]]:rounded-e-xs',
    className
  )}
  {...restProps}
/>