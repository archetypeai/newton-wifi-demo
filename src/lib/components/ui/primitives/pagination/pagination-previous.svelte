<script>
  import { Pagination as PaginationPrimitive } from 'bits-ui';
  import ChevronLeftIcon from '@lucide/svelte/icons/chevron-left';
  import { buttonVariants } from '@atai/ds-ui-svelte/atai/primitives/button/index.js';
  import { cn } from '$lib/utils.js';

  let { ref = $bindable(null), class: className, ...restProps } = $props();
</script>

<PaginationPrimitive.PrevButton
  bind:ref
  aria-label="Go to previous page"
  class={cn(
    buttonVariants({
      size: 'default',
      variant: 'ghost',
      class: 'gap-1 px-2.5 sm:ps-2.5'
    }),
    className
  )}
  {...restProps}
>
  <ChevronLeftIcon />
  <span class="hidden sm:block">Previous</span></PaginationPrimitive.PrevButton
>