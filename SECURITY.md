# Security

This repository is a local-development and controlled-experiment project.

## Never commit
- API keys/tokens;
- `.env`;
- production credentials/endpoints;
- private certificates;
- real user/customer data.

## Tool safety
- no unrestricted LLM-facing shell;
- no arbitrary mutating SQL;
- mutating operations scoped to named demo resources;
- risky operations require policy/approval;
- demo fault injection must not target production infrastructure.

## Reporting
For a public repository, report security issues privately to the maintainer rather than opening an exploit-detail public issue.
