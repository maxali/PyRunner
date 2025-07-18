# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Building and Running
```bash
# Build and start the service
cd pyrunner
docker-compose up --build

# Build Docker image only
docker build -t pyrunner .

# Run container directly
docker run -p 8000:8000 pyrunner

# Run in development mode (local Python)
cd pyrunner
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testing
```bash
# Run comprehensive API tests
cd pyrunner/examples
python test_api.py

# Test single endpoint
curl -X POST http://localhost:8000/run -H "Content-Type: application/json" -d '{"code": "print(\"Hello\")"}'

# Health check
curl http://localhost:8000/
```

## Architecture Overview

PyRunner is a containerized Python code execution service with three core architectural layers:

### Security Layer (`app/security.py`)
- **SecurityValidator**: AST-based code validation using whitelist approach
- **SecurityChecker**: Visitor pattern implementation that traverses AST nodes
- Blocks dangerous imports/builtins while allowing scientific libraries (numpy, sympy, pandas, etc.)
- Validates against file system access, network operations, and code injection attempts

### Execution Layer (`app/executor.py`)
- **CodeExecutor**: Manages isolated subprocess execution with resource limits
- Creates temporary files for code execution with automatic cleanup
- Implements concurrent memory monitoring with early termination
- Uses Unix resource limits (RLIMIT_AS, RLIMIT_CPU, RLIMIT_NOFILE)
- Process group management for reliable cleanup on timeout/memory exceeded

### API Layer (`app/main.py`)
- **FastAPI application** with two endpoints: health check (`/`) and code execution (`/run`)
- **Lifecycle management**: Pre-imports scientific libraries during startup for faster cold starts
- **Request flow**: Validation → Security Check → Execution → Response formatting
- **Error handling**: Comprehensive exception handling with structured error responses

### Data Models (`app/models.py`)
- **CodeRequest**: Input validation with timeout (1-300s) and memory limits (64-2048MB)
- **ExecutionResponse**: Structured output with status, stdout/stderr, execution metrics
- **ExecutionStatus**: Enum for success/error/timeout/memory_exceeded states

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

## Configuration

### Environment Variables
- `PYTHONUNBUFFERED=1`: Immediate stdout/stderr output
- `PYTHONDONTWRITEBYTECODE=1`: Prevents .pyc file creation

### Docker Resource Limits
- Memory: 512MB reserved, 2GB limit
- CPU: 0.5 cores reserved, 2 cores limit
- Health check: 30s interval, 10s timeout

### API Limits
- Code size: 1MB maximum
- Execution timeout: 1-300 seconds
- Memory limit: 64-2048MB per execution
- Allowed libraries: math, numpy, sympy, pandas, matplotlib, scipy, sklearn, etc.

## Debugging and Monitoring

### Logs
- Structured logging to stdout with timestamps
- Request/response logging with execution metrics
- Security validation warnings
- Error tracking with stack traces

### Health Monitoring
- Health check endpoint returns service capabilities
- Memory usage tracking per execution
- Execution time metrics
- Process monitoring with psutil

## Security Considerations

This service is designed for safe execution of untrusted Python code. Key security measures:

- Code validation before execution using AST parsing
- Subprocess isolation with resource limits
- No file system or network access
- Whitelist of allowed modules only
- Memory and CPU limits prevent DoS attacks
- Process cleanup prevents resource leaks