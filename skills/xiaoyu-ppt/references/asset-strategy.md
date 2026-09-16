# Asset and Figma Strategy

Choose the lowest-complexity medium that preserves meaning, editability, and authenticity.

## Default hierarchy

1. **Native PowerPoint:** titles, body text, tables, cards, timelines, simple architecture, ordinary flows, connectors, and PowerPoint-supported charts.
2. **Authentic source artifact:** user-designed prototype, product screenshot, interface state, source chart, scanned document excerpt, or supplied image when the artifact itself is evidence.
3. **Figma or another visual tool:** a genuinely complex diagram, illustration, or composited visual that cannot be made cleanly with native PowerPoint in reasonable time.

Do not build an entire presentation as Figma frames and import every slide as an image unless the user explicitly requests that workflow.

## Source artifacts

- Prefer the original user artifact over a speculative reconstruction.
- Preserve originals and annotate copies. For sensitive data, use flattened sanitized image copies; cropping or overlay masks alone may leave raw pixels recoverable in the PPTX. Follow [privacy-and-transfer.md](privacy-and-transfer.md).
- Remove names, companies, customers, data sets, URLs, accounts, addresses, infrastructure details, and hidden metadata when sanitization is required.
- Keep captions and annotations native when possible so the presenter can edit them.
- Never imply that a prototype is implemented or that a design result is a production metric.

## Figma use

Use Figma for a bounded asset with a clear slide purpose. Keep a source-to-slide mapping and export SVG for vector diagrams or 2× PNG for raster-heavy visuals. Inspect exports for missing icons, text substitution, baseline drift, clipped arrows, and transparent-background surprises before inserting them.

If a native PowerPoint diagram can communicate the same relationship cleanly, prefer the native version because it remains editable and reduces cross-tool layout drift.
