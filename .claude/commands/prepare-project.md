**System Goal:**  
Design a Python execution backend service that:
- Receives arbitrary Python code via an API
- Runs that code in an isolated, ephemeral session
- Returns the result (or error)
- Supports preinstalled packages like `sympy`
- Is containerized for security and portability
- Prioritizes fast cold starts and execution time

**Constraints:**
- Use Docker as the isolation environment
- API must support stateless POST requests (each call runs independently)
- Preinstall key libraries like `sympy`, `numpy`, etc.
- Container should terminate or reset state after code execution
- Avoid long container startup times (optimize for speed)
- Must prevent infinite loops and malicious code (basic sandboxing)
- Must be easy to deploy locally or on a cloud platform

**Tasks:**
1. Read the <sample_implementation> and analyse it.
2. Write Implementation plan and step by step tasks.
3. Save the plan and the tasks in .claude/commands/implementation-plan.md file.
4. Provide a summary.


Fast, Sandbox-Style Python Execution Service

<sample_implementation>
NOTE: This is suggestion only.
PLease review and take inspirations.
Change any architecture as you see fit.

The image is based on python:3.11-slim, installs only sympy + essential runtime wheels, strips caches, and ends around 46 MB.
Security measures include resource limits (CPU, RSS, file-size), subprocess isolation via -I (isolated mode), a seccomp profile blocking networking, and a five-second watchdog. Cold start on a t4g.small averages ~320 ms; null snippet calls return in ≈12 ms.

⸻

Dockerfile

# -------- build stage --------
FROM python:3.11-slim AS build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip wheel --no-cache-dir -r requirements.txt -w /tmp/wheels

COPY . .

# -------- runtime stage --------
FROM python:3.11-slim

# minimal core utils for proc / seccomp
RUN apt-get update -qq \
 && apt-get install -y --no-install-recommends libseccomp2 ca-certificates tini \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=build /tmp/wheels /tmp/wheels
RUN pip install --no-cache-dir /tmp/wheels/* \
 && rm -rf /tmp/wheels

COPY --from=build /app /app

# Default seccomp profile (no network syscalls, no mount)
COPY seccomp_profile.json /app/seccomp_profile.json
ENTRYPOINT ["/usr/bin/tini","--"]

# uvicorn with one worker; busy-loop prevention via --limit-concurrency 1
CMD ["uvicorn","main:app","--host","0.0.0.0","--port","8000","--workers","1","--timeout-keep-alive","5"]


⸻

requirements.txt

fastapi==0.111.0
uvicorn==0.30.1
sympy==1.12


⸻

utils.py

import os, resource, signal, json, subprocess, tempfile, time, uuid, pathlib

CPU_TIME_SEC = 5          # hard wall
MEM_LIMIT_MB = 256        # address space
FILE_SIZE_MB = 1          # disallow large writes

SECURE_BUILTINS = {
    "__builtins__": {
        name: __builtins__[name]
        for name in ("abs", "bool", "complex", "dict", "float", "int", "len",
                     "list", "max", "min", "pow", "range", "set", "str", "tuple",
                     "print", "enumerate", "zip", "map", "filter", "sum")
    }
}

def _set_limits():
    # CPU / wall
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_TIME_SEC, CPU_TIME_SEC))
    # Addr space
    mem_bytes = MEM_LIMIT_MB * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
    # File size
    fsz = FILE_SIZE_MB * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_FSIZE, (fsz, fsz))

def run_snippet(code: str):
    """
    Executes code in a restricted subprocess; returns (stdout, stderr, ms).
    """
    uid = uuid.uuid4().hex
    src_path = pathlib.Path(tempfile.gettempdir()) / f"{uid}.py"
    src_path.write_text(code, encoding="utf-8")

    cmd = ["python", "-I", str(src_path)]  # -I = isolated: no PYTHON* env, no site
    start = time.perf_counter()

    proc = subprocess.Popen(
        cmd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=_set_limits,
        text=True
    )

    try:
        out, err = proc.communicate(timeout=CPU_TIME_SEC + 1)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, err = "", "Execution timed out after 5 s."
    finally:
        src_path.unlink(missing_ok=True)

    elapsed = int((time.perf_counter() - start) * 1000)
    return out, err, elapsed


⸻

main.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from utils import run_snippet

app = FastAPI(title="Sandboxed Python Runner", version="1.0")

class CodeRequest(BaseModel):
    code: str

class CodeResponse(BaseModel):
    stdout: str
    stderr: str
    exec_time_ms: int

@app.post("/run", response_model=CodeResponse)
def run_code(req: CodeRequest):
    if len(req.code) > 20_000:
        raise HTTPException(status_code=413, detail="Code too large (max 20 KB)")
    out, err, ms = run_snippet(req.code)
    return CodeResponse(stdout=out, stderr=err, exec_time_ms=ms)


⸻

seccomp_profile.json

{
  "defaultAction": "SCMP_ACT_ALLOW",
  "archMap": [{ "architecture": "SCMP_ARCH_X86_64", "subArchitectures": [] }],
  "syscalls": [
    { "names": ["socket", "connect", "accept", "sendto", "recvfrom", "sendmsg",
                "recvmsg", "bind", "listen", "getsockname", "getpeername",
                "shutdown"], "action": "SCMP_ACT_ERRNO" }
  ]
}


⸻

README.md

# Sandboxed Python Runner

## Quick Start
```bash
# Build (≈46 MB)
docker build -t py-runner .
# Launch
docker run -p 8000:8000 py-runner

Example

curl -X POST http://localhost:8000/run \
     -H "Content-Type: application/json" \
     -d '{"code": "import sympy as sp\nprint(sp.factorial(20))"}'

{
  "stdout": "2432902008176640000\n",
  "stderr": "",
  "exec_time_ms": 14
}

Architecture
	•	FastAPI + Uvicorn → low-latency REST & auto-docs.
	•	Subprocess isolation (python -I) + resource limits + seccomp profile forbid networking & large writes.
	•	Lightweight base (python:3.11-slim) keeps image <50 MB.
	•	tini as PID 1 for proper signal handling.

Hardening Tips
	•	Consider an unprivileged user (USER 1001) and --read-only Docker flag.
	•	Mount /tmp as tmpfs to guarantee in-memory execution.
	•	Rotate seccomp/SELinux profiles for stricter syscall allow-lists.

Benchmarks (t4g.small, 1 vCPU)

Snippet	Mean (ms)	p95 (ms)
pass	12	16
sympy.factorint(10**10)	37	43

All runs include process spawn & JSON serialization.

---

*(Feel free to extend caching or tune limits; the skeleton is production-grade and passes all listed functional targets.)*

<sample_implementation>