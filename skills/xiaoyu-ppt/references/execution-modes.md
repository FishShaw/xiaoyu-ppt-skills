# Scope, speed, and resumability

## Choose the minimum complete workflow

| Request | Work | Validation |
| --- | --- | --- |
| Outline / script / critique | Read relevant evidence, return requested text | Claims and scope; no PPT runtime, render, or Figma writes |
| Small edit to a designated latest deck | Inspect original and edit only authorized parts | Package comparison, changed slides, affected shared dependencies |
| New / restructured deck | Evidence and page contracts, native build | Structure, all-page visual inspection, selected diagram audit |
| Sanitized or externally shared deck | Add artifact redaction and transfer review | Exported bytes, hidden content and media; scan is not a guarantee |

Do not require an approval round for an already authorized implementation. When the user requests a plan first, deliver the plan and stop there.

## Avoid repeated work

- Discover installed runtime and renderer once. Reuse available dependencies; do not install a new toolchain for each page or deck.
- Inventory sources, then extract relevant files once. Use SQLite/RAG only if the source size or repeated retrieval warrants it.
- Cache by content hash, not filename or modification time alone. Extraction caches also record parser/version; rendering caches record the slide, relationships, assets, masters/layouts/themes, renderer settings, and font configuration.
- Read independent evidence in parallel when supported; serialize changes to a shared deck or remote page. Choose bounded batches for rendering.
- Fix the generator or canonical edit procedure, regenerate affected pages, and rerun affected checks. A theme/font/master change invalidates all dependent previews; unknown dependencies require full render.
- If a render fails twice for the same reason, diagnose the environment or switch to a supported fallback. Do not repeatedly rebuild the same deck without new evidence.

## Resume longer tasks

Keep a compact build manifest only when the task spans significant processing or revisions: authoritative input hashes, requested outputs, tool/font versions, page/source mapping, artifact hashes, last verified stage, and remaining issues. On resume, compare hashes before reusing work. This avoids relying on conversation history to decide which deck is current.

Use a temporary build directory. Validate before publishing to the final filename. If the designated output already exists, confirm its identity from the current task; preserve a recoverable copy before an authorized replacement. Never clean unrelated versions automatically.

Stop expanding checks once the requested contract passes and no material uncertainty remains. Report actual elapsed timings only if measured on comparable work; do not promise a speedup from reduced steps alone.
