<script>
	import { cn } from '$lib/utils.js';
	import BackgroundCard from '$lib/components/ui/patterns/background-card/index.js';
	import { Button } from '$lib/components/ui/primitives/button/index.js';
	import { ScrollArea } from '$lib/components/ui/primitives/scroll-area/index.js';
	import MessageSquareIcon from '@lucide/svelte/icons/message-square';
	import SendIcon from '@lucide/svelte/icons/send';
	import SpinnerIcon from '@lucide/svelte/icons/loader';
	import Trash2Icon from '@lucide/svelte/icons/trash-2';
	import HomeIcon from '@lucide/svelte/icons/home';
	import UsersIcon from '@lucide/svelte/icons/users';
	import ShieldAlertIcon from '@lucide/svelte/icons/shield-alert';
	import { marked } from 'marked';

	marked.setOptions({ breaks: true, gfm: true });

	let {
		messages = $bindable([]),
		loading = false,
		disabled = false,
		windowLabel = 'current',
		onsend,
		class: className,
		...restProps
	} = $props();

	let QUICK_PROMPTS = $derived([
		{
			label: 'Home?',
			icon: HomeIcon,
			query: `Is anyone home based on this ${windowLabel}? Give a direct yes/no with one sentence of evidence from the device behavior.`
		},
		{
			label: 'Active device',
			icon: UsersIcon,
			query:
				'Which device in this snapshot looks most like someone actively using it (vs idle/background)? Explain what in the traffic tells you.'
		},
		{
			label: 'Anomaly',
			icon: ShieldAlertIcon,
			query:
				'Is anything unusual or suspicious in this snapshot — a device talking when nobody should be home, unexpected protocols, or spikes? Or does it look routine?'
		}
	]);

	let inputValue = $state('');
	let textareaRef = $state(null);

	function autoResize() {
		if (!textareaRef) return;
		textareaRef.style.height = 'auto';
		textareaRef.style.height = Math.min(textareaRef.scrollHeight, 120) + 'px';
	}

	function handleSubmit(e) {
		e.preventDefault();
		const text = inputValue.trim();
		if (!text || loading || disabled) return;
		inputValue = '';
		if (textareaRef) textareaRef.style.height = 'auto';
		onsend?.(text);
	}

	function handleKeydown(e) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSubmit(e);
		}
	}
</script>

<BackgroundCard
	title="Ask Newton"
	icon={MessageSquareIcon}
	class={cn('flex max-h-full flex-col gap-3 overflow-hidden', className)}
	{...restProps}
>
	{#if messages.length > 0}
		<div class="flex items-center justify-between">
			<div class="flex flex-wrap gap-1.5">
				{#each QUICK_PROMPTS as prompt (prompt.label)}
					<Button
						variant="outline"
						size="sm"
						disabled={disabled || loading}
						onclick={() => onsend?.(prompt.query)}
					>
						<prompt.icon class="size-3" aria-hidden="true" />
						{prompt.label}
					</Button>
				{/each}
			</div>
			<Button
				variant="ghost"
				size="icon-sm"
				aria-label="Clear chat"
				onclick={() => (messages = [])}
			>
				<Trash2Icon class="size-3.5" />
			</Button>
		</div>
	{/if}

	<ScrollArea class="min-h-0 flex-1">
		<div class="flex flex-col gap-3 pr-3">
			{#if messages.length === 0}
				<div class="flex flex-col items-center gap-3 py-6">
					<p class="text-muted-foreground text-center text-sm">
						Ask Newton about the current window's WiFi snapshot.
					</p>
					<div class="flex flex-wrap justify-center gap-1.5">
						{#each QUICK_PROMPTS as prompt (prompt.label)}
							<Button
								variant="outline"
								size="sm"
								disabled={disabled || loading}
								onclick={() => onsend?.(prompt.query)}
							>
								<prompt.icon class="size-3" aria-hidden="true" />
								{prompt.label}
							</Button>
						{/each}
					</div>
				</div>
			{:else}
				{#each messages as msg (msg.id)}
					<div
						class={cn(
							'rounded-md px-3 py-2 text-sm',
							msg.role === 'user'
								? 'bg-secondary text-secondary-foreground ml-8'
								: 'bg-atai-neutral/10 text-foreground border-atai-neutral/20 mr-8 border'
						)}
					>
						{#if msg.role === 'assistant'}
							<div
								class="prose-sm prose-invert leading-relaxed [&_ol]:list-decimal [&_ol]:pl-5 [&_p]:my-1.5 [&_ul]:list-disc [&_ul]:pl-5 [&_li]:my-0.5 [&_strong]:text-foreground"
							>
								{@html marked(msg.text)}
							</div>
						{:else}
							<p class="whitespace-pre-wrap leading-relaxed">{msg.text}</p>
						{/if}
						<span class="font-mono text-[10px] opacity-50">
							{#if msg.windowLabel}
								about {msg.windowLabel}
							{:else}
								{new Date(msg.timestamp).toLocaleTimeString('en-US', {
									hour12: false,
									hour: '2-digit',
									minute: '2-digit'
								})}
							{/if}
						</span>
					</div>
				{/each}
				{#if loading}
					<div class="bg-muted mr-8 flex items-center gap-2 rounded-md px-3 py-2">
						<SpinnerIcon class="text-muted-foreground size-4 animate-spin" />
						<span class="text-muted-foreground text-sm">Thinking...</span>
					</div>
				{/if}
			{/if}
		</div>
	</ScrollArea>

	<form class="flex items-end gap-2" onsubmit={handleSubmit}>
		<textarea
			bind:this={textareaRef}
			bind:value={inputValue}
			oninput={autoResize}
			onkeydown={handleKeydown}
			placeholder={disabled ? 'Load a window first...' : 'Ask about this WiFi window...'}
			{disabled}
			rows="1"
			class={cn(
				'border-input bg-transparent ring-ring/50 placeholder:text-muted-foreground flex-1 resize-none rounded-xs border px-3 py-2 text-sm outline-none transition-colors',
				'focus-visible:border-ring focus-visible:ring-[3px]',
				'disabled:pointer-events-none disabled:opacity-50'
			)}
		></textarea>
		<Button
			type="submit"
			size="icon"
			disabled={disabled || loading || !inputValue.trim()}
			aria-label="Send message"
		>
			<SendIcon class="size-4" />
		</Button>
	</form>
</BackgroundCard>
