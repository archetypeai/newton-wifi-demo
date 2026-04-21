---
paths:
  - '**/*.svelte'
  - '**/*.svelte.js'
  - '**/*.svelte.ts'
---

# Svelte 5 State Management

Svelte 5 uses runes - special `$` prefixed primitives that control reactivity.

## $state - Reactive State

Declare reactive state that triggers UI updates when changed:

```svelte
<script>
  let count = $state(0);
  let user = $state({ name: 'Alice', age: 30 });
</script>

<button onclick={() => count++}>
  Clicked {count} times
</button>
```

### Deep Reactivity

Objects and arrays become deeply reactive proxies:

```svelte
<script>
  let todos = $state([{ done: false, text: 'Learn Svelte 5' }]);

  // This triggers updates - the array is a proxy
  todos.push({ done: false, text: 'Build app' });

  // This also triggers updates
  todos[0].done = true;
</script>
```

### $state.raw - Non-Proxied State

For large objects you don't plan to mutate, use `$state.raw` for better performance:

```svelte
<script>
  // Must reassign entirely, can't mutate
  let data = $state.raw({ items: largeArray });

  // This won't trigger updates
  data.items.push(newItem);

  // This will - full reassignment
  data = { items: [...data.items, newItem] };
</script>
```

### $state.snapshot - Get Plain Object

