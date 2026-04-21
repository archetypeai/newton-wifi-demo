<script>
	import { cn } from '$lib/utils.js';
	import BackgroundCard from '$lib/components/ui/patterns/background-card/index.js';
	import { Badge } from '$lib/components/ui/primitives/badge/index.js';
	import RouterIcon from '@lucide/svelte/icons/router';
	import WifiIcon from '@lucide/svelte/icons/wifi';
	import WifiOffIcon from '@lucide/svelte/icons/wifi-off';
	import ActivityIcon from '@lucide/svelte/icons/activity';
	import PauseIcon from '@lucide/svelte/icons/pause';
	import MinusIcon from '@lucide/svelte/icons/minus';
	import HelpCircleIcon from '@lucide/svelte/icons/help-circle';
	import BrainIcon from '@lucide/svelte/icons/brain';

	/**
	 * @typedef {{ mac: string, label: string, online: boolean, up_bytes_quarter: number, down_bytes_quarter: number, flows_quarter: number, protocols: string[] }} Device
	 * @typedef {{ label: string, verdict: string, confidence: number, reason: string }} Prediction
	 */

	/** @type {{ frame: {window_start?: string, gateway_mac?: string, devices?: Device[]} | null, predictions?: Prediction[] | null, predictionLoading?: boolean, class?: string }} */
	let {
		frame = null,
		predictions = null,
		predictionLoading = false,
		class: className,
		...restProps
	} = $props();

	const VERDICT_META = {
		online_active: { title: 'ACTIVE', icon: ActivityIcon, text: 'text-atai-good' },
		online_idle: { title: 'IDLE', icon: PauseIcon, text: 'text-atai-warning' },
		offline: { title: 'OFFLINE', icon: MinusIcon, text: 'text-muted-foreground' },
		unknown: { title: '—', icon: HelpCircleIcon, text: 'text-muted-foreground' }
	};

	function meta(verdict) {
		return VERDICT_META[verdict] ?? VERDICT_META.unknown;
	}

	function formatBytes(n) {
		if (!n) return '0';
		if (n < 1024) return `${n} B`;
		if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
		return `${(n / 1024 / 1024).toFixed(2)} MB`;
	}

	function formatTime(iso) {
		if (!iso) return '—';
		const d = new Date(iso);
		return d.toLocaleString('en-US', {
			weekday: 'short',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit',
			hour12: false
		});
	}

	let devices = $derived(frame?.devices ?? []);
	let predictionsByLabel = $derived.by(() => {
		/** @type {Record<string, Prediction>} */
		const map = {};
		for (const p of predictions ?? []) map[p.label] = p;
		return map;
	});
	let onlineCount = $derived(devices.filter((d) => d.online).length);
	let activeCount = $derived(
		(predictions ?? []).filter((p) => p.verdict === 'online_active').length
	);

	// Compare: was Newton right? (is online iff verdict != offline)
	function agreement(device, pred) {
		if (!pred || pred.verdict === 'unknown') return null;
		const newtonOnline = pred.verdict !== 'offline';
		return device.online === newtonOnline ? 'match' : 'mismatch';
	}
</script>

<BackgroundCard
	title="Home WiFi Gateway — Ground Truth vs Newton"
	icon={RouterIcon}
	class={cn('flex max-h-full flex-col gap-3 overflow-hidden', className)}
	{...restProps}
