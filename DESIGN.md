---
version: 1.0
name: What-Went-Wrong-design
description: Visual system for What Went Wrong, a tool that replays the moments before a goal and shows where the defending team's shape broke. Adapted from the Vercel-inspired DESIGN.md in VoltAgent/awesome-design-md, keeping its stark ink-on-near-white system, 4px spacing, type hierarchy and stacked-shadow elevation. Vercel's brand colours, mesh gradient and proprietary fonts are replaced with our own. The only saturated colour in the product is data. Blue is the defence, red is the collapse.

colors:
  # Neutrals (kept from the source system; `mute` darkened for WCAG AA)
  primary: "#171717"
  on-primary: "#ffffff"
  ink: "#171717"
  body: "#4d4d4d"
  mute: "#6b6b6b"          # source used #888888 (3.5:1, fails AA), ours is 5.3:1 on white
  hairline: "#ebebeb"
  hairline-strong: "#a1a1a1"
  canvas: "#ffffff"
  canvas-soft: "#fafafa"
  canvas-soft-2: "#f5f5f5"
  selection-bg: "#171717"
  selection-fg: "#f2f2f2"

  # Our brand / data colours (replace Vercel's link blue + mesh gradient)
  defence: "#1d5fd0"        # defending team: dots, cover shadows, pressure field. 5.8:1 on white
  defence-soft: "#dce8fb"   # fills, selected-row tint, legend chips
  defence-deep: "#174a9f"   # hover / pressed
  attack: "#171717"         # attacking team = ink. The threat is neutral, the defence is the subject
  collapse: "#c4261b"       # the moment the shape broke. Only used for that meaning. 5.8:1 on white
  collapse-soft: "#fbe4e1"
  collapse-deep: "#9b1d14"
  ball: "#ffffff"           # with an ink stroke
  keeper-ring: "#171717"

  # Status (kept semantically, retuned for contrast)
  warning: "#b45309"        # 5.0:1 on white, used for "not enough defenders visible"
  warning-soft: "#fef3c7"
  success: "#177245"        # 6.0:1; rarely used ("shape held")

  # Pitch
  pitch: "#f7f8f7"
  pitch-line: "#c8c8c8"     # decorative; contrast not required

typography:
  display-lg:   { fontFamily: "Inter, system-ui, sans-serif", fontSize: 32px, fontWeight: 600, lineHeight: 40px, letterSpacing: -1.28px }
  display-md:   { fontFamily: "Inter, system-ui, sans-serif", fontSize: 24px, fontWeight: 600, lineHeight: 32px, letterSpacing: -0.96px }
  display-sm:   { fontFamily: "Inter, system-ui, sans-serif", fontSize: 20px, fontWeight: 600, lineHeight: 28px, letterSpacing: -0.6px }
  body-lg:      { fontFamily: "Inter, system-ui, sans-serif", fontSize: 18px, fontWeight: 400, lineHeight: 28px }
  body-md:      { fontFamily: "Inter, system-ui, sans-serif", fontSize: 16px, fontWeight: 400, lineHeight: 24px }
  body-sm:      { fontFamily: "Inter, system-ui, sans-serif", fontSize: 14px, fontWeight: 400, lineHeight: 20px, letterSpacing: -0.28px }
  body-sm-strong: { fontFamily: "Inter, system-ui, sans-serif", fontSize: 14px, fontWeight: 500, lineHeight: 20px, letterSpacing: -0.28px }
  caption:      { fontFamily: "Inter, system-ui, sans-serif", fontSize: 12px, fontWeight: 400, lineHeight: 16px }
  caption-mono: { fontFamily: "JetBrains Mono, ui-monospace, monospace", fontSize: 12px, fontWeight: 400, lineHeight: 16px }
  data-xl:      { fontFamily: "JetBrains Mono, ui-monospace, monospace", fontSize: 40px, fontWeight: 500, lineHeight: 44px, letterSpacing: -1.2px }
  button-md:    { fontFamily: "Inter, system-ui, sans-serif", fontSize: 14px, fontWeight: 500, lineHeight: 20px }

rounded:
  none: 0px
  xs: 4px
  sm: 6px     # buttons, inputs, list rows (app scale, the only button radius we use)
  md: 8px     # cards, panels, the pitch frame
  lg: 12px    # empty-state card, large callouts
  full: 9999px # badges, legend chips, timeline points

spacing:
  xxs: 4px
  xs: 8px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  2xl: 40px
  3xl: 48px
  4xl: 64px

