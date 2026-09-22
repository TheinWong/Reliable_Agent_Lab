.PHONY: help lint test test-python test-java dev-up dev-down smoke-test

help:
	@echo "Reliable Agent Lab"
	@echo ""
	@echo "Targets become active as milestones create their workspaces:"
	@echo "  make lint"
	@echo "  make test"
	@echo "  make test-python"
	@echo "  make test-java"
	@echo "  make dev-up"
	@echo "  make dev-down"
	@echo "  make smoke-test"

lint:
	@if [ -f pyproject.toml ] || [ -f agent/pyproject.toml ] || [ -f api/pyproject.toml ]; then \
		ruff check . && ruff format --check .; \
	else \
		echo "Python workspace not created yet."; \
	fi

test: test-python test-java

test-python:
	@if [ -f pyproject.toml ]; then \
		pytest; \
	elif [ -f agent/pyproject.toml ] || [ -f api/pyproject.toml ]; then \
		echo "Python workspace exists. Add the agreed monorepo test command before relying on this target."; \
		exit 1; \
	else \
		echo "Python workspace not created yet."; \
	fi

test-java:
	@if [ -f demo-service/pom.xml ]; then \
		cd demo-service && mvn test; \
	else \
		echo "Java workspace not created yet."; \
	fi

dev-up:
	@if [ -f infra/docker-compose.yml ]; then \
		docker compose -f infra/docker-compose.yml up -d; \
	else \
		echo "infra/docker-compose.yml not created yet."; \
		exit 1; \
	fi

dev-down:
	@if [ -f infra/docker-compose.yml ]; then \
		docker compose -f infra/docker-compose.yml down; \
	else \
		echo "infra/docker-compose.yml not created yet."; \
	fi

smoke-test:
	@if [ -x scripts/smoke-test.sh ]; then \
		scripts/smoke-test.sh; \
	else \
		echo "scripts/smoke-test.sh not created yet."; \
		exit 1; \
	fi
