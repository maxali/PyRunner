"""Unit tests for security validation"""

import pytest
import ast
from unittest.mock import patch, MagicMock

from app.security import SecurityValidator, SecurityChecker
from app.models import CodeRequest


class TestSecurityValidator:
    """Test cases for SecurityValidator class"""
    
    def test_init(self):
        """Test SecurityValidator initialization"""
        validator = SecurityValidator()
        assert validator is not None
        assert hasattr(validator, 'validate_code')
    
    @pytest.mark.unit
    def test_validate_allowed_import(self):
        """Test validation of allowed imports"""
        allowed_codes = [
            "import math",
            "import numpy as np",
            "from collections import Counter",
            "import itertools, functools",
        ]
        
        for code in allowed_codes:
            is_valid, error_message = SecurityValidator.validate_code(code)
            assert is_valid, f"Code should be valid: {code}"
            assert error_message == ""
    
    @pytest.mark.unit
    def test_validate_blocked_import(self):
        """Test validation of blocked imports"""
        blocked_codes = [
            "import os",
            "import subprocess",
            "import sys",
            "from os import path",
            "import socket",
        ]
        
        for code in blocked_codes:
            is_valid, error_message = SecurityValidator.validate_code(code)
            assert not is_valid, f"Code should be blocked: {code}"
            assert error_message != ""
    
    @pytest.mark.unit
    def test_validate_builtin_functions(self):
        """Test validation of dangerous builtin functions"""
        dangerous_codes = [
            "__import__('os')",
            "exec('print(1)')",
            "eval('1+1')",
            "compile('1+1', '<string>', 'eval')",
            "getattr(builtins, '__import__')",
            "open('file.txt')",
            "input('Enter: ')",
        ]
        
        for code in dangerous_codes:
            is_valid, error_message = SecurityValidator.validate_code(code)
            assert not is_valid, f"Code should be blocked: {code}"
            assert error_message != ""
    
    @pytest.mark.unit
    def test_validate_complex_expressions(self):
        """Test validation of complex expressions"""
        # Valid complex code
        valid_code = """
import math
import numpy as np

def calculate_pi():
    return math.pi

arr = np.array([1, 2, 3])
result = np.sum(arr) + calculate_pi()
print(f'Result: {result}')
"""
        is_valid, error_message = SecurityValidator.validate_code(valid_code)
        assert is_valid
        assert error_message == ""
    
    @pytest.mark.unit
    def test_validate_nested_security_violation(self):
        """Test validation of nested security violations"""
        # Nested violation
        nested_code = """
def malicious_function():
    import os
    return os.getcwd()

result = malicious_function()
print(result)
"""
        is_valid, error_message = SecurityValidator.validate_code(nested_code)
        assert not is_valid
        assert "os" in error_message.lower()
    
    @pytest.mark.unit
    def test_validate_syntax_error(self):
        """Test validation of code with syntax errors"""
        invalid_syntax = "print('hello world'"  # Missing closing parenthesis
        is_valid, error_message = SecurityValidator.validate_code(invalid_syntax)
        assert not is_valid
        assert "syntax" in error_message.lower()
    
    @pytest.mark.unit
    def test_validate_empty_code(self):
        """Test validation of empty code"""
        is_valid, error_message = SecurityValidator.validate_code("")
        assert is_valid
        assert error_message == ""
    
    @pytest.mark.unit
    def test_validate_whitespace_only(self):
        """Test validation of whitespace-only code"""
        is_valid, error_message = SecurityValidator.validate_code("   \n  \t  ")
        assert is_valid
        assert error_message == ""


