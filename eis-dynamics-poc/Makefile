.PHONY: help install dev lint test format clean tf-init tf-plan tf-apply

PYTHON := python3
PIP := $(PYTHON) -m pip
ENV := dev

help:
	@echo "EIS-D365 POC Development Commands"
	@echo ""
	@echo "Python:"
	@echo "  make install    - Install production dependencies"
	@echo "  make dev        - Install development dependencies"
	@echo "  make lint       - Run linter (ruff)"
	@echo "  make format     - Format code (black + ruff)"
	@echo "  make test       - Run unit tests"
	@echo "  make test-cov   - Run tests with coverage"
	@echo ""
	@echo "Terraform:"
	@echo "  make tf-init    - Initialize Terraform (ENV=dev|staging|prod)"
	@echo "  make tf-plan    - Plan infrastructure changes"
	@echo "  make tf-apply   - Apply infrastructure changes"
	@echo ""
	@echo "Services:"
	@echo "  make run-claims - Run AI Claims service locally"
	@echo "  make run-rating - Run Rating Engine locally"
	@echo "  make run-portal - Run Agent Portal locally"

# Python commands
install:
	$(PIP) install -e ./src/shared

dev:
	$(PIP) install -e "./src/shared[dev]"
	pre-commit install

lint:
	ruff check ./src ./tests

format:
	black ./src ./tests
	ruff check --fix ./src ./tests

test:
	pytest ./tests/unit -v

test-cov:
	pytest ./tests/unit -v --cov=src --cov-report=html

test-integration:
	pytest ./tests/integration -v

test-e2e:
	pytest ./tests/e2e -v

# Terraform commands
tf-init:
	cd infrastructure/environments/$(ENV) && terraform init

tf-plan:
	cd infrastructure/environments/$(ENV) && terraform plan -out=tfplan

tf-apply:
	cd infrastructure/environments/$(ENV) && terraform apply tfplan

tf-destroy:
	cd infrastructure/environments/$(ENV) && terraform destroy

# Service commands
run-claims:
	cd src/ws2_ai_claims && uvicorn app.main:app --reload --port 8001

run-integration:
	cd src/ws3_integration && uvicorn app.main:app --reload --port 8002

run-rating:
	cd src/ws5_rating_engine && uvicorn app.main:app --reload --port 8003

run-portal:
	cd src/ws4_agent_portal && npm run dev

# Clean commands
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .coverage htmlcov/ 2>/dev/null || true
