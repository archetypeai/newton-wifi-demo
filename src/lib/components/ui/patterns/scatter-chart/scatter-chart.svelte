<script>
  import BackgroundCard from '$lib/components/ui/patterns/background-card/index.js';
  import * as Chart from '$lib/components/ui/primitives/chart/index.js';
  import {
    CHART_COLORS,
    buildChartConfig,
    slidingWindow
  } from '$lib/components/ui/primitives/chart/chart-utils.js';
  import { ScatterChart } from 'layerchart';
  import { scaleLinear } from 'd3-scale';

  /**
   * @typedef {Object} Props
   * @property {string} [title="SCATTER"] - card header label
   * @property {import('svelte').Component} [icon] - lucide icon component for header
   * @property {Array<Record<string, any>>} [data=[]] - array of data points
   * @property {string} [xKey="x"] - data key for x-axis values
   * @property {string} [yKey="y"] - data key for y-axis values
   * @property {string} [categoryKey] - data key for category grouping; when set, points are split into colored series
   * @property {Record<string, string>} [categories={}] - map of category value to display label
   * @property {number} [maxPoints] - enables streaming mode with sliding window
   * @property {number} xMin - minimum x-axis value (required)
   * @property {number} xMax - maximum x-axis value (required)
   * @property {number} yMin - minimum y-axis value (required)
   * @property {number} yMax - maximum y-axis value (required)
   * @property {number[]} [xTicks] - explicit x-axis tick values
   * @property {number[]} [yTicks] - explicit y-axis tick values
   * @property {string} [class] - additional CSS classes
   */

  /** @type {Props} */
  let {
    title = 'SCATTER',
    icon: Icon = undefined,
    data = [],
    xKey = 'x',
    yKey = 'y',
    categoryKey = undefined,
    categories = {},
    maxPoints = undefined,
    xMin,
    xMax,
    yMin,
    yMax,
    xTicks,
    yTicks,
    class: className,
    ...restProps
  } = $props();

  // create a sliding window of data
  let displayData = $derived(slidingWindow(data, maxPoints));

  // derive series config from categoryKey and categories prop
  let series = $derived.by(() => {
    if (categoryKey && Object.keys(categories).length > 0) {
      const categoryKeys = Object.keys(categories);
      return categoryKeys.map((catValue, i) => ({
        key: catValue,
        label: categories[catValue],
        color: CHART_COLORS[i % CHART_COLORS.length],
        data: displayData
          .filter((d) => d[categoryKey] === catValue)
          .map((d) => ({ x: d[xKey], y: d[yKey] }))
      }));
    }
    return [
      {
        key: 'data',
        label: 'Data',
        color: CHART_COLORS[0],
        data: displayData.map((d) => ({ x: d[xKey], y: d[yKey] }))
      }
    ];
  });

  // build chart config for Chart.Container
  let chartConfig = $derived(buildChartConfig(series));

  // x-axis & y-axis scales and domains
  const xScale = scaleLinear();
  const yScale = scaleLinear();
  let xDomain = $derived([xMin, xMax]);
  let yDomain = $derived([yMin, yMax]);
</script>

<BackgroundCard {title} icon={Icon} class={className} {...restProps}>
  <Chart.Container config={chartConfig} class="aspect-auto h-[220px] w-full">
    <ScatterChart
      data={displayData.map((d) => ({ x: d[xKey], y: d[yKey] }))}
      x="x"
      y="y"
      {xScale}
      {yScale}
      {xDomain}
      {yDomain}
      {series}
      legend={false}
      labels={false}
      padding={{ left: 20, bottom: 15 }}
      props={{
        points: {
          fillOpacity: 0.6,
          strokeWidth: 1,
          r: 3
        },
        highlight: {
          points: { r: 5 }
        },
        tooltip: {
          context: { mode: 'voronoi' }
        },
        xAxis: {
          ticks: xTicks,
          format: (v) => v.toString()
        },
        yAxis: {
          ticks: yTicks,
          format: (v) => v.toString()
        },
        grid: {
          x: true,
          y: true,
          xTicks: xTicks,
          yTicks: yTicks
        }
      }}
    >
      {#snippet tooltip()}
        <Chart.ScatterTooltip />
      {/snippet}
    </ScatterChart>
  </Chart.Container>

  <!-- legend section -->
  {#if series.length > 0}
    <div class="flex items-center justify-center gap-10">
      {#each series as s (s.key)}
        <div class="flex items-center gap-2">
          <div class="size-2 rounded-full bg-(--legend-color)" style:--legend-color={s.color}></div>
          <span class="font-mono uppercase">{s.label}</span>
        </div>
      {/each}
    </div>
  {/if}
</BackgroundCard>