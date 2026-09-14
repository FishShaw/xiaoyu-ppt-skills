# Layout and Geometry

Use this reference when a slide contains a process, architecture, timeline, state machine, swimlane, or three or more connected nodes.

## Build from coordinates, not eyesight

Define nodes first, then derive connectors from node bounds.

For a left-to-right chain:

```text
node[i].centerY = sharedCenterY
gap = constant
arrow.start = (node[i].right, sharedCenterY)
arrow.end   = (node[i+1].left, sharedCenterY)
```

For a vertical handoff, use the source bottom-center and target top-center. Use elbow segments for orthogonal routes; do not create a diagonal line merely to bridge misaligned nodes.

## Invariants

- Repeated nodes share width, height, baseline, radius, and internal padding unless difference carries meaning.
- Equal relationships use equal gaps. Calculate positions from the first node and gap; do not place each node independently.
- Directed connectors have real arrowheads.
- A connector endpoint meets the target boundary within 0.08 inch unless a visible routing gap is intentional.
- Connectors remain horizontal or vertical when the requested diagram is orthogonal.
- Lines run behind nodes and never through text.
- Labels do not sit on top of line segments unless a dedicated label background masks the line.
- All geometry remains inside the slide canvas and at least 0.5 inch from the external edge unless deliberately full-bleed.

## QA

Run `scripts/audit_presentation.py` for important ordered flows:

```sh
python scripts/audit_presentation.py deck.pptx --aspect 16:9 --slide 3 --chain 'Input|Process|Output'
```

Selectors must be exact, unique node text or `id:<shape-id>`; use shape IDs for separate label boxes. IDs are scoped to a slide. The label order is the intended left-to-right or top-to-bottom order; it must not be inferred by sorting coordinates. The default aspect ratio is unrestricted; specify a ratio only when required. Use `--orientation horizontal` or `vertical` to disambiguate.

The audit reports spacing, axis alignment, overlap/order, arrowheads, attachment and text obstacles for the selected straight chain. Grouped/rotated objects and bent/custom connector paths produce an unsupported result, requiring transform/path-aware inspection. Other slides and graphics are not certified by a chain PASS. A nonzero exit means failure or an unverified condition, never silent success.

Reports use a new `--output` path and never overwrite inputs or existing reports. A package outside read-size limits needs a reviewed large-file workflow; do not silently disable safeguards.

For branching graphs, elbow routes, or swimlanes, add source-level assertions for every repeated-node group and connector. The generic chain audit verifies one ordered path; it does not prove an arbitrary graph correct.

A contact sheet verifies rhythm; inspect complex diagram slides at original resolution. Automated geometry and visual inspection are complementary.
