# ScatterChart Pattern Reference

Scatter plots for cluster visualizations, embedding data, and 2D point clouds.

## Installation

```bash
npx shadcn-svelte@latest add --registry https://design-system.archetypeai.workers.dev/r scatter-chart
```

This installs `ScatterChart.svelte` and its dependencies (`card`, `chart`, `utils`, `layerchart`, `d3-scale`).

## Props

| Prop          | Type                       | Default      | Description                                                                |
| ------------- | -------------------------- | ------------ | -------------------------------------------------------------------------- |
| `title`       | string                     | `"SCATTER"`  | Card header label                                                          |
| `icon`        | Component                  | undefined    | Lucide icon component for header                                           |
| `data`        | Array<Record<string, any>> | `[]`         | Array of data points                                                       |
| `xKey`        | string                     | `"x"`        | Data key for x-axis values                                                 |
| `yKey`        | string                     | `"y"`        | Data key for y-axis values                                                 |
| `categoryKey` | string                     | undefined    | Data key for category grouping; when set, points split into colored series |
| `categories`  | Record<string, string>     | `{}`         | Map of category value to display label                                     |
| `maxPoints`   | number                     | undefined    | Enables streaming mode with sliding window                                 |
| `xMin`        | number                     | **required** | Minimum x-axis value                                                       |
| `xMax`        | number                     | **required** | Maximum x-axis value                                                       |
| `yMin`        | number                     | **required** | Minimum y-axis value                                                       |
| `yMax`        | number                     | **required** | Maximum y-axis value                                                       |
| `xTicks`      | number[]                   | undefined    | Explicit x-axis tick values                                                |
| `yTicks`      | number[]                   | undefined    | Explicit y-axis tick values                                                |
| `class`       | string                     | undefined    | Additional CSS classes                                                     |

## Key Behaviors

- **Category mode** (`categoryKey` + `categories` set): Points are split into colored series by category value. Each category gets its own legend entry and color from theme palette.
- **Single series mode** (no `categoryKey`): All points rendered as one series with `--chart-1` color.
- **Streaming mode** (`maxPoints` set): Sliding window drops oldest points as new ones arrive.
- **Tooltip**: Uses voronoi-based hover with `Chart.ScatterTooltip` showing x/y coordinates.
- **Scales**: Both axes use `scaleLinear()` (numeric data only, no time axis).

## Preparing Embedding Data

The `embedding.csv` contains dimensionality-reduced coordinates. To prepare it for ScatterChart:

```svelte
<script>
  import embeddingCsv from '$lib/data/embedding.csv?raw';

  function parseCsv(csvText) {
    const lines = csvText
      .trim()
      .split('\n')
      .filter((line) => line.trim());
    if (lines.length === 0) return [];
    const headers = lines[0].split(',').map((h) => h.trim());
    return lines.slice(1).map((line) => {
      const values = line.split(',');
      const row = {};
      headers.forEach((header, index) => {
        row[header] = values[index]?.trim() || '';
      });
      return row;
    });
  }

  const rawRows = parseCsv(embeddingCsv);
  const data = rawRows.map((row) => ({
    x: parseFloat(row.embeddings_1),
    y: parseFloat(row.embeddings_2)
  }));
</script>
```

## Complete Example — Clustered Scatter

```svelte
<script>
  import ScatterChart from '$lib/components/ui/patterns/scatter-chart/index.js';
  import ScatterChartIcon from '@lucide/svelte/icons/scatter-chart';
  import embeddingCsv from '$lib/data/embedding.csv?raw';

  function parseCsv(csvText) {
    const lines = csvText
      .trim()
      .split('\n')
      .filter((line) => line.trim());
    if (lines.length === 0) return [];
    const headers = lines[0].split(',').map((h) => h.trim());
    return lines.slice(1).map((line) => {
      const values = line.split(',');
      const row = {};
      headers.forEach((header, index) => {
        row[header] = values[index]?.trim() || '';
      });
      return row;
    });
  }

  const rawRows = parseCsv(embeddingCsv);
  const data = rawRows.map((row) => ({
    x: parseFloat(row.embeddings_1),
    y: parseFloat(row.embeddings_2),
    cluster:
      parseFloat(row.embeddings_1) < -2
        ? 'left'
        : parseFloat(row.embeddings_1) > 2
          ? 'right'
          : 'center'
  }));

  const categories = {
    left: 'Cluster A',
    center: 'Cluster B',
    right: 'Cluster C'
  };
</script>

<ScatterChart
  title="EMBEDDING CLUSTERS"
  icon={ScatterChartIcon}
  {data}
  categoryKey="cluster"
  {categories}
  xMin={-10}
  xMax={5}
  yMin={-6}
  yMax={10}
  xTicks={[-10, -5, 0, 5]}
  yTicks={[-5, 0, 5, 10]}
/>
```

## Complete Example — Streaming Scatter

```svelte
<script>
  import { onMount, onDestroy } from 'svelte';
  import ScatterChart from '$lib/components/ui/patterns/scatter-chart/index.js';
  import ScatterChartIcon from '@lucide/svelte/icons/scatter-chart';

  let streamData = $state([]);
  let interval;

  const clusters = ['alpha', 'beta', 'gamma'];
  const categories = { alpha: 'Alpha', beta: 'Beta', gamma: 'Gamma' };

  onMount(() => {
    interval = setInterval(() => {
      const cluster = clusters[Math.floor(Math.random() * clusters.length)];
      const cx = cluster === 'alpha' ? -5 : cluster === 'beta' ? 0 : 3;
      const cy = cluster === 'alpha' ? 3 : cluster === 'beta' ? -2 : 5;
      streamData = [
        ...streamData,
        {
          x: cx + (Math.random() - 0.5) * 4,
          y: cy + (Math.random() - 0.5) * 4,
          cluster
        }
      ];
    }, 200);
  });

  onDestroy(() => clearInterval(interval));
</script>

<ScatterChart
  title="STREAMING EMBEDDINGS"
  icon={ScatterChartIcon}
  data={streamData}
  categoryKey="cluster"
  {categories}
  maxPoints={60}
  xMin={-10}
  xMax={5}
  yMin={-6}
  yMax={10}
  xTicks={[-10, -5, 0, 5]}
  yTicks={[-5, 0, 5, 10]}
/>
```

## Building Inline (Without Pattern)

If the `scatter-chart` pattern is not installed, use `card` + `chart` primitives with `ScatterChart` from layerchart:

```svelte
<script>
  import * as Chart from '$lib/components/ui/primitives/chart/index.js';
  import { ScatterChart } from 'layerchart';
  import { scaleLinear } from 'd3-scale';

  let { data } = $props();

  const chartConfig = {
    data: { label: 'Points', color: 'var(--chart-1)' }
  };

  const series = [
    {
      key: 'data',
      label: 'Points',
      color: 'var(--chart-1)',
      data: data.map((d) => ({ x: d.x, y: d.y }))
    }
  ];
</script>

<Chart.Container config={chartConfig} class="aspect-auto h-[220px] w-full">
  <ScatterChart
    {data}
    x="x"
    y="y"
    xScale={scaleLinear()}
    yScale={scaleLinear()}
    {series}
    legend={false}
    labels={false}
    props={{
      points: { fillOpacity: 0.6, strokeWidth: 1, r: 3 },
      highlight: { points: { r: 5 } },
      tooltip: { context: { mode: 'voronoi' } }
    }}
  >
    {#snippet tooltip()}
      <Chart.ScatterTooltip />
    {/snippet}
  </ScatterChart>
</Chart.Container>
```
