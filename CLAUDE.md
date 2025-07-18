# CLAUDE.md

This file provides comprehensive guidance to Claude Code (claude.ai/code) when working with the PyRunner codebase. It includes architecture details, development workflows, testing strategies, and best practices for maintaining and extending the service.

## Quick Reference

### Essential Commands
```bash
# Development workflow
make test           # Run all tests
make test-unit      # Run unit tests only
make test-coverage  # Run tests with coverage report
make lint           # Check code style
make format         # Auto-format code

# Docker operations
docker-compose up --build    # Build and start service
docker-compose logs -f       # View logs
docker-compose down          # Stop service

# Local development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Testing endpoints
curl http://localhost:8000/                                    # Health check
curl -X POST http://localhost:8000/run \                      # Execute code
  -H "Content-Type: application/json" \
  -d '{"code": "print(\"Hello\")", "timeout": 30}'
```

### Running Tests
```bash
# Full test suite with proper async handling
python -m pytest tests/ --asyncio-mode=auto -v

# Category-specific tests
python -m pytest tests/ -m unit --asyncio-mode=auto
python -m pytest tests/ -m integration --asyncio-mode=auto
python -m pytest tests/ -m security --asyncio-mode=auto
python -m pytest tests/ -m performance --asyncio-mode=auto

# Test with coverage
python -m pytest tests/ --asyncio-mode=auto --cov=app --cov-report=html

# Run specific test file or function
python -m pytest tests/unit/test_security.py::test_blocked_imports -v

# Using the test runner script
python scripts/run_tests.py --all --coverage --report
```

## Architecture Deep Dive

PyRunner implements a defense-in-depth security architecture with three isolated layers:

### 1. Security Layer (`app/security.py`)
```python
# Key components:
class SecurityValidator:
    """Main security interface - validates code before execution"""
    def validate_code(self, code: str) -> tuple[bool, Optional[str]]

class SecurityChecker(ast.NodeVisitor):
    """AST visitor that enforces security rules"""
    # Checks for:
    # - Dangerous imports (os, subprocess, socket, etc.)
    # - Unsafe builtins (eval, exec, compile, __import__)
    # - File operations (open, file)
    # - Attribute access to internals (__globals__, __code__)
```

**Security Rules:**
- Whitelist approach: Only explicitly allowed modules can be imported
- No file system access (blocks open(), os.*, pathlib, etc.)
- No network operations (blocks socket, urllib, requests, etc.)
- No code generation (blocks eval, exec, compile)
- No introspection of internals (blocks __globals__, __code__, etc.)

### 2. Execution Layer (`app/executor.py`)
```python
class CodeExecutor:
    """Manages sandboxed code execution with resource limits"""
    
    async def execute_code(self, code: str, timeout: int, memory_limit: int)
    # Key features:
    # - Subprocess isolation (separate process group)
    # - Resource limits via resource.setrlimit()
    # - Concurrent memory monitoring with psutil
    # - Automatic cleanup on timeout/error
```

**Resource Management:**
- **Memory**: Dual enforcement (OS limit + active monitoring)
- **CPU Time**: Hard limit prevents infinite loops
- **File Descriptors**: Limited to 50 to prevent resource exhaustion
- **Process Groups**: Ensures all child processes are cleaned up

### 3. API Layer (`app/main.py`)
```python
@app.on_event("startup")
async def startup_event():
    """Pre-load libraries for faster execution"""
    
@app.post("/run")
async def execute_code(request: CodeRequest) -> ExecutionResponse:
    """Main execution endpoint with validation pipeline"""
```

**Request Pipeline:**
1. Input validation (Pydantic models)
2. Security validation (AST analysis)
3. Resource allocation
4. Code execution in subprocess
5. Result formatting and metrics

### Data Flow
```
Client Request → FastAPI → Validation → Security Check → Executor
                                ↓                            ↓
                           (Reject if unsafe)        (Subprocess + Limits)
                                                            ↓
                                                     Memory Monitor
                                                            ↓
Client ← Response ← Metrics ← Cleanup ← Results
```

## Implementation Details

### Code Execution Flow

