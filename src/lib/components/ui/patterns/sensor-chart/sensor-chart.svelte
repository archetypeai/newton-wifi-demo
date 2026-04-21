<script>
  import { formatMMSS } from '$lib/utils.js';
  import BackgroundCard from '$lib/components/ui/patterns/background-card/index.js';
  import * as Chart from '$lib/components/ui/primitives/chart/index.js';
  import {
    CHART_COLORS,
    buildChartConfig,
    slidingWindow
  } from '$lib/components/ui/primitives/chart/chart-utils.js';
  import { LineChart } from 'layerchart';
  import { curveNatural } from 'd3-shape';
  import { scaleUtc, scaleLinear } from 'd3-scale';

  /**
   * @typedef {Object} Props
   * @property {string} [title="SENSOR"] - card header label identifying the sensor
   * @property {import('svelte').Component} [icon] - lucide icon component for header
   * @property {Array<Record<string, any>>} [data=[]] - array of data points to chart
   * @property {Record<string, string>} [signals={}] - map of data key to display label
   * @property {string} [xKey="timestamp"] - data key for x-axis values
   * @property {number} [maxPoints] - enables streaming mode with sliding window
   * @property {number} yMin - minimum y-axis value (required)
   * @property {number} yMax - maximum y-axis value (required)
   * @property {number[]} [yTicks] - explicit y-axis tick values
   * @property {"both"|"x"|"y"|"none"} [axis="both"] - which axes to display
   * @property {string} [class] - additional CSS classes
   */

  /** @type {Props} */
  let {
    title = 'UNKNOWN SENSOR',
    icon: Icon = undefined,
    data = [],
    signals = {},
    xKey = 'timestamp',
    maxPoints = undefined,
    yMin,
    yMax,
    yTicks,
    axis = 'both',
    class: className,
    ...restProps
  } = $props();

  // data → series → config → formatting → scales

  // create a sliding window of data
  let displayData = $derived(slidingWindow(data, maxPoints));
  let indexedData = $derived(displayData.map((d, i) => ({ ...d, _index: i })));

  // derive series config from signals prop
  let series = $derived(
    Object.entries(signals).map(([key, label], i) => ({
      key,
      label,
      color: CHART_COLORS[i % CHART_COLORS.length]
    }))
  );

  // build chart config for Chart.Container
  let chartConfig = $derived(buildChartConfig(series));

  // get base timestamp for relative time formatting
  let baseTimestamp = $derived(
    displayData.length > 0 && displayData[0][xKey] ? new Date(displayData[0][xKey]).getTime() : 0
  );

  // format time as MM:SS relative to first data point
  function formatTime(date) {
    if (!baseTimestamp) return formatMMSS(0);
    return formatMMSS(Math.floor((date.getTime() - baseTimestamp) / 1000));
  }

  // use index-based x for streaming (maxPoints set), timestamp for static
  let useIndexX = $derived(maxPoints !== undefined);

  // y-axis scale and domain
  const yScale = scaleLinear();
  let xDomain = $derived(useIndexX ? [0, (maxPoints || displayData.length) - 1] : undefined);
  let yDomain = $derived([yMin, yMax]);
</script>

<BackgroundCard {title} icon={Icon} class={className} {...restProps}>
  <Chart.Container config={chartConfig} class="aspect-auto h-[220px] w-full">
    <LineChart
      data={indexedData}
      x={useIndexX ? '_index' : xKey}
      xScale={useIndexX ? scaleLinear() : scaleUtc()}
      {xDomain}
      {yScale}
      {yDomain}
      {axis}
      {series}
      tooltip={false}
      padding={{ left: 20, bottom: 15 }}
      props={{
        spline: {
          curve: curveNatural,
          strokeWidth: 1.5
        },
        xAxis: {
          format: formatTime
        },
        yAxis: {
          ticks: yTicks,
          format: (v) => v.toString()
        },
        grid: {
          y: true,
          x: false,
          yTicks: yTicks
        },
        highlight: {
          lines: false,
          points: false
        }
      }}
    />
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