.PHONY: help install dev test lint format clean docker-build docker-up docker-down migrate migrate-create

# Colors for terminal output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)DocVector - Development Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Setup:$(NC)"
	@echo "  make install           - Install dependencies with Poetry"
	@echo "  make install-dev       - Install with dev dependencies"
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@echo "  make dev               - Run development server (with hot reload)"
	@echo "  make worker            - Run Celery worker"
	@echo "  make shell             - Start IPython shell with app context"
	@echo ""
	@echo "$(GREEN)Testing:$(NC)"
	@echo "  make test              - Run test suite"
	@echo "  make test-cov          - Run tests with coverage report"
	@echo "  make test-watch        - Run tests in watch mode"
	@echo ""
	@echo "$(GREEN)Code Quality:$(NC)"
	@echo "  make lint              - Run linters (ruff, mypy)"
	@echo "  make format            - Format code (black, ruff)"
	@echo "  make check             - Run all checks (lint + test)"
	@echo ""
	@echo "$(GREEN)Docker:$(NC)"
	@echo "  make docker-build      - Build Docker images"
	@echo "  make docker-up         - Start all services"
	@echo "  make docker-down       - Stop all services"
	@echo "  make docker-logs       - View logs"
	@echo "  make docker-clean      - Remove containers and volumes"
	@echo ""
	@echo "$(GREEN)Database:$(NC)"
	@echo "  make migrate           - Run database migrations"
	@echo "  make migrate-create    - Create new migration (usage: make migrate-create message='add field')"
	@echo "  make migrate-downgrade - Rollback last migration"
	@echo "  make db-shell          - Open PostgreSQL shell"
	@echo ""
	@echo "$(GREEN)Utilities:$(NC)"
	@echo "  make clean             - Clean temporary files"
	@echo "  make clean-all         - Clean everything (including venv)"
	@echo "  make seed              - Seed database with sample data"

# ==============================================================================
# SETUP
# ==============================================================================

install: ## Install dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	poetry install --no-dev

install-dev: ## Install with dev dependencies
	@echo "$(BLUE)Installing dependencies (including dev)...$(NC)"
	poetry install

# ==============================================================================
# DEVELOPMENT
# ==============================================================================

dev: ## Run development server
	@echo "$(BLUE)Starting development server...$(NC)"
	poetry run uvicorn docvector.api.main:app --reload --host 0.0.0.0 --port 8000

worker: ## Run Celery worker
	@echo "$(BLUE)Starting Celery worker...$(NC)"
	poetry run celery -A docvector.tasks.celery_app worker --loglevel=info --concurrency=4

beat: ## Run Celery beat scheduler
	@echo "$(BLUE)Starting Celery beat...$(NC)"
	poetry run celery -A docvector.tasks.celery_app beat --loglevel=info

flower: ## Run Flower (Celery monitoring)
	@echo "$(BLUE)Starting Flower...$(NC)"
	poetry run celery -A docvector.tasks.celery_app flower --port=5555

shell: ## Start IPython shell
	@echo "$(BLUE)Starting IPython shell...$(NC)"
	poetry run ipython

# ==============================================================================
# TESTING
# ==============================================================================

test: ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	poetry run pytest -v

test-cov: ## Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	poetry run pytest -v --cov=docvector --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)Coverage report generated in htmlcov/index.html$(NC)"

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	poetry run ptw --runner "pytest -v"

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	poetry run pytest -v -m integration

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	poetry run pytest -v -m "not integration and not e2e"

# ==============================================================================
# CODE QUALITY
# ==============================================================================

lint: ## Run linters
	@echo "$(BLUE)Running linters...$(NC)"
	@echo "$(YELLOW)Running ruff...$(NC)"
	poetry run ruff check src/ tests/
	@echo "$(YELLOW)Running mypy...$(NC)"
	poetry run mypy src/

format: ## Format code
	@echo "$(BLUE)Formatting code...$(NC)"
	@echo "$(YELLOW)Running black...$(NC)"
	poetry run black src/ tests/
	@echo "$(YELLOW)Running ruff --fix...$(NC)"
	poetry run ruff check --fix src/ tests/

check: lint test ## Run all checks

pre-commit: ## Run pre-commit hooks
	@echo "$(BLUE)Running pre-commit hooks...$(NC)"
	poetry run pre-commit run --all-files

# ==============================================================================
# DOCKER
# ==============================================================================

