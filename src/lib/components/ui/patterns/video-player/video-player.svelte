<script>
  import { cn, formatMMSS } from '$lib/utils.js';
  import { Card } from '$lib/components/ui/primitives/card/index.js';
  import { AspectRatio } from '$lib/components/ui/primitives/aspect-ratio/index.js';
  import { Button } from '$lib/components/ui/primitives/button/index.js';
  import Slider from '$lib/components/ui/primitives/slider/index.js';
  import PlayIcon from '@lucide/svelte/icons/play';
  import PauseIcon from '@lucide/svelte/icons/pause';

  /**
   * @typedef {Object} Props
   * @property {string} src - video source URL (remote or static path)
   * @property {string} [poster] - thumbnail image shown before playback
   * @property {boolean} [autoplay=false] - auto-start playback on mount
   * @property {boolean} [muted=false] - mute audio
   * @property {boolean} [controls=true] - show custom controls overlay
   * @property {number} [ratio=16/9] - aspect ratio for the video container
   * @property {string} [class] - additional CSS classes
   */

  /** @type {Props} */
  let {
    src,
    poster,
    autoplay = false,
    muted = false,
    controls = true,
    ratio = 16 / 9,
    class: className,
    ...restProps
  } = $props();

  let time = $state(0);
  let duration = $state(0);
  let paused = $state(true);
  let controlsVisible = $state(true);
  let hideTimer;

  function resetControls() {
    controlsVisible = true;
    clearTimeout(hideTimer);
  }

  function scheduleHide(delay) {
    hideTimer = setTimeout(() => {
      controlsVisible = false;
    }, delay);
  }

  function showControls() {
    resetControls();
    if (!paused) scheduleHide(2500);
  }

  function handleMouseLeave() {
    if (!paused) scheduleHide(1000);
  }
</script>

<Card
  class={cn('relative overflow-hidden p-0', className)}
  onmouseenter={showControls}
  onmousemove={showControls}
  onmouseleave={handleMouseLeave}
  {...restProps}
>
  <AspectRatio {ratio}>
    <video
      {src}
      {poster}
      {autoplay}
      {muted}
      bind:currentTime={time}
      bind:duration
      bind:paused
      class="absolute inset-0 h-full w-full rounded-xs object-cover"
      onplay={showControls}
      onpause={resetControls}
      onended={resetControls}
    ></video>

    {#if !controls && (paused || controlsVisible)}
      <button
        class={cn(
          'absolute inset-0 flex cursor-pointer items-center justify-center transition-opacity duration-300',
          paused || controlsVisible ? 'opacity-100' : 'pointer-events-none opacity-0'
        )}
        onclick={() => (paused = !paused)}
        aria-label={paused ? 'Play' : 'Pause'}
      >
        <span
          class="bg-background/30 hover:bg-background/40 flex size-14 items-center justify-center rounded-full backdrop-blur-xs transition-colors"
        >
          {#if paused}
            <PlayIcon strokeWidth={1.25} class="text-foreground size-7" aria-hidden="true" />
          {:else}
            <PauseIcon strokeWidth={1.25} class="text-foreground size-7" aria-hidden="true" />
          {/if}
        </span>
      </button>
    {/if}

    {#if controls}
      <div
        class={cn(
          'bg-card/20 absolute inset-x-0 bottom-0 flex items-center justify-between gap-4 px-3 py-1.5 backdrop-blur-xs transition-opacity duration-300',
          controlsVisible ? 'opacity-100' : 'pointer-events-none opacity-0'
        )}
      >
        <Button
          variant="default"
          size="icon"
          class="bg-background/30 hover:bg-background/40 cursor-pointer rounded-full"
          onclick={() => (paused = !paused)}
          aria-label={paused ? 'Play' : 'Pause'}
        >
          {#if paused}
            <PlayIcon strokeWidth={2} class="text-foreground size-4" aria-hidden="true" />
          {:else}
            <PauseIcon strokeWidth={2} class="text-foreground size-4" aria-hidden="true" />
          {/if}
        </Button>

        <Slider
          value={[time]}
          max={duration || 1}
          step={0.1}
          aria-label="Seek"
          class="**:data-[slot=slider-track]:bg-background/60 **:data-[slot=slider-range]:bg-foreground/90 **:data-[slot=slider-thumb]:bg-foreground max-w-100 min-w-0 flex-1 **:data-[slot=slider-thumb]:size-3.5 **:data-[slot=slider-thumb]:cursor-grab **:data-[slot=slider-thumb]:border-0 **:data-[slot=slider-thumb]:shadow-md **:data-[slot=slider-track]:h-1.5"
          onValueCommit={(v) => {
            time = v[0];
          }}
        />

        <span class="bg-background/30 text-foreground rounded-full px-3 py-1.5 whitespace-nowrap">
          {formatMMSS(time)} / {formatMMSS(duration)}
        </span>
      </div>
    {/if}
  </AspectRatio>
</Card>