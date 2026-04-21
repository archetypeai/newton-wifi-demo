<script module>
  import { tv } from 'tailwind-variants';

  export const switchVariants = tv({
    base: 'peer inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent shadow-xs transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=unchecked]:bg-input',
    variants: {
      size: {
        sm: 'h-4 w-7',
        default: 'h-5 w-9',
        lg: 'h-6 w-11'
      }
    },
    defaultVariants: {
      size: 'default'
    }
  });

  export const switchThumbVariants = tv({
    base: 'pointer-events-none block h-4 w-4 rounded-full bg-background shadow-lg ring-0 transition-transform data-[state=checked]:translate-x-4 data-[state=unchecked]:translate-x-0',
    variants: {
      size: {
        sm: 'h-3 w-3 data-[state=checked]:translate-x-3',
        default: 'h-4 w-4 data-[state=checked]:translate-x-4',
        lg: 'h-5 w-5 data-[state=checked]:translate-x-5'
      }
    },
    defaultVariants: {
      size: 'default'
    }
  });
</script>

<script>
  import { Switch as SwitchPrimitive } from 'bits-ui';
  import { cn } from '$lib/utils.js';

  let {
    ref = $bindable(null),
    checked = $bindable(false),
    class: className,
    size = 'default',
    ...restProps
  } = $props();
</script>

<SwitchPrimitive.Root
  bind:ref
  bind:checked
  data-slot="switch"
  class={cn(switchVariants({ size }), className)}
  {...restProps}
>
  <SwitchPrimitive.Thumb data-slot="switch-thumb" class={cn(switchThumbVariants({ size }))} />
</SwitchPrimitive.Root>