# Coding Standards

## General
- Optimize for readability and inspectability.
- Keep functions/modules cohesive.
- Avoid speculative abstractions.
- Keep public contracts typed.
- Document surprising behavior, not obvious syntax.
- No secrets or machine-specific paths in committed code.

## Python
- Python 3.12.
- Use type hints for public/internal domain contracts.
- Use Pydantic for API/tool/model contracts where validation is useful.
- Prefer explicit exceptions/error results over silent `None` for operational failures.
- Never use bare `except:`.
- External I/O requires timeouts.
- Keep prompt templates separate from transport/API glue.
- Format/lint with Ruff; use the selected type checker consistently.
- Tests with pytest.

## Java
- Java 21 + Spring Boot + Maven.
- Constructor injection.
- Controllers stay thin.
- Service layer owns business/fault behavior.
- Use configuration/profiles carefully; fault injection must be explicit and local-demo-only.
- Use structured logging and trace propagation.
- Tests with JUnit/Spring test tools as appropriate.

## Naming
Prefer domain names (`Incident`, `SpecialistReport`, `RemediationPlan`) over framework names in business/domain layers.

## Comments/docs
Record why an implementation exists when it encodes a reliability or multi-agent design decision.
