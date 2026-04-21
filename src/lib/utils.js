import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

// constants: health tiers
const HEALTH_TIERS = {
  good: { bg: 'bg-atai-good', text: 'text-atai-good' },
  warning: { bg: 'bg-atai-warning', text: 'text-atai-warning' },
  critical: { bg: 'bg-atai-critical', text: 'text-atai-critical' }
};

// utility: merge class names
export function cn(...inputs) {
  return twMerge(clsx(inputs));
}

// utility: clamp a value between a minimum and maximum
export function clamp(value, min = 0, max = 100) {
  return Math.max(min, Math.min(max, value));
}

// utility: get the health tier for a score
export function healthTier(score, variant = 'bg') {
  if (score >= 67) return HEALTH_TIERS.good[variant];
  if (score >= 34) return HEALTH_TIERS.warning[variant];
  return HEALTH_TIERS.critical[variant];
}

// utility: format a total seconds into MM:SS
export function formatMMSS(totalSeconds) {
  const s = Math.floor(totalSeconds);
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
}