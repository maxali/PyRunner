# Python Execution Backend Service

A fast, secure, containerized Python execution service with API access, supporting preinstalled scientific libraries and optimized for low-latency execution.

## Project Structure

```
pyrunner/
├── Dockerfile
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── executor.py
│   ├── models.py
│   └── security.py
├── docker-compose.yml
├── .dockerignore
└── examples/
    ├── test_api.py
    └── README.md
```

## Implementation

### 1. Dockerfile

```dockerfile
# Multi-stage build for smaller final image
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    gfortran \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.11-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user for security
RUN useradd -m -s /bin/bash pyrunner

# Create app directory
WORKDIR /app

# Copy application code
COPY app/ ./app/

# Change ownership
RUN chown -R pyrunner:pyrunner /app

# Switch to non-root user
USER pyrunner

# Expose port
EXPOSE 8000

# Pre-compile Python files for faster startup
RUN python -m py_compile app/*.py

# Use uvicorn with optimized settings
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--loop", "uvloop"]
```

### 2. requirements.txt

```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
pydantic==2.5.0
sympy==1.12
numpy==1.26.2
pandas==2.1.3
matplotlib==3.8.2
scipy==1.11.4
scikit-learn==1.3.2
requests==2.31.0
aiofiles==23.2.1
psutil==5.9.6
```

### 3. app/__init__.py

```python
"""PyRunner - Fast Python Execution Backend Service"""

__version__ = "1.0.0"
```

### 4. app/models.py

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any
from enum import Enum


class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    MEMORY_EXCEEDED = "memory_exceeded"


class CodeRequest(BaseModel):
    code: str = Field(..., description="Python code to execute")
    timeout: Optional[int] = Field(
        default=30, 
        ge=1, 
        le=300,
        description="Execution timeout in seconds (1-300)"
    )
    memory_limit: Optional[int] = Field(
        default=512,
        ge=64,
        le=2048,
        description="Memory limit in MB (64-2048)"
    )
    
    @validator('code')
    def validate_code(cls, v):
        if not v.strip():
            raise ValueError("Code cannot be empty")
        if len(v) > 1_000_000:  # 1MB limit
            raise ValueError("Code too large (max 1MB)")
        return v


class ExecutionResponse(BaseModel):
    status: ExecutionStatus
    stdout: str = ""
    stderr: str = ""
    execution_time: float = Field(..., description="Execution time in seconds")
    memory_used: Optional[float] = Field(None, description="Memory used in MB")
    error: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "stdout": "Hello, World!\n",
                "stderr": "",
                "execution_time": 0.023,
                "memory_used": 45.2
            }
        }
```

### 5. app/security.py

```python
import re
import ast
from typing import Set, List


