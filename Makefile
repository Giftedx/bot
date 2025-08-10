# Variables
PYTHON = python3
PIP = pip3
DOCKER = docker
DOCKER_COMPOSE = docker-compose

# Virtual Environment
VENV_DIR = .venv
VENV_ACTIVATE = $(VENV_DIR)/bin/activate
PYTHON_VENV = $(VENV_DIR)/bin/python
PIP_VENV = $(VENV_DIR)/bin/pip

PYTEST = $(VENV_DIR)/bin/pytest
COVERAGE = $(VENV_DIR)/bin/coverage
BLACK = $(VENV_DIR)/bin/black
ISORT = $(VENV_DIR)/bin/isort
MYPY = $(VENV_DIR)/bin/mypy
FLAKE8 = $(VENV_DIR)/bin/flake8

# Docker image names
BOT_IMAGE = osrs-discord-bot
PROMETHEUS_IMAGE = osrs-discord-bot-prometheus
GRAFANA_IMAGE = osrs-discord-bot-grafana

.PHONY: help install dev-install test lint format type-check clean build run run-dev stop logs monitoring

help:
	@echo "Available commands:"
	@echo "  install        - Install production dependencies"
	@echo "  dev-install    - Install all dependencies for development"
	@echo "  test           - Run tests"
	@echo "  lint           - Run linting"
	@echo "  format         - Format code"
	@echo "  type-check     - Run type checking"
	@echo "  clean          - Clean up build artifacts"
	@echo "  build          - Build Docker images"
	@echo "  run            - Run in production mode"
	@echo "  run-dev        - Run in development mode"
	@echo "  stop           - Stop all containers"
	@echo "  logs           - View logs from Docker containers"
	@echo "  monitoring     - Start Prometheus and Grafana for monitoring"

install:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		$(PYTHON) -m venv $(VENV_DIR); \
	fi
	$(PIP_VENV) install .

dev-install:
	@if [ ! -d "$(VENV_DIR)" ]; then \
		$(PYTHON) -m venv $(VENV_DIR); \
	fi
	$(PIP_VENV) install --upgrade pip
	$(PIP_VENV) install -e .
	$(PIP_VENV) install -e .[dev]

setup:
	@echo "Running comprehensive environment setup..."
	$(PYTHON_VENV) setup_env.py

quick-setup:
	@echo "Running quick setup (dependencies only)..."
	@if [ ! -d "$(VENV_DIR)" ]; then \
		$(PYTHON) -m venv $(VENV_DIR); \
	fi
	$(PIP_VENV) install --upgrade pip
	$(PIP_VENV) install python-dotenv PyYAML discord.py aiohttp pydantic fastapi uvicorn prometheus_client

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
	find . -type d -name ".venv" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type f -name ".DS_Store" -delete

build:
	$(DOCKER_COMPOSE) build
	$(DOCKER_COMPOSE) -f docker-compose.monitoring.yml build

run:
	$(DOCKER_COMPOSE) -f docker/docker-compose.yml up -d --build

run-dev:
	$(DOCKER_COMPOSE) -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up --build

stop:
	$(DOCKER_COMPOSE) -f docker/docker-compose.yml -f docker/docker-compose.dev.yml down

logs:
	$(DOCKER_COMPOSE) -f docker/docker-compose.yml -f docker/docker-compose.dev.yml logs -f

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

 