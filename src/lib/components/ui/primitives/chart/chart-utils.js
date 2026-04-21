import { getContext, setContext } from 'svelte';

// constants: themes for chart colors
export const THEMES = { light: '', dark: '.dark' };

// constants: chart colors
export const CHART_COLORS = [
  'var(--chart-1)',
  'var(--chart-2)',
  'var(--chart-3)',
  'var(--chart-4)',
  'var(--chart-5)'
];

// utility: extracts item config from payload
export function getPayloadConfigFromPayload(config, payload, key) {
  if (typeof payload !== 'object' || payload === null) return undefined;

  const payloadPayload =
    'payload' in payload && typeof payload.payload === 'object' && payload.payload !== null
      ? payload.payload
      : undefined;

  let configLabelKey = key;

  if (payload.key === key) {
    configLabelKey = payload.key;
  } else if (payload.name === key) {
    configLabelKey = payload.name;
  } else if (key in payload && typeof payload[key] === 'string') {
    configLabelKey = payload[key];
  } else if (
    payloadPayload !== undefined &&
    key in payloadPayload &&
    typeof payloadPayload[key] === 'string'
  ) {
    configLabelKey = payloadPayload[key];
  }

  return configLabelKey in config ? config[configLabelKey] : config[key];
}

const chartContextKey = Symbol('chart-context');

// utility: sets chart context
export function setChartContext(value) {
  return setContext(chartContextKey, value);
}

// utility: gets chart context
export function getChartContext() {
  return getContext(chartContextKey);
}

// utility: builds chart config
export function buildChartConfig(series) {
  return Object.fromEntries(series.map((s) => [s.key, { label: s.label, color: s.color }]));
}

// utility: creates a sliding window of data
export function slidingWindow(data, maxPoints) {
  return maxPoints && data.length > maxPoints ? data.slice(-maxPoints) : data;
}