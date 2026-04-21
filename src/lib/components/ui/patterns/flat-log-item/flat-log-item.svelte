<script>
  import { cn } from '$lib/utils.js';
  import * as Item from '$lib/components/ui/primitives/item/index.js';
  import Badge from '$lib/components/ui/primitives/badge/index.js';
  import CircleCheckIcon from '@lucide/svelte/icons/circle-check';
  import TriangleAlertIcon from '@lucide/svelte/icons/triangle-alert';
  import CircleXIcon from '@lucide/svelte/icons/circle-x';
  import InfoIcon from '@lucide/svelte/icons/info';
  import { marked } from 'marked';

  marked.setOptions({ breaks: true, gfm: true });

  const STATUS_MAP = {
    good: { stripe: 'bg-atai-good', badge: 'bg-atai-good' },
    warning: { stripe: 'bg-atai-warning', badge: 'bg-atai-warning' },
    critical: { stripe: 'bg-atai-critical', badge: 'bg-atai-critical' },
    neutral: { stripe: 'bg-muted-foreground', badge: 'bg-muted-foreground' }
  };

  /**
   * @typedef {'good' | 'warning' | 'critical' | 'neutral'} Status
   */

  /**
   * @typedef {Object} Props
   * @property {string} title - status label text (e.g. "HEALTHY", "VIOLATION")
   * @property {string} message - log message body
   * @property {Status} status - drives icon, color bar, and title color
   * @property {string} [detail] - optional right-aligned metadata (e.g. timestamp "00:01:29", row range "Rows 6144–7168")
   * @property {string} [class] - additional CSS classes
   */

  /** @type {Props} */
  let { title, message, status, detail, class: className, ...restProps } = $props();

  let tier = $derived(STATUS_MAP[status] ?? STATUS_MAP.neutral);
</script>

<Item.Root
  variant="outline"
  class={cn('relative flex-col items-stretch overflow-hidden pl-5', className)}
  {...restProps}
>
  <div class={cn('absolute inset-y-0 left-0 w-1', tier.stripe)}></div>
  <Item.Header>
    <Badge
      variant="outline"
      class={cn(
        'flex items-center gap-1 border-transparent pl-1 font-mono text-xs font-medium text-black/70 uppercase [&>svg]:size-4',
        tier.badge
      )}
    >
      {#if status === 'good'}
        <CircleCheckIcon class="size-4" strokeWidth={1.5} aria-hidden="true" />
      {:else if status === 'warning'}
        <TriangleAlertIcon class="size-4" strokeWidth={1.5} aria-hidden="true" />
      {:else if status === 'critical'}
        <CircleXIcon class="size-4" strokeWidth={1.5} aria-hidden="true" />
      {:else}
        <InfoIcon class="size-4" strokeWidth={1.5} aria-hidden="true" />
      {/if}
      {title}
    </Badge>
    {#if detail}
      <span class="text-foreground font-mono text-sm font-normal">{detail}</span>
    {/if}
  </Item.Header>

  <Item.Content>
    <div class="text-muted-foreground prose-sm leading-relaxed [&_ol]:list-decimal [&_ol]:pl-5 [&_p]:my-1 [&_ul]:list-disc [&_ul]:pl-5 [&_li]:my-0.5 [&_strong]:text-foreground">
      {@html marked(message)}
    </div>
  </Item.Content>
</Item.Root>