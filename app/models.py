from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Dict, Any
from enum import Enum


class ExecutionStatus(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
    MEMORY_EXCEEDED = "memory_exceeded"


class CodeRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    
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
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        if not v.strip():
            raise ValueError("Code cannot be empty")
        if len(v) > 1_000_000:  # 1MB limit
            raise ValueError("Code too large (max 1MB)")
        return v


class ExecutionResponse(BaseModel):
    model_config = ConfigDict(
        extra='forbid',
        json_schema_extra = {
            "example": {
                "status": "success",
                "stdout": "Hello, World!\n",
                "stderr": "",
                "execution_time": 0.023,
                "memory_used": 45.2
            }
        }
    )
    
    status: ExecutionStatus
    stdout: str = ""
    stderr: str = ""
    execution_time: float = Field(..., description="Execution time in seconds")
    memory_used: Optional[float] = Field(None, description="Memory used in MB")
    error: Optional[str] = None