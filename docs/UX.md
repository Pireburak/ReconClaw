# ReconClaw UX Guidelines

Rules for any change to `templates/` and `static/`. Each rule cites the `ui-ux-pro-max` rule ID it comes from, so reviewers can look it up. Priority runs top to bottom: when two rules conflict, the earlier section wins.

**Design direction:** a "classified dossier" for security operators. Dense, calm, monospace-led, minimal color. Dark is the default theme and light is the "paper file" theme. UI copy is Turkish.

---

## 1. Accessibility `CRITICAL`

| Rule | Requirement | ID |
|---|---|---|
| Contrast | Text 4.5:1, large text and UI borders 3:1. Check dark and light separately. | `color-accessible-pairs` |
| `--faint` is decoration | `--faint` measures about 3:1 in dark and about 2.4:1 in light. Use it for dividers and disabled hints only, never for text that carries meaning. | `contrast-readability` |
| Focus | Every interactive element shows `:focus-visible` (the existing `outline: 1px solid var(--cyan); offset 2px`). Never `outline: none` without a replacement. | `focus-states` |
| Focus never hidden | The dock, sticky bars and toasts must not cover the focused control. | `focus-not-obscured` |
| Keyboard | Tab order follows visual order. Every command-palette and dock action works by keyboard. | `keyboard-nav` |
| Not by color alone | Severity always pairs color with a label or icon (`CRITICAL`, `HIGH`, ...). Charts add shape or text. | `color-not-only` |
| Names | Icon-only buttons need `aria-label`. Decorative icons are `aria-hidden`. | `aria-labels`, `icon-context` |
| Headings | One `h1` per page, then sequential levels. The `.panel h3` counter is visual only. | `heading-hierarchy` |
| Motion | Honor `prefers-reduced-motion` (already in `style.css`). Any new animation must be covered by it. | `reduced-motion` |
| Authentication | Login allows paste and password managers. The captcha and email code need a non-puzzle path. | `accessible-authentication` |

## 2. Touch & Interaction `CRITICAL`

- **Targets:** at least 44x44px on touch layouts (24px absolute floor on desktop), with 8px between targets. `touch-target-size`, `web-target-size`, `touch-spacing`
- **Hover is never required.** The dock tooltip must also open on `:focus-visible`. `hover-vs-tap`
- **Async buttons:** disable and show progress while a scan or request runs. `loading-buttons`
- **Feedback within 100ms** of a press. `tap-feedback-speed`
- **Clickable means `cursor: pointer`.** `cursor-pointer`

## 3. Performance `HIGH`

- Fonts: `font-display: swap`, preload only the two critical files. `font-loading`, `font-preload`
- Images declare `width`/`height` or `aspect-ratio`. Below-the-fold images use `loading="lazy"`. `image-dimension`, `lazy-load-below-fold`
- Anything over 1s shows a skeleton or progress, not a bare spinner. Scans use the radar and terminal view. `progressive-loading`
- Reserve space for async content (stat cards, charts, reports) so nothing jumps. `content-jumping`
- Tables or lists of 50+ rows are virtualized or paged. `virtualize-lists`
- Debounce input, scroll and resize handlers. `debounce-throttle`

## 4. Style `HIGH`

- **One visual language.** No gradients, glass or glow. Flat panels, 1px `--line` borders, `--shadow` as the only elevation. `consistency`, `elevation-consistent`
- **No emoji as icons.** Use the existing SVG (Lucide-line) set at one stroke width. `no-emoji-icons`, `icon-style-consistent`
- **One primary action per screen.** Secondary actions are visually quieter. `primary-action`
- **Dark and light are designed together.** Every new color needs both values. `dark-mode-pairing`
- **States are distinct:** hover, pressed, disabled and read-only must each look different. `state-clarity`, `read-only-distinction`

## 5. Layout & Responsive `HIGH`

| Item | Rule |
|---|---|
| Breakpoints | 1200 / 1100 / 860 / 420px (the ones already in `style.css`). Do not add new ones. |
| Approach | Mobile first. No horizontal scroll at 375px. |
| Spacing | 4px base scale (4, 8, 12, 16, 24, 32). |
| Viewport | `width=device-width, initial-scale=1`. Never disable zoom. Use `dvh`, not `100vh`. |
| Line length | 60-75 characters for prose. |
| Layers | A fixed z-index scale. No ad-hoc `z-index: 9999`. |
| Fixed UI | The dock and top bar reserve padding for content beneath. |
| Long values | Hostnames, banners and hashes wrap (`overflow-wrap: anywhere`). Never `word-break: break-all` on prose. |

## 6. Typography & Color `MEDIUM`

**Type roles.** Headings use Barlow Condensed (600-700). Body and data use IBM Plex Mono. The grade stamp and classified marks use Courier Prime. Scale: 12 / 14 / 16 / 18 / 24 / 32.

