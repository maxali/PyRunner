# PyRunner Test Suite

A comprehensive testing suite for PyRunner built with pytest, featuring automated service management, test categorization, and CI/CD integration.

## Overview

This test suite provides thorough validation of PyRunner's functionality through:
- **Unit Tests**: Fast, isolated tests for individual components
- **Integration Tests**: End-to-end tests with running service
- **Security Tests**: Comprehensive security validation
- **Performance Tests**: Resource limit and performance validation

## Quick Start

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
make test

# Run specific test categories
make test-unit
make test-integration
make test-security
make test-performance

# Run with coverage
make test-coverage
```

## Test Structure

```
tests/
├── conftest.py                    # Pytest configuration and fixtures
├── fixtures/
│   └── test_data.py              # Test data and code samples
├── unit/
│   ├── test_security.py          # Security validation unit tests
│   ├── test_executor.py          # Code executor unit tests
│   └── test_models.py            # Data model tests
└── integration/
    ├── test_api.py               # API endpoint tests
    ├── test_security.py          # Security integration tests
    ├── test_resource_limits.py   # Resource limit tests
    └── test_end_to_end.py        # Complex scenario tests
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
- **Fast execution** (< 1 second per test)
- **No external dependencies** (no running service required)
- **Focused on individual components**
- **Mocked external calls**

```bash
# Run unit tests only
pytest tests/unit/ -m unit
make test-unit
```

### Integration Tests (`@pytest.mark.integration`)
- **Requires running PyRunner service**
- **End-to-end functionality validation**
- **Real API calls and responses**
- **Service lifecycle management**

```bash
# Run integration tests only
pytest tests/integration/ -m integration
make test-integration
```

### Security Tests (`@pytest.mark.security`)
- **Security validation and bypass attempts**
- **Module whitelist/blacklist testing**
- **Dangerous function detection**
- **Complex security scenarios**

```bash
# Run security tests only
pytest tests/ -m security
make test-security
```

### Performance Tests (`@pytest.mark.performance`)
- **Resource limit enforcement**
- **Timeout handling**
- **Memory usage monitoring**
- **Concurrent execution testing**

```bash
# Run performance tests only
pytest tests/ -m performance
make test-performance
```

### Slow Tests (`@pytest.mark.slow`)
- **Long-running tests** (> 5 seconds)
- **Resource-intensive operations**
- **Timeout testing**
- **Large data processing**

```bash
# Skip slow tests
pytest tests/ -m "not slow"

# Run only slow tests
pytest tests/ -m slow
```

## Running Tests

### Using the Test Runner

The `run_tests.py` script provides convenient test execution with automatic service management:

```bash
# Basic usage
python run_tests.py                    # Run all tests
python run_tests.py -v                 # Verbose output
python run_tests.py --coverage         # With coverage report

# Specific test categories
python run_tests.py --unit             # Unit tests only
python run_tests.py --integration      # Integration tests only
python run_tests.py --security         # Security tests only
python run_tests.py --performance      # Performance tests only

# Specific tests
python run_tests.py --test tests/unit/test_security.py
python run_tests.py --test tests/integration/test_api.py::TestHealthEndpoint::test_health_check
```

### Using Makefile

The Makefile provides shortcuts for common operations:

```bash
make test              # Run all tests
make test-unit         # Unit tests only
make test-integration  # Integration tests only
make test-security     # Security tests only
make test-performance  # Performance tests only
make test-coverage     # Tests with coverage
make test-watch        # Watch mode (if pytest-watch installed)
```

### Using pytest directly

```bash
# Run all tests
pytest tests/

# Run specific test files
pytest tests/unit/test_security.py
pytest tests/integration/test_api.py

# Run specific test methods
pytest tests/unit/test_security.py::TestSecurityValidator::test_validate_allowed_import

# Run tests with markers
pytest tests/ -m "unit and not slow"
pytest tests/ -m "integration and security"

# Run with coverage
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
```

## Test Configuration

### pytest.ini

The test suite is configured via `pytest.ini`:

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

### Coverage Configuration

Coverage is configured via `.coveragerc`:

```ini
[run]
source = app
omit = 
    */tests/*
    */venv/*
    */debug_*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    if __name__ == .__main__.:
```

## Test Fixtures

### Service Management

The test suite automatically manages the PyRunner service for integration tests:

```python
@pytest.fixture(scope="session")
async def pyrunner_service():
    """Start PyRunner service for integration tests"""
    service = PyRunnerService()
    await service.start()
    try:
        yield service
    finally:
        await service.stop()
```

### HTTP Client

An HTTP client is provided for API testing:

```python
@pytest.fixture
async def api_client(pyrunner_service):
    """HTTP client for API tests"""
    async with httpx.AsyncClient(base_url=pyrunner_service.base_url) as client:
        yield client
```

### Test Data

Test data and code samples are provided via fixtures:

```python
@pytest.fixture
def valid_code_samples():
    """Valid code samples for testing"""
    return VALID_CODE_SAMPLES

@pytest.fixture
def invalid_code_samples():
    """Invalid code samples for testing"""
    return INVALID_CODE_SAMPLES
```

