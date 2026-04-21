---
paths:
  - '**/chart*/**'
  - '**/*Chart*.svelte'
  - '**/*chart*.svelte'
  - '**/dashboard*/**'
---

# Chart Rules

## Stack

- **layerchart** - Svelte-native charting library
- **d3-scale** - Scale functions (scaleUtc, scaleLinear, scaleOrdinal)
- **d3-shape** - Curve functions (curveNatural, curveMonotoneX)
- **Chart primitives** - Chart.Container, Chart.Tooltip from the design system

## Chart.Container

Wrap all charts in Chart.Container with a config prop:

```svelte
<script>
  import * as Chart from '$lib/components/ui/primitives/chart/index.js';

  const chartConfig = {
    temperature: { label: 'Temperature', color: 'var(--chart-1)' },
    humidity: { label: 'Humidity', color: 'var(--chart-2)' }
  };
</script>

<Chart.Container config={chartConfig} class="aspect-auto h-[220px] w-full">
  <LineChart ... />
</Chart.Container>
```

The config maps data keys to labels and colors for tooltips and legends.

## Chart Token Colors

Use semantic chart colors from the theme:

```javascript
const chartColors = [
  'var(--chart-1)', // purple
  'var(--chart-2)', // red-orange
  'var(--chart-3)', // green
  'var(--chart-4)', // yellow
  'var(--chart-5)' // coral
];
```

In series config:

```javascript
let series = $derived(
  Object.entries(signals).map(([key, label], i) => ({
    key,
    label,
    color: chartColors[i % chartColors.length]
  }))
);
```

## LineChart Pattern

Basic line chart with layerchart:

```svelte
<script>
  import { LineChart } from 'layerchart';
  import { scaleUtc, scaleLinear } from 'd3-scale';
  import { curveNatural } from 'd3-shape';

  let { data, xKey = 'timestamp', yMin, yMax } = $props();

  const series = [{ key: 'value', label: 'Value', color: 'var(--chart-1)' }];
</script>

<LineChart
  {data}
  x={xKey}
  xScale={scaleUtc()}
  yScale={scaleLinear()}
  yDomain={[yMin, yMax]}
  {series}
  props={{
    spline: {
      curve: curveNatural,
      strokeWidth: 1.5
    }
  }}
/>
```

## D3 Scale Usage

### Time Scale (x-axis with dates)

```javascript
import { scaleUtc } from 'd3-scale';

xScale={scaleUtc()}
```

### Linear Scale (numeric values)

```javascript
import { scaleLinear } from 'd3-scale';

yScale={scaleLinear()}
yDomain={[0, 100]}  // fixed domain
```

### Dynamic Domain

```javascript
// Let layerchart calculate domain from data
yDomain = { undefined };

// Or calculate manually
let yDomain = $derived([
  Math.min(...data.map((d) => d.value)),
  Math.max(...data.map((d) => d.value))
]);
```

## Streaming Data Pattern

For real-time charts with a sliding window:

```svelte
<script>
  let {
    data = [],
    maxPoints = 100,  // sliding window size
    ...
  } = $props();

  // Slice to maxPoints for display
  let displayData = $derived(
    maxPoints && data.length > maxPoints 
      ? data.slice(-maxPoints) 
      : data
  );

  // Add index for stable x positioning
  let indexedData = $derived(
    displayData.map((d, i) => ({ ...d, _index: i }))
  );

  // Use index-based x scale for streaming
  let useIndexX = $derived(maxPoints !== undefined);
  let xDomain = $derived(
    useIndexX ? [0, (maxPoints || displayData.length) - 1] : undefined
  );
</script>

<LineChart
  data={indexedData}
  x={useIndexX ? '_index' : xKey}
  xScale={useIndexX ? scaleLinear() : scaleUtc()}
  {xDomain}
  ...
/>
```

## Axis Configuration

```svelte
<LineChart
  axis="both"  // "both" | "x" | "y" | "none"
  props={{
    xAxis: {
      format: (date) => formatTime(date)  // custom formatter
    },
    yAxis: {
      ticks: [0, 25, 50, 75, 100],  // explicit tick values
      format: (v) => `${v}%`
    },
    grid: {
      y: true,
      x: false,
      yTicks: [0, 25, 50, 75, 100]
    }
  }}
/>
```

## Time Formatting

Relative time (MM:SS from start):

```javascript
let baseTimestamp = $derived(
  displayData.length > 0 && displayData[0][xKey] ? new Date(displayData[0][xKey]).getTime() : 0
);

function formatTime(date) {
  if (!baseTimestamp) return '00:00';
  const diffMs = date.getTime() - baseTimestamp;
  const totalSeconds = Math.floor(diffMs / 1000);
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;
  return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}
```

## Curve Types

```javascript
import { curveNatural, curveMonotoneX, curveStep, curveLinear } from 'd3-shape';

props={{
  spline: {
    curve: curveNatural,    // smooth natural curve
    // curve: curveMonotoneX, // monotonic (no overshooting)
    // curve: curveStep,      // stepped line
    // curve: curveLinear,    // straight lines
    strokeWidth: 1.5
  }
}}
```

## Tooltip Integration

```svelte
<LineChart
  tooltip={false}  // disable default tooltip
  ...
/>

<!-- Or use custom Chart.Tooltip -->
<Chart.Container config={chartConfig}>
  <LineChart tooltip={{ ... }} />
</Chart.Container>
```

## Legend Pattern

Manual legend below chart:

```svelte
{#if series.length > 0}
  <div class="flex items-center justify-center gap-10">
    {#each series as s (s.key)}
      <div class="flex items-center gap-2">
        <div class="size-2 rounded-full bg-(--legend-color)" style:--legend-color={s.color}></div>
        <span class="text-foreground text-sm">{s.label}</span>
      </div>
    {/each}
  </div>
{/if}
```

For a complete chart pattern example, see the `sensor-chart` pattern source in `$lib/components/ui/patterns/sensor-chart/`.
