#!/usr/bin/env python3
"""
Test script to verify the executor fix works
"""
import asyncio
import sys
import os
sys.path.append('/Users/gbmoalab/git/PyRunner')

from app.executor import CodeExecutor
from app.models import ExecutionStatus

async def test_basic_execution():
    """Test basic code execution"""
    print("Testing basic code execution...")
    
    code = 'print("Hello, World!")'
    status, stdout, stderr, exec_time, memory = await CodeExecutor.execute(code, timeout=10, memory_limit=128)
    
    print(f"Status: {status}")
    print(f"Stdout: {repr(stdout)}")
    print(f"Stderr: {repr(stderr)}")
    print(f"Execution time: {exec_time:.3f}s")
    print(f"Memory used: {memory}MB")
    
    if status == ExecutionStatus.SUCCESS and "Hello, World!" in stdout:
        print("✓ Basic execution test PASSED")
        return True
    else:
        print("✗ Basic execution test FAILED")
        return False

async def test_math_execution():
    """Test mathematical operations"""
    print("\nTesting mathematical operations...")
    
    code = '''
import math
result = math.sqrt(16) + math.pi
print(f"Result: {result}")
'''
    
    status, stdout, stderr, exec_time, memory = await CodeExecutor.execute(code, timeout=10, memory_limit=128)
    
    print(f"Status: {status}")
    print(f"Stdout: {repr(stdout)}")
    print(f"Stderr: {repr(stderr)}")
    
    if status == ExecutionStatus.SUCCESS and "Result:" in stdout:
        print("✓ Math execution test PASSED")
        return True
    else:
        print("✗ Math execution test FAILED")
        return False

async def test_error_handling():
    """Test error handling"""
    print("\nTesting error handling...")
    
    code = '''
print("Before error")
raise ValueError("Test error")
print("After error")
'''
    
    status, stdout, stderr, exec_time, memory = await CodeExecutor.execute(code, timeout=10, memory_limit=128)
    
    print(f"Status: {status}")
    print(f"Stdout: {repr(stdout)}")
    print(f"Stderr: {repr(stderr)}")
    
    if status == ExecutionStatus.ERROR and "Before error" in stdout and "ValueError" in stderr:
        print("✓ Error handling test PASSED")
        return True
    else:
        print("✗ Error handling test FAILED")
        return False

async def test_timeout():
    """Test timeout handling"""
    print("\nTesting timeout handling...")
    
    code = '''
import time
print("Starting sleep")
time.sleep(10)
print("Should not reach here")
'''
    
    status, stdout, stderr, exec_time, memory = await CodeExecutor.execute(code, timeout=2, memory_limit=128)
    
    print(f"Status: {status}")
    print(f"Stdout: {repr(stdout)}")
    print(f"Stderr: {repr(stderr)}")
    print(f"Execution time: {exec_time:.3f}s")
    
    if status == ExecutionStatus.TIMEOUT and exec_time >= 2:
        print("✓ Timeout test PASSED")
        return True
    else:
        print("✗ Timeout test FAILED")
        return False

async def run_all_tests():
    """Run all tests"""
    print("PyRunner Executor Fix Verification")
    print("=" * 50)
    
    tests = [
        test_basic_execution,
        test_math_execution,
        test_error_handling,
        test_timeout
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if await test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests PASSED! Executor is working correctly.")
        return True
    else:
        print("✗ Some tests FAILED. Need further investigation.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)