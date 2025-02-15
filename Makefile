# Variables
PYTHON = python3
PIP = pip3
DOCKER = docker
DOCKER_COMPOSE = docker-compose
PYTEST = pytest
COVERAGE = coverage
BLACK = black
ISORT = isort
MYPY = mypy
FLAKE8 = flake8

# Docker image names
BOT_IMAGE = osrs-discord-bot
PROMETHEUS_IMAGE = osrs-discord-bot-prometheus
GRAFANA_IMAGE = osrs-discord-bot-grafana

.PHONY: help install dev-install test lint format type-check clean build run run-dev stop logs monitoring

help:
	@echo "Available commands:"
	@echo "  install        - Install production dependencies"
	@echo "  dev-install   - Install development dependencies"
	@echo "  test          - Run tests"
	@echo "  lint          - Run linting"
	@echo "  format        - Format code"
	@echo "  type-check    - Run type checking"
	@echo "  clean         - Clean up build artifacts"
	@echo "  build         - Build Docker images"
	@echo "  run           - Run in production mode"
	@echo "  run-dev       - Run in development mode"
	@echo "  stop          - Stop all containers"
	@echo "  logs          - View logs"
	@echo "  monitoring    - Start monitoring stack"

install:
	$(PIP) install -r requirements.txt

dev-install:
	$(PIP) install -r requirements-dev.txt
	pre-commit install

test:
	$(PYTEST) tests/ -v --cov=src --cov-report=term-missing

lint:
	$(FLAKE8) src/ tests/
	$(BLACK) --check src/ tests/
	$(ISORT) --check-only src/ tests/

format:
	$(BLACK) src/ tests/
	$(ISORT) src/ tests/

type-check:
	$(MYPY) src/ tests/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".DS_Store" -delete

build:
	$(DOCKER_COMPOSE) build
	$(DOCKER_COMPOSE) -f docker-compose.monitoring.yml build

run:
	$(DOCKER_COMPOSE) up -d

run-dev:
	$(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.monitoring.yml up -d

stop:
	$(DOCKER_COMPOSE) down
	$(DOCKER_COMPOSE) -f docker-compose.monitoring.yml down

logs:
	$(DOCKER_COMPOSE) logs -f

monitoring:
	$(DOCKER_COMPOSE) -f docker-compose.monitoring.yml up -d

# Database management
db-migrate:
	alembic upgrade head

db-rollback:
	alembic downgrade -1

db-revision:
	alembic revision --autogenerate -m "$(message)"

# Development shortcuts
dev: dev-install format lint type-check test

# Production deployment
deploy: clean build run monitoring
	@echo "Deployment complete. Check logs with 'make logs'"

# Monitoring management
monitoring-logs:
	$(DOCKER_COMPOSE) -f docker-compose.monitoring.yml logs -f

monitoring-stop:
	$(DOCKER_COMPOSE) -f docker-compose.monitoring.yml down

monitoring-restart:
	$(DOCKER_COMPOSE) -f docker-compose.monitoring.yml restart

# Security checks
security-check:
	safety check
	bandit -r src/
	pip-audit

# Documentation
docs:
	cd docs && make html

# Version management
bump-version:
	bump2version $(part)

# Container management
prune:
	$(DOCKER) system prune -f
	$(DOCKER) volume prune -f

rebuild: clean build run
