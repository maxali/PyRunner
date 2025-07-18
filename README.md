# PyRunner

A secure, containerized Python code execution service with preinstalled scientific libraries and comprehensive resource limits.

## Features

- **Secure Code Execution**: AST-based validation blocks dangerous operations
- **Resource Limits**: Configurable timeout and memory limits
- **Scientific Libraries**: Pre-loaded NumPy, Pandas, SciPy, Sympy, Matplotlib, Scikit-learn
- **Fast Cold Starts**: Optimized Docker image with pre-compiled libraries
- **Comprehensive Testing**: 158 tests with 97% pass rate (153 passing)
- **Production Ready**: Docker containerization with health checks

## Quick Start

### Using Docker Compose (Recommended)

```bash
cd pyrunner
docker-compose up --build
```

### Using Docker

```bash
# Build and run
docker build -t pyrunner .
docker run -p 8000:8000 pyrunner

# Or for development
cd pyrunner
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing the API

```bash
# Health check
curl http://localhost:8000/

# Execute Python code
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"Hello, PyRunner!\")"}'
```

## API Reference

### Health Check

```http
GET /
```

**Response:**
```json
{
  "service": "PyRunner",
  "status": "healthy",
  "version": "1.0.0",
  "capabilities": {
    "max_timeout": 300,
    "max_memory_mb": 2048,
    "libraries": ["sympy", "numpy", "pandas", "matplotlib", "scipy", "sklearn"]
  }
}
```

### Code Execution

```http
POST /run
```

**Request Body:**
```json
{
  "code": "print('Hello, World!')",
  "timeout": 30,
  "memory_limit": 512
}
```

**Response:**
```json
{
  "status": "success",
  "stdout": "Hello, World!\n",
  "stderr": "",
  "execution_time": 0.023,
  "memory_used": 45.2,
  "error": null
}
```

## Parameters

| Parameter | Type | Required | Default | Range | Description |
|-----------|------|----------|---------|-------|-------------|
| `code` | string | Yes | - | 1-1MB | Python code to execute |
| `timeout` | integer | No | 30 | 1-300 | Execution timeout in seconds |
| `memory_limit` | integer | No | 512 | 64-2048 | Memory limit in MB |

## Response Status

- `success`: Code executed successfully
- `error`: Runtime error, syntax error, or security violation
- `timeout`: Execution exceeded time limit
- `memory_exceeded`: Execution exceeded memory limit

## Security Features

### Allowed Libraries

Scientific computing libraries are whitelisted:
- **Math**: `math`, `cmath`, `decimal`, `fractions`, `statistics`
- **Data**: `numpy`, `pandas`, `collections`, `itertools`, `functools`
- **Scientific**: `sympy`, `scipy`, `matplotlib`, `sklearn`
- **Utilities**: `datetime`, `json`, `csv`, `re`, `random`

### Blocked Operations

The security layer blocks dangerous operations:
- **File System**: `os`, `subprocess`, `open`, `file`
- **Network**: `socket`, `urllib`, `httplib`, `requests`
- **Code Injection**: `eval`, `exec`, `compile`, `__import__`
- **Introspection**: `__globals__`, `__code__`, `__class__`

## Usage Examples

### Basic Mathematics

```python
import requests

response = requests.post('http://localhost:8000/run', json={
    "code": """
import math
result = math.sqrt(16) + math.pi
print(f'Result: {result}')
""",
    "timeout": 10
})

print(response.json()['stdout'])  # Result: 7.141592653589793
```

### Scientific Computing

```python
response = requests.post('http://localhost:8000/run', json={
    "code": """
import numpy as np
import pandas as pd

# Create data
data = np.random.randn(100)
df = pd.DataFrame({'values': data})

# Calculate statistics
print(f'Mean: {df.values.mean():.3f}')
print(f'Std: {df.values.std():.3f}')
print(f'Count: {len(df)}')
""",
    "memory_limit": 256
})
```

### Symbolic Mathematics

```python
response = requests.post('http://localhost:8000/run', json={
    "code": """
import sympy as sp

# Define symbol
x = sp.Symbol('x')

# Solve equation
equation = x**2 - 4*x + 3
solutions = sp.solve(equation, x)
print(f'Solutions: {solutions}')

# Calculus
f = x**3 - 2*x**2 + x
derivative = sp.diff(f, x)
print(f'Derivative: {derivative}')
""",
    "timeout": 15
})
```

## Development

### Project Structure

```
PyRunner/
├── app/
│   ├── main.py          # FastAPI application
│   ├── models.py        # Pydantic models
│   ├── executor.py      # Code execution engine
│   └── security.py      # Security validation
├── tests/
│   ├── unit/           # Unit tests (67 tests)
│   └── integration/    # Integration tests (91 tests)
├── examples/
│   └── test_api.py     # API usage examples
├── docker-compose.yml  # Docker compose configuration
├── Dockerfile         # Container definition
└── requirements.txt   # Python dependencies
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/ --asyncio-mode=auto

# Run specific test types
python -m pytest tests/ -m unit --asyncio-mode=auto          # Unit tests only
python -m pytest tests/ -m integration --asyncio-mode=auto   # Integration tests only
python -m pytest tests/ -m security --asyncio-mode=auto      # Security tests only

# Run with coverage
python -m pytest tests/ --asyncio-mode=auto --cov=app --cov-report=html

# Using the test runner
python run_tests.py --unit --coverage
python run_tests.py --integration -v
```

### Test Results

- **Total Tests**: 158
- **Passing**: 153 (97%)
- **Unit Tests**: 67 (100% passing)
- **Integration Tests**: 91 (94% passing)

### Architecture

PyRunner uses a three-layer architecture:

1. **API Layer** (`main.py`): FastAPI application with request validation
2. **Security Layer** (`security.py`): AST-based code validation
3. **Execution Layer** (`executor.py`): Sandboxed subprocess execution

### Security Model

- **Whitelist Approach**: Only approved libraries are allowed
- **AST Validation**: Code is parsed and validated before execution
- **Process Isolation**: Code runs in separate subprocess with resource limits
- **Resource Monitoring**: Real-time memory and CPU usage tracking

## Production Deployment

### Resource Limits

Configure container resources:

```yaml
resources:
  requests:
    memory: "512Mi"
    cpu: "500m"
  limits:
    memory: "2Gi"
    cpu: "2"
```

### Health Monitoring

The service includes built-in health checks:

```yaml
livenessProbe:
  httpGet:
    path: /
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10
```

### Scaling

For high-throughput scenarios:

1. **Horizontal Scaling**: Deploy multiple containers
2. **Load Balancing**: Use nginx or cloud load balancer
3. **Resource Optimization**: Tune memory and CPU limits
4. **Monitoring**: Implement metrics collection

## Performance

- **Cold Start**: ~200ms (pre-loaded libraries)
- **Execution**: Variable (depends on code complexity)
- **Memory**: 50-100MB base usage
- **Throughput**: 100+ requests/second (simple operations)

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PYTHONUNBUFFERED` | `1` | Immediate stdout/stderr output |
| `PYTHONDONTWRITEBYTECODE` | `1` | Prevent .pyc file creation |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `python run_tests.py --coverage`
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Check the [examples](./examples/) directory
- Review the [test cases](./tests/) for usage patterns
- Open an issue for bug reports or feature requests

## Changelog

### v1.0.0
- Initial release
- Secure code execution with AST validation
- Resource limits (timeout, memory)
- Pre-loaded scientific libraries
- Comprehensive test suite (158 tests)
- Docker containerization
- FastAPI web service