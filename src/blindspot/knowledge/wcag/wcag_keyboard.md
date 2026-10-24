# WCAG 2.2: Keyboard Navigation & Focus Playbook

## Checkpoint 2.1.1: Keyboard Operability (Level A)
All interactive functionality must be operable using only the keyboard (Tab, Shift+Tab, Enter, Space, Escape, Arrow keys).

### Common Failure Patterns:
1. Custom interactive components (`<div onClick="...">` or `<span class="btn">`) missing `tabindex="0"` and keyboard event listeners (`onKeyDown`).
2. Dropdown menus and modals that cannot be navigated or closed with Escape.
3. Carousels or sliders that only advance via drag/swipe mouse gestures.

## Checkpoint 2.1.2: No Keyboard Trap (Level A)
Keyboard focus must never be trapped in a sub-component or modal without a way to exit using standard keys (Tab or Escape).

## Checkpoint 2.4.7: Focus Visible (Level AA)
Any keyboard-operable interface must have a visible keyboard focus indicator.

### Red Flags:
- CSS rules stripping outline: `outline: none` or `outline: 0` without an alternative `:focus-visible` ring.
- Focus indicator color blends into background (e.g. blue ring on blue button).

### Remediation:
- Use native HTML elements (`<button>`, `<a>`, `<input>`, `<select>`) whenever possible.
- If using `outline: none`, explicitly provide `:focus-visible { outline: 2px solid #3182ce; outline-offset: 2px; }`.
- Ensure modals trap focus *inside* the modal while open, and return focus to the trigger button upon closing.
