# Test Implementation Plan: PyRunner Testing Suite

## Overview
Convert the current ad-hoc test scripts into a proper testing suite using pytest, with proper test organization, fixtures, and build-time integration.

## Current State Analysis

### Existing Test Files:
- `test_api_endpoints.py` - Basic API functionality tests
- `test_comprehensive_api.py` - Full API integration tests
- `test_security_validation.py` - Security validation tests
- `test_resource_limits.py` - Resource management tests
- `test_executor_fix.py` - Low-level executor tests
- `examples/test_api.py` - Example API usage (needs fixing)

### Issues with Current Tests:
1. **No proper test framework** - Using custom test runners instead of pytest
2. **No test isolation** - Tests depend on external service running
3. **No fixtures** - Duplicated setup code across files
4. **No build integration** - Can't run tests in CI/CD pipelines
5. **Manual service management** - Tests require manual service startup
6. **No test categorization** - No way to run specific test suites
7. **No test reporting** - No standardized test output format

## Implementation Plan

### Phase 1: Test Framework Setup

#### 1.1 Dependencies and Configuration
- **Add pytest dependencies to requirements.txt**:
  ```
  pytest>=7.0.0
  pytest-asyncio>=0.21.0
  pytest-cov>=4.0.0
  pytest-timeout>=2.1.0
  httpx>=0.24.0  # For async HTTP client
  ```

- **Create pytest configuration** (`pytest.ini`):
  ```ini
  [tool:pytest]
  testpaths = tests
  python_files = test_*.py
  python_classes = Test*
  python_functions = test_*
  asyncio_mode = auto
  timeout = 300
  markers =
      unit: Unit tests
      integration: Integration tests
      security: Security validation tests
      performance: Performance tests
      slow: Slow tests (>5 seconds)
  ```

#### 1.2 Test Directory Structure
```
tests/
├── __init__.py
├── conftest.py                 # Pytest fixtures and configuration
├── unit/
│   ├── __init__.py
│   ├── test_security.py        # Security validation unit tests
│   ├── test_executor.py        # Executor unit tests
│   └── test_models.py          # Model validation tests
├── integration/
│   ├── __init__.py
│   ├── test_api.py             # API integration tests
│   ├── test_resource_limits.py # Resource management tests
│   └── test_end_to_end.py      # Full end-to-end tests
└── fixtures/
    ├── __init__.py
    └── test_data.py            # Test data and code samples
```

### Phase 2: Test Infrastructure

#### 2.1 Test Fixtures (`tests/conftest.py`)
- **Service lifecycle fixture** - Start/stop PyRunner service for tests
- **HTTP client fixture** - Configured httpx client for API calls
- **Test data fixtures** - Code samples for testing
- **Security test fixtures** - Allowed/blocked module lists
- **Performance test fixtures** - Timeout and memory configurations

#### 2.2 Test Utilities (`tests/utils/`)
- **Service management** - Functions to start/stop/check service
- **Test helpers** - Common assertion helpers
- **Data generators** - Generate test code samples
- **Mock utilities** - Mock external dependencies

### Phase 3: Test Implementation

#### 3.1 Unit Tests (`tests/unit/`)

**`test_security.py`**:
- Test SecurityValidator class methods
- Test AST parsing and validation
- Test allowed/blocked module detection
- Test security bypass attempt detection
- Parameterized tests for all security rules

**`test_executor.py`**:
- Test CodeExecutor methods in isolation
- Test resource limit setting (mocked)
- Test memory monitoring logic
- Test process cleanup
- Test timeout handling

**`test_models.py`**:
- Test Pydantic model validation
- Test request/response serialization
- Test parameter validation ranges
- Test error handling in models

#### 3.2 Integration Tests (`tests/integration/`)

**`test_api.py`**:
- Test API endpoints with live service
- Test request/response format
- Test error handling
- Test concurrent requests
- Test parameter validation

**`test_resource_limits.py`**:
- Test timeout enforcement
- Test memory limit enforcement
- Test CPU-intensive operations
- Test process cleanup
- Test concurrent execution

**`test_end_to_end.py`**:
- Full workflow tests
- Scientific library integration
- Real-world code execution scenarios
- Performance benchmarks

### Phase 4: Test Categorization and Markers

#### 4.1 Test Categories
- **`@pytest.mark.unit`** - Fast unit tests, no external dependencies
- **`@pytest.mark.integration`** - Tests requiring running service
- **`@pytest.mark.security`** - Security validation tests
- **`@pytest.mark.performance`** - Performance and resource tests
- **`@pytest.mark.slow`** - Tests taking >5 seconds

#### 4.2 Test Selection
```bash
# Run all tests
pytest

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run security tests
pytest -m security

# Skip slow tests
pytest -m "not slow"
```

### Phase 5: CI/CD Integration