## Test Data

### Valid Code Samples

The test suite includes comprehensive code samples for testing:

```python
VALID_CODE_SAMPLES = {
    "basic_print": "print('Hello from PyRunner!')",
    "basic_math": "import math\nprint(f'π = {math.pi}')",
    "numpy_array": "import numpy as np\narr = np.array([1, 2, 3])\nprint(f'Array: {arr}')",
    # ... many more samples
}
```

### Invalid Code Samples

Security test samples for blocked operations:

```python
INVALID_CODE_SAMPLES = {
    "os_import": "import os\nprint(os.getcwd())",
    "subprocess_call": "import subprocess\nresult = subprocess.run(['echo', 'test'])",
    "dynamic_import": "__import__('os').getcwd()",
    # ... many more samples
}
```

## Writing Tests

### Unit Test Example

```python
import pytest
from app.security import SecurityValidator

class TestSecurityValidator:
    @pytest.mark.unit
    def test_validate_allowed_import(self):
        validator = SecurityValidator()
        result = validator.validate_code("import math")
        assert result.is_valid
        assert result.error_message == ""
    
    @pytest.mark.unit
    def test_validate_blocked_import(self):
        validator = SecurityValidator()
        result = validator.validate_code("import os")
        assert not result.is_valid
        assert "os" in result.error_message.lower()
```

### Integration Test Example

```python
import pytest
import httpx
from tests.conftest import assert_success_response

class TestAPI:
    @pytest.mark.integration
    async def test_code_execution(self, api_client: httpx.AsyncClient):
        payload = {"code": "print('hello')"}
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "hello")
```

## CI/CD Integration

### GitHub Actions

The test suite integrates with GitHub Actions for automated testing:

```yaml
name: PyRunner Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.9, '3.10', '3.11', '3.12']
    
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run tests
      run: pytest tests/ --cov=app --cov-report=xml
```

### Local CI Simulation

```bash
# Simulate full CI pipeline
make ci-test
```

## Test Reports

### Coverage Reports

```bash
# Generate HTML coverage report
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html

# Generate terminal coverage report
pytest tests/ --cov=app --cov-report=term-missing
```

### Test Results

```bash
# Generate JUnit XML report
pytest tests/ --junitxml=test-results.xml

# Verbose output with timing
pytest tests/ -v --durations=10
```

## Debugging Tests

### Running Individual Tests

```bash
# Run single test with full output
pytest tests/unit/test_security.py::TestSecurityValidator::test_validate_allowed_import -v -s

# Run with debugger
pytest tests/unit/test_security.py::TestSecurityValidator::test_validate_allowed_import --pdb
```

### Test Isolation

```bash
# Run tests in isolated processes
pytest tests/ --forked

# Run with clean imports
pytest tests/ --import-mode=importlib
```

## Performance Considerations

### Test Execution Times

- **Unit tests**: < 1 second each
- **Integration tests**: 1-5 seconds each
- **Performance tests**: 5-30 seconds each
- **End-to-end tests**: 10-60 seconds each

### Parallel Execution

```bash
# Run tests in parallel (requires pytest-xdist)
pip install pytest-xdist
pytest tests/ -n auto
```

### Test Optimization

- Unit tests use mocking to avoid external dependencies
- Integration tests reuse service instances when possible
- Performance tests use appropriate timeouts
- Slow tests are marked for selective execution

## Troubleshooting

### Common Issues

1. **Service startup failures**: Check port availability
2. **Test timeouts**: Increase timeout values for slow systems
3. **Import errors**: Ensure all dependencies are installed
4. **Permission errors**: Check file permissions for test files

### Debug Mode

```bash
# Run with debug logging
pytest tests/ --log-cli-level=DEBUG

# Run with full traceback
pytest tests/ --tb=long

# Run with captured output
pytest tests/ -s
```

## Contributing

### Adding New Tests

1. **Choose appropriate test type** (unit vs integration)
2. **Add appropriate markers** (`@pytest.mark.unit`, etc.)
3. **Use existing fixtures** when possible
4. **Follow naming conventions** (`test_*.py`, `Test*`, `test_*`)
5. **Add to appropriate directory** (`tests/unit/` or `tests/integration/`)

### Test Guidelines

- Write clear, descriptive test names
- Use appropriate assertions
- Test both success and failure cases
- Include edge cases and boundary conditions
- Keep tests isolated and independent
- Use fixtures for common setup
- Document complex test scenarios

### Updating Test Data

When adding new test scenarios:

1. Add code samples to `tests/fixtures/test_data.py`
2. Update expected outputs and errors
3. Add corresponding test cases
4. Update documentation if needed

## Maintenance

### Regular Tasks

- **Update test dependencies** regularly
- **Review test coverage** and add missing tests
- **Performance monitoring** of test execution times
- **Security test updates** as new threats emerge

### Test Cleanup

```bash
# Clean up test artifacts
make clean

# Remove Python cache files
make clean-cache
```

This comprehensive test suite ensures PyRunner's reliability, security, and performance through automated testing with proper CI/CD integration.