<script>
  import Command from './command.svelte';
  import * as Dialog from '$lib/components/ui/primitives/dialog/index.js';
  import { cn } from '$lib/utils.js';
  let {
    open = $bindable(false),
    ref = $bindable(null),
    value = $bindable(''),
    title = 'Command Palette',
    description = 'Search for a command to run',
    portalProps,
    children,
    class: className,
    ...restProps
  } = $props();
</script>

<Dialog.Root bind:open {...restProps}>
  <Dialog.Header class="sr-only">
    <Dialog.Title>{title}</Dialog.Title>
    <Dialog.Description>{description}</Dialog.Description>
  </Dialog.Header>
  <Dialog.Content class={cn('overflow-hidden p-0 sm:max-w-2xl', className)} {portalProps}>
    <Command
      class="**:data-command-group:px-2 **:data-command-input:h-12 **:data-command-item:px-2 **:data-command-item:py-3 **:data-[slot=command-input-wrapper]:h-12 [&_[data-command-group]:not([hidden])_~[data-command-group]]:pt-0 [&_[data-command-input-wrapper]_svg]:h-5 [&_[data-command-input-wrapper]_svg]:w-5 [&_[data-command-item]_svg]:h-5 [&_[data-command-item]_svg]:w-5"
      {...restProps}
      bind:value
      bind:ref
      {children}
    />
  </Dialog.Content>
</Dialog.Root>