1. **Request Reception** (app/main.py:execute_code)
   - Validate request parameters
   - Check code size (max 1MB)
   - Initialize response tracking

2. **Security Validation** (app/security.py:validate_code)
   - Parse code into AST
   - Traverse AST nodes checking against rules
   - Return validation result with specific error if found

3. **Execution Setup** (app/executor.py:execute_code)
   - Create temporary Python file
   - Set up subprocess with resource limits
   - Start memory monitoring task

4. **Process Execution**
   - Run in separate process group
   - Apply resource limits (memory, CPU, file descriptors)
   - Capture stdout/stderr
   - Monitor for timeout/memory exceeded

5. **Cleanup and Response**
   - Kill process group if still running
   - Clean up temporary files
   - Format execution metrics
   - Return structured response

### Error Handling Patterns

```python
# Security validation errors
if "import os" in code:
    return ExecutionResponse(
        status=ExecutionStatus.ERROR,
        error="SecurityError: Import of 'os' is not allowed"
    )

# Resource limit errors
if memory_used > memory_limit:
    process.terminate()
    return ExecutionResponse(
        status=ExecutionStatus.MEMORY_EXCEEDED,
        error=f"Memory limit exceeded: {memory_used}MB > {memory_limit}MB"
    )

# Execution errors
try:
    result = await execute_code(...)
except asyncio.TimeoutError:
    return ExecutionResponse(
        status=ExecutionStatus.TIMEOUT,
        error=f"Execution timed out after {timeout} seconds"
    )
```

## Key Technical Decisions

### Resource Management
- Memory limits enforced at both OS level (resource.setrlimit) and process monitoring level
- CPU time limits prevent infinite loops (300s hard limit)
- File descriptor limits (50) prevent resource exhaustion
- Process groups enable reliable cleanup of child processes

### Security Model
- Whitelist-based security: Only approved scientific libraries allowed
- AST parsing blocks dangerous patterns before execution
- Subprocess isolation prevents access to main application state
- No persistent storage or network access for executed code

### Performance Optimizations
- Multi-stage Docker build minimizes image size
- Pre-compilation of Python files reduces startup time
- Scientific libraries pre-imported during application startup
- Uvloop for faster async operations
- Single worker per container (scale horizontally)

## Configuration and Limits

### Environment Configuration
```bash
# Required environment variables
export PYTHONUNBUFFERED=1          # Real-time output
export PYTHONDONTWRITEBYTECODE=1   # No .pyc files

# Optional configuration
export LOG_LEVEL=INFO              # Logging level (DEBUG, INFO, WARNING, ERROR)
export WORKERS=1                    # Number of Uvicorn workers (keep at 1)
export HOST=0.0.0.0                # Bind address
export PORT=8000                    # Service port
```

### Resource Limits

| Resource | Min | Default | Max | Notes |
|----------|-----|---------|-----|-------|
| Timeout | 1s | 30s | 300s | Hard kill after timeout |
| Memory | 64MB | 512MB | 2048MB | Monitored every 0.1s |
| CPU Time | - | 300s | 300s | Prevents infinite loops |
| File Descriptors | - | 50 | 50 | Prevents resource leaks |
| Code Size | 1 byte | - | 1MB | Request validation |
| Process Group | - | Yes | - | Ensures cleanup |

### Docker Resource Configuration
```yaml
# docker-compose.yml
services:
  pyrunner:
    deploy:
      resources:
        limits:
          memory: 2G      # Container memory limit
          cpus: '2'       # CPU cores limit
        reservations:
          memory: 512M    # Reserved memory
          cpus: '0.5'     # Reserved CPU
```

### Allowed Python Libraries

**Core Libraries:**
- Math: `math`, `cmath`, `decimal`, `fractions`, `statistics`
- Data: `collections`, `itertools`, `functools`, `operator`
- Time: `datetime`, `time` (limited functions)
- Text: `re`, `string`, `textwrap`
- Data formats: `json`, `csv`

