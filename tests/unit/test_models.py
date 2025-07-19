"""Unit tests for data models"""

import pytest
from pydantic import ValidationError

from app.models import CodeRequest, ExecutionResponse, ExecutionStatus


class TestCodeRequest:
    """Test cases for CodeRequest model"""
    
    @pytest.mark.unit
    def test_valid_code_request(self):
        """Test valid code request creation"""
        request = CodeRequest(
            code="print('hello')",
            timeout=30,
            memory_limit=512
        )
        
        assert request.code == "print('hello')"
        assert request.timeout == 30
        assert request.memory_limit == 512
    
    @pytest.mark.unit
    def test_default_values(self):
        """Test code request with default values"""
        request = CodeRequest(code="print('hello')")
        
        assert request.code == "print('hello')"
        assert request.timeout == 30
        assert request.memory_limit == 512
    
    @pytest.mark.unit
    def test_minimum_values(self):
        """Test code request with minimum allowed values"""
        request = CodeRequest(
            code="print('hello')",
            timeout=1,
            memory_limit=64
        )
        
        assert request.timeout == 1
        assert request.memory_limit == 64
    
    @pytest.mark.unit
    def test_maximum_values(self):
        """Test code request with maximum allowed values"""
        request = CodeRequest(
            code="print('hello')",
            timeout=300,
            memory_limit=2048
        )
        
        assert request.timeout == 300
        assert request.memory_limit == 2048
    
    @pytest.mark.unit
    def test_empty_code_validation(self):
        """Test code request with empty code is rejected"""
        with pytest.raises(ValidationError):
            CodeRequest(code="")
    
    @pytest.mark.unit
    def test_whitespace_code_validation(self):
        """Test code request with whitespace-only code is rejected"""
        with pytest.raises(ValidationError):
            CodeRequest(code="   \n  \t  ")
    
    @pytest.mark.unit
    def test_large_code(self):
        """Test code request with large code"""
        large_code = "print('hello')\n" * 1000
        request = CodeRequest(code=large_code)
        assert request.code == large_code
    
    @pytest.mark.unit
    def test_multiline_code(self):
        """Test code request with multiline code"""
        multiline_code = """
import math
import numpy as np

def calculate():
    result = math.pi * 2
    return result

print(calculate())
"""
        request = CodeRequest(code=multiline_code)
        assert request.code == multiline_code
    
    @pytest.mark.unit
    def test_invalid_timeout_zero(self):
        """Test code request with zero timeout"""
        with pytest.raises(ValidationError) as exc_info:
            CodeRequest(code="print('hello')", timeout=0)
        
        assert "Input should be greater than or equal to 1" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_invalid_timeout_negative(self):
        """Test code request with negative timeout"""
        with pytest.raises(ValidationError) as exc_info:
            CodeRequest(code="print('hello')", timeout=-1)
        
        assert "Input should be greater than or equal to 1" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_invalid_timeout_too_large(self):
        """Test code request with timeout too large"""
        with pytest.raises(ValidationError) as exc_info:
            CodeRequest(code="print('hello')", timeout=400)
        
        assert "Input should be less than or equal to 300" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_invalid_memory_limit_too_small(self):
        """Test code request with memory limit too small"""
        with pytest.raises(ValidationError) as exc_info:
            CodeRequest(code="print('hello')", memory_limit=32)
        
        assert "Input should be greater than or equal to 64" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_invalid_memory_limit_too_large(self):
        """Test code request with memory limit too large"""
        with pytest.raises(ValidationError) as exc_info:
            CodeRequest(code="print('hello')", memory_limit=4096)
        
        assert "Input should be less than or equal to 2048" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_invalid_memory_limit_zero(self):
        """Test code request with zero memory limit"""
        with pytest.raises(ValidationError) as exc_info:
            CodeRequest(code="print('hello')", memory_limit=0)
        
        assert "Input should be greater than or equal to 64" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_invalid_memory_limit_negative(self):
        """Test code request with negative memory limit"""
        with pytest.raises(ValidationError) as exc_info:
            CodeRequest(code="print('hello')", memory_limit=-100)
        
        assert "Input should be greater than or equal to 64" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_code_request_serialization(self):
        """Test code request serialization"""
        request = CodeRequest(
            code="print('hello')",
            timeout=60,
            memory_limit=1024
        )
        
        data = request.model_dump()
        assert data == {
            "code": "print('hello')",
            "timeout": 60,
            "memory_limit": 1024,
            "auto_print": True
        }
    
    @pytest.mark.unit
    def test_code_request_deserialization(self):
        """Test code request deserialization"""
        data = {
            "code": "print('hello')",
            "timeout": 60,
            "memory_limit": 1024
        }
        
        request = CodeRequest.model_validate(data)
        assert request.code == "print('hello')"
        assert request.timeout == 60
        assert request.memory_limit == 1024