class SecurityValidator:
    """Basic security validation for Python code"""
    
    # Dangerous imports and functions
    DANGEROUS_IMPORTS = {
        'os', 'subprocess', 'sys', 'importlib', 'eval', 'exec',
        'compile', '__import__', 'open', 'file', 'input', 'raw_input',
        'socket', 'urllib', 'httplib', 'ftplib', 'telnetlib',
        'pickle', 'cPickle', 'marshal', 'shelve'
    }
    
    DANGEROUS_BUILTINS = {
        'eval', 'exec', 'compile', '__import__', 'open', 'file',
        'input', 'raw_input', 'execfile', 'reload'
    }
    
    # Allowed modules for scientific computing
    ALLOWED_MODULES = {
        'math', 'cmath', 'decimal', 'fractions', 'random', 'statistics',
        'itertools', 'functools', 'operator', 'collections', 'heapq',
        'bisect', 'array', 'datetime', 'calendar', 'copy', 'pprint',
        're', 'string', 'textwrap', 'unicodedata', 'json', 'csv',
        'numpy', 'sympy', 'pandas', 'matplotlib', 'scipy', 'sklearn'
    }
    
    @classmethod
    def validate_code(cls, code: str) -> tuple[bool, str]:
        """
        Validate Python code for security issues.
        Returns (is_valid, error_message)
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, f"Syntax error: {str(e)}"
        
        validator = SecurityChecker(cls.DANGEROUS_IMPORTS, cls.DANGEROUS_BUILTINS, cls.ALLOWED_MODULES)
        try:
            validator.visit(tree)
        except SecurityError as e:
            return False, str(e)
        
        return True, ""


class SecurityError(Exception):
    """Raised when security violation is detected"""
    pass


class SecurityChecker(ast.NodeVisitor):
    """AST visitor to check for security issues"""
    
    def __init__(self, dangerous_imports: Set[str], dangerous_builtins: Set[str], allowed_modules: Set[str]):
        self.dangerous_imports = dangerous_imports
        self.dangerous_builtins = dangerous_builtins
        self.allowed_modules = allowed_modules
    
    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            module_name = alias.name.split('.')[0]
            if module_name in self.dangerous_imports:
                raise SecurityError(f"Import of '{module_name}' is not allowed")
            if module_name not in self.allowed_modules and not module_name.startswith('_'):
                raise SecurityError(f"Import of '{module_name}' is not in the allowed list")
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            module_name = node.module.split('.')[0]
            if module_name in self.dangerous_imports:
                raise SecurityError(f"Import from '{module_name}' is not allowed")
            if module_name not in self.allowed_modules and not module_name.startswith('_'):
                raise SecurityError(f"Import from '{module_name}' is not in the allowed list")
        self.generic_visit(node)
    
    def visit_Call(self, node: ast.Call):
        # Check for dangerous function calls
        if isinstance(node.func, ast.Name):
            if node.func.id in self.dangerous_builtins:
                raise SecurityError(f"Call to '{node.func.id}' is not allowed")
        
        # Check for getattr/setattr/delattr
        if isinstance(node.func, ast.Name) and node.func.id in {'getattr', 'setattr', 'delattr'}:
            raise SecurityError(f"Call to '{node.func.id}' is not allowed")
        
        self.generic_visit(node)
    
    def visit_Attribute(self, node: ast.Attribute):
        # Check for dangerous attribute access patterns
        dangerous_attrs = {'__globals__', '__code__', '__class__', '__bases__', '__subclasses__'}
        if node.attr in dangerous_attrs:
            raise SecurityError(f"Access to '{node.attr}' attribute is not allowed")
        self.generic_visit(node)
```

### 6. app/executor.py

```python
import asyncio
import subprocess
import tempfile
import time
import psutil
import os
import signal
from typing import Tuple, Optional
from app.models import ExecutionStatus


class CodeExecutor:
    """Executes Python code in an isolated subprocess with resource limits"""
    
    @staticmethod
    async def execute(code: str, timeout: int = 30, memory_limit: int = 512) -> Tuple[ExecutionStatus, str, str, float, Optional[float]]:
        """
        Execute Python code with timeout and memory limits.
        Returns (status, stdout, stderr, execution_time, memory_used)
        """
        start_time = time.time()
        
        # Create temporary file for code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name
        
        try:
            # Prepare subprocess with resource limits
            process = await asyncio.create_subprocess_exec(
                'python', '-u', temp_file,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=lambda: CodeExecutor._set_limits(memory_limit),
                start_new_session=True  # Create new process group for cleanup
            )
            
            # Monitor memory usage
            memory_monitor_task = asyncio.create_task(
                CodeExecutor._monitor_memory(process.pid, memory_limit)
            )
            
            try:
                # Wait for completion with timeout
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
                
                execution_time = time.time() - start_time
                
                # Cancel memory monitor
                memory_monitor_task.cancel()
                try:
                    max_memory = await memory_monitor_task
                except asyncio.CancelledError:
                    max_memory = None
                
                # Determine status
                if process.returncode == 0:
                    status = ExecutionStatus.SUCCESS
                elif process.returncode == -signal.SIGKILL:
                    status = ExecutionStatus.MEMORY_EXCEEDED
                    stderr = b"Memory limit exceeded"
                else:
                    status = ExecutionStatus.ERROR
                
                return (
                    status,
                    stdout.decode('utf-8', errors='replace'),
                    stderr.decode('utf-8', errors='replace'),
                    execution_time,
                    max_memory
                )
                
            except asyncio.TimeoutError:
                # Kill the process group
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    await asyncio.sleep(0.5)  # Give it time to terminate
                    if process.returncode is None:
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
                
                memory_monitor_task.cancel()
                
                return (
                    ExecutionStatus.TIMEOUT,
                    "",
                    f"Execution timed out after {timeout} seconds",
                    timeout,
                    None
                )
                
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_file)
            except:
                pass
    
    @staticmethod
    def _set_limits(memory_limit_mb: int):
        """Set resource limits for the subprocess"""
        import resource
        
        # Set memory limit
        memory_bytes = memory_limit_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
        
        # Set CPU time limit (hard limit)
        resource.setrlimit(resource.RLIMIT_CPU, (300, 300))
        
        # Limit file descriptors
        resource.setrlimit(resource.RLIMIT_NOFILE, (50, 50))
        
        # Disable core dumps
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    
    @staticmethod
    async def _monitor_memory(pid: int, limit_mb: int) -> Optional[float]:
        """Monitor memory usage of a process"""
        max_memory = 0
        limit_bytes = limit_mb * 1024 * 1024
        
        try:
            process = psutil.Process(pid)
            while True:
                try:
                    memory_info = process.memory_info()
                    memory_mb = memory_info.rss / 1024 / 1024
                    max_memory = max(max_memory, memory_mb)
                    
                    # Kill if exceeds limit
                    if memory_info.rss > limit_bytes:
                        process.kill()
                        break
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    break
                
                await asyncio.sleep(0.1)
                
        except Exception:
            pass
        
        return max_memory if max_memory > 0 else None
```

### 7. app/main.py

```python
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import sys
from app.models import CodeRequest, ExecutionResponse, ExecutionStatus
from app.executor import CodeExecutor
from app.security import SecurityValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    logger.info("PyRunner service starting up...")
    # Pre-import commonly used modules to reduce cold start
    import numpy
    import sympy
    import pandas
    logger.info("Pre-loaded scientific libraries")
    yield
    logger.info("PyRunner service shutting down...")


app = FastAPI(
    title="PyRunner API",
    description="Fast Python execution backend with preinstalled scientific libraries",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "PyRunner",
        "status": "healthy",
        "version": "1.0.0",
        "capabilities": {
            "max_timeout": 300,
            "max_memory_mb": 2048,
            "libraries": ["sympy", "numpy", "pandas", "matplotlib", "scipy", "sklearn"]
        }
    }


@app.post("/run", response_model=ExecutionResponse)
async def run_code(request: CodeRequest):
    """Execute Python code and return results"""
    logger.info(f"Received code execution request (length: {len(request.code)} chars)")
    
    # Validate code for security
    is_valid, error_msg = SecurityValidator.validate_code(request.code)
    if not is_valid:
        logger.warning(f"Code validation failed: {error_msg}")
        return ExecutionResponse(
            status=ExecutionStatus.ERROR,
            stderr=f"Security validation failed: {error_msg}",
            execution_time=0.0,
            error=error_msg
        )
    
    # Execute code
    try:
        status, stdout, stderr, exec_time, memory_used = await CodeExecutor.execute(
            request.code,
            timeout=request.timeout,
            memory_limit=request.memory_limit
        )
        
        logger.info(f"Code execution completed: status={status}, time={exec_time:.3f}s")
        
        return ExecutionResponse(
            status=status,
            stdout=stdout,
            stderr=stderr,
            execution_time=round(exec_time, 3),
            memory_used=round(memory_used, 2) if memory_used else None,
            error=stderr if status == ExecutionStatus.ERROR else None
        )
        
    except Exception as e:
        logger.error(f"Unexpected error during code execution: {str(e)}")
        return ExecutionResponse(
            status=ExecutionStatus.ERROR,
            stderr=f"Internal error: {str(e)}",
            execution_time=0.0,
            error=str(e)
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )
```

### 8. docker-compose.yml

```yaml
version: '3.8'

services:
  pyrunner:
    build: .
    ports:
      - "8000:8000"
    environment:
      - PYTHONUNBUFFERED=1
      - PYTHONDONTWRITEBYTECODE=1
    restart: unless-stopped
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### 9. .dockerignore

```
**/__pycache__
**/*.pyc
**/*.pyo
**/*.pyd
.Python
pip-log.txt
pip-delete-this-directory.txt
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.log
.git
.gitignore
.mypy_cache
.pytest_cache
.hypothesis
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
examples/
README.md
docker-compose.yml
Dockerfile
```

### 10. examples/test_api.py

```python
import requests
import json
import time

# API endpoint
API_URL = "http://localhost:8000/run"

# Test cases
test_cases = [
    {
        "name": "Basic Math",
        "code": """
