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