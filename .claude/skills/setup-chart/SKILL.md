---
name: setup-chart
description: Sets up data visualizations using layerchart and the Chart primitive. Use when creating line charts, scatter plots, area charts, time series visualizations, sensor displays, embedding plots, streaming data charts, or any data visualization component. Also use when the user asks about charting, graphing, plotting data, visualizing metrics, displaying real-time sensor data, or showing scatter/cluster plots.
---

# Setting Up Charts

Build charts using layerchart wrapped in the Chart.Container primitive.

## Discovering Components

Before building, check which components are installed in the project already:

1. List `$lib/components/ui/primitives/` and `$lib/components/ui/patterns/` to discover available primitives and patterns
2. Only use components that actually exist in the project
3. Charts require at minimum: `chart`. For card-wrapped charts: `card`, `chart`

## Chart Primitive Installation

The `chart` primitive is a multi-file package (chart-container, chart-style, chart-tooltip, scatter-tooltip, chart-utils, index). These files use relative imports between each other (e.g., `./chart-utils.js`).

**NEVER manually create chart primitive files.** Always install via the registry:

```bash
npx shadcn-svelte@latest add --registry https://design-system.archetypeai.workers.dev/r chart
```

If you create individual files by hand, relative imports will break and the chart will fail to render.

## Choosing a Chart Type

| User wants                                                          | Pattern      | Reference                                                  |
| ------------------------------------------------------------------- | ------------ | ---------------------------------------------------------- |
| Line chart, time series, sensor data, streaming lines               | SensorChart  | [references/sensor-chart.md](references/sensor-chart.md)   |
| Scatter plot, cluster visualization, embedding plot, 2D point cloud | ScatterChart | [references/scatter-chart.md](references/scatter-chart.md) |

Read the appropriate reference file for pattern-specific props, complete examples, and data preparation.

## Sample Data

**WARNING: Always `cp` the CSV files. NEVER recreate or rewrite the CSV data.**

Forbidden methods for CSVs: `Write` tool, `cat >`, `echo >`, heredoc. These will corrupt or truncate the data.

### Time Series Data (for SensorChart)

```bash
mkdir -p src/lib/data
cp data/timeseries.csv src/lib/data/timeseries.csv
```

174 rows of accelerometer + gyroscope readings. Columns: `timestamp`, `accel_x`, `accel_y`, `accel_z`, `gyro_x`.

### Embedding Data (for ScatterChart)

```bash
mkdir -p src/lib/data
cp data/embedding.csv src/lib/data/embedding.csv
```

40 rows of 2D embedding coordinates. Columns: `file_path`, `variates`, `indices`, `read_indices`, `window_sizes`, `sensor_timestamps`, `timestamps`, `embeddings_1`, `embeddings_2`.

For scatter charts, map `embeddings_1` to x and `embeddings_2` to y.

## CSV Loading Pattern

Load CSV data using Vite's `?raw` import:

```svelte
<script>
  import timeseriesCsv from '$lib/data/timeseries.csv?raw';

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

  const rawRows = parseCsv(timeseriesCsv);
  const data = rawRows.map((row) => ({
    timestamp: new Date(row.timestamp),
    accel_x: parseFloat(row.accel_x),
    accel_y: parseFloat(row.accel_y),
    accel_z: parseFloat(row.accel_z)
  }));
</script>
```

## Chart.Container

Always wrap charts in `Chart.Container` with a config:

```svelte
<Chart.Container config={chartConfig} class="aspect-auto h-[220px] w-full">
  <!-- chart content -->
</Chart.Container>
```

The config maps data keys to labels and colors for tooltips/legends.

## Semantic Chart Colors

Use theme colors for consistency:

```javascript
const chartColors = [
  'var(--chart-1)', // purple
  'var(--chart-2)', // red-orange
  'var(--chart-3)', // green
  'var(--chart-4)', // yellow
  'var(--chart-5)' // coral
];
```

Build series config:

```javascript
let series = $derived(
  Object.entries(signals).map(([key, label], i) => ({
    key,
    label,
    color: chartColors[i % chartColors.length]
  }))
);
```

## D3 Scales

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

## Streaming Data Pattern

For real-time charts with a sliding window, use `maxPoints`. Both SensorChart and ScatterChart support this prop.

The pattern works by:

1. Slicing data to keep only the last `maxPoints` entries
2. For line charts: re-indexing x-axis with `_index` (not timestamps) so the line scrolls smoothly
3. For scatter charts: the sliding window just drops old points

```javascript
let displayData = $derived(maxPoints && data.length > maxPoints ? data.slice(-maxPoints) : data);
```

See the pattern-specific reference files for complete streaming examples.

## Axis Configuration

```svelte
<LineChart
  axis="both"
  props={{
    xAxis: {
      format: (date) => formatTime(date)
    },
    yAxis: {
      ticks: [0, 25, 50, 75, 100],
      format: (v) => `${v}%`
    },
    grid: {
      y: true,
      x: false
    }
  }}
/>
```

## Curve Types

```javascript
import { curveNatural, curveMonotoneX, curveStep, curveLinear } from 'd3-shape';

props={{
  spline: {
    curve: curveNatural,    // smooth natural curve
    strokeWidth: 1.5
  }
}}
```

## Legend Pattern

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

## Pattern References

- [references/sensor-chart.md](references/sensor-chart.md) — SensorChart pattern: line charts, time series, sensor data, streaming lines
- [references/scatter-chart.md](references/scatter-chart.md) — ScatterChart pattern: scatter plots, cluster visualizations, embedding plots
