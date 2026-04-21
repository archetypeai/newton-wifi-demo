<script>
  import MinusIcon from '@lucide/svelte/icons/minus';

  let { ref = $bindable(null), children, ...restProps } = $props();
</script>

<div bind:this={ref} data-slot="input-otp-separator" role="separator" {...restProps}>
  {#if children}
    {@render children?.()}
  {:else}
    <MinusIcon />
  {/if}
</div>