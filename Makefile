# ==========================================
# Kiko — AI Job Assistant (Monorepo Makefile)
# ==========================================

.PHONY: help up down dev-bot dev-backend dev-web dev-worker dev-parser test migrate

help:
	@echo "Available commands:"
	@echo "  make up          - Start local Docker infrastructure (PostgreSQL, etc.)"
	@echo "  make down        - Stop local Docker infrastructure"
	@echo "  make migrate     - Run database migrations"
	@echo "  make dev-bot     - Run Telegram Bot locally (apps/bot)"
	@echo "  make dev-backend - Run Go Core Backend locally (apps/backend)"
	@echo "  make dev-web     - Run Web Client locally (apps/web)"
	@echo "  make dev-worker  - Run AI Worker locally (apps/ai-worker)"
	@echo "  make dev-parser  - Run Vacancy Parser locally (apps/parser)"
	@echo "  make test        - Run test suite"

# Docker orchestration
up:
	docker compose up -d

down:
	docker compose down

# Database
migrate:
	python database/scripts/migrate.py

# Local development runners
dev-bot:
	cd apps/bot && python run.py

dev-backend:
	cd apps/backend && go run cmd/api/main.go

dev-web:
	cd apps/web && npm run dev

dev-worker:
	cd apps/ai-worker && python run_worker.py

dev-parser:
	cd apps/parser && python run_parser.py

# Testing
test:
	pytest -v
