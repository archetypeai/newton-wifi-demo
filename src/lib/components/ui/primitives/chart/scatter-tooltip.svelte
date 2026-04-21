<script>
  import { getTooltipContext, Tooltip } from 'layerchart';

  const tooltipCtx = getTooltipContext();

  // layerchart can provide data in different ways depending on chart type
  const point = $derived.by(() => {
    // try direct data property first
    if (tooltipCtx.data?.x !== undefined) return tooltipCtx.data;
    // try payload array (like other charts use)
    if (tooltipCtx.payload?.[0]?.payload) return tooltipCtx.payload[0].payload;
    if (tooltipCtx.payload?.[0]) return tooltipCtx.payload[0];
    return null;
  });
</script>

<Tooltip.Root variant="none">
  <div
    class="border-border/50 bg-background grid min-w-32 items-start gap-1.5 rounded-xs border px-2.5 py-1.5 text-xs shadow-xl"
  >
    {#if point}
      <div class="flex items-center justify-between gap-4">
        <span class="text-muted-foreground">x</span>
        <span class="text-foreground font-mono font-medium tabular-nums"
          >{point.x?.toFixed(3) ?? '–'}</span
        >
      </div>
      <div class="flex items-center justify-between gap-4">
        <span class="text-muted-foreground">y</span>
        <span class="text-foreground font-mono font-medium tabular-nums"
          >{point.y?.toFixed(3) ?? '–'}</span
        >
      </div>
    {:else}
      <span class="text-muted-foreground">no data</span>
    {/if}
  </div>
</Tooltip.Root>