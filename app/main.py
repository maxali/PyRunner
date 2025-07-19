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
    """Root endpoint with service info"""
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


@app.get("/health")
async def health():
    """Health check endpoint for Container Apps"""
    return {"status": "healthy"}


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
            memory_limit=request.memory_limit,
            auto_print=request.auto_print
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