#### 5.1 GitHub Actions Workflow (`.github/workflows/test.yml`)
```yaml
name: Test PyRunner
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, 3.10, 3.11, 3.12]
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v3
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run unit tests
        run: pytest -m unit --cov=app --cov-report=xml
      - name: Run integration tests
        run: pytest -m integration
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

#### 5.2 Docker Test Environment
- **Multi-stage Dockerfile** with test stage
- **Docker Compose** for test environment
- **Test containers** for isolated testing

### Phase 6: Test Data and Fixtures

#### 6.1 Test Code Samples (`tests/fixtures/test_data.py`)
```python
# Valid code samples
VALID_CODE_SAMPLES = {
    "basic_math": "import math\nprint(math.pi)",
    "numpy_array": "import numpy as np\nprint(np.array([1,2,3]))",
    # ... more samples
}

# Invalid code samples
INVALID_CODE_SAMPLES = {
    "os_import": "import os\nprint(os.getcwd())",
    "subprocess_call": "import subprocess\nsubprocess.run(['ls'])",
    # ... more samples
}
```

#### 6.2 Performance Test Data
```python
# Performance test configurations
PERFORMANCE_CONFIGS = {
    "timeout_tests": [
        {"timeout": 1, "expected_duration": 1.0},
        {"timeout": 5, "expected_duration": 5.0},
    ],
    "memory_tests": [
        {"memory_limit": 64, "code": "..."},
        {"memory_limit": 256, "code": "..."},
    ]
}
```

### Phase 7: Test Reporting and Coverage

#### 7.1 Coverage Configuration (`.coveragerc`)
```ini
[run]
source = app
omit = 
    */tests/*
    */venv/*
    */migrations/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
```

#### 7.2 Test Reports
- **HTML coverage reports** for local development
- **XML coverage reports** for CI/CD
- **JUnit XML reports** for test results
- **Performance benchmarks** with timing reports

### Phase 8: Migration Strategy

#### 8.1 File Conversions
1. **`test_api_endpoints.py`** → `tests/integration/test_api.py`
2. **`test_security_validation.py`** → `tests/unit/test_security.py` + `tests/integration/test_security_integration.py`
3. **`test_resource_limits.py`** → `tests/integration/test_resource_limits.py`
4. **`test_executor_fix.py`** → `tests/unit/test_executor.py`
5. **`test_comprehensive_api.py`** → `tests/integration/test_end_to_end.py`
6. **`examples/test_api.py`** → `tests/examples/test_usage_examples.py`

#### 8.2 Service Management
- **Test service fixtures** - Automatic service startup/shutdown
- **Port management** - Dynamic port allocation for tests
- **Service health checks** - Ensure service is ready before tests
- **Cleanup procedures** - Proper test isolation

### Phase 9: Development Workflow

#### 9.1 Local Development
```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests during development
pytest --cov=app --cov-report=html

# Run specific test categories
pytest -m "unit and not slow"
pytest -m "integration and security"

# Run tests with output
pytest -v -s
```

#### 9.2 Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-unit
        name: pytest-unit
        entry: pytest -m unit
        language: system
        always_run: true
        pass_filenames: false
```

### Phase 10: Documentation and Maintenance

#### 10.1 Test Documentation
- **Test README** - How to run tests
- **Test guidelines** - Writing new tests
- **CI/CD documentation** - Build pipeline explanation
- **Coverage reports** - How to interpret results

#### 10.2 Maintenance Procedures
- **Test data updates** - Keep test samples current
- **Performance baselines** - Update performance expectations
- **Security test updates** - Add new security test cases
- **Dependency updates** - Keep test dependencies current

## Implementation Order

### Priority 1 (Week 1):
1. Set up pytest configuration and directory structure
2. Create basic fixtures and service management
3. Convert unit tests (security, executor, models)
4. Set up coverage reporting

### Priority 2 (Week 2):
1. Convert integration tests (API, resource limits)
2. Set up CI/CD pipeline
3. Create test data fixtures
4. Implement test categorization

### Priority 3 (Week 3):
1. Performance and benchmark tests
2. End-to-end integration tests
3. Docker test environment
4. Documentation and guidelines

### Priority 4 (Week 4):
1. Advanced test features (parameterization, fixtures)
2. Test optimization and parallel execution
3. Monitoring and reporting improvements
4. Developer workflow integration

## Success Criteria

- ✅ All tests run with `pytest` command
- ✅ Tests can run in CI/CD without manual service management
- ✅ >90% code coverage on core functionality
- ✅ Tests complete in <2 minutes for unit tests, <5 minutes for integration
- ✅ Clear test categories and selective test running
- ✅ Comprehensive test reporting and coverage
- ✅ No dependency on external services for unit tests
- ✅ Proper test isolation and cleanup
- ✅ Documentation for test writing and maintenance

## Expected Benefits

1. **Automated testing** - No manual service management
2. **Better CI/CD integration** - Reliable build pipelines
3. **Improved code quality** - Comprehensive test coverage
4. **Developer productivity** - Fast, reliable test feedback
5. **Maintainability** - Well-organized, documented tests
6. **Confidence** - Thorough validation of all functionality
7. **Performance tracking** - Benchmark regression detection
8. **Security assurance** - Comprehensive security validation

This plan transforms the current ad-hoc testing approach into a professional, maintainable, and automated testing suite suitable for production use.