# WCAG 2.2: Color Contrast Playbook

## Checkpoint 1.4.3: Contrast (Minimum) (Level AA)
The visual presentation of text and images of text must have a contrast ratio of at least:
- **4.5:1** for regular text (under 18pt or under 14pt bold).
- **3.0:1** for large text (18pt and larger, or 14pt bold and larger).

### Common Failure Patterns:
1. Light gray text (`#999999` or `#a0aec0`) on white backgrounds.
2. White text on light pastel buttons or tags (e.g., light blue `#63b3ed`, light green `#9ae6b4`).
3. Text overlaid on background imagery or gradients without a solid backdrop or scrim.
4. Placeholder text in `<input>` fields that is too faint to be legible.

### Checkpoint 1.4.11: Non-text Contrast (Level AA)
The visual presentation of the following must have a contrast ratio of at least **3.0:1** against adjacent color(s):
- **User Interface Components:** Visual information required to identify UI components (input borders, button outlines, active tab indicators).
- **Graphical Objects:** Icons representing actions (search magnifying glass, close 'X', shopping cart).

### Remediation:
- Darken text colors on light backgrounds (e.g. use `#2d3748` instead of `#a0aec0`).
- Ensure input borders have `#718096` or darker border color rather than `#e2e8f0`.
- Add drop shadows or semi-transparent scrims behind text placed on images.
