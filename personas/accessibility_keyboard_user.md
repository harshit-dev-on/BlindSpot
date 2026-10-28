# Persona Blueprint: Accessibility & Keyboard-Only Specialist

**Target Archetype:** Motor-Impaired & Keyboard-Only User  
**Audience:** Users navigating without a mouse, relying exclusively on standard keyboard navigation (Tab, Shift+Tab, Enter, Spacebar, Escape) and assistive technologies.

---

### Persona 1: Alex - Keyboard Navigation Specialist
- **Experience Level:** Advanced
- **Device & Interaction:** Desktop Keyboard Only (No mouse pointer or touch input)
- **Primary Goal:** Successfully navigate the website's main menu, search bar, and primary actions using only keyboard keystrokes with clear visual focus indicators.
- **Likely Difficulties:** Missing or faint `:focus-visible` styling, keyboard focus traps in modal dialogs, non-focusable custom `<div>` buttons, missing skip-to-content links.
- **Accessibility Needs:** Keyboard-Only Navigation & High Focus Contrast

#### Assigned Tasks:
1. **Header Navigation & Focus Order**:
   - **Objective:** Navigate through header links and controls using sequential Tab keystrokes and verify logical tab order.
   - **Starting Conditions:** Starts at top of homepage.
   - **Observable Success Criteria:** Keyboard focus indicator moves sequentially through primary interactive controls, search input is reachable via Tab.
   - **Evidence to Collect:** Focused element tags, active focus state contrast, tab index attributes.

2. **Activate Search or Menu via Keyboard**:
   - **Objective:** Reach the primary search input or category menu using Tab, enter a search query or press Enter to activate the dropdown.
   - **Starting Conditions:** Starts on homepage with focus inside header.
   - **Observable Success Criteria:** Input field accepts keyboard typing, dropdown menu or search suggestion overlay expands upon Enter/Space.
   - **Evidence to Collect:** Expanded ARIA attribute (`aria-expanded='true'`), keyboard typed value.

3. **Verify Dialog Dismissal & Skip Links**:
   - **Objective:** Trigger or encounter an overlay dialog/popup and verify it can be dismissed cleanly using the Escape key or a focusable close button.
   - **Starting Conditions:** Starts with an overlay or modal present.
   - **Observable Success Criteria:** Overlay closes upon Escape or close button activation, focus safely returns to trigger element.
   - **Evidence to Collect:** Close button ARIA label, modal visibility status.
