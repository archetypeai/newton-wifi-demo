<script>
  import { cn } from '$lib/utils.js';
  import Logo from '$lib/components/ui/patterns/logo/index.js';
  import Badge from '$lib/components/ui/primitives/badge/index.js';
  import Button from '$lib/components/ui/primitives/button/index.js';
  import SeparatorIcon from '@lucide/svelte/icons/minus';
  import SunIcon from '@lucide/svelte/icons/sun';
  import MoonIcon from '@lucide/svelte/icons/moon';

  const browser = typeof window !== 'undefined';

  /**
   * @typedef {Object} Props
   * @property {import('svelte').Snippet} [partnerLogo] - optional partner logo snippet for co-branding
   * @property {string} [class] - additional CSS classes
   * @property {import('svelte').Snippet} [children] - action content for the right side
   * @property {boolean} [darkToggle=true] - show built-in dark mode toggle (opt out with false)
   */

  /** @type {Props} */
  let { partnerLogo, class: className, children, darkToggle = true, ...restProps } = $props();

  const prefersDark = browser && window.matchMedia('(prefers-color-scheme: dark)').matches;
  if (browser) document.documentElement.classList.toggle('dark', prefersDark);

  let darkMode = $state(prefersDark);

  $effect(() => {
    document.documentElement.classList.toggle('dark', darkMode);
  });

  function toggleDark() {
    const apply = () => {
      darkMode = !darkMode;
    };

    if (document.startViewTransition) {
      document.startViewTransition(apply);
    } else {
      apply();
    }
  }
</script>

<header
  class={cn('border-border flex items-center justify-between border-b px-4 py-2', className)}
  {...restProps}
>
  <div class="flex items-center gap-3">
    <Logo class="h-6" />
    {#if partnerLogo}
      <SeparatorIcon class="text-muted-foreground size-6" strokeWidth={1} aria-hidden="true" />
      {@render partnerLogo()}
    {:else}
      <SeparatorIcon class="text-muted-foreground size-6" strokeWidth={1} aria-hidden="true" />
      <Badge variant="outline" class="text-muted-foreground">Partner Logo</Badge>
    {/if}
  </div>

  {#if children || darkToggle}
    <div class="flex items-center gap-2">
      {#if children}
        {@render children()}
      {/if}
      {#if darkToggle}
        <Button variant="outline" size="icon" onclick={toggleDark} aria-label="Toggle dark mode">
          {#if darkMode}
            <SunIcon />
          {:else}
            <MoonIcon />
          {/if}
        </Button>
      {/if}
    </div>
  {/if}
</header>