>
	<div class="flex items-center justify-between gap-4">
		<div class="text-muted-foreground font-mono text-xs">
			{#if frame}
				window: {formatTime(frame.window_start)}
				<span class="text-border mx-2">|</span>
				gateway:
				<span class="text-foreground">{frame.gateway_mac}</span>
			{:else}
				no frame loaded
			{/if}
		</div>
		<div class="flex gap-1.5">
			<Badge variant="secondary" class="font-mono">{onlineCount}/{devices.length} online</Badge>
			{#if predictions}
				<Badge variant="outline" class="font-mono">
					<BrainIcon class="mr-1 size-3" aria-hidden="true" />
					{activeCount} active
				</Badge>
			{/if}
		</div>
	</div>

	<!-- Header row -->
	<div
		class="text-muted-foreground border-border grid grid-cols-[140px_minmax(180px,1fr)_minmax(220px,1.4fr)] items-center gap-3 border-b pb-1.5 font-mono text-[10px] tracking-wider uppercase"
	>
		<div>Device</div>
		<div>Ground truth (gateway)</div>
		<div class="flex items-center gap-1">
			<BrainIcon class="size-3" aria-hidden="true" />
			Newton's verdict
		</div>
	</div>

	<div class="flex-1 overflow-auto">
		<div role="list" class="flex flex-col">
			{#each devices as device (device.mac)}
				{@const pred = predictionsByLabel[device.label]}
				{@const m = meta(pred?.verdict)}
				{@const agree = agreement(device, pred)}
				<div
					role="listitem"
					class="border-border grid grid-cols-[140px_minmax(180px,1fr)_minmax(220px,1.4fr)] items-center gap-3 border-b py-1.5 text-xs last:border-b-0"
				>
					<!-- Device identity -->
					<div class="flex min-w-0 items-center gap-2">
						{#if device.online}
							<WifiIcon class="text-atai-good size-3.5 shrink-0" aria-hidden="true" />
						{:else}
							<WifiOffIcon
								class="text-muted-foreground size-3.5 shrink-0"
								aria-hidden="true"
							/>
						{/if}
						<div class="min-w-0">
							<div class="font-mono text-xs leading-tight">{device.label}</div>
							<div class="text-muted-foreground truncate font-mono text-[10px] leading-tight">
								{device.mac}
							</div>
						</div>
					</div>

					<!-- Ground truth (single line) -->
					<div class="flex min-w-0 items-center gap-2 font-mono text-xs">
						<span
							class={cn(
								'shrink-0',
								device.online ? 'text-atai-good' : 'text-muted-foreground'
							)}
						>
							{device.online ? 'ONLINE' : 'OFFLINE'}
						</span>
						{#if device.online}
							<span class="text-muted-foreground shrink-0">·</span>
							<span class="shrink-0">↑{formatBytes(device.up_bytes_quarter)}</span>
							<span class="shrink-0">↓{formatBytes(device.down_bytes_quarter)}</span>
							<span class="text-muted-foreground shrink-0">{device.flows_quarter}f</span>
							{#if device.protocols?.length}
								<span class="text-muted-foreground truncate text-[11px]">
									{device.protocols.slice(0, 3).join('/')}{device.protocols.length > 3
										? `+${device.protocols.length - 3}`
										: ''}
								</span>
							{/if}
						{/if}
					</div>

					<!-- Newton verdict (single line + reason on hover via title) -->
					<div class="min-w-0" title={pred?.reason ?? ''}>
						{#if predictionLoading && !pred}
							<div class="bg-muted/30 h-3.5 w-32 animate-pulse rounded-xs"></div>
						{:else if pred}
							<div class="flex items-center gap-2">
								<m.icon class={cn('size-3.5 shrink-0', m.text)} aria-hidden="true" />
								<span class={cn('font-mono text-xs', m.text)}>{m.title}</span>
								{#if pred.verdict !== 'offline' && pred.verdict !== 'unknown'}
									<span class="text-muted-foreground font-mono text-[11px]">
										({pred.confidence.toFixed(2)})
									</span>
								{/if}
								{#if agree === 'match'}
									<span
										class="text-atai-good bg-atai-good/10 rounded-xs px-1 py-0.5 font-mono text-[10px]"
									>
										✓ match
									</span>
								{:else if agree === 'mismatch'}
									<span
										class="text-atai-critical bg-atai-critical/10 rounded-xs px-1 py-0.5 font-mono text-[10px]"
									>
										✗ mismatch
									</span>
								{/if}
								<span class="text-muted-foreground truncate text-[11px]">
									— {pred.reason}
								</span>
							</div>
						{:else}
							<div class="text-muted-foreground font-mono text-xs">—</div>
						{/if}
					</div>
				</div>
			{/each}
		</div>
	</div>
</BackgroundCard>
