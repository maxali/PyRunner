# PyRunner

A secure, containerized Python code execution service designed to safely run untrusted Python code with comprehensive resource limits and pre-installed scientific computing libraries.

## Overview

PyRunner provides a REST API for executing Python code in a secure, isolated environment. It's built with FastAPI and Docker, offering robust security through AST-based code validation, subprocess isolation, and strict resource limits. The service is optimized for scientific computing workflows with pre-loaded libraries like NumPy, Pandas, SymPy, and more.

## Key Features

- **🔒 Security-First Design**: Multi-layer security with AST validation, process isolation, and whitelisted imports
- **📊 Scientific Computing Ready**: Pre-loaded NumPy, Pandas, SciPy, SymPy, Matplotlib, Scikit-learn
- **⚡ Performance Optimized**: ~200ms cold starts with pre-compiled libraries and uvloop
- **🎯 Resource Management**: Configurable CPU, memory, and execution time limits
- **🧪 Battle-Tested**: 158 tests covering security, performance, and edge cases
- **🐳 Production Ready**: Docker containerization with health checks and horizontal scaling support
- **📈 Real-time Monitoring**: Execution metrics, memory usage tracking, and structured logging

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/pyrunner.git
cd pyrunner

# Start the service
docker-compose up --build

# Service will be available at http://localhost:8000
```

### Using Docker

```bash
# Build the image
docker build -t pyrunner .

# Run the container
docker run -p 8000:8000 pyrunner
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
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

## API Parameters

| Parameter | Type | Required | Default | Range | Description |
|-----------|------|----------|---------|-------|-------------|
| `code` | string | Yes | - | 1-1MB | Python code to execute |
| `timeout` | integer | No | 30 | 1-300 | Execution timeout in seconds |
| `memory_limit` | integer | No | 512 | 64-2048 | Memory limit in MB |

## Response Format

### Success Response
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

### Error Response
```json
{
  "status": "error",
  "stdout": "",
  "stderr": "NameError: name 'undefined' is not defined",
  "execution_time": 0.012,
  "memory_used": 42.1,
  "error": "NameError on line 1"
}
```

### Status Values
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

# Run specific test categories
python -m pytest tests/ -m unit --asyncio-mode=auto          # Unit tests only
python -m pytest tests/ -m integration --asyncio-mode=auto   # Integration tests only
python -m pytest tests/ -m security --asyncio-mode=auto      # Security tests only
python -m pytest tests/ -m performance --asyncio-mode=auto   # Performance tests only

# Run with coverage
python -m pytest tests/ --asyncio-mode=auto --cov=app --cov-report=html

# Using the test runner script
python scripts/run_tests.py --unit --coverage
python scripts/run_tests.py --integration -v
python scripts/run_tests.py --all --report

# Run specific test files
python -m pytest tests/unit/test_security.py -v
python -m pytest tests/integration/test_api.py::test_execute_code_success
```

### Test Coverage

- **Total Tests**: 158
- **Pass Rate**: 97% (153 passing)
- **Coverage**: 95%+ for core modules

#### Test Breakdown
- **Unit Tests**: 67 tests
  - Security validation: 25 tests
  - Model validation: 15 tests
  - Executor logic: 27 tests
- **Integration Tests**: 91 tests
  - API endpoints: 30 tests
  - Resource limits: 35 tests
  - Error scenarios: 26 tests

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

### Azure Container Apps (Recommended)

PyRunner is optimized for Azure Container Apps deployment with automated CI/CD:

```bash
# Quick setup
./scripts/setup-azure.sh

# Deploy via GitHub Actions
git push origin main
```

See [DEPLOYMENT.md](./docs/DEPLOYMENT.md) for detailed deployment instructions.

### Docker Compose Production

```yaml
version: '3.8'

services:
  pyrunner:
    image: pyrunner:latest
    ports:
      - "8000:8000"
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 2G
          cpus: '2'
        reservations:
          memory: 512M
          cpus: '0.5'
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pyrunner
spec:
  replicas: 3
  selector:
    matchLabels:
      app: pyrunner
  template:
    metadata:
      labels:
        app: pyrunner
    spec:
      containers:
      - name: pyrunner
        image: pyrunner:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2"
        livenessProbe:
          httpGet:
            path: /
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

### Scaling Strategies

#### Horizontal Scaling
- Deploy multiple container instances behind a load balancer
- Each container handles requests independently
- Recommended: 3-5 instances for high availability

#### Load Balancing
```nginx
upstream pyrunner {
    server pyrunner1:8000;
    server pyrunner2:8000;
    server pyrunner3:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://pyrunner;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### Monitoring and Observability
- Use Prometheus metrics endpoint (if configured)
- Monitor key metrics: request rate, execution time, memory usage
- Set up alerts for: high error rates, resource exhaustion, long execution times

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

## Troubleshooting

### Common Issues

#### Container fails to start
```bash
# Check logs
docker-compose logs pyrunner

# Verify port availability
lsof -i :8000
```

#### Code execution timeouts
- Increase timeout parameter (max 300s)
- Optimize code for performance
- Consider breaking into smaller operations

#### Memory limit exceeded
- Increase memory_limit parameter (max 2048MB)
- Use memory-efficient algorithms
- Process data in chunks

#### Import errors
- Check if library is in allowed list
- Use only whitelisted scientific libraries
- No external package installation supported

### Debug Mode

Enable detailed logging:
```bash
# Set log level
export LOG_LEVEL=DEBUG

# Run with verbose output
docker-compose up --build
```

## Security Best Practices

1. **Network Isolation**: Deploy in isolated network segment
2. **API Authentication**: Add authentication layer (OAuth2, API keys)
3. **Rate Limiting**: Implement request throttling
4. **Input Validation**: Additional validation at API gateway
5. **Audit Logging**: Log all execution requests
6. **Regular Updates**: Keep dependencies updated

## Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add/update tests as needed
5. Run the test suite: `python scripts/run_tests.py --all --coverage`
6. Ensure code quality: `make lint format`
7. Commit your changes (`git commit -m 'Add amazing feature'`)
8. Push to the branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guide
- Add type hints to all functions
- Write comprehensive tests for new features
- Update documentation as needed
- Ensure all tests pass before submitting PR

## Changelog

### v1.0.0 (2024-01)
- Initial release
- Core features:
  - Secure code execution with AST validation
  - Resource limits (timeout, memory)
  - Pre-loaded scientific libraries
  - Comprehensive test suite (158 tests)
  - Docker containerization
  - FastAPI web service
  - Real-time memory monitoring
  - Process group management