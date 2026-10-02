# v0.1.0 Release Criteria

Release only when:
- clean-checkout local quick start works;
- all required CI checks are green;
- at least four deterministic scenarios are automated;
- multi-agent delegation is real and traceable;
- at least one approval pause/resume works across process restart;
- one idempotency regression test exists;
- tool contracts have timeout/error tests;
- public docs do not claim future work as complete;
- security rules prevent unrestricted destructive tooling;
- learning walkthrough and interview notebook are populated;
- no secrets or private endpoints are present.

## v0.1.0 code-MVP audit — 2026-10-02

The clean-checkout quick start, four automated scenarios, multi-agent traces, restart/resume, idempotency, timeout/error tests, docs, and scoped operations have direct evidence in [`VERIFICATION_AUDIT.md`](VERIFICATION_AUDIT.md). The final import passed hosted Python, Java, and Compose checks on both push and PR runs. The committed files were reviewed for common embedded-secret patterns and include only an example environment file, not a real `.env`. The project is a deterministic local demo without live-model calls or model-token cost. The code-MVP criteria are met; a version tag and GitHub Release remain unpublished and require separate owner authorization.
