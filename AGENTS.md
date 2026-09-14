# Repository workflow

- Never commit or push directly to `main`. The README-only initialization is complete.
- Start a `feat/`, `fix/`, `docs/` or `chore/` branch from the current main. Preserve unrelated user changes.
- Run `python scripts/check_repo.py`, `python -m unittest discover -s tests -v` and the relevant integration tests before pushing.
- Push the branch, wait for that commit's CI to succeed, then open a PR. Do not merge or bypass protection without user direction.
- The required `CI Gate` must cover every dependency job; a skipped or cancelled dependency is not success.
- Presentation/geometry changes require review of the CI preview artifacts. Do not equate a geometry PASS with visual quality.
- Never upload personal presentations, original prototypes, transcripts, local memory, credentials or machine-specific paths. Fixtures must be synthetic and reproducible.
- Source of truth for the distributable skill is `skills/xiaoyu-ppt/`. Do not copy private project instructions into it.
- If source changes affect the packaged skill, bump its semantic version before release. Keep dependency and action versions pinned and review Dependabot changes through PRs.
- Do not change repository protections to get a PR through. Report unmet checks and fix the branch.
- Global local installation changes require explicit user authorization; a GitHub release does not silently replace local files.
