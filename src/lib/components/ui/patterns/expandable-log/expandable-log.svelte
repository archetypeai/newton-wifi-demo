<script>
  import { cn } from '$lib/utils.js';
  import * as Collapsible from '$lib/components/ui/primitives/collapsible/index.js';
  import * as Item from '$lib/components/ui/primitives/item/index.js';
  import Badge from '$lib/components/ui/primitives/badge/index.js';
  import ChevronDownIcon from '@lucide/svelte/icons/chevron-down';
  import ChevronUpIcon from '@lucide/svelte/icons/chevron-up';
  import ClockIcon from '@lucide/svelte/icons/clock';
  import ThumbsUpIcon from '@lucide/svelte/icons/thumbs-up';
  import ThumbsDownIcon from '@lucide/svelte/icons/thumbs-down';

  /**
   * @typedef {Object} LogEntry
   * @property {string} [id] - unique identifier for keyed iteration
   * @property {string} timestamp - formatted timestamp string
   * @property {string} message - log message content
   */

  /**
   * @typedef {Object} Props
   * @property {string} title - header title text
   * @property {string} description - header description text
   * @property {number} [count=0] - badge count displayed in header
   * @property {boolean} [open=false] - bindable collapsed/expanded state
   * @property {LogEntry[]} [logs=[]] - array of log entries to display
   * @property {string} [class] - additional CSS classes
   */

  /** @type {Props} */
  let {
    title,
    description,
    count = 0,
    open = $bindable(false),
    logs = [],
    class: className,
    ...restProps
  } = $props();
</script>

<div class={cn(className)} {...restProps}>
  <Collapsible.Root bind:open>
    <Collapsible.Trigger class="w-full cursor-pointer">
      <div class="flex flex-col gap-2">
        <!-- badge, title, description row -->
        <div class="flex w-full items-center gap-4">
          <!-- circular badge -->
          <Badge
            variant="number-default"
            class="bg-atai-good size-6 rounded-full border-0 text-sm text-black/70"
          >
            {count}
          </Badge>
          <!-- title and description -->
          <div class="flex min-w-0 flex-1 flex-col items-start gap-1">
            <h3 class="text-foreground text-left text-lg leading-tight font-normal">{title}</h3>
            <p class="text-muted-foreground">{description}</p>
          </div>
        </div>

        <!-- show less/show more trigger -->
        <div class="flex items-center gap-1.5 pl-10">
          <span class="text-foreground">{open ? 'Show Less' : 'Show More'}</span>
          {#if open}
            <ChevronUpIcon class="size-4" />
          {:else}
            <ChevronDownIcon class="size-4" />
          {/if}
        </div>
      </div>
    </Collapsible.Trigger>

    <Collapsible.Content>
      <div class="mt-4 pl-10">
        <div class="flex gap-4">
          <div class="bg-border w-px self-stretch"></div>
          <Item.Group class="flex flex-col gap-4">
            {#each logs as log (log.id || log.timestamp || log.message)}
              <Item.Root variant="default" class="flex flex-col gap-3 border-0 bg-transparent p-0">
                <Item.Content class="flex flex-col gap-3">
                  <!-- timestamp badge -->
                  <Badge variant="timestamp" class="flex w-fit items-center gap-1.5 px-2 py-1">
                    <ClockIcon class="size-5" />
                    <span class="text-background font-mono text-xs">{log.timestamp}</span>
                  </Badge>

                  <!-- log message -->
                  <p class="text-muted-foreground leading-relaxed whitespace-pre-wrap">
                    {log.message}
                  </p>

                  <!-- feedback actions -->
                  <Item.Actions class="mt-0">
                    <button
                      type="button"
                      class="text-muted-foreground hover:text-foreground rounded-xs p-1 transition-colors"
                      aria-label="Thumbs up"
                    >
                      <ThumbsUpIcon class="size-4" />
                    </button>
                    <button
                      type="button"
                      class="text-muted-foreground hover:text-foreground rounded-xs p-1 transition-colors"
                      aria-label="Thumbs down"
                    >
                      <ThumbsDownIcon class="size-4" />
                    </button>
                  </Item.Actions>
                </Item.Content>
              </Item.Root>
            {/each}
          </Item.Group>
        </div>
      </div>
    </Collapsible.Content>
  </Collapsible.Root>
</div>