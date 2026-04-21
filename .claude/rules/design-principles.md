---
paths:
  - '**/*.svelte'
  - '**/+page.svelte'
---

# Physical AI Design Principles

## Scope

This design system targets the **Measure** and **Reason** layers of the Physical AI stack. Interfaces built with it should support **augmentation** (helping humans perceive the physical world) and **dialogue** (helping humans reason about it). Operation and cooperation — where AI takes action in the world — are out of scope currently but will become relevant in the future.

## The Physical AI Stack

Physical AI capabilities form a dependency stack where each layer builds on the one below:

1. **Interpret** — Make the physical world legible by surfacing signals, anomalies, and structures from sensor data
2. **Reason** — Enable shared reasoning between humans and AI: explore hypotheses, compare alternatives, support decisions
3. **Operate** — Delegated action: human sets intent, system executes within defined boundaries (future scope)
4. **Co-operate** — Joint action: shared agency through mutual adjustment between humans and AI (future scope)

## Agency

### Human Agency Comes First

At the Measure layer, the AI augments human perception — it surfaces what would otherwise remain invisible. The human retains full responsibility to interpret and act. Interfaces should present information without prescribing conclusions.

At the Reason layer, interaction is dialogic. The AI contributes explanations and comparisons, but the human drives inquiry and judgment. Interfaces should enable exploration, not deliver verdicts.

At the Operate layer, humans shift from direct control to goal-setting and supervision. The AI executes within defined boundaries, and responsibility becomes distributed. Interfaces should make intent, constraints, and system behavior transparent.

At the Co-operate layer, humans and AI act as coordinated participants. Action is jointly negotiated, and intent, context, and responsibility are shared and continuously adjusted. Interfaces should support mutual awareness and fluid handoffs.

### Interaction Is Situated

Interaction unfolds within a three-way relationship: **person, system, and physical world**. Meaning arises from how sensor data, context, and human intent come together in a specific place and moment. Interfaces must maintain this connection to the physical context being observed — sensor sources, locations, time ranges, environmental conditions. Do not abstract away the situational grounding.

## Design Implications

### Make the World Legible

- Prioritize data clarity: visualizations should reveal structure in sensor data — trends, anomalies, distributions, correlations
- Use semantic tokens (e.g. `text-atai-good`, `text-atai-warning`, `text-atai-critical`) to communicate meaningful states, not for decorative emphasis
- Design for continuous monitoring: prefer dashboards and live views over static reports

### Support Dialogue, Not Monologue

- Provide entry points for inquiry: interfaces should invite questions, comparisons, and hypothesis exploration
- Frame AI output as contribution, not conclusion — use language and layout that position AI reasoning as input to human judgment
- Enable iterative refinement: conversational flows, follow-up exploration, adjustable parameters

### Preserve Physical Context

- Show provenance: which sensors, what time range, what conditions produced the data being displayed
- Ground abstract representations in physical reality — link charts to sensor locations, timestamps to real events
- Consider operational environments: interfaces may be used in the field, not only at a desk

### Respect the Stack Boundary

- Default to interfaces that support perception and reasoning rather than autonomous AI action
- Where possible, distinguish between "the system shows" (Measure) and "the system suggests" (Reason)
- Prefer framing AI output as observations or suggestions rather than commands or decisions

## Aesthetic Conventions

### Typography
- Use mono font (`font-mono`) with careful consideration: prefer it on badges, buttons, card headers, and numeric values. Do not apply mono to body text or descriptions.

### Card Defaults
- For single-purpose card components (status display, score, chart), use BackgroundCard as the default container.
- Status cards showing a single metric or state often do not need a CardHeader — omit when content is self-explanatory.