elevation:
  level-1: "inset 0 0 0 1px #00000014"
  level-2: "0 1px 1px #00000005, 0 2px 2px #0000000a, inset 0 0 0 1px #00000014"
  level-3: "0 2px 2px #0000000a, 0 8px 8px -8px #0000000a, inset 0 0 0 1px #00000014"
  level-5: "0 1px 1px #00000005, 0 8px 16px -4px #0000000a, 0 24px 32px -8px #0000000f, inset 0 0 0 1px #00000014"

motion:
  fast: 120ms     # hover, press
  frame: 250ms    # player / overlay transitions between frames
  easing: "cubic-bezier(0.2, 0, 0, 1)"
  reduced: 0ms    # everything snaps under prefers-reduced-motion

components:
  app-header:      { backgroundColor: "{colors.canvas}", borderBottom: "{colors.hairline}", height: 56px, padding: "0 {spacing.lg}" }
  step-row:        { backgroundColor: "{colors.canvas}", hover: "{colors.canvas-soft-2}", selectedBackground: "{colors.canvas-soft-2}", activeIndicator: "{colors.primary}", rounded: "{rounded.sm}", padding: "{spacing.xs} {spacing.sm}", minHeight: 44px }
  button-primary:  { backgroundColor: "{colors.primary}", textColor: "{colors.on-primary}", typography: "{typography.button-md}", rounded: "{rounded.sm}", height: 32px, padding: "0 {spacing.sm}" }
  button-secondary: { backgroundColor: "{colors.canvas}", textColor: "{colors.ink}", border: "{colors.hairline}", typography: "{typography.button-md}", rounded: "{rounded.sm}", height: 32px, padding: "0 {spacing.sm}" }
  icon-button:     { backgroundColor: "{colors.canvas}", textColor: "{colors.ink}", border: "{colors.hairline}", rounded: "{rounded.sm}", size: 32px, hitArea: 44px }
  toggle-chip:     { backgroundColor: "{colors.canvas}", onBackground: "{colors.canvas-soft-2}", textColor: "{colors.body}", onTextColor: "{colors.ink}", border: "{colors.hairline}", rounded: "{rounded.full}", height: 28px, padding: "0 {spacing.sm}" }
  card:            { backgroundColor: "{colors.canvas}", rounded: "{rounded.md}", padding: "{spacing.md}", shadow: "{elevation.level-2}" }
  badge:           { backgroundColor: "{colors.canvas-soft-2}", textColor: "{colors.body}", typography: "{typography.caption}", rounded: "{rounded.full}", padding: "0 {spacing.xs}" }
  badge-collapse:  { backgroundColor: "{colors.collapse-soft}", textColor: "{colors.collapse-deep}", typography: "{typography.caption}", rounded: "{rounded.full}" }
  callout-collapse: { backgroundColor: "{colors.collapse-soft}", borderLeft: "3px {colors.collapse}", textColor: "{colors.ink}", rounded: "{rounded.sm}", padding: "{spacing.sm} {spacing.md}" }
  callout-warning: { backgroundColor: "{colors.warning-soft}", textColor: "{colors.ink}", icon: "{colors.warning}", rounded: "{rounded.sm}", padding: "{spacing.sm} {spacing.md}" }
  metric-meter:    { track: "{colors.canvas-soft-2}", fill: "{colors.defence}", height: 6px, rounded: "{rounded.full}" }
  pitch-frame:     { backgroundColor: "{colors.pitch}", line: "{colors.pitch-line}", rounded: "{rounded.md}", shadow: "{elevation.level-1}" }
  empty-state:     { backgroundColor: "{colors.canvas-soft}", rounded: "{rounded.lg}", padding: "{spacing.3xl}" }
---

## Overview

What Went Wrong replays the passes, carries and tackles before a goal and asks one question: **when did the defending team's shape stop protecting the goal?** People arrive knowing football, not StatsBomb, so the interface has one job: show the pitch, say plainly what you're looking at, and point at the moment it broke.

The visual system comes from Vercel's DESIGN.md: an ink-on-near-white surface, a disciplined grey ladder, Inter and JetBrains Mono, a 4px grid and stacked hairline elevation. Vercel's decoration (the mesh gradient) is gone. **The data is the only colour.** Everything chrome is grey, so the eye goes to blue (the defence) and red (the collapse).

