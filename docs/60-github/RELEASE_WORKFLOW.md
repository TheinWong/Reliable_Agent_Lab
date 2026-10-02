# Release Workflow

## Versioning
Start with `v0.1.0` for the first credible public MVP.
Use semantic versioning pragmatically.

## Pre-release checklist
- criteria in `docs/50-roadmap/RELEASE_CRITERIA.md` green;
- changelog/release notes summarize actual implemented capabilities;
- README quick start rerun from a clean checkout;
- Docker images/build artifacts do not contain secrets;
- live-model requirements and costs are clearly documented;
- known limitations are explicit.

## Publishing
Tag/release publishing is an external irreversible-ish action. Codex must not publish a release unless explicitly authorized in the current thread.
