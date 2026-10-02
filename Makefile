.PHONY: help sync lint test python-test java-test compose-check dev-up dev-down smoke-test mcp-smoke scenario evaluate

SCENARIO ?= redis-unavailable

help:
	@echo "sync            Resolve the locked Python development environment"
	@echo "lint            Run Python format, lint and strict type checks"
	@echo "test            Run Python and Java unit tests"
	@echo "compose-check   Validate the Compose model"
	@echo "dev-up          Build and start the first vertical slice"
	@echo "dev-down        Stop the local stack"
	@echo "smoke-test      Verify healthy order and incident paths"
	@echo "mcp-smoke       Verify four MCP servers and duplicate-safe reset"
	@echo "scenario        Run SCENARIO=redis-unavailable, mysql-unavailable, inventory-latency, or payment-5xx"
	@echo "evaluate        Check latest persisted S1-S4 incidents against ground-truth fixtures"

sync:
	uv sync --frozen

lint:
	uv run ruff format --check .
	uv run ruff check .
	uv run mypy src

python-test:
	uv run pytest

java-test:
	docker run --rm -v reliable-agent-lab-maven-cache:/root/.m2 -v "$(CURDIR)/services/order-service:/workspace" -w /workspace maven:3.9.11-eclipse-temurin-21 mvn -B -ntp verify
	docker run --rm -v reliable-agent-lab-maven-cache:/root/.m2 -v "$(CURDIR)/services/downstream-service:/workspace" -w /workspace maven:3.9.11-eclipse-temurin-21 mvn -B -ntp verify

test: python-test java-test

compose-check:
	docker compose config --quiet

dev-up:
	docker compose up -d --build --wait --wait-timeout 240

dev-down:
	docker compose down --remove-orphans

smoke-test:
	bash scripts/smoke.sh

mcp-smoke:
	docker compose exec -T agent-api python -m reliable_agent_lab.mcp_smoke

scenario:
	@case "$(SCENARIO)" in redis-unavailable|mysql-unavailable) bash scripts/scenarios/$(SCENARIO).sh ;; inventory-latency|payment-5xx) bash scripts/scenarios/downstream-fault.sh $(SCENARIO) ;; *) echo "unsupported SCENARIO=$(SCENARIO)" >&2; exit 2 ;; esac

evaluate:
	uv run python scripts/evaluate_scenarios.py