**Key characteristics:**
- One colour story: **blue = the defence** (dots, the passing lanes they block, the ground they cover), **ink = the attack**, **red = the collapse moment and nothing else**. Gaps in the blue are the story.
- Plain-language labels first, technical labels second. "Shape score 42 / 100", not "Composite 0.42".
- Mono is for numbers, timestamps and data captions, never prose.
- The pitch is the hero and gets the most space at every breakpoint.

## Colors

### Neutrals
Inherited from the source system: `ink` #171717 (headings, primary buttons, attacking players), `body` #4d4d4d (secondary text), `mute` #6b6b6b (captions, hints; darkened from the source's #888888 to pass WCAG AA), `hairline` #ebebeb (borders and dividers), `canvas` #ffffff (cards), `canvas-soft` #fafafa (page), `canvas-soft-2` #f5f5f5 (hover, selected rows, tracks).

### Data colours (ours)
- **Defence** `#1d5fd0`: defending outfield players, cover-shadow cones (at low alpha), the pressure field (a sequential ramp from transparent to defence), metric meter fills. `defence-soft` #dce8fb for tints, `defence-deep` #174a9f for hover.
- **Attack** `#171717` (ink): attacking players. They're neutral on purpose; the app is about the defence.
- **Collapse** `#c4261b`: the collapse frame marker, the collapse callout, the drop in the score. Reserved: never for errors, never for decoration. `collapse-soft` #fbe4e1, `collapse-deep` #9b1d14.
- **Keeper**: same team colour as their side, drawn larger with an ink outline ring. Keepers are not given a third hue.
- **Ball**: white with a 1.5px ink stroke, drawn on top of everything.
- **Player on the ball**: a 2px ink halo ring offset 3px from the dot.

Blue against ink holds under all common colour-vision deficiencies, because it differs in luminance and not only hue. Red is only ever paired with a label or a dashed line, never colour alone.

### Status
- **Warning** `#b45309` on `warning-soft` #fef3c7: "Only 4 defenders in view. Score not reliable."
- **Error** uses ink text on `canvas-soft-2` with an icon and a retry action. Red is reserved for the collapse.
- **Success** `#177245`: optional "shape held" note. Use rarely.

### Pitch
`pitch` #f7f8f7 surface, `pitch-line` #c8c8c8 markings at 1px. There is no grass green: a monochrome pitch lets the data colours carry meaning. Every player dot gets a 1.5px white stroke so it separates from the pressure field beneath it (non-text contrast ≥ 3:1).

## Typography

**Inter** (400/500/600) for everything readable; **JetBrains Mono** (400/500) for numbers, clocks and data captions. Both come from Google Fonts with `font-display: swap`. They replace Vercel's proprietary Geist and Geist Mono and are the substitutes the source document itself recommends.

| Token | Size / LH | Weight | Use |
|---|---|---|---|
| display-lg | 32/40, −1.28px | 600 | Empty-state headline |
| display-md | 24/32, −0.96px | 600 | Match title above the pitch |
| display-sm | 20/28, −0.6px | 600 | Panel titles |
| body-lg | 18/28 | 400 | Empty-state lead |
| body-md | 16/24 | 400 | Explanations, callouts |
| body-sm | 14/20 | 400 | Default UI text, list rows |
| body-sm-strong | 14/20 | 500 | Row titles, labels |
| caption | 12/16 | 400 | Hints, secondary row text, legend |
| caption-mono | 12/16 | 400 | Clock times, frame counters, axis ticks |
| data-xl | 40/44, −1.2px | 500 mono | The shape score |
| button-md | 14/20 | 500 | All buttons |

**Principles**
- Sentence case everywhere, including labels and headings. No uppercase text.
- 600 is the weight ceiling.
- **12px is the floor.** Nothing renders smaller.
- All changing numbers use `font-variant-numeric: tabular-nums`.

## Layout

### Spacing
4px base. Tokens `xxs` 4 · `xs` 8 · `sm` 12 · `md` 16 · `lg` 24 · `xl` 32 · `2xl` 40 · `3xl` 48 · `4xl` 64. Tight inside a group (`xs`), wide between groups (`lg`).

### App structure
- **Header** (56px): wordmark, one-line purpose, "How it works" link.
- **Desktop ≥ 1200px**: three columns: selection rail (280px) · analysis stage (fluid, pitch + timeline) · insight panel (320px).
- **Tablet 768–1199px**: the selection rail becomes a collapsible drawer; stage and insight panel stack, with the pitch first.
- **Mobile < 768px**: single column. Selection is a stepped sheet; pitch full width; timeline below; insight cards below that. Page gutters 16px.
- The pitch scales fluidly via `viewBox` and is never fixed-pixel. Max stage width 960px.

