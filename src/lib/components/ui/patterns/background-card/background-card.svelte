<script>
  import { cn } from '$lib/utils.js';
  import {
    Card,
    CardHeader,
    CardTitle,
    CardContent
  } from '$lib/components/ui/primitives/card/index.js';

  /**
   * @typedef {Object} Props
   * @property {string} [title=""] - card header label (mono, uppercase)
   * @property {import('svelte').Component} [icon] - lucide icon component for header
   * @property {string} [class] - additional CSS classes
   */

  /** @type {Props} */
  let { title = '', icon: Icon = undefined, class: className, children, ...restProps } = $props();
</script>

<Card class={cn('p-4', className)} {...restProps}>
  <CardHeader class="flex flex-row items-center justify-between p-0">
    <CardTitle class="text-foreground font-mono text-base font-normal tracking-wider uppercase">
      {title}
    </CardTitle>
    {#if Icon}
      <Icon strokeWidth={1.25} class="text-muted-foreground size-6" aria-hidden="true" />
    {/if}
  </CardHeader>

  <CardContent class="flex min-h-0 flex-1 flex-col gap-6 p-0">
    {@render children?.()}
  </CardContent>
</Card>