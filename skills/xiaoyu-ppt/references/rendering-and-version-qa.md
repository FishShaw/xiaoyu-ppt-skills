# Rendering and Version QA

## Rendering trust

Before interpreting a render, confirm that the renderer displayed the document's language. Missing Chinese or other glyphs makes the visual QA incomplete even when OOXML is valid.

For a new deck, choose a font available to both the target environment and the QA renderer. Configure the provided LibreOffice Fontconfig before the first render when needed.

For a canonical user-edited deck:

1. Preserve unauthorized fonts and pages.
2. If the renderer omits glyphs, do not modify the delivered deck to satisfy the renderer.
3. Create a temporary render-only copy with a verified available font using `make_render_safe_copy.py input.pptx unique-qa.pptx --font 'Font Name'`. It refuses existing outputs. The substitute may change line breaks and widths: it verifies readability under that substitution, not the original font's exact layout. Mark original-font fidelity unverified unless checked in a compatible renderer.
4. Compare the entire package, including media, charts, relationships, theme, masters, layouts and notes. Identical slide XML alone does not prove unchanged appearance.

Never write “visual QA passed” if the contact sheet contains missing text.

## Canonical edits

- Copy the authoritative deck to the requested output; never regenerate from an old script or outline.
- Apply only the authorized slide or part changes.
- Run `audit_presentation.py output.pptx --canonical input.pptx --changed-slide 5`. Slide numbers follow presentation order, not XML filenames. Only that slide part is allowed by default; authorized notes, media or chart changes need individual exact `--allow-part` entries. Review shared dependencies before allowing them: changing a shared image may affect an unauthorized slide. Slide reordering is rejected by this surgical-edit check.
- Render source and result using the same renderer when pixel or image-hash comparison is useful.
- Pass the source deck as `--original` to the `pptx` validator.

## Delivery checks

1. Extract text and check order, omissions, placeholders, and unsupported claims.
2. Run the `pptx` OOXML validator.
3. Run `scripts/audit_presentation.py` for geometry or canonical preservation.
4. Render all new/restructured slides and inspect the contact sheet. For surgical edits reuse prior verified renders only with matching dependency and renderer hashes; otherwise render again.
5. Inspect dense or connected slides at original resolution.
6. Confirm requested filenames and one authoritative PPTX.

Reports should state what was actually checked, including tolerances and any fallback. Avoid unsupported phrases such as “pixel perfect” or “fully verified”.

Distinguish pass / fail / unsupported / not checked. `audit_presentation.py` does not run Office schema validation, pixel rendering, OCR, font-fit checks, or comprehensive privacy scans. Its success is scoped to requested checks. Keep final QA tied to the final artifact hash.
