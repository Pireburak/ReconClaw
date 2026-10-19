# Tasks & Implementation Plan for Burak

This document outlines the design system, typography, GPU-accelerated rendering, and Apple HIG icon/logo overhaul for **ReconClaw**.

**Rules:** One step at a time, verify each step before the next, no skipped step, no non-working part.

---

## 1. Typography & GPU-Enhanced Rendering (2026 SecOps Standard)

### The Problem in Current ReconClaw
- Headings use `Barlow Condensed` and body text uses `IBM Plex Mono` without hardware antialiasing or optical sizing adjustments, making dense security scans hard to read over long operating sessions.
- Text rendering does not use GPU compositor layers or subpixel antialiasing tokens (`-webkit-font-smoothing`, `-moz-osx-font-smoothing`), causing blurry glyphs on Retina and high-DPI displays.
- Numeric telemetry (ports, IP addresses, CVE IDs, risk score meters, timestamps) lacks explicit OpenType features (`tnum` tabular figures, slashed zero `zero`, and character disambiguation `cv02`/`cv11`), causing visual layout jitter when scan logs stream in real time.

### 2026 SecOps Typography Stack & Tokens
1. **Font Roles**:
   - **UI Sans (Navigation, Labels, Cards, Modals)**:
     - `Inter Variable` or `Geist Sans` with optical sizing (`font-optical-sizing: auto`).
     - Native Apple system fallback: `-apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display", sans-serif`.
   - **Monospace Telemetry (Terminal, CVEs, Hashes, IP/Ports, Tables)**:
     - `JetBrains Mono Variable` or `Geist Mono` (replaces raw `IBM Plex Mono`).
     - Native fallback: `ui-monospace, "SF Mono", Menlo, Consolas, monospace`.
   - **Stamp & Security Classification**:
     - `Courier Prime` (retained specifically for the classified "GİZLİ" / Dossier watermark stamp only).

2. **Global Hardware Acceleration & Font Smoothing Tokens** (add to `static/css/style.css`):
   ```css
   :root {
     --font-sans: "Inter Variable", -apple-system, BlinkMacSystemFont, "SF Pro Text", "Segoe UI", sans-serif;
     --font-mono: "JetBrains Mono Variable", ui-monospace, "SF Mono", Menlo, monospace;
     --font-stamp: "Courier Prime", monospace;
   }

   body {
     font-family: var(--font-sans);
     -webkit-font-smoothing: antialiased;
     -moz-osx-font-smoothing: grayscale;
     text-rendering: optimizeLegibility;
     font-feature-settings: "cv02", "cv03", "cv04", "cv11", "zero";
   }

   /* High-density telemetry columns & streaming logs */
   .telemetry-data,
   .port-badge,
   .cve-id,
   .timestamp,
   .metric-value,
   table td.numeric {
     font-family: var(--font-mono);
     font-variant-numeric: tabular-nums;
     font-feature-settings: "tnum", "zero";
     transform: translateZ(0); /* Force GPU compositor layer to prevent redraw blur */
   }
   ```

3. **Type Scale Hierarchy**:
   | Role | Size (px / rem) | Weight | Line Height | Usage |
   |---|---|---|---|---|
   | Micro | 10px / 0.625rem | 600 | 1.2 | Protocol pills, CVE severity tags, compact chips |
   | Caption | 12px / 0.75rem | 500 | 1.33 | Timestamp footnotes, table subheaders, metadata |
   | Body Small | 13px / 0.8125rem | 400 | 1.4 | Report tables, service banners, finding descriptions |
   | Body Base | 14px / 0.875rem | 400/500 | 1.45 | Default UI labels, form controls, narrative text |
   | Subhead | 16px / 1.0rem | 600 | 1.4 | Panel headers, card section titles |
   | Title | 20px / 1.25rem | 700 | 1.3 | Modal headers, dashboard stat group titles |
   | Display | 28px–36px | 800 | 1.1 | Scorecards (0–100 risk score), Security Grade (A+…F) |

4. **SecOps Color Tokens & WCAG Contrast**:
   - Modern dark-mode palette designed for eye fatigue reduction:
     - `surface-0`: `#0B0F17` (Deep Obsidian foundation)
     - `surface-1`: `#111827` (Panel surface)
     - `surface-2`: `#1F2937` (Card / Hover surface)
     - `surface-border`: `#374151` / `rgba(255, 255, 255, 0.08)`
   - Semantic Severity Palettes (tested for WCAG AAA contrast against dark backgrounds):
     - **Critical**: Crimson / Scarlet (`#EF4444` text, `#7F1D1D` border/tint)
     - **High**: Vivid Amber / Orange (`#F97316` text, `#7C2D12` border/tint)
     - **Medium**: Golden Amber (`#F59E0B` text, `#78350F` border/tint)
     - **Low / Info**: Cyan / Sky Blue (`#06B6D4` text, `#164E63` border/tint)
     - **Clean / Safe**: Emerald Green (`#10B981` text, `#064E3B` border/tint)