class TestExecutionResponse:
    """Test cases for ExecutionResponse model"""
    
    @pytest.mark.unit
    def test_success_response(self):
        """Test successful execution response"""
        response = ExecutionResponse(
            status=ExecutionStatus.SUCCESS,
            stdout="Hello World\n",
            stderr="",
            execution_time=0.123,
            memory_used=1024 * 1024
        )
        
        assert response.status == ExecutionStatus.SUCCESS
        assert response.stdout == "Hello World\n"
        assert response.stderr == ""
        assert response.execution_time == 0.123
        assert response.memory_used == 1024 * 1024
        assert response.error is None
    
    @pytest.mark.unit
    def test_error_response(self):
        """Test error execution response"""
        response = ExecutionResponse(
            status=ExecutionStatus.ERROR,
            stdout="",
            stderr="ValueError: Test error\n",
            execution_time=0.050,
            memory_used=512 * 1024,
            error="Code execution failed"
        )
        
        assert response.status == ExecutionStatus.ERROR
        assert response.stdout == ""
        assert response.stderr == "ValueError: Test error\n"
        assert response.execution_time == 0.050
        assert response.memory_used == 512 * 1024
        assert response.error == "Code execution failed"
    
    @pytest.mark.unit
    def test_timeout_response(self):
        """Test timeout execution response"""
        response = ExecutionResponse(
            status=ExecutionStatus.TIMEOUT,
            stdout="",
            stderr="",
            execution_time=5.0,
            memory_used=2048 * 1024,
            error="Execution timed out"
        )
        
        assert response.status == ExecutionStatus.TIMEOUT
        assert response.execution_time == 5.0
        assert response.error == "Execution timed out"
    
    @pytest.mark.unit
    def test_memory_exceeded_response(self):
        """Test memory exceeded execution response"""
        response = ExecutionResponse(
            status=ExecutionStatus.MEMORY_EXCEEDED,
            stdout="",
            stderr="",
            execution_time=1.5,
            memory_used=1024 * 1024 * 1024,  # 1GB
            error="Memory limit exceeded"
        )
        
        assert response.status == ExecutionStatus.MEMORY_EXCEEDED
        assert response.memory_used == 1024 * 1024 * 1024
        assert response.error == "Memory limit exceeded"
    
    @pytest.mark.unit
    def test_response_with_optional_fields(self):
        """Test response with optional fields"""
        response = ExecutionResponse(
            status=ExecutionStatus.SUCCESS,
            stdout="Result: 42\n",
            stderr="Warning: deprecated function\n",
            execution_time=0.789,
            memory_used=256 * 1024
        )
        
        assert response.status == ExecutionStatus.SUCCESS
        assert response.stdout == "Result: 42\n"
        assert response.stderr == "Warning: deprecated function\n"
        assert response.execution_time == 0.789
        assert response.memory_used == 256 * 1024
        assert response.error is None
    
    @pytest.mark.unit
    def test_response_serialization(self):
        """Test response serialization"""
        response = ExecutionResponse(
            status=ExecutionStatus.SUCCESS,
            stdout="Hello World\n",
            stderr="",
            execution_time=0.123,
            memory_used=1024 * 1024
        )
        
        data = response.model_dump()
        expected = {
            "status": "success",
            "stdout": "Hello World\n",
            "stderr": "",
            "execution_time": 0.123,
            "memory_used": 1024 * 1024,
            "error": None
        }
        assert data == expected
    
    @pytest.mark.unit
    def test_response_deserialization(self):
        """Test response deserialization"""
        data = {
            "status": "success",
            "stdout": "Hello World\n",
            "stderr": "",
            "execution_time": 0.123,
            "memory_used": 1024 * 1024,
            "error": None
        }
        
        response = ExecutionResponse.model_validate(data)
        assert response.status == ExecutionStatus.SUCCESS
        assert response.stdout == "Hello World\n"
        assert response.stderr == ""
        assert response.execution_time == 0.123
        assert response.memory_used == 1024 * 1024
        assert response.error is None
    
    @pytest.mark.unit
    def test_response_with_unicode(self):
        """Test response with unicode characters"""
        response = ExecutionResponse(
            status=ExecutionStatus.SUCCESS,
            stdout="Hello 世界! 🌍\n",
            stderr="",
            execution_time=0.1,
            memory_used=1024
        )
        
        assert response.stdout == "Hello 世界! 🌍\n"
        
        # Test serialization/deserialization with unicode
        data = response.model_dump()
        deserialized = ExecutionResponse.model_validate(data)
        assert deserialized.stdout == "Hello 世界! 🌍\n"
    
    @pytest.mark.unit
    def test_response_with_long_output(self):
        """Test response with long output"""
        long_output = ("Line {}\n".format(i) for i in range(1000))
        long_output_str = "".join(long_output)
        
        response = ExecutionResponse(
            status=ExecutionStatus.SUCCESS,
            stdout=long_output_str,
            stderr="",
            execution_time=2.5,
            memory_used=10 * 1024 * 1024
        )
        
        assert len(response.stdout) > 8000  # Should be quite long
        assert response.stdout.startswith("Line 0\n")
        assert response.stdout.endswith("Line 999\n")


class TestExecutionStatus:
    """Test cases for ExecutionStatus enum"""
    
    @pytest.mark.unit
    def test_status_values(self):
        """Test execution status enum values"""
        assert ExecutionStatus.SUCCESS == "success"
        assert ExecutionStatus.ERROR == "error"
        assert ExecutionStatus.TIMEOUT == "timeout"
        assert ExecutionStatus.MEMORY_EXCEEDED == "memory_exceeded"
    
    @pytest.mark.unit
    def test_status_from_string(self):
        """Test creating status from string"""
        assert ExecutionStatus("success") == ExecutionStatus.SUCCESS
        assert ExecutionStatus("error") == ExecutionStatus.ERROR
        assert ExecutionStatus("timeout") == ExecutionStatus.TIMEOUT
        assert ExecutionStatus("memory_exceeded") == ExecutionStatus.MEMORY_EXCEEDED
    
    @pytest.mark.unit
    def test_status_serialization(self):
        """Test status serialization in response"""
        response = ExecutionResponse(
            status=ExecutionStatus.SUCCESS,
            stdout="test",
            stderr="",
            execution_time=0.1,
            memory_used=1024
        )
        
        data = response.model_dump()
        assert data["status"] == "success"
    
    @pytest.mark.unit
    def test_all_status_values(self):
        """Test all status values are accounted for"""
        expected_statuses = {"success", "error", "timeout", "memory_exceeded"}
        actual_statuses = {status.value for status in ExecutionStatus}
        
        assert actual_statuses == expected_statuses