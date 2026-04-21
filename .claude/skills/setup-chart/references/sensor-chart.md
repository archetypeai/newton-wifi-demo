# SensorChart Pattern Reference

Line charts for time series data, sensor readings, and streaming signals.

## Installation

```bash
npx shadcn-svelte@latest add --registry https://design-system.archetypeai.workers.dev/r sensor-chart
```

This installs `SensorChart.svelte` and its dependencies (`card`, `chart`, `utils`, `layerchart`, `d3-scale`, `d3-shape`).

## Props

| Prop        | Type                                   | Default            | Description                                       |
| ----------- | -------------------------------------- | ------------------ | ------------------------------------------------- |
| `title`     | string                                 | `"UNKNOWN SENSOR"` | Card header label identifying the sensor          |
| `icon`      | Component                              | undefined          | Lucide icon component for header                  |
| `data`      | Array<Record<string, any>>             | `[]`               | Array of data points to chart                     |
| `signals`   | Record<string, string>                 | `{}`               | Map of data key to display label (defines series) |
| `xKey`      | string                                 | `"timestamp"`      | Data key for x-axis values                        |
| `maxPoints` | number                                 | undefined          | Enables streaming mode with sliding window        |
| `yMin`      | number                                 | **required**       | Minimum y-axis value                              |
| `yMax`      | number                                 | **required**       | Maximum y-axis value                              |
| `yTicks`    | number[]                               | undefined          | Explicit y-axis tick values                       |
| `axis`      | `"both"` \| `"x"` \| `"y"` \| `"none"` | `"both"`           | Which axes to display                             |
| `class`     | string                                 | undefined          | Additional CSS classes                            |

## Key Behaviors

- **Static mode** (no `maxPoints`): Uses `scaleUtc()` for x-axis with timestamp-based positioning. X-axis shows MM:SS relative to first data point.
- **Streaming mode** (`maxPoints` set): Uses `scaleLinear()` with index-based x positioning (`_index`). Data window slides as new points arrive.
- **Series**: Derived from `signals` prop. Each entry maps a data key to a display label and auto-assigns theme colors (`--chart-1` through `--chart-5`).
- **Curve**: Uses `curveNatural` from d3-shape for smooth lines.
- **Chart type**: Uses `LineChart` from layerchart — NOT `AreaChart` (which renders with unwanted fill).

## Complete Example — Static Data

```svelte
<script>
  import SensorChart from '$lib/components/ui/patterns/sensor-chart/index.js';
  import AudioWaveformIcon from '@lucide/svelte/icons/audio-waveform';
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

<SensorChart
  title="ACCELERATION SENSOR"
  icon={AudioWaveformIcon}
  {data}
  signals={{ accel_x: 'Accel X', accel_y: 'Accel Y', accel_z: 'Accel Z' }}
  yMin={-30}
  yMax={30}
  yTicks={[-30, -15, 0, 15, 30]}
/>
```

## Complete Example — Streaming Data

For real-time data with a sliding window, use the `maxPoints` prop and feed data incrementally:

```svelte
<script>
  import { onMount, onDestroy } from 'svelte';
  import SensorChart from '$lib/components/ui/patterns/sensor-chart/index.js';
  import ThermometerIcon from '@lucide/svelte/icons/thermometer';

  let streamingData = $state([]);
  let interval;

  onMount(() => {
    interval = setInterval(() => {
      streamingData = [
        ...streamingData,
        {
          timestamp: new Date(),
          gyro_x: (Math.random() - 0.5) * 4
        }
      ];
    }, 120);
  });

  onDestroy(() => clearInterval(interval));
</script>

<SensorChart
  title="GYROSCOPE SENSOR"
  icon={ThermometerIcon}
  data={streamingData}
  signals={{ gyro_x: 'Gyro X' }}
  maxPoints={50}
  yMin={-2}
  yMax={2}
  yTicks={[-2, -1, 0, 1, 2]}
  axis="y"
/>
```

## Building Inline (Without Pattern)

If the `sensor-chart` pattern is not installed, build the equivalent using `card` + `chart` primitives with `LineChart` from layerchart:

```svelte
<script>
  import * as Chart from '$lib/components/ui/primitives/chart/index.js';
  import { LineChart } from 'layerchart';
  import { scaleUtc, scaleLinear } from 'd3-scale';
  import { curveNatural } from 'd3-shape';

  let { data } = $props();

  const chartConfig = {
    value: { label: 'Value', color: 'var(--chart-1)' }
  };
</script>

<Chart.Container config={chartConfig} class="h-[220px] w-full">
  <LineChart
    {data}
    x="timestamp"
    xScale={scaleUtc()}
    yScale={scaleLinear()}
    series={[{ key: 'value', color: 'var(--chart-1)' }]}
    tooltip={false}
    props={{
      spline: { curve: curveNatural, strokeWidth: 1.5 },
      grid: { y: true, x: false },
      highlight: { lines: false, points: false }
    }}
  />
</Chart.Container>
```
