# PyRunner Testing and Debugging Plan
Your task is to debug, test and fix all the issues. Follow this document.

## Current Status
- ✅ Service starts successfully
- ✅ Health endpoint responds correctly
- ✅ API structure and routing working
- ✅ Security validation working (correctly blocks dangerous imports)
- ❌ Code execution fails with "Exception occurred in preexec_fn" error

## Critical Issues to Debug

### 1. Primary Issue: preexec_fn Error
**Problem**: All code execution attempts fail with "Exception occurred in preexec_fn"
**Location**: `app/executor.py` - subprocess resource limit setup
**Priority**: CRITICAL

#### Investigation Steps:
1. **Check resource limits compatibility**:
   - Verify `resource.setrlimit()` calls are valid for macOS
   - Test individual resource limits (RLIMIT_AS, RLIMIT_CPU, RLIMIT_NOFILE)
   - Check if limits are within system bounds

2. **Debug preexec_fn function**:
   - Add logging to preexec_fn to identify exact failure point
   - Test preexec_fn independently outside subprocess
   - Validate process group creation (`os.setpgrp()`)

3. **Platform-specific issues**:
   - macOS vs Linux resource limit differences
   - Docker vs native execution environment differences

### 2. Security Validation Testing

#### Current Status:
- ✅ Blocks dangerous imports (tested with 'time' module)
- ✅ AST parsing working
- ❌ Whitelist validation needs verification

#### Testing Plan:
1. **Allowed modules test**:
   ```python
   # Test each allowed module
   test_cases = [
       "import math; print(math.pi)",
       "import numpy; print(numpy.array([1,2,3]))",
       "import sympy; print(sympy.symbols('x'))",
       "import pandas; print(pandas.__version__)"
   ]
   ```

2. **Blocked modules test**:
   ```python
   # Should fail security validation
   blocked_cases = [
       "import os; print(os.getcwd())",
       "import subprocess; subprocess.run(['ls'])",
       "import sys; print(sys.path)"
   ]
   ```

3. **Edge cases**:
   - Dynamic imports: `__import__('os')`
   - Nested imports: `from os import path`
   - Aliased imports: `import os as operating_system`

### 3. Memory and Resource Management

#### Testing Requirements:
1. **Memory limit enforcement**:
   - Test with small memory limits (64MB)
   - Test with memory-intensive operations
   - Verify memory monitoring accuracy

2. **CPU timeout enforcement**:
   - Test with infinite loops
   - Test with CPU-intensive operations
   - Verify timeout accuracy

3. **Process cleanup**:
   - Test process group termination
   - Verify no zombie processes
   - Test concurrent execution limits

### 4. API Integration Testing

#### Test Cases:
1. **Valid requests**:
   - Simple print statements
   - Mathematical calculations
   - Scientific library usage
   - Error handling in user code

2. **Invalid requests**:
   - Malformed JSON
   - Invalid timeout values
   - Invalid memory limits
   - Code size limits

3. **Edge cases**:
   - Empty code
   - Very large code
   - Unicode characters
   - Special characters in output

## Debugging Methodology

### Phase 1: Isolate preexec_fn Issue
1. **Create minimal test**:
   ```python
   import subprocess
   import resource
   import os
   
   def test_preexec():
       try:
           os.setpgrp()
           resource.setrlimit(resource.RLIMIT_AS, (64 * 1024 * 1024, 64 * 1024 * 1024))
           resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
           resource.setrlimit(resource.RLIMIT_NOFILE, (50, 50))
           print("preexec_fn succeeded")
       except Exception as e:
           print(f"preexec_fn failed: {e}")
   
   # Test outside subprocess
   test_preexec()
   
   # Test in subprocess
   subprocess.run(['python', '-c', 'print("test")'], preexec_fn=test_preexec)
   ```

2. **Check system limits**:
   ```bash
   ulimit -a  # Check current limits
   sysctl -a | grep kern.maxproc  # Check process limits
   ```

### Phase 2: Fix Resource Limits
1. **Implement fallback resource limits**:
   - Detect platform capabilities
   - Use safe defaults if limits fail
   - Add comprehensive error handling

2. **Test incremental fixes**:
   - Test each resource limit individually
   - Verify subprocess execution works
   - Validate memory monitoring

### Phase 3: Comprehensive Testing
1. **Security validation**:
   - Test all allowed modules
   - Test all blocked modules
   - Test edge cases

2. **Performance testing**:
   - Test concurrent requests
   - Test memory usage
   - Test timeout accuracy

3. **Integration testing**:
   - End-to-end API tests
   - Docker container tests
   - Production-like scenarios

## Implementation Steps

### Step 1: Debug preexec_fn (HIGH PRIORITY)
- [ ] Add detailed logging to executor.py
- [ ] Test resource limits individually
- [ ] Implement platform-specific fixes
- [ ] Test minimal subprocess execution

### Step 2: Validate Security Layer
- [ ] Test all allowed modules
- [ ] Test blocked modules
- [ ] Test edge cases and bypass attempts
- [ ] Verify whitelist is complete

### Step 3: Resource Management
- [ ] Test memory limits
- [ ] Test CPU timeouts
- [ ] Test process cleanup
- [ ] Test concurrent execution

### Step 4: API Testing
- [ ] Test valid requests
- [ ] Test invalid requests
- [ ] Test error handling
- [ ] Test edge cases

### Step 5: Integration Testing
- [ ] End-to-end testing
- [ ] Docker testing
- [ ] Performance testing
- [ ] Security testing

## Expected Outcomes

### Success Criteria:
1. **Code execution works**: Simple print statements execute successfully
2. **Security validation works**: Dangerous code is blocked, safe code is allowed
3. **Resource limits work**: Memory and CPU limits are enforced
4. **API responds correctly**: All endpoints return proper JSON responses
5. **Error handling works**: Graceful handling of all error conditions

### Performance Targets:
- **Cold start time**: < 2 seconds
- **Execution time**: < 1 second for simple operations
- **Memory usage**: < 512MB base usage
- **Concurrent requests**: Handle 10+ concurrent requests

## Tools and Resources

### Debugging Tools:
- **Process monitoring**: `ps`, `top`, `htop`
- **Memory monitoring**: `valgrind`, `memory_profiler`
- **Network testing**: `curl`, `httpie`
- **Load testing**: `ab`, `wrk`

### Testing Frameworks:
- **API testing**: `requests`, `pytest`
- **Security testing**: Custom AST validation
- **Performance testing**: `time`, `memory_profiler`

### Logging Strategy:
- **Structured logging**: JSON format with timestamps
- **Log levels**: DEBUG for development, INFO for production
- **Log locations**: stdout for containers, files for debugging

## Risk Mitigation

### Security Risks:
- **Code injection**: Validate all inputs
- **Resource exhaustion**: Enforce strict limits
- **Privilege escalation**: Run with minimal permissions

### Performance Risks:
- **Memory leaks**: Monitor memory usage
- **CPU exhaustion**: Enforce timeouts
- **Disk usage**: Clean up temporary files

### Operational Risks:
- **Service unavailability**: Health checks and monitoring
- **Configuration errors**: Validate all settings
- **Dependency issues**: Pin versions and test upgrades

This plan provides a systematic approach to debugging and testing the PyRunner service, with focus on resolving the critical preexec_fn error and ensuring robust operation.