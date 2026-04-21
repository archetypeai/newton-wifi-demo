<script>
  import { LinkPreview as HoverCardPrimitive } from 'bits-ui';

  let { open = $bindable(false), ...restProps } = $props();
</script>

<HoverCardPrimitive.Root bind:open {...restProps} />