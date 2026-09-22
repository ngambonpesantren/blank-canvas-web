# Collapsible Table of Contents and Heading Folding

## Goal
Add a dynamic heading outline directly below Properties, and allow every Markdown heading (levels 1–6) to collapse or expand its section in both editing and reading modes.

## Implementation
- Parse the current Markdown body into a stable heading tree using heading level, visible label, source position, and generated anchor.
- Add an accessible **Table of contents** collapsible below Properties.
  - Nest headings according to levels 1–6.
  - Give headings with descendants an expand/collapse control.
  - Clicking the heading label navigates to that heading without toggling its branch.
  - Keep the outline synchronized immediately as headings are edited.
- Add CodeMirror heading folding in source and live-edit modes.
  - Show a fold control beside headings that contain content.
  - Fold from a heading through the line before the next heading of the same or higher level.
  - Preserve document text and saved Markdown; folding changes presentation only.
- Add reading-mode heading folding.
  - Render heading controls and hide/show each heading’s section recursively.
  - Support nested collapse independently and keep links, tags, lists, and code rendering intact.
- Ensure split mode gets editor folding on the left and reading folding on the right.
- Use semantic styling, keyboard-operable controls, focus states, and `aria-expanded` labels.

## Technical details
- Create a shared heading parser/tree utility so the ToC, editor fold ranges, and reading view use identical boundaries.
- Implement CodeMirror folding with its language fold service and gutter controls.
- Extend the Markdown renderer with heading IDs and section-aware rendering state.
- Keep collapse state local to the open note and reconcile it when headings change.

## Verification
- Test irregular heading nesting, duplicate names, empty sections, all levels 1–6, and edits that add/remove headings.
- Verify ToC navigation and independent nested expansion by keyboard and pointer.
- Verify source, live, reading, and split modes in the running app.
- Confirm TypeScript and the preview build are clean.