Get a non-reactive copy of a state proxy (useful for APIs that don't expect proxies):

```svelte
<script>
  let state = $state({ count: 0 });

  function save() {
    // Pass plain object to external API
    const snapshot = $state.snapshot(state);
    localStorage.setItem('state', JSON.stringify(snapshot));
  }
</script>
```

### Class Fields

Use $state in class fields:

```svelte
<script>
  class Counter {
    count = $state(0);

    increment() {
      this.count++;
    }
  }

  let counter = new Counter();
</script>
```

## $derived - Computed Values

Declare values that automatically update when dependencies change:

```svelte
<script>
  let count = $state(0);
  let doubled = $derived(count * 2);
  let quadrupled = $derived(doubled * 2);
</script>

<p>{count} × 2 = {doubled}</p><p>{count} × 4 = {quadrupled}</p>
```

### $derived.by - Complex Derivations

For multi-line logic, use `$derived.by`:

```svelte
<script>
  let items = $state([1, 2, 3, 4, 5]);

  let stats = $derived.by(() => {
    const sum = items.reduce((a, b) => a + b, 0);
    const avg = sum / items.length;
    const max = Math.max(...items);
    return { sum, avg, max };
  });
</script>

<p>Sum: {stats.sum}, Avg: {stats.avg}, Max: {stats.max}</p>
```

### Overriding Derived Values (Optimistic UI)

Derived values can be temporarily overridden:

```svelte
<script>
  let { post } = $props();
  let likes = $derived(post.likes);

  async function like() {
    likes++; // Optimistic update
    try {
      await api.likePost(post.id);
    } catch {
      likes--; // Rollback on failure
    }
  }
</script>
```

## $effect - Side Effects

Run code when reactive dependencies change:

```svelte
<script>
  let count = $state(0);

  $effect(() => {
    console.log('Count changed to', count);
    document.title = `Count: ${count}`;
  });
</script>
```

### Teardown / Cleanup

Return a function to clean up before re-running or on destroy:

```svelte
<script>
  let interval = $state(1000);

  $effect(() => {
    const id = setInterval(() => {
      console.log('tick');
    }, interval);

    // Cleanup: runs before re-run and on component destroy
    return () => clearInterval(id);
  });
</script>
```

### $effect.pre - Run Before DOM Updates

Rarely needed - runs before DOM updates:

```svelte
<script>
  let messages = $state([]);
  let container;

  $effect.pre(() => {
    // Check scroll position before DOM updates
    messages.length; // Track this dependency

    if (container && shouldAutoScroll(container)) {
      // Will scroll after DOM updates
      tick().then(() => container.scrollTo(0, container.scrollHeight));
    }
  });
</script>
```

### When NOT to Use $effect

**Don't sync state - use $derived instead:**

```svelte
<script>
  let count = $state(0);

  // BAD - don't do this
  let doubled = $state(0);
  $effect(() => {
    doubled = count * 2;
  });

  // GOOD - use $derived
  let doubled = $derived(count * 2);
</script>
```

**Don't create infinite loops:**

```svelte
<script>
  let count = $state(0);

  // BAD - infinite loop! reads and writes count
  $effect(() => {
    count = count + 1;
  });
</script>
```

**Use callbacks for linked values instead of effects:**

```svelte
<script>
  let spent = $state(0);
  let left = $derived(100 - spent);

  // Update spent via callback, not effect
  function updateLeft(newLeft) {
    spent = 100 - newLeft;
  }
</script>

<input type="range" bind:value={spent} max={100} />
<input type="range" value={left} oninput={(e) => updateLeft(+e.target.value)} max={100} />
```

## $bindable - Two-Way Binding

Enable parent components to bind to a prop:

```svelte
<!-- FancyInput.svelte -->
<script>
  let { value = $bindable(''), ...props } = $props();
</script>

<input bind:value {value} {...props} />
```

```svelte
<!-- Parent.svelte -->
<script>
  import FancyInput from './FancyInput.svelte';
  let name = $state('');
</script>

<FancyInput bind:value={name} /><p>Hello, {name}!</p>
```

See [components.md](./components.md) for more on `$props()` and `$bindable()`.

## $inspect - Debugging (Dev Only)

Log when values change (removed in production builds):

```svelte
<script>
  let count = $state(0);
  let user = $state({ name: 'Alice' });

  // Logs whenever count or user changes
  $inspect(count, user);
</script>
```

### Custom Inspection

```svelte
<script>
  let count = $state(0);

  $inspect(count).with((type, value) => {
    if (type === 'update') {
      debugger; // Break on changes
    }
  });
</script>
```

### Trace Effect Dependencies

```svelte
<script>
  $effect(() => {
    $inspect.trace(); // Must be first statement
    doSomethingComplex();
  });
</script>
```

## Common Gotchas

### Destructuring Breaks Reactivity

```svelte
<script>
  let user = $state({ name: 'Alice', age: 30 });

  // BAD - name and age are not reactive
  let { name, age } = user;

  // GOOD - access via object
  // In template: {user.name}, {user.age}
</script>
```

### Async Code Doesn't Track Dependencies

Only synchronously-read state inside `$effect` is tracked. State read inside `setTimeout`, `await`, or callbacks is not tracked.

### Exporting Reassigned State

Can't directly export state that gets reassigned. Wrap in an object instead:

```javascript
// state.svelte.js
export const counter = $state({ count: 0 });
export function increment() {
  counter.count++;
}
```

### Effects Only Run in Browser

`$effect` doesn't run during SSR:

```svelte
<script>
  $effect(() => {
    // Safe to use browser APIs here
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  });
</script>
```

## Quick Reference

| Rune                | Purpose           | Example                                  |
| ------------------- | ----------------- | ---------------------------------------- |
| `$state(value)`     | Reactive state    | `let count = $state(0)`                  |
| `$state.raw(value)` | Non-proxied state | `let data = $state.raw(bigObject)`       |
| `$derived(expr)`    | Computed value    | `let doubled = $derived(count * 2)`      |
| `$derived.by(fn)`   | Complex computed  | `$derived.by(() => { ... })`             |
| `$effect(fn)`       | Side effect       | `$effect(() => { ... })`                 |
| `$effect.pre(fn)`   | Pre-DOM effect    | `$effect.pre(() => { ... })`             |
| `$props()`          | Component props   | `let { foo } = $props()`                 |
| `$bindable()`       | Two-way prop      | `let { value = $bindable() } = $props()` |
| `$inspect(...)`     | Debug logging     | `$inspect(count)`                        |
