---
name: fix-metadata
description: Updates a SvelteKit project's metadata including page titles, favicons, meta descriptions, Open Graph tags, and SEO tags. Use when updating the favicon, setting page titles, adding OG tags, fixing SEO metadata, branding a project's tab/title, or when the user mentions "metadata", "favicon", "page title", "OG tags", or "SEO".
---

# Fixing Metadata

Update page titles, favicons, and meta tags in SvelteKit projects using the design system.

## Where Metadata Lives

| Location                     | What goes there                                                  |
| ---------------------------- | ---------------------------------------------------------------- |
| `src/app.html`               | Favicon `<link>`, charset, viewport, base HTML                   |
| `src/routes/+layout.svelte`  | Global `<svelte:head>` for site-wide title, description, OG tags |
| `src/routes/**/+page.svelte` | Per-route `<svelte:head>` for page-specific titles               |

## Favicon

### Install the ATAI Favicon

This skill ships with the default Archetype AI favicon in `assets/favicon.ico`. Copy it to the project:

```bash
cp assets/favicon.ico static/favicon.ico
```

### Update app.html

Ensure `src/app.html` references the favicon:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <link rel="icon" href="%sveltekit.assets%/favicon.ico" />
    %sveltekit.head%
  </head>
  <body data-sveltekit-prerender="true">
    <div style="display: contents">%sveltekit.body%</div>
  </body>
</html>
```

For SVG favicons (sharper at all sizes):

```html
<link rel="icon" href="%sveltekit.assets%/favicon.svg" type="image/svg+xml" />
<link rel="icon" href="%sveltekit.assets%/favicon.ico" sizes="any" />
```

## Page Title and Description

Add a global `<svelte:head>` in the root layout:

```svelte
<!-- src/routes/+layout.svelte -->
<script>
  let { children } = $props();
</script>

<svelte:head>
  <title>My App — Archetype AI</title>
  <meta name="description" content="Brief description of the application." />
</svelte:head>

{@render children?.()}
```

## Open Graph Tags

Add OG tags for social sharing previews:

```svelte
<svelte:head>
  <title>My App — Archetype AI</title>
  <meta name="description" content="Brief description of the application." />

  <!-- Open Graph -->
  <meta property="og:title" content="My App — Archetype AI" />
  <meta property="og:description" content="Brief description of the application." />
  <meta property="og:type" content="website" />
  <meta property="og:image" content="https://example.com/og-image.png" />
  <meta property="og:url" content="https://example.com" />

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="My App — Archetype AI" />
  <meta name="twitter:description" content="Brief description of the application." />
  <meta name="twitter:image" content="https://example.com/og-image.png" />
</svelte:head>
```

## Per-Route Metadata

Override the global title on specific pages:

```svelte
<!-- src/routes/dashboard/+page.svelte -->
<svelte:head>
  <title>Dashboard — My App</title>
</svelte:head>

<!-- page content -->
```

SvelteKit merges `<svelte:head>` from layouts and pages — the most specific (page-level) wins for duplicate tags like `<title>`.

## Verification

- [ ] `static/favicon.ico` exists and is the ATAI favicon
- [ ] `app.html` has `<link rel="icon">` pointing to the favicon
- [ ] Root layout has `<svelte:head>` with title and description
- [ ] OG tags are present if social sharing is needed
- [ ] Per-route pages override title where appropriate
- [ ] Browser tab shows the correct favicon and title
