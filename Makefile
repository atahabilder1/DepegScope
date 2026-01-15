# DepegScope Makefile
# Convenience commands for common tasks

.PHONY: help install dev-install clean test lint format collect build simulate report all

# Default target
help:
	@echo "DepegScope - Stablecoin Depeg Contagion Analysis"
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Setup:"
	@echo "  install      Install production dependencies"
	@echo "  dev-install  Install development dependencies"
	@echo "  clean        Remove generated files and caches"
	@echo ""
	@echo "Development:"
	@echo "  test         Run test suite"
	@echo "  lint         Run linting checks"
	@echo "  format       Format code with black and isort"
	@echo ""
	@echo "Analysis Pipeline:"
	@echo "  collect      Collect data from APIs"
	@echo "  build        Build dependency graph"
	@echo "  simulate     Run simulation"
	@echo "  report       Generate risk report"
	@echo "  all          Run complete pipeline"
	@echo ""
	@echo "Jupyter:"
	@echo "  notebook     Start Jupyter notebook server"

# =============================================================================
# Setup
# =============================================================================

install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements.txt
	pip install pytest pytest-cov black isort flake8 mypy pre-commit
	pre-commit install || true

clean:
	rm -rf __pycache__ .pytest_cache .mypy_cache .coverage htmlcov
	rm -rf **/__pycache__ **/.pytest_cache
	rm -rf build dist *.egg-info
	rm -rf data/raw/*.json data/processed/*.json
	rm -rf reports/*.json reports/plots/*
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

# =============================================================================
# Development
# =============================================================================

test:
	pytest tests/ -v --cov=src --cov-report=term-missing

test-fast:
	pytest tests/ -v -x --tb=short

lint:
	flake8 src/ scripts/ tests/ --max-line-length=100 --ignore=E501,W503
	mypy src/ --ignore-missing-imports || true

format:
	black src/ scripts/ tests/ --line-length=100
	isort src/ scripts/ tests/ --profile=black

# =============================================================================
# Analysis Pipeline
# =============================================================================

collect:
	python scripts/collect_data.py --days 365 --top-protocols 100

collect-fast:
	python scripts/collect_data.py --days 90 --top-protocols 50 --skip-prices

build:
	python scripts/build_graph.py --min-tvl 1000000 --export-graph

simulate:
	python scripts/run_simulation.py --scenario usdc_svb --monte-carlo 100

simulate-all:
	python scripts/run_simulation.py --trigger USDC --severity 0.1 --monte-carlo 500 --output reports/usdc_sim.json
	python scripts/run_simulation.py --trigger USDT --severity 0.1 --monte-carlo 500 --output reports/usdt_sim.json
	python scripts/run_simulation.py --trigger DAI --severity 0.1 --monte-carlo 500 --output reports/dai_sim.json

report:
	python scripts/generate_report.py --format all --generate-plots

all: collect build simulate report
	@echo "Complete pipeline finished!"

# =============================================================================
# Jupyter
# =============================================================================

notebook:
	jupyter notebook notebooks/

# =============================================================================
# Docker (optional)
# =============================================================================

docker-build:
	docker build -t depegscope .

docker-run:
	docker run -it --rm -v $(PWD)/data:/app/data -v $(PWD)/reports:/app/reports depegscope