class TestSecurityChecker:
    """Test cases for SecurityChecker class"""
    
    def test_init(self):
        """Test SecurityChecker initialization"""
        checker = SecurityChecker(
            SecurityValidator.DANGEROUS_IMPORTS,
            SecurityValidator.DANGEROUS_BUILTINS,
            SecurityValidator.ALLOWED_MODULES
        )
        assert checker is not None
        assert hasattr(checker, 'visit')
    
    @pytest.mark.unit
    def test_visit_import(self):
        """Test visiting import nodes"""
        from app.security import SecurityError
        
        checker = SecurityChecker(
            SecurityValidator.DANGEROUS_IMPORTS,
            SecurityValidator.DANGEROUS_BUILTINS,
            SecurityValidator.ALLOWED_MODULES
        )
        
        # Test allowed import
        allowed_import = ast.parse("import math").body[0]
        checker.visit(allowed_import)  # Should not raise exception
        
        # Test blocked import
        checker = SecurityChecker(
            SecurityValidator.DANGEROUS_IMPORTS,
            SecurityValidator.DANGEROUS_BUILTINS,
            SecurityValidator.ALLOWED_MODULES
        )
        blocked_import = ast.parse("import os").body[0]
        with pytest.raises(SecurityError) as exc_info:
            checker.visit(blocked_import)
        assert "os" in str(exc_info.value).lower()
    
    @pytest.mark.unit
    def test_visit_importfrom(self):
        """Test visiting import from nodes"""
        from app.security import SecurityError
        
        checker = SecurityChecker(
            SecurityValidator.DANGEROUS_IMPORTS,
            SecurityValidator.DANGEROUS_BUILTINS,
            SecurityValidator.ALLOWED_MODULES
        )
        
        # Test allowed import from
        allowed_import = ast.parse("from math import pi").body[0]
        checker.visit(allowed_import)  # Should not raise exception
        
        # Test blocked import from
        checker = SecurityChecker(
            SecurityValidator.DANGEROUS_IMPORTS,
            SecurityValidator.DANGEROUS_BUILTINS,
            SecurityValidator.ALLOWED_MODULES
        )
        blocked_import = ast.parse("from os import path").body[0]
        with pytest.raises(SecurityError) as exc_info:
            checker.visit(blocked_import)
        assert "os" in str(exc_info.value).lower()
    
    @pytest.mark.unit
    def test_visit_call(self):
        """Test visiting call nodes"""
        from app.security import SecurityError
        
        checker = SecurityChecker(
            SecurityValidator.DANGEROUS_IMPORTS,
            SecurityValidator.DANGEROUS_BUILTINS,
            SecurityValidator.ALLOWED_MODULES
        )
        
        # Test allowed function call
        allowed_call = ast.parse("print('hello')").body[0]
        checker.visit(allowed_call)  # Should not raise exception
        
        # Test blocked function call
        checker = SecurityChecker(
            SecurityValidator.DANGEROUS_IMPORTS,
            SecurityValidator.DANGEROUS_BUILTINS,
            SecurityValidator.ALLOWED_MODULES
        )
        blocked_call = ast.parse("__import__('os')").body[0]
        with pytest.raises(SecurityError) as exc_info:
            checker.visit(blocked_call)
        assert "__import__" in str(exc_info.value).lower()
    
    @pytest.mark.unit
    def test_visit_attribute(self):
        """Test visiting attribute nodes"""
        from app.security import SecurityError
        
        checker = SecurityChecker(
            SecurityValidator.DANGEROUS_IMPORTS,
            SecurityValidator.DANGEROUS_BUILTINS,
            SecurityValidator.ALLOWED_MODULES
        )
        
        # Test allowed attribute access
        allowed_attr = ast.parse("math.pi").body[0]
        checker.visit(allowed_attr)  # Should not raise exception
        
        # Test blocked attribute access
        checker = SecurityChecker(
            SecurityValidator.DANGEROUS_IMPORTS,
            SecurityValidator.DANGEROUS_BUILTINS,
            SecurityValidator.ALLOWED_MODULES
        )
        blocked_attr = ast.parse("obj.__globals__").body[0]
        with pytest.raises(SecurityError) as exc_info:
            checker.visit(blocked_attr)
        assert "__globals__" in str(exc_info.value).lower()
    
    @pytest.mark.unit
    def test_multiple_violations(self):
        """Test detection of multiple security violations"""
        from app.security import SecurityError
        
        checker = SecurityChecker(
            SecurityValidator.DANGEROUS_IMPORTS,
            SecurityValidator.DANGEROUS_BUILTINS,
            SecurityValidator.ALLOWED_MODULES
        )
        
        code_with_violations = """
import os
import subprocess
exec('print(1)')
"""
        tree = ast.parse(code_with_violations)
        # Should raise on first violation
        with pytest.raises(SecurityError) as exc_info:
            checker.visit(tree)
        assert "os" in str(exc_info.value).lower()
    
    @pytest.mark.unit
    def test_complex_nested_violations(self):
        """Test detection of violations in complex nested structures"""
        from app.security import SecurityError
        
        checker = SecurityChecker(
            SecurityValidator.DANGEROUS_IMPORTS,
            SecurityValidator.DANGEROUS_BUILTINS,
            SecurityValidator.ALLOWED_MODULES
        )
        
        nested_code = """
def outer_function():
    def inner_function():
        import os
        return os.getcwd()
    return inner_function()

class TestClass:
    def method(self):
        exec('import sys')
        return sys.path

result = outer_function()
test = TestClass()
path = test.method()
"""
        tree = ast.parse(nested_code)
        # Should raise on first violation
        with pytest.raises(SecurityError) as exc_info:
            checker.visit(tree)
        assert "os" in str(exc_info.value).lower()


class TestCodeRequestValidation:
    """Test cases for CodeRequest model validation"""
    
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
        assert request.timeout == 30  # Default timeout
        assert request.memory_limit == 512  # Default memory limit
    
    @pytest.mark.unit
    def test_invalid_timeout(self):
        """Test code request with invalid timeout"""
        with pytest.raises(ValueError):
            CodeRequest(code="print('hello')", timeout=0)
        
        with pytest.raises(ValueError):
            CodeRequest(code="print('hello')", timeout=400)
    
    @pytest.mark.unit
    def test_invalid_memory_limit(self):
        """Test code request with invalid memory limit"""
        with pytest.raises(ValueError):
            CodeRequest(code="print('hello')", memory_limit=32)
        
        with pytest.raises(ValueError):
            CodeRequest(code="print('hello')", memory_limit=4096)
    
    @pytest.mark.unit
    def test_empty_code(self):
        """Test code request with empty code"""
        from pydantic import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            CodeRequest(code="")
        assert "Code cannot be empty" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_large_code(self):
        """Test code request with large code"""
        large_code = "print('hello')\n" * 10000
        request = CodeRequest(code=large_code)
        assert request.code == large_code