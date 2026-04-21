<script>
	import Menubar from '$lib/components/ui/patterns/menubar/index.js';
	import { Button } from '$lib/components/ui/primitives/button/index.js';
	import StatusBadge from '$lib/components/ui/patterns/status-badge/status-badge.svelte';
	import ComparisonGrid from '$lib/components/ui/custom/comparison-grid.svelte';
	import AnalysisLog from '$lib/components/ui/custom/analysis-log.svelte';
	import ChatPanel from '$lib/components/ui/custom/chat-panel.svelte';
	import {
		loadManifest,
		loadFrame,
		loadEvents,
		analyze,
		analyzeRealtime,
		predictDevices
	} from '$lib/api/newton.js';
	import PlayIcon from '@lucide/svelte/icons/play';
	import PauseIcon from '@lucide/svelte/icons/pause';

	// ── shared state ──────────────────────────────────────────────────────────
	let manifest = $state(null);
	let loadError = $state(null);
	let mode = $state('frame'); // 'frame' | 'realtime'

	let chatMessages = $state([]);
	let chatLoading = $state(false);
	let busy = $state(false);
	let predictions = $state(null);
	let predictionFrameId = $state(null);
	let predictingBusy = $state(false);
	let entries = $state([]);

	// ── 15-min frame mode ─────────────────────────────────────────────────────
	let currentIndex = $state(0);
	let currentFrame = $state(null);
	let highlightsOnly = $state(true);
	let framePlaying = $state(false);
	let framePlayTimer = $state(null);
	let autoAnalyze = $state(true);
	const FRAME_PLAY_INTERVAL_MS = 5000;

	// ── realtime mode ─────────────────────────────────────────────────────────
	let events = $state(null); // full event list
	let sessionStartEpoch = $state(null);
	let playhead = $state(0); // seconds since session start
	let rtSkipEmpty = $state(true);
	let rtPlaying = $state(false);
	let rtTimer = $state(null);
	let lastAnalysisWallMs = $state(0);
	let tickAnalysisIntervalMs = $state(5000); // wall-time between Newton fires
	// Window width tracks the analysis cadence — each call sees exactly the
	// captured time since the previous call, with zero overlap and zero gap.
	let rollingWindowS = $derived(tickAnalysisIntervalMs / 1000);
	const TICK_MS = 100;
	const EMPTY_SKIP_THRESHOLD_S = 60;
	const ANALYSIS_INTERVALS_MS = [1000, 2000, 5000, 10000, 30000];

	// ── load manifest on mount ────────────────────────────────────────────────
	$effect(() => {
		loadManifest()
			.then((m) => {
				manifest = m;
				const first = highlightsOnly && m.highlights?.length ? m.highlights[0] : 0;
				selectWindow(first);
			})
			.catch((err) => (loadError = err.message));
	});

	// ── 15-min frame logic ────────────────────────────────────────────────────
	async function selectWindow(index) {
		if (manifest == null || index < 0 || index >= manifest.n_windows) return;
		currentIndex = index;
		try {
			currentFrame = await loadFrame(index);
			if (autoAnalyze) {
				runPrediction(currentFrame);
				runAnalysis(currentFrame, formatWindowLabel(currentFrame));
			}
		} catch (err) {
			console.error(err);
		}
	}

	function advanceFrame() {
		if (!manifest) return;
		const list =
			highlightsOnly && manifest.highlights?.length
				? manifest.highlights
				: manifest.activity.map((a) => a.window_index);
		const pos = list.indexOf(currentIndex);
		const next = pos === -1 ? list[0] : list[(pos + 1) % list.length];
		selectWindow(next);
	}

	function toggleFramePlay() {
		if (framePlaying) {
			clearInterval(framePlayTimer);
			framePlayTimer = null;
			framePlaying = false;
		} else {
			framePlaying = true;
			framePlayTimer = setInterval(advanceFrame, FRAME_PLAY_INTERVAL_MS);
		}
	}

	// ── realtime logic ────────────────────────────────────────────────────────
	async function ensureEventsLoaded() {
		if (events || !manifest) return;
		const data = await loadEvents();
		events = data.events;
		sessionStartEpoch = manifest.session_start_epoch;
	}

	let rollingEvents = $derived.by(() => {
		if (!events || mode !== 'realtime') return [];
		const start = playhead - rollingWindowS;
		return events.filter((e) => e.t >= start && e.t <= playhead);
	});

	let rollingFrame = $derived.by(() => {
		if (!manifest || !sessionStartEpoch) return null;
		/** @type {Record<string, {up_bytes: number, down_bytes: number, up_packets: number, down_packets: number, flows: number, prots: Set<string>}>} */
		const agg = {};
		for (const ev of rollingEvents) {
			if (!agg[ev.mac])
				agg[ev.mac] = {
					up_bytes: 0,
					down_bytes: 0,
					up_packets: 0,
					down_packets: 0,
					flows: 0,
					prots: new Set()
				};
			const b = agg[ev.mac];
			b.up_bytes += ev.up_bytes;
			b.down_bytes += ev.down_bytes;
			b.up_packets += ev.up_packets;
			b.down_packets += ev.down_packets;
			b.flows += 1;
			b.prots.add(ev.protocol);
		}
		const startEpoch = sessionStartEpoch + playhead - rollingWindowS;
		const endEpoch = sessionStartEpoch + playhead;
		return {
			window_start: new Date(startEpoch * 1000).toISOString(),
			window_end: new Date(endEpoch * 1000).toISOString(),
			window_start_epoch: startEpoch,
			gateway_mac: manifest.gateway_mac,
			devices: manifest.devices.map((d) => {
				const b = agg[d.mac];
				if (!b)
					return {
						mac: d.mac,
						label: d.label,
						online: false,
						up_bytes_quarter: 0,
						down_bytes_quarter: 0,
						up_packets_quarter: 0,
						down_packets_quarter: 0,
						flows_quarter: 0,
						protocols: []
					};
				return {
					mac: d.mac,
					label: d.label,
					online: true,
					up_bytes_quarter: b.up_bytes,
					down_bytes_quarter: b.down_bytes,
					up_packets_quarter: b.up_packets,
					down_packets_quarter: b.down_packets,
					flows_quarter: b.flows,
					protocols: [...b.prots].sort()
				};
			})
		};
	});

	function tick() {
		if (!events || events.length === 0) return;
		const dt = TICK_MS / 1000;
		let newHead = playhead + dt;

		// Skip idle stretches
		if (rtSkipEmpty) {
			const next = events.find((e) => e.t > playhead);
			if (next && next.t - playhead > EMPTY_SKIP_THRESHOLD_S) {
				newHead = next.t;
			}
		}

		playhead = newHead;

		// Per-tick Newton fire (wall-clock cadence, independent of playback speed)
		const now = Date.now();
		if (
			rtPlaying &&
			rollingFrame &&
			!predictingBusy &&
			!busy &&
			now - lastAnalysisWallMs >= tickAnalysisIntervalMs
		) {
			lastAnalysisWallMs = now;
			runPrediction(rollingFrame);
			runAnalysis(rollingFrame, formatRealtimeLabel(), true);
		}

		// Stop at the end
		const last = events[events.length - 1];
		if (playhead > last.t_end + 10) stopRealtime();
	}

	async function startRealtime() {
		await ensureEventsLoaded();
		if (!events) return;
		if (playhead === 0) playhead = events[0].t;
		lastAnalysisWallMs = 0; // force a fire on the next tick
		rtPlaying = true;
		rtTimer = setInterval(tick, TICK_MS);
	}

	function stopRealtime() {
		if (rtTimer) clearInterval(rtTimer);
		rtTimer = null;
		rtPlaying = false;
	}

	function toggleRealtimePlay() {
		if (rtPlaying) stopRealtime();
		else startRealtime();
	}

	function resetRealtime() {
		stopRealtime();
		playhead = events?.[0]?.t ?? 0;
		lastAnalysisWallMs = 0;
	}

	function bumpAnalysisInterval() {
		const i = ANALYSIS_INTERVALS_MS.indexOf(tickAnalysisIntervalMs);
		tickAnalysisIntervalMs = ANALYSIS_INTERVALS_MS[(i + 1) % ANALYSIS_INTERVALS_MS.length];
	}

	function formatRealtimeLabel() {
		if (!sessionStartEpoch) return '—';
		const epoch = sessionStartEpoch + playhead;
		return new Date(epoch * 1000).toLocaleString('en-US', {
			weekday: 'short',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit',
			second: '2-digit',
			hour12: false
		});
	}

	// ── switching modes ───────────────────────────────────────────────────────
	async function switchMode(next) {
		if (next === mode) return;
		stopRealtime();
		if (framePlaying) toggleFramePlay();
		mode = next;
		if (next === 'realtime') await ensureEventsLoaded();
	}

	function inferStatus(verdict) {
		const v = verdict.toUpperCase();
		if (v === 'OCCUPIED' || v === 'LIKELY_OCCUPIED') return 'good';
		if (v === 'AMBIGUOUS') return 'warning';
		return 'neutral';
	}

	function parseVerdict(text) {
		const upper = text.toUpperCase();
		const match = upper.match(/\b(OCCUPIED|LIKELY_OCCUPIED|AMBIGUOUS|LIKELY_EMPTY|EMPTY)\b/);
		return match ? match[1] : 'OBSERVING';
	}

	function formatWindowLabel(frame) {
		if (!frame) return '—';
		const d = new Date(frame.window_start);
		return d.toLocaleString('en-US', {
			weekday: 'short',
			month: 'short',
			day: 'numeric',
			hour: '2-digit',
			minute: '2-digit',
			hour12: false
		});
	}

	function toRealtimeFrame(frame) {
		// Rename fields from `_quarter` (Xfinity 15-min convention) to `_window`
		// for the realtime endpoint, which reasons over a 30-second rolling window.
		return {
			window_start: frame.window_start,
			window_end: frame.window_end,
			window_start_epoch: frame.window_start_epoch,
			gateway_mac: frame.gateway_mac,
			devices: frame.devices.map((d) => ({
				mac: d.mac,
				label: d.label,
				online: d.online,
				up_bytes_window: d.up_bytes_quarter,
				down_bytes_window: d.down_bytes_quarter,
				up_packets_window: d.up_packets_quarter,
				down_packets_window: d.down_packets_quarter,
				flows_window: d.flows_quarter,
				protocols: d.protocols
			}))
		};
	}

	async function runAnalysis(frame, label, realtime = false) {
		if (busy || !frame) return;
		busy = true;
		try {
			const result = realtime
				? await analyzeRealtime(toRealtimeFrame(frame))
				: await analyze(frame);
			const verdict = parseVerdict(result.analysis);
			const status = inferStatus(verdict);
			entries = [
				{
					id: crypto.randomUUID(),
					text: result.analysis,
					timestamp: result.timestamp,
					windowLabel: label,
					verdict,
					status
				},
				...entries.slice(0, 49)
			];
		} catch (err) {
			console.error('Analysis failed:', err);
		} finally {
			busy = false;
		}
	}

	async function runPrediction(frame) {
		if (predictingBusy || !frame) return;
		const frameId = frame.window_start_epoch;
		predictingBusy = true;
		try {
			const result = await predictDevices(frame);
			predictions = result.predictions;
			predictionFrameId = frameId;
		} catch (err) {
			console.error('Prediction failed:', err);
		} finally {
			predictingBusy = false;
		}
	}

	async function handleChatSend(text) {
		const isRealtime = mode === 'realtime';
		const frame = isRealtime ? rollingFrame : currentFrame;
		if (!frame) return;
		const msgWindowLabel = isRealtime ? formatRealtimeLabel() : formatWindowLabel(frame);
		chatMessages = [
			...chatMessages,
			{
				id: crypto.randomUUID(),
				role: 'user',
				text,
				timestamp: Date.now(),
				windowLabel: msgWindowLabel
			}
		];
		chatLoading = true;

		while (busy) await new Promise((r) => setTimeout(r, 150));
		busy = true;

		try {
			const result = isRealtime
				? await analyzeRealtime(toRealtimeFrame(frame), text)
				: await analyze(frame, text);
			chatMessages = [
				...chatMessages,
				{
					id: crypto.randomUUID(),
					role: 'assistant',
					text: result.analysis,
					timestamp: result.timestamp,
					windowLabel: msgWindowLabel
				}
			];
		} catch (err) {
			chatMessages = [
				...chatMessages,
				{
					id: crypto.randomUUID(),
					role: 'assistant',
					text: `Error: ${err.message}`,
					timestamp: Date.now(),
					windowLabel: msgWindowLabel
				}
			];
		} finally {
			busy = false;
			chatLoading = false;
		}
	}

	// ── derived for UI ────────────────────────────────────────────────────────
	let displayFrame = $derived(mode === 'realtime' ? rollingFrame : currentFrame);
	// Predictions are "fresh" if they correspond to the currently-displayed frame.
	// 15-min mode: strict match on window_start_epoch.
	// Realtime: allow drift within the rolling-window duration (rollingFrame shifts every tick).
	let predictionsMatch = $derived.by(() => {
		if (predictions == null || predictionFrameId == null || !displayFrame) return false;
		if (mode === 'frame') return predictionFrameId === displayFrame.window_start_epoch;
		return Math.abs(predictionFrameId - displayFrame.window_start_epoch) <= rollingWindowS;
	});
	let chatWindowLabel = $derived(
		mode === 'realtime' ? `rolling ${rollingWindowS}-second window` : '15-minute window'
	);