- Body text is at least 16px on mobile and has `line-height` 1.5. `readable-font-size`, `line-height`
- Data columns, timers, ports and scores use tabular figures. `number-tabular`
- **Always tokens, never raw hex in components.** `color-semantic`

| Token | Meaning |
|---|---|
| `--bg` `--panel` `--panel-2` `--line` | Surfaces and borders |
| `--text` `--muted` `--faint` | Text, secondary, decoration only |
| `--cyan` | Accent, set by `data-accent` (ink, copper, signal, olive, steel) |
| `--red` `--orange` `--yellow` `--green` `--blue` | Severity only, never decoration |
| `--classified` | The "GİZLİ" stamp only |

- Severity order is fixed: critical `--red`, high `--orange`, medium `--yellow`, low `--blue`, ok `--green`. Do not reuse these colors for non-severity meaning. `color-not-decorative-only`

## 7. Animation `MEDIUM`

- Animate `transform` and `opacity` only. Never width, height, top or left. `transform-performance`
- Use shared duration and easing tokens: about 150ms for micro feedback, 200-300ms for panels. Exit is about 60-70% of enter. `duration-timing`, `exit-faster-than-enter`
- Every animation must show cause and effect (a result arriving, a state changing). Decoration is not a reason. `motion-meaning`
- Never block input during an animation, and keep it interruptible. `no-blocking-animation`, `interruptible`
- At most 1-2 animated elements per view. `excessive-motion`

## 8. Forms & Feedback `MEDIUM`

- Every input has a visible `<label>`. A placeholder is never the label. `input-labels`
- Errors appear below the field, say cause and fix, and link with `aria-describedby`. After a failed submit, focus the error summary or the first invalid field. `error-placement`, `error-clarity`, `focus-management`
- Validate on blur, not on every keystroke. `inline-validation`
- Use semantic input types and `autocomplete` (`email`, `one-time-code`, `current-password`). Offer a show/hide password toggle. `input-type-keyboard`, `autofill-support`, `password-toggle`
- Destructive actions (delete target, revoke token, delete account) require a confirmation, use the danger color, and are separated from primary actions. `confirmation-dialogs`, `destructive-emphasis`
- Toasts auto-dismiss in 3-5s, use `aria-live="polite"` and never take focus. `toast-dismiss`, `toast-accessibility`
- Every empty list gets a message and a next action ("no scans yet, start one"). `empty-states`
- A failed request shows a retry. Plan-limit errors state the limit and the upgrade path. `error-recovery`, `timeout-feedback`

## 9. Navigation `HIGH`

- The dock is primary navigation. It keeps the same place on every page and stays at 5 items or fewer on small screens (extra items go to an overflow menu). `navigation-consistency`, `bottom-nav-limit`, `overflow-menu`
- The current location is always highlighted, and nav items have both icon and label (the tooltip is not enough on touch). `nav-state-active`, `nav-label-icon`
- Every key view has a URL, including shared report links. `deep-linking`
- Back restores scroll, filters and form input. `state-preservation`
- After a view change, move focus to the main content. `focus-on-route-change`
- Modals dismiss with a visible close, `Esc`, and a confirm if there are unsaved changes. They are never used for primary navigation. `modal-escape`, `sheet-dismiss-confirm`, `modal-vs-navigation`
- Logout and account deletion sit apart from normal nav. `destructive-nav-separation`

## 10. Charts & Data `LOW`

- Match chart to data: trend is a line, comparison is a bar, proportion is a donut with 5 or fewer parts. `chart-type`, `no-pie-overuse`
- Every chart has a legend, an accessible text summary (`aria-label`) and a table alternative. `legend-visible`, `screen-reader-summary`, `data-table`
- Tooltips work on focus and tap, not only hover. `tooltip-keyboard`
- Use `--line` at low contrast for gridlines, 3:1 for data marks, 4.5:1 for data text. `gridline-subtle`, `contrast-data`
- Show an empty state and an error state with retry, never a blank axis frame. `empty-data-state`, `error-state-chart`
- Format numbers and dates for the user's locale. `number-formatting`

---

## Pre-merge checklist

- [ ] Works at 375px with no horizontal scroll, and in both dark and light themes
- [ ] All five accents keep text at 4.5:1
- [ ] Full flow completes with keyboard only; focus ring always visible
- [ ] No raw hex, no emoji icons, no new breakpoint
- [ ] `prefers-reduced-motion` respected
- [ ] Empty, loading and error states exist for every new view
- [ ] Severity shown with text or icon, not color alone

## How to look up a rule

The rule set ships with the `ui-ux-pro-max` skill. Full text of every ID is in `.agents/skills/ui-ux-pro-max/references/quick-reference.md`, and it is searchable:

```bash
python3 .agents/skills/ui-ux-pro-max/scripts/search.py "focus not obscured" --domain ux
```
