<script>
  import { LinkPreview as HoverCardPrimitive } from 'bits-ui';

  let { ...restProps } = $props();
</script>

<HoverCardPrimitive.Portal {...restProps} />