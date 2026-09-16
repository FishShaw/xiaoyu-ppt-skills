# Security boundaries

- Public repository: only synthetic fixtures and generic skill sources. Do not upload user decks, prototypes or documents even as CI artifacts.
- PR workflows use read-only tokens and ephemeral GitHub-hosted runners. No deployment secrets or `pull_request_target` execution.
- Action references are pinned to commit SHAs; npm dependencies are installed from a committed lockfile with lifecycle scripts disabled.
- The distributed `.skill` package only includes its own Markdown, Python and YAML sources. Node and rendering dependencies are test-only, never shipped.
- Package parsing is bounded, rejects suspicious XML/ZIP layouts and refuses output overwrite. This does not replace sandboxing arbitrary Office documents.

## Dependency audit

`python scripts/audit_dependencies.py` runs the current npm advisory scan. Unrecognized high/critical findings block CI. An exception must match the exact advisory URL, package/version, development-only scope and approval/expiry dates. Exceptions last at most 31 days and expire closed. The repository starts with no exceptions; add one only after owner approval, in a PR with a documented mitigation.

Initial scan found [ICNS parser denial of service](https://github.com/advisories/GHSA-w3rx-r6r6-pgpr) and [JXL/HEIF parser denial of service](https://github.com/advisories/GHSA-5p2g-fcmc-qvqq) in `image-size`, inherited by the PptxGenJS test dependency. At setup there was no patched published version. Do not run `npm audit fix --force` blindly: its proposed downgrade is not an appropriate migration.

The fixture generator disables every image parser except PNG, only consumes a program-generated PNG, and runs with a timeout. These mitigations reduce this test exposure but do not mean the dependency itself is patched. The owner approved exactly these two advisories for test-only image-size 1.2.1 from 2026-09-14 through 2026-10-14. New advisories, changed versions and expired exceptions still fail. Release creation reruns the live audit, so an old successful CI cannot bypass expiration or newly disclosed findings.

## Administration

main protections apply to administrators but administrators retain the ability to change repository settings. Do not bypass protection to make CI green. Review sensitive workflow changes and inspect visual evidence in the PR.

Report suspected vulnerabilities to the repository owner without including private artifacts or credentials in a public issue.