### Touch targets
Every interactive element has a hit area of at least 44×44px on coarse pointers (32px visual buttons get padding). Timeline points enlarge their hit area invisibly.

## Elevation & depth

Stacked shadows from the source system, unchanged:

| Level | Use |
|---|---|
| level-1: inset hairline | Pitch frame, list groups |
| level-2: subtle drop | Cards in the insight panel |
| level-3: soft stack | Selection drawer on tablet |
| level-5: modal | "How it works" dialog, mobile sheet |

Never a single heavy drop shadow.

## Shapes
`sm` 6px for every button, input and list row (one button radius only, no pill CTAs). `md` 8px for cards and the pitch frame. `lg` 12px for the empty-state card. `full` for badges, chips and timeline points.

## Components

- **App header**: canvas, hairline bottom border. Wordmark in body-sm-strong, purpose line in caption mute.
- **Step rows** (competition, match, goal): full-width `<button>`s at 44px minimum; selected state is a `canvas-soft-2` background plus a 2px ink left indicator plus `aria-current`. Groups are numbered "1 Competition · 2 Match · 3 Goal" and collapse to a one-line summary once chosen.
- **Buttons**: primary (ink fill) and secondary (canvas + hairline). Icon buttons are 32px visual with a 44px hit area and SVG icons (no emoji glyphs).
- **Toggle chips**: switch pitch overlays (cover shadows, pressure) on and off. `aria-pressed`.
- **Legend**: always visible under the pitch. Swatch plus plain words: "Defending team", "Attacking team", "Ball", "On the ball", "Passing lane blocked", "Defensive pressure".
- **Shape timeline** (the hero chart): full stage width, about 120px tall. Line of the shape score per frame, with gaps where it can't be scored. A dashed red vertical marker labelled "Collapse" and a filled ink marker for the current frame. Click or arrow-key any point to jump there. It replaces the separate slider, dot row and sparkline.
- **Shape score card**: the score in data-xl with a verbal band ("Solid" ≥ 70, "Stretched" 40–69, "Broken" < 40) and the change since the previous frame.
- **Metric meters**: label, a one-sentence visible explanation, value, and `role="meter"`. No hover-only explanations.
- **Collapse callout**: collapse-soft background, 3px collapse left border, a sentence describing what dropped and by how much, and a "Jump to collapse" button.
- **Warning callout**: for fewer than 6 defenders in view.
- **Empty state**: says what the app does in one sentence, shows a three-step "how to read it" strip, and offers one example goal to start with.

## Motion
- Frame-to-frame player movement takes 250ms; overlays crossfade. Large ball jumps snap.
- Players are not keyed to identities, so dots **crossfade** rather than slide when the player set changes, to avoid implying movement that didn't happen.
- Under `prefers-reduced-motion: reduce` every transition is 0ms and autoplay stays paused until explicitly started.
- Animate transform and opacity only. Never `transition: all`.

## Accessibility (non-negotiable)
- Visible `:focus-visible` ring everywhere: `0 0 0 2px canvas, 0 0 0 4px ink`.
- Skip link to the analysis stage. Heading order h1 → h2 → h3.
- The pitch SVG has `role="img"` and a live text summary ("Frame 7 of 15, 34:12, Pass by the attacking team. 7 defenders in view. Shape score 42, down 18.").
- Async states (loading, errors, collapse reached) are announced through a polite live region.
- Keyboard shortcuts (←/→ step, Space play) only fire when focus isn't in a form control.
- `color-scheme: light`, a `theme-color` meta tag, and `touch-action: manipulation`.

## Do's and don'ts

### Do
- Keep chrome grey so blue and red mean something.
- Say what a number means in words next to it.
- Give the pitch the most space at every width.
- Use mono for numbers and clocks only.
- Use stacked hairline shadows.

### Don't
- Don't use red for anything except the collapse (errors use ink + icon).
- Don't introduce a new accent colour. Ink, greys, defence blue and collapse red are the whole palette.
- Don't use grass green or photographic textures on the pitch.
- Don't hide explanations behind `title` tooltips.
- Don't set text below 12px or use uppercase headings.
- Don't use emoji or Unicode glyphs as icons; use inline SVG.
- Don't use weight 700 or above.

## Theme
Light only for v1, as in the source system. A dark theme would be derived later by flipping the neutral ladder while keeping defence and collapse hues; it's out of scope until requested.
