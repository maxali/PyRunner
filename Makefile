# PyRunner Makefile

.PHONY: help install test test-unit test-integration test-security test-performance test-all clean lint format docker-build docker-run docker-test

# Default target
help:
	@echo "PyRunner Development Commands"
	@echo "============================="
	@echo ""
	@echo "Setup:"
	@echo "  install          Install dependencies"
	@echo "  install-dev      Install development dependencies"
	@echo ""
	@echo "Testing:"
	@echo "  test             Run all tests"
	@echo "  test-unit        Run unit tests only"
	@echo "  test-integration Run integration tests only"
	@echo "  test-security    Run security tests only"
	@echo "  test-performance Run performance tests only"
	@echo "  test-coverage    Run tests with coverage report"
	@echo "  test-watch       Run tests in watch mode"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint             Run linting checks"
	@echo "  format           Format code"
	@echo "  security-scan    Run security scan"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build     Build Docker image"
	@echo "  docker-run       Run Docker container"
	@echo "  docker-test      Test Docker deployment"
	@echo ""
	@echo "Cleanup:"
	@echo "  clean            Clean up generated files"
	@echo "  clean-cache      Clean Python cache files"

# Installation
install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements.txt
	pip install pytest pytest-asyncio pytest-cov pytest-timeout httpx
	pip install black flake8 isort bandit

# Testing
test:
	python run_tests.py -v

test-unit:
	python run_tests.py --unit -v

test-integration:
	python run_tests.py --integration -v

test-security:
	python run_tests.py --security -v

test-performance:
	python run_tests.py --performance -v

test-coverage:
	python run_tests.py -v --coverage

test-watch:
	pytest-watch --runner "python run_tests.py"

test-all: test-unit test-integration test-security test-performance

# Code Quality
lint:
	@echo "Running flake8..."
	flake8 app/ tests/ --max-line-length=100 --ignore=E203,W503
	@echo "Running black check..."
	black --check app/ tests/
	@echo "Running isort check..."
	isort --check-only app/ tests/

format:
	@echo "Formatting with black..."
	black app/ tests/
	@echo "Sorting imports with isort..."
	isort app/ tests/

security-scan:
	@echo "Running bandit security scan..."
	bandit -r app/ -f json -o bandit-report.json
	@echo "Security scan complete. Report saved to bandit-report.json"

# Docker
docker-build:
	docker build -t pyrunner .

docker-run:
	docker run -d -p 8000:8000 --name pyrunner pyrunner

docker-test:
	@echo "Building Docker image..."
	docker build -t pyrunner-test .
	@echo "Starting Docker container..."
	docker run -d -p 8000:8000 --name pyrunner-test pyrunner-test
	@echo "Waiting for service to start..."
	sleep 10
	@echo "Testing Docker service..."
	curl -f http://localhost:8000/ || (docker stop pyrunner-test && docker rm pyrunner-test && exit 1)
	curl -f -X POST http://localhost:8000/run \
		-H "Content-Type: application/json" \
		-d '{"code": "print(\"Docker test successful!\")"}' || (docker stop pyrunner-test && docker rm pyrunner-test && exit 1)
	@echo "Stopping Docker container..."
	docker stop pyrunner-test
	docker rm pyrunner-test
	@echo "Docker test completed successfully!"

# Development server
dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Cleanup
clean:
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf bandit-report.json
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

clean-cache:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

# CI/CD simulation
ci-test:
	@echo "Simulating CI/CD pipeline..."
	@echo "Step 1: Install dependencies"
	make install-dev
	@echo "Step 2: Run linting"
	make lint
	@echo "Step 3: Run unit tests"
	make test-unit
	@echo "Step 4: Run integration tests"
	make test-integration
	@echo "Step 5: Run security scan"
	make security-scan
	@echo "Step 6: Test Docker build"
	make docker-test
	@echo "CI/CD simulation completed successfully!"

# Quick development setup
setup: install-dev
	@echo "Development environment setup complete!"
	@echo "Run 'make test' to run all tests"
	@echo "Run 'make dev' to start development server"