docker-build: ## Build Docker images
	@echo "$(BLUE)Building Docker images...$(NC)"
	docker-compose build

docker-up: ## Start all services
	@echo "$(BLUE)Starting all services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Services started!$(NC)"
	@echo "API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Qdrant: http://localhost:6333/dashboard"

docker-up-monitoring: ## Start services with monitoring
	@echo "$(BLUE)Starting services with monitoring...$(NC)"
	docker-compose --profile monitoring up -d

docker-down: ## Stop all services
	@echo "$(BLUE)Stopping all services...$(NC)"
	docker-compose down

docker-logs: ## View logs
	@echo "$(BLUE)Viewing logs (Ctrl+C to exit)...$(NC)"
	docker-compose logs -f

docker-ps: ## Show running containers
	@echo "$(BLUE)Running containers:$(NC)"
	docker-compose ps

docker-clean: ## Remove containers and volumes
	@echo "$(YELLOW)Removing containers and volumes...$(NC)"
	docker-compose down -v
	@echo "$(GREEN)Cleaned!$(NC)"

docker-restart: ## Restart services
	@echo "$(BLUE)Restarting services...$(NC)"
	docker-compose restart

# ==============================================================================
# DATABASE
# ==============================================================================

migrate: ## Run migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	poetry run alembic upgrade head

migrate-create: ## Create new migration
	@echo "$(BLUE)Creating new migration...$(NC)"
	@if [ -z "$(message)" ]; then \
		echo "$(YELLOW)Usage: make migrate-create message='your message'$(NC)"; \
		exit 1; \
	fi
	poetry run alembic revision --autogenerate -m "$(message)"

migrate-downgrade: ## Rollback last migration
	@echo "$(BLUE)Rolling back last migration...$(NC)"
	poetry run alembic downgrade -1

migrate-history: ## Show migration history
	@echo "$(BLUE)Migration history:$(NC)"
	poetry run alembic history

db-shell: ## Open PostgreSQL shell
	@echo "$(BLUE)Opening PostgreSQL shell...$(NC)"
	docker-compose exec postgres psql -U docvector -d docvector

db-reset: ## Reset database (WARNING: Destructive!)
	@echo "$(YELLOW)WARNING: This will delete all data!$(NC)"
	@echo "Press Ctrl+C to cancel, or Enter to continue..."
	@read confirm
	docker-compose exec postgres psql -U docvector -c "DROP DATABASE IF EXISTS docvector;"
	docker-compose exec postgres psql -U docvector -c "CREATE DATABASE docvector;"
	poetry run alembic upgrade head

# ==============================================================================
# UTILITIES
# ==============================================================================

clean: ## Clean temporary files
	@echo "$(BLUE)Cleaning temporary files...$(NC)"
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	find . -type d -name '.pytest_cache' -exec rm -rf {} +
	find . -type d -name '.mypy_cache' -exec rm -rf {} +
	find . -type d -name '.ruff_cache' -exec rm -rf {} +
	rm -rf build dist htmlcov .coverage
	@echo "$(GREEN)Cleaned!$(NC)"

clean-all: clean ## Clean everything
	@echo "$(BLUE)Cleaning everything...$(NC)"
	rm -rf .venv
	@echo "$(GREEN)Cleaned!$(NC)"

seed: ## Seed database with sample data
	@echo "$(BLUE)Seeding database...$(NC)"
	poetry run python scripts/seed_data.py

init: install docker-up migrate ## Initialize project
	@echo "$(GREEN)Project initialized!$(NC)"
	@echo "Run 'make dev' to start development server"

# ==============================================================================
# CI/CD
# ==============================================================================

ci: lint test ## Run CI checks
	@echo "$(GREEN)CI checks passed!$(NC)"

build-prod: ## Build production Docker image
	@echo "$(BLUE)Building production image...$(NC)"
	docker build -f deployment/docker/Dockerfile -t docvector:latest .

# ==============================================================================
# MONITORING
# ==============================================================================

health: ## Check service health
	@echo "$(BLUE)Checking service health...$(NC)"
	@curl -s http://localhost:8000/api/v1/health | jq .

stats: ## Show system stats
	@echo "$(BLUE)System statistics:$(NC)"
	@curl -s http://localhost:8000/api/v1/stats | jq .

# ==============================================================================
# DEFAULT
# ==============================================================================

.DEFAULT_GOAL := help
