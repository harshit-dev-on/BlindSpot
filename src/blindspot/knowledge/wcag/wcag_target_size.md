# WCAG 2.2: Target Size (Minimum) Playbook

## Checkpoint 2.5.8: Target Size (Minimum) (Level AA) - WCAG 2.2 New Requirement
The size of the target for pointer inputs must be at least **24 by 24 CSS pixels**, except where:
- **Spacing:** The target with its surrounding spacing totals at least 24px diameter circle.
- **Inline:** The target is in a sentence or block of text (inline links).
- **Essential:** A particular presentation of target is legally or functionally essential.

### Common Failure Patterns:
1. Compact icon buttons (e.g. table action icons, delete trash cans, small pagination chevrons) with bounding boxes like 14x14px or 16x16px without padding.
2. Clustered tags or tag removal 'x' buttons that are too small to reliably tap on touchscreens.
3. Mobile hamburger menu bars with small click areas.

### Remediation:
- Add padding to small icons: `padding: 8px; min-width: 24px; min-height: 24px; box-sizing: border-box;`.
- Increase spacing between adjacent buttons to at least 12px.
- Use pseudo-elements (`::after`) to invisibly expand hit target area to at least 44x44px for optimal mobile touch usability.
