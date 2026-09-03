[🇫🇷 Version française](design-system.fr.md) | 🇬🇧 English version

---

# Design System - Stamped

**Type:** Design reference - visual conventions observed in the code.
**Scope:** Frontend (Vue 3, plain scoped CSS per component, no CSS framework, no design tokens).

> Unlike some sibling projects, there is no formal design audit behind this document and no centralized token file (`:root` CSS variables, Tailwind config, etc.). Colors and spacing are hardcoded per component. This document records the conventions actually followed, as a baseline for consistency in future work - not a set of enforced rules.

## Overview

Stamped is a dark-themed, map-centric single page app. The map is the primary surface; side panels (quest list, storyline, status dashboard) are secondary and dense, favoring information density over decoration.

## Colors

No shared palette or CSS custom properties exist; each component declares its own hex values in a `<style scoped>` block. Recurring values across components:

| Value | Typical use |
|---|---|
| `#1a1a2e`, `#1e1e38`, `#0e0e22` | Dark background surfaces |
| `#2a2a4e`, `#3b3b6e` | Panel/card backgrounds, borders |
| `#e85d04` | Accent / active state |
| `#c0392b`, `#f87171`, `#ff6b6b` | Danger / destructive actions (delete) |
| `#888`, `#666`, `#999`, `#aaa` | Secondary/muted text |
| `#ccc`, `#f0f0f0` | Light text on dark surfaces |

New components should reuse these values rather than introducing new ones for the same role (background, accent, danger, muted text).

## Typography

Global body font is set once in `frontend/src/assets/base.css`: `Inter` with a system-font fallback stack, `font-size: 15px`, `line-height: 1.6`. Monospace (`font-family: monospace`) appears locally for a small number of technical values (hashes, coordinates).

## Layout

`App.vue` uses a CSS grid root layout: `grid-template-columns: minmax(180px, max-content) 1fr` (two columns - sidebar and content), extended to three columns (`minmax(180px, max-content) minmax(180px, max-content) 1fr`) when a second sidebar panel is open. The map fills the remaining space.

## Spacing

No spacing scale is defined; `gap` and `padding` values are chosen ad hoc per component, typically in the `0.2rem`-`1.5rem` range. `border-radius` is small and consistent: `2px`-`4px` across buttons, tiles and panels - no fully rounded (`border-radius: 50%`) or sharp (`0`) elements observed outside of standard form controls.

## Naming convention

Component class names loosely follow BEM (`block__element--modifier`), e.g. `.storyline__action-btn--pin`, `.unquested__action-btn--danger`. This is not enforced by any linter rule; it is a convention to follow when adding new component styles.

## Do's and don'ts

### Do
- Reuse an existing hex value for the same role (background, accent, danger, muted text) instead of picking a new one.
- Follow the `block__element--modifier` naming pattern for new component classes.
- Keep `border-radius` in the `2px`-`4px` range for consistency with existing components.

### Don't
- Introduce a CSS framework or a new styling approach without prior agreement - the project intentionally has none today.
- Add global CSS variables without also migrating existing hardcoded values, which would leave two competing systems side by side.
