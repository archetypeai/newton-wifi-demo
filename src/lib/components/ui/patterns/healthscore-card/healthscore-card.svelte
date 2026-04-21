<script>
  import { clamp, healthTier } from '$lib/utils.js';
  import { CardDescription } from '$lib/components/ui/primitives/card/index.js';
  import { Progress } from '$lib/components/ui/primitives/progress/index.js';
  import BackgroundCard from '$lib/components/ui/patterns/background-card/index.js';
  import HeartPulseIcon from '@lucide/svelte/icons/heart-pulse';

  /**
   * @typedef {Object} Props
   * @property {string} [title="HEALTH SCORE"] - card header label
   * @property {import('svelte').Component} [icon] - lucide icon component for header
   * @property {string} [summary] - descriptive text below title
   * @property {number} [score=92] - health score value (0-100, clamped)
   * @property {string} [class] - additional CSS classes
   */

  /** @type {Props} */

  let {
    title = 'HEALTH SCORE',
    icon: Icon = HeartPulseIcon,
    summary = 'Factory floor in optimal condition. All machines running smoothly with no early signs of wear.',
    score = 92,
    class: className,
    ...restProps
  } = $props();

  let clampedScore = $derived(clamp(score));
  let progressColor = $derived(healthTier(clampedScore));
</script>

<BackgroundCard {title} icon={Icon} class={className} {...restProps}>
  <!-- state summary -->
  <CardDescription class="text-foreground text-2xl font-normal">
    {summary}
  </CardDescription>

  <!-- score section -->
  <div class="flex flex-col">
    <!-- score value-->
    <div class="text-muted-foreground flex flex-row items-baseline gap-2 font-mono uppercase">
      <p class="text-foreground text-3xl font-medium md:text-4xl">
        {clampedScore}
      </p>
      <p class="text-muted-foreground text-sm">%</p>
    </div>

    <!-- score progress bar -->
    <div class="mt-2 flex flex-col gap-2">
      <div class="flex w-full items-center justify-between">
        <span>0</span>
        <span>50</span>
        <span>100</span>
      </div>
      <Progress
        max={100}
        value={clampedScore}
        class="bg-primary/20 h-1.25"
        indicatorClass={progressColor}
        aria-label="{title} {clampedScore}%"
      />
    </div>
  </div>
</BackgroundCard>