---

## 2. Icon & Logo Overhaul (Apple Human Interface Guidelines 2026)

### The Problem in Current ReconClaw
- Current `static/img/logo.png`, `static/favicon.png`, and `static/img/apple-touch-icon.png` degrade significantly at small sizes (`16×16` browser tab, `32×32` bookmark, `48×48` taskbar).
- Fine lines, subtle gradients, and complex details turn into blurry, illegible artifacts.
- Missing optical scaling and lack of support for modern OS appearance modes (Dark Mode, Tinted Home Screens, Monochromatic Taskbars).

### Requirements & Solutions (Apple HIG Alignment)
1. **Core Silhouette & Simplicity**:
   - Focus on **one bold, memorable concept**: a razor-sharp geometric Claw silhouette enclosing a subtle optical radar/aperture pulse.
   - Zero embedded text, zero micro-illustrations, zero UI screenshots inside the icon.
   - Confident stroke weights that stay crisp down to `16×16px`.

2. **Optical Sizing & Multi-Scale Assets**:
   - Do not merely downsample a single SVG. Produce scale-specific vector geometry:
     - **16×16 & 32×32 (`favicon.ico`, `favicon.png`)**: Thick silhouette, bold contrast, simplified geometry without interior hairline paths or shadows.
     - **64×64 & 128×128 (Navigation & Header)**: Refined vector geometry matching the UI theme.
     - **180×180 (`apple-touch-icon.png`)**: Apple iOS/iPadOS home screen standard with 10% keyline padding (unrounded corners; OS applies squircle mask).
     - **512×512 & 1024×1024 (Master / Store)**: Full-fidelity master rendered on a 1024×1024 artboard.

3. **2026 Apple HIG Appearance Variants**:
   - **Default Appearance**: Full-color rich icon on dark obsidian canvas.
   - **Dark Appearance**: Calibrated luminance with low-glare dark background for system dark modes.
   - **Tinted & Clear Appearance**: Monochromatic alpha mask variant supporting iOS 18+ and macOS Sequoia tinted themes (system applies user-chosen accent color or frosted glass translucency without losing icon identity).

4. **Web Deliverables in `static/`**:
   - `static/favicon.ico`: Multi-size binary ICO containing 16×16, 32×32, and 48×48 bitmaps.
   - `static/favicon.svg`: Modern vector favicon supporting `@media (prefers-color-scheme: dark)` and `light`.
   - `static/img/apple-touch-icon.png`: 180×180 PNG for Apple devices.
   - `static/site.webmanifest`: PWA icons (`192×192`, `512×512`, maskable).

---

## 3. Phased Step-by-Step Execution Plan

| Step | Action | Done when |
|---|---|---|
| **B1** | **Download & Self-Host Fonts**<br>Download WOFF2 files for `Inter Variable` and `JetBrains Mono Variable` into `static/fonts/`. Update `static/fonts/fonts.css`. | Font files exist locally in `static/fonts/` with `font-display: swap` and zero external CDN requests. |
| **B2** | **Apply GPU Smoothing & OpenType Tokens**<br>Add `-webkit-font-smoothing`, `-moz-osx-font-smoothing`, `optimizeLegibility`, and `tabular-nums` rules to `static/css/style.css`. | Running scans and live counters show zero text blur on Retina and zero layout shift on tabular data. |
| **B3** | **SecOps Color Tokens Refactor**<br>Introduce `--surface-0` through `--surface-2` and calibrated WCAG AAA severity tokens into `static/css/style.css`. | Contrast checker passes ≥ 4.5:1 for all text and ≥ 3:1 for all borders/pills across both dark and light modes. |
| **B4** | **Design Vector Icon Master (1024×1024)**<br>Design minimal, memorable claw glyph following Apple HIG keyline grid and squircle safe zones. | Master SVG exists with bold silhouette, no embedded text, and clear readability at 16px preview. |
| **B5** | **Generate Multi-Size Favicon Package**<br>Export optical 16px/32px/48px `favicon.ico`, scalable `favicon.svg` with dark/light scheme support, and 180×180 `apple-touch-icon.png`. | Browser tab at 16px shows a crisp, recognizable icon in Chrome, Safari, and Edge. |
| **B6** | **Template Integration & Verification**<br>Update `templates/base.html` `<head>` tags to link modern favicon, SVG icon, and apple-touch-icon. | All pages load new typography and icons without broken references or console errors. |
| **B7** | **Documentation & Knowledge Graph Update**<br>Update `docs/UX.md` section 6 and `docs/PLAN.md`. Run `lat check`. | All validation checks pass with 0 errors. |
