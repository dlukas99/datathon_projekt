# Prije potpisa: developer commands. Requires GNU make, uv, Node.js 22+ and Docker.

BACKEND  := backend
FRONTEND := frontend
COMPOSE_DEV := docker compose -f deploy/docker-compose.dev.yml

.PHONY: setup data dev valhalla test lint build e2e screenshots verify readme-check

setup:
	cd $(BACKEND) && uv sync
	cd $(FRONTEND) && npm ci
	cd $(FRONTEND) && npx playwright install chromium

data:
	cd $(BACKEND) && uv run python -m ingest.run_all

valhalla:
	$(COMPOSE_DEV) up -d valhalla

dev: valhalla
	cd $(BACKEND) && uv run uvicorn app.main:app --reload --port 8000 --no-access-log & \
	cd $(FRONTEND) && npm run dev; \
	wait

test:
	cd $(BACKEND) && uv run pytest -q
	cd $(FRONTEND) && npm test

lint:
	cd $(BACKEND) && uv run ruff check . && uv run ruff format --check . && uv run mypy
	cd $(FRONTEND) && npm run lint && npm run typecheck

build:
	cd $(FRONTEND) && npm run build

e2e: build
	cd $(FRONTEND) && npx playwright test

screenshots: build
	cd $(FRONTEND) && npx playwright test --config playwright.screenshots.config.ts

readme-check:
	cd $(BACKEND) && uv run python ../scripts/check_readme.py

verify: lint test build e2e readme-check
	@echo "make verify: sve provjere prošle"