**Scientific Libraries:**
- `numpy` - Numerical computing
- `pandas` - Data analysis
- `scipy` - Scientific computing
- `sympy` - Symbolic mathematics
- `matplotlib` - Plotting (non-interactive)
- `sklearn` - Machine learning
- `statsmodels` - Statistical modeling

**Blocked Modules:**
- System: `os`, `sys`, `subprocess`, `shutil`
- Network: `socket`, `urllib`, `requests`, `http`
- Files: `open`, `file`, `pathlib`, `glob`
- Code: `eval`, `exec`, `compile`, `ast`
- Import: `importlib`, `__import__`

## Development Workflows

### Adding a New Allowed Library

1. Update `ALLOWED_MODULES` in `app/security.py`:
```python
ALLOWED_MODULES = {
    # ... existing modules ...
    'new_library',  # Add your library here
}
```

2. Add to Docker requirements:
```bash
# requirements.txt
new-library==1.2.3
```

3. Pre-import in `app/main.py` for performance:
```python
@app.on_event("startup")
async def startup_event():
    exec("import new_library")
```

4. Add security tests:
```python
# tests/unit/test_security.py
def test_new_library_allowed():
    code = "import new_library"
    valid, error = validator.validate_code(code)
    assert valid
```

5. Add integration tests:
```python
# tests/integration/test_api.py
@pytest.mark.asyncio
async def test_new_library_execution():
    response = await client.post("/run", json={
        "code": "import new_library; print(new_library.__version__)"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "success"
```

### Modifying Resource Limits

1. Update model validation in `app/models.py`:
```python
class CodeRequest(BaseModel):
    timeout: int = Field(default=30, ge=1, le=300)  # Modify max here
    memory_limit: int = Field(default=512, ge=64, le=2048)  # Modify max here
```

2. Update executor limits in `app/executor.py`:
```python
# Adjust resource limits
resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
resource.setrlimit(resource.RLIMIT_CPU, (300, 300))  # Modify CPU limit
```

3. Update tests for new limits:
```python
# tests/integration/test_resource_limits.py
@pytest.mark.parametrize("memory_limit", [64, 512, 2048])  # Test new limits
```

### Debugging Failed Executions

1. Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. Add debug prints in executor:
```python
print(f"[DEBUG] Starting execution with limits: {memory_limit}MB, {timeout}s")
print(f"[DEBUG] Process PID: {process.pid}")
print(f"[DEBUG] Memory usage: {memory_used}MB")
```

3. Check process output:
```python
stdout, stderr = await process.communicate()
print(f"[DEBUG] Exit code: {process.returncode}")
print(f"[DEBUG] Stdout: {stdout}")
print(f"[DEBUG] Stderr: {stderr}")
```

## Testing Guidelines

### Test Categories

**Unit Tests** (`tests/unit/`)
- Test individual components in isolation
- Mock external dependencies
- Focus on edge cases and error conditions
- Run quickly (<0.1s per test)

**Integration Tests** (`tests/integration/`)
- Test full request/response flow
- Verify resource limits work correctly
- Test error scenarios end-to-end
- May take longer (timeout tests)

**Security Tests** (`tests/unit/test_security.py`)
- Verify all dangerous operations are blocked
- Test AST validation comprehensively
- Ensure no bypass methods exist
- Critical for safety

**Performance Tests** (`tests/integration/test_performance.py`)
- Measure execution overhead
- Verify cold start times
- Test concurrent request handling
- Profile memory usage

### Writing New Tests

```python
# Use proper async test decoration
@pytest.mark.asyncio
@pytest.mark.integration
async def test_feature():
    # Arrange
    code = "import numpy as np; print(np.array([1,2,3]))"
    
    # Act
    response = await client.post("/run", json={"code": code})
    
    # Assert
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == "success"
    assert "[1 2 3]" in result["stdout"]
```

### Test Data Management

Use fixtures for common test data:
```python
@pytest.fixture
def scientific_code():
    return """
import numpy as np
import pandas as pd
data = pd.DataFrame({'x': [1, 2, 3]})
print(data.describe())
"""
```

## Debugging and Monitoring

### Local Debugging

1. **Run with debugger:**
```bash
python -m pdb -m uvicorn app.main:app --reload
```

