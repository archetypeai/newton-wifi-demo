<script>
  import { cn } from '$lib/utils.js';
  import * as InputGroup from '$lib/components/ui/primitives/input-group/index.js';
  import KeyRoundIcon from '@lucide/svelte/icons/key-round';
  import EyeIcon from '@lucide/svelte/icons/eye';
  import EyeOffIcon from '@lucide/svelte/icons/eye-off';

  /**
   * @typedef {Object} Props
   * @property {string} [value=''] - the API key string (bindable)
   * @property {string} [label] - accessible aria-label for the input
   * @property {string} [placeholder=''] - input placeholder text
   * @property {boolean} [readonly=false] - whether the input is read-only
   * @property {string} [class] - additional CSS classes on root
   */

  /** @type {Props} */
  let {
    value = $bindable(''),
    label,
    placeholder = '',
    readonly = false,
    class: className,
    ...restProps
  } = $props();

  let visible = $state(false);

  function toggleVisibility() {
    visible = !visible;
  }
</script>

<InputGroup.Root class={cn(className)} {...restProps}>
  <InputGroup.Addon>
    <KeyRoundIcon class="size-4" aria-hidden="true" />
  </InputGroup.Addon>
  <InputGroup.Input
    type={visible ? 'text' : 'password'}
    bind:value
    {placeholder}
    {readonly}
    aria-label={label}
  />
  {#if value}
    <InputGroup.Addon align="inline-end">
      <InputGroup.Button
        size="icon-xs"
        onclick={toggleVisibility}
        aria-label={visible ? 'Hide API key' : 'Show API key'}
      >
        {#if visible}
          <EyeOffIcon class="size-3.5" aria-hidden="true" />
        {:else}
          <EyeIcon class="size-3.5" aria-hidden="true" />
        {/if}
      </InputGroup.Button>
    </InputGroup.Addon>
  {/if}
</InputGroup.Root>