import math
print(f"Pi: {math.pi}")
print(f"Square root of 16: {math.sqrt(16)}")
print(f"2^10: {2**10}")
"""
    },
    {
        "name": "SymPy Example",
        "code": """
from sympy import symbols, expand, factor
x, y = symbols('x y')
expr = (x + y)**3
print(f"Expression: {expr}")
print(f"Expanded: {expand(expr)}")
print(f"Factored: {factor(x**3 - y**3)}")
"""
    },
    {
        "name": "NumPy Array Operations",
        "code": """
import numpy as np
arr = np.array([1, 2, 3, 4, 5])
print(f"Array: {arr}")
print(f"Mean: {arr.mean()}")
print(f"Standard deviation: {arr.std()}")
print(f"Cumulative sum: {arr.cumsum()}")
"""
    },
    {
        "name": "Error Handling",
        "code": """
# This will cause an error
print(1 / 0)
"""
    },
    {
        "name": "Timeout Test",
        "code": """
import time
print("Starting long computation...")
time.sleep(35)  # This will timeout
print("This won't be printed")
""",
        "timeout": 2
    },
    {
        "name": "Memory Test",
        "code": """
# Try to allocate large array
import numpy as np
print("Allocating memory...")
arr = np.zeros((1000, 1000, 100))  # ~800MB
print(f"Array shape: {arr.shape}")
""",
        "memory_limit": 256
    }
]

def test_api():
    """Test the PyRunner API with various code examples"""
    
    for test in test_cases:
        print(f"\n{'='*50}")
        print(f"Test: {test['name']}")
        print(f"{'='*50}")
        
        payload = {
            "code": test["code"],
            "timeout": test.get("timeout", 30),
            "memory_limit": test.get("memory_limit", 512)
        }
        
        start_time = time.time()
        
        try:
            response = requests.post(API_URL, json=payload)
            elapsed_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                print(f"Status: {result['status']}")
                print(f"Execution time: {result['execution_time']}s")
                print(f"API call time: {elapsed_time:.3f}s")
                
                if result.get('memory_used'):
                    print(f"Memory used: {result['memory_used']}MB")
                
                if result['stdout']:
                    print(f"\nOutput:\n{result['stdout']}")
                
                if result['stderr']:
                    print(f"\nErrors:\n{result['stderr']}")
            else:
                print(f"Error: HTTP {response.status_code}")
                print(response.text)
                
        except Exception as e:
            print(f"Request failed: {str(e)}")

if __name__ == "__main__":
    print("Testing PyRunner API...")
    print("Make sure the service is running on http://localhost:8000")
    input("Press Enter to start tests...")
    test_api()
```

### 11. examples/README.md

```markdown
# PyRunner API Examples

## Quick Start

1. Start the PyRunner service:
```bash
docker-compose up
```

2. Test the API:
```bash
python test_api.py
```

## API Usage

### Basic Example

```python
import requests

response = requests.post('http://localhost:8000/run', json={
    "code": "print('Hello, World!')",
    "timeout": 30,
    "memory_limit": 512
})

result = response.json()
print(result['stdout'])  # Hello, World!
```

### Using Scientific Libraries

```python
code = """
import sympy as sp
x = sp.Symbol('x')
equation = x**2 - 4
solutions = sp.solve(equation, x)
print(f"Solutions: {solutions}")
"""

response = requests.post('http://localhost:8000/run', json={"code": code})
```

### Error Handling

The API returns appropriate status codes:
- `success`: Code executed successfully
- `error`: Code execution failed (syntax error, runtime error, etc.)
- `timeout`: Execution exceeded time limit
- `memory_exceeded`: Execution exceeded memory limit

### Security

The API validates code before execution and blocks:
- Dangerous imports (os, subprocess, etc.)
- File system access
- Network operations
- Unsafe builtins (eval, exec, etc.)

Only whitelisted scientific computing libraries are allowed.

## Deployment

### Local Development
```bash
docker build -t pyrunner .
docker run -p 8000:8000 pyrunner
```

### Production Deployment

For production, consider:
1. Using a reverse proxy (nginx, traefik)
2. Implementing rate limiting
3. Adding authentication
4. Monitoring and logging
5. Horizontal scaling with load balancer

### Performance Optimization

The service is optimized for fast cold starts:
- Multi-stage Docker build for smaller images
- Pre-compiled Python files
- Pre-imported common libraries
- Uvloop for faster async operations
- Single worker process per container (scale horizontally)

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
```
```

## Key Features

1. **Fast Cold Starts**: 
   - Multi-stage Docker build reduces image size
   - Pre-compiled Python files
   - Pre-imported common libraries
   - Optimized base image (python:3.11-slim)

2. **Security**:
   - AST-based code validation
   - Whitelist of allowed modules
   - Resource limits (CPU, memory, file descriptors)
   - Non-root user execution
   - Process isolation with subprocess

3. **Performance Optimizations**:
   - Uvloop for faster async operations
   - Memory monitoring with early termination
   - Subprocess pooling possibility for future enhancement
   - Efficient resource cleanup

4. **API Features**:
   - RESTful JSON API
   - Configurable timeouts and memory limits
   - Detailed execution metrics
   - CORS support for web frontends
   - Health check endpoint

5. **Preinstalled Libraries**:
   - SymPy for symbolic mathematics
   - NumPy for numerical computing
   - Pandas for data analysis
   - Matplotlib for plotting
   - SciPy for scientific computing
   - Scikit-learn for machine learning

## Usage

1. Build and run with Docker Compose:
```bash
docker-compose up --build
```

2. Test the API:
```bash
curl -X POST http://localhost:8000/run \
  -H "Content-Type: application/json" \
  -d '{"code": "import sympy\nprint(sympy.pi)"}'
```

3. Run the test suite:
```bash
cd examples
python test_api.py
```

This implementation provides a secure, fast, and scalable Python execution backend suitable for educational platforms, online judges, or computational services.