</script>

<svelte:head>
	<title>Newton WiFi Demo — Is Anyone Home?</title>
</svelte:head>

{#snippet partnerSnippet()}
	<span class="text-muted-foreground font-mono text-sm tracking-wider uppercase">
		WiFi Occupancy
	</span>
{/snippet}

<div
	class="bg-background text-foreground grid h-screen w-screen grid-rows-[auto_1fr] overflow-hidden"
>
	<Menubar partnerLogo={partnerSnippet}>
		<div class="flex items-center gap-3">
			<div class="bg-muted flex items-center gap-0 rounded-xs p-0.5">
				<button
					type="button"
					class={mode === 'frame'
						? 'bg-background rounded-xs px-2.5 py-1 font-mono text-[11px]'
						: 'text-muted-foreground hover:text-foreground px-2.5 py-1 font-mono text-[11px]'}
					onclick={() => switchMode('frame')}
				>
					15-min
				</button>
				<button
					type="button"
					class={mode === 'realtime'
						? 'bg-background rounded-xs px-2.5 py-1 font-mono text-[11px]'
						: 'text-muted-foreground hover:text-foreground px-2.5 py-1 font-mono text-[11px]'}
					onclick={() => switchMode('realtime')}
				>
					Realtime
				</button>
			</div>

			{#if manifest}
				<StatusBadge label="Newton" percentage={100} initial="N" />
				<div class="text-muted-foreground hidden font-mono text-xs md:block">
					GHOST-IoT
					<span class="text-border px-1">·</span>
					{#if mode === 'frame'}
						window #{currentIndex}/{manifest.n_windows - 1}
					{:else}
						{formatRealtimeLabel()}
					{/if}
				</div>
			{/if}

			{#if mode === 'frame'}
				<Button variant={framePlaying ? 'outline' : 'default'} size="sm" onclick={toggleFramePlay}>
					{#if framePlaying}
						<PauseIcon class="size-3.5" aria-hidden="true" /> Pause
					{:else}
						<PlayIcon class="size-3.5" aria-hidden="true" /> Play
					{/if}
				</Button>
			{:else}
				<Button
					variant="outline"
					size="sm"
					onclick={bumpAnalysisInterval}
					title="Wall-clock interval between Newton predictions"
				>
					every {tickAnalysisIntervalMs / 1000}s
				</Button>
				<Button
					variant={rtSkipEmpty ? 'default' : 'outline'}
					size="sm"
					onclick={() => (rtSkipEmpty = !rtSkipEmpty)}
					title="Auto-jump playhead through dead stretches"
				>
					Skip gaps
				</Button>
				<Button variant="outline" size="sm" onclick={resetRealtime}>Reset</Button>
				<Button variant={rtPlaying ? 'outline' : 'default'} size="sm" onclick={toggleRealtimePlay}>
					{#if rtPlaying}
						<PauseIcon class="size-3.5" aria-hidden="true" /> Pause
					{:else}
						<PlayIcon class="size-3.5" aria-hidden="true" /> Play
					{/if}
				</Button>
			{/if}
		</div>
	</Menubar>

	<main
		id="main-content"
		class="grid grid-cols-[2fr_1fr] gap-4 overflow-hidden p-4"
	>
		<h1 class="sr-only">Newton WiFi Occupancy Demo</h1>

		{#if loadError}
			<div class="col-span-2 flex items-center justify-center">
				<div
					class="border-destructive/30 bg-destructive/10 rounded-xs border p-6 font-mono text-sm"
				>
					<div class="text-destructive mb-2">Failed to load data</div>
					<div class="text-muted-foreground">{loadError}</div>
					<div class="text-muted-foreground mt-3">
						Run <code class="bg-muted px-1">python3 scripts/preprocess.py</code> first.
					</div>
				</div>
			</div>
		{:else}
			<div class="flex min-h-0 flex-col gap-4 overflow-hidden">
				<ComparisonGrid
					frame={displayFrame}
					predictions={predictionsMatch ? predictions : null}
					predictionLoading={predictingBusy || !predictionsMatch}
					class="shrink-0"
				/>
				<AnalysisLog {entries} class="min-h-0 flex-1" />
			</div>

			<ChatPanel
				bind:messages={chatMessages}
				loading={chatLoading}
				disabled={!displayFrame}
				windowLabel={chatWindowLabel}
				onsend={handleChatSend}
				class="max-h-full"
			/>
		{/if}
	</main>
</div>