2. **Add breakpoints:**
```python
import pdb; pdb.set_trace()
```

3. **Inspect execution:**
```python
# In executor.py
logger.debug(f"Executing code: {code[:100]}...")
logger.debug(f"Process started with PID: {process.pid}")
logger.debug(f"Memory usage: {memory_used}/{memory_limit}MB")
```

### Production Monitoring

1. **Structured Logging:**
```python
import structlog
logger = structlog.get_logger()

logger.info("code_execution_started", 
    request_id=request_id,
    timeout=timeout,
    memory_limit=memory_limit
)
```

2. **Metrics Collection:**
```python
# Add to execution response
execution_metrics = {
    "execution_time": end_time - start_time,
    "memory_peak": max_memory_used,
    "cpu_time": process_cpu_time,
    "exit_code": process.returncode
}
```

3. **Health Check Enhancement:**
```python
@app.get("/health/detailed")
async def detailed_health():
    return {
        "status": "healthy",
        "uptime": time.time() - start_time,
        "total_requests": request_counter,
        "active_executions": active_count,
        "memory_usage": get_process_memory()
    }
```

## Security Best Practices

### Code Review Checklist

- [ ] No new imports added to ALLOWED_MODULES without security review
- [ ] No modifications to SecurityChecker bypass rules
- [ ] Resource limits are not increased beyond safe thresholds
- [ ] No direct file system access in any code path
- [ ] Subprocess isolation is maintained
- [ ] Error messages don't leak sensitive information
- [ ] All user input is validated

### Security Testing

1. **Fuzzing:**
```python
# Test with random/malformed input
import hypothesis
@hypothesis.given(hypothesis.strategies.text())
def test_random_code_execution(code):
    # Should never crash the service
    response = client.post("/run", json={"code": code})
    assert response.status_code in [200, 400, 422]
```

2. **Penetration Testing:**
```python
# tests/security/test_exploits.py
EXPLOIT_ATTEMPTS = [
    "__import__('os').system('ls')",
    "exec(open('/etc/passwd').read())",
    "import sys; sys.modules['os'] = __import__('os')",
    # Add more exploit attempts
]

for exploit in EXPLOIT_ATTEMPTS:
    result = execute_code(exploit)
    assert result.status == "error"
    assert "security" in result.error.lower()
```

## Common Patterns and Recipes

### Handling Large Computations

```python
# Pattern: Process data in chunks to avoid memory issues
code = """
import numpy as np

# Process in chunks
results = []
chunk_size = 1000000
for i in range(0, 10000000, chunk_size):
    chunk = np.arange(i, min(i + chunk_size, 10000000))
    results.append(np.mean(chunk ** 2))
    
print(f'Final result: {np.mean(results)}')
"""
```

### Scientific Computing Workflow

```python
# Pattern: Complete analysis pipeline
code = """
import numpy as np
import pandas as pd
from scipy import stats
import matplotlib.pyplot as plt

# Generate sample data
np.random.seed(42)
data = np.random.normal(100, 15, 1000)

# Statistical analysis
df = pd.DataFrame({'values': data})
print(f"Mean: {df.values.mean():.2f}")
print(f"Std: {df.values.std():.2f}")
print(f"Skewness: {stats.skew(data):.2f}")
print(f"Kurtosis: {stats.kurtosis(data):.2f}")

# Normality test
statistic, p_value = stats.normaltest(data)
print(f"\nNormality test p-value: {p_value:.4f}")
"""
```

### Error Handling in User Code

```python
# Pattern: Graceful error handling
code = """
try:
    import numpy as np
    result = np.divide(1, 0)  # Will cause warning, not error
except Exception as e:
    print(f"Error occurred: {type(e).__name__}: {e}")
else:
    print(f"Result: {result}")
finally:
    print("Execution completed")
"""
```

## Deployment Considerations

### Kubernetes Configuration

```yaml
# Additional security context
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  readOnlyRootFilesystem: true
  capabilities:
    drop:
      - ALL
```

### Auto-scaling Configuration

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: pyrunner-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: pyrunner
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```