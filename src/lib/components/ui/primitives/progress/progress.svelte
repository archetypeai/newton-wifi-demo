<script>
  import { Progress as ProgressPrimitive } from 'bits-ui';
  import { cn } from '$lib/utils.js';

  let {
    ref = $bindable(null),
    class: className,
    max = 100,
    value,
    indicatorClass = 'bg-primary',
    ...restProps
  } = $props();
</script>

<ProgressPrimitive.Root
  bind:ref
  data-slot="progress"
  class={cn('bg-primary/20 relative h-2 w-full overflow-hidden rounded-full', className)}
  {value}
  {max}
  {...restProps}
>
  <div
    data-slot="progress-indicator"
    class={cn('h-full w-full flex-1 transition-all', indicatorClass)}
    style="transform: translateX(-{100 - (100 * (value ?? 0)) / (max ?? 1)}%)"
  ></div>
</ProgressPrimitive.Root>