<script>
	import { cn } from '$lib/utils.js';
	import BackgroundCard from '$lib/components/ui/patterns/background-card/index.js';
	import FlatLogItem from '$lib/components/ui/patterns/flat-log-item/index.js';
	import { ScrollArea } from '$lib/components/ui/primitives/scroll-area/index.js';
	import BrainIcon from '@lucide/svelte/icons/brain';

	/**
	 * @typedef {Object} LogEntry
	 * @property {string} id
	 * @property {string} text
	 * @property {number} timestamp
	 * @property {string} windowLabel
	 * @property {'good' | 'warning' | 'critical' | 'neutral'} status
	 * @property {string} verdict
	 */

	/** @type {{ entries?: LogEntry[], class?: string }} */
	let { entries = [], class: className, ...restProps } = $props();
</script>

<BackgroundCard
	title="Newton Occupancy Analysis"
	icon={BrainIcon}
	class={cn('flex max-h-full flex-col gap-3 overflow-hidden', className)}
	{...restProps}
>
	<ScrollArea class="min-h-0 flex-1">
		<div class="flex flex-col gap-2 pr-3">
			{#if entries.length === 0}
				<p class="text-muted-foreground py-8 text-center text-sm">
					Play the session or pick a window — Newton's verdict per 15-min snapshot will appear here.
				</p>
			{:else}
				{#each entries as entry (entry.id)}
					<FlatLogItem
						title={entry.verdict}
						message={entry.text}
						status={entry.status}
						detail={entry.windowLabel}
					/>
				{/each}
			{/if}
		</div>
	</ScrollArea>
</BackgroundCard>
