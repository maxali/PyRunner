#!/usr/bin/env python3
"""
Debug script to identify the preexec_fn issue in executor.py
"""
import subprocess
import resource
import os
import sys
import tempfile

def test_preexec_fn(memory_limit_mb=64):
    """Test the preexec_fn function to identify the failing component"""
    print(f"Testing preexec_fn with memory limit: {memory_limit_mb}MB")
    
    def preexec_fn():
        """Replicated preexec_fn from executor.py"""
        print("Starting preexec_fn...")
        
        try:
            # Test process group creation
            print("Setting process group...")
            os.setpgrp()
            print("✓ Process group set successfully")
            
            # Test memory limit
            print("Setting memory limit...")
            memory_bytes = memory_limit_mb * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
            print(f"✓ Memory limit set to {memory_bytes} bytes")
            
            # Test CPU time limit
            print("Setting CPU time limit...")
            resource.setrlimit(resource.RLIMIT_CPU, (300, 300))
            print("✓ CPU time limit set to 300 seconds")
            
            # Test file descriptor limit
            print("Setting file descriptor limit...")
            resource.setrlimit(resource.RLIMIT_NOFILE, (50, 50))
            print("✓ File descriptor limit set to 50")
            
            # Test core dump limit
            print("Setting core dump limit...")
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            print("✓ Core dump limit set to 0")
            
            print("All preexec_fn operations completed successfully!")
            
        except Exception as e:
            print(f"✗ preexec_fn failed: {e}")
            print(f"Error type: {type(e)}")
            import traceback
            traceback.print_exc()
            raise
    
    # First test preexec_fn directly (not in subprocess)
    print("\n=== Testing preexec_fn directly ===")
    try:
        preexec_fn()
        print("✓ Direct preexec_fn test passed")
    except Exception as e:
        print(f"✗ Direct preexec_fn test failed: {e}")
        return False
    
    # Test in subprocess
    print("\n=== Testing preexec_fn in subprocess ===")
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write('print("Hello from subprocess")')
            temp_file = f.name
        
        result = subprocess.run(
            ['python', '-u', temp_file],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=preexec_fn
        )
        
        print(f"Return code: {result.returncode}")
        print(f"Stdout: {result.stdout.decode()}")
        print(f"Stderr: {result.stderr.decode()}")
        
        if result.returncode == 0:
            print("✓ Subprocess preexec_fn test passed")
            return True
        else:
            print("✗ Subprocess preexec_fn test failed")
            return False
            
    except Exception as e:
        print(f"✗ Subprocess test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        try:
            os.unlink(temp_file)
        except:
            pass

def check_system_limits():
    """Check current system resource limits"""
    print("\n=== Current System Resource Limits ===")
    
    limits = {
        'RLIMIT_AS': resource.RLIMIT_AS,
        'RLIMIT_CPU': resource.RLIMIT_CPU,
        'RLIMIT_NOFILE': resource.RLIMIT_NOFILE,
        'RLIMIT_CORE': resource.RLIMIT_CORE,
    }
    
    for name, limit in limits.items():
        try:
            soft, hard = resource.getrlimit(limit)
            print(f"{name}: soft={soft}, hard={hard}")
        except Exception as e:
            print(f"{name}: ERROR - {e}")

def test_individual_limits():
    """Test each resource limit individually"""
    print("\n=== Testing Individual Resource Limits ===")
    
    # Test process group
    print("Testing process group creation...")
    try:
        pid = os.fork()
        if pid == 0:  # Child process
            os.setpgrp()
            print("✓ Process group creation works")
            os._exit(0)
        else:  # Parent process
            os.waitpid(pid, 0)
    except Exception as e:
        print(f"✗ Process group creation failed: {e}")
    
    # Test memory limit
    print("Testing memory limit...")
    try:
        memory_bytes = 64 * 1024 * 1024  # 64MB
        current_soft, current_hard = resource.getrlimit(resource.RLIMIT_AS)
        print(f"Current memory limit: soft={current_soft}, hard={current_hard}")
        
        # Try to set a reasonable limit
        if current_hard == resource.RLIM_INFINITY or memory_bytes <= current_hard:
            resource.setrlimit(resource.RLIMIT_AS, (memory_bytes, memory_bytes))
            print("✓ Memory limit setting works")
            # Reset to original
            resource.setrlimit(resource.RLIMIT_AS, (current_soft, current_hard))
        else:
            print(f"✗ Memory limit too high: {memory_bytes} > {current_hard}")
    except Exception as e:
        print(f"✗ Memory limit failed: {e}")
    
    # Test CPU limit
    print("Testing CPU limit...")
    try:
        current_soft, current_hard = resource.getrlimit(resource.RLIMIT_CPU)
        print(f"Current CPU limit: soft={current_soft}, hard={current_hard}")
        
        cpu_limit = 300
        if current_hard == resource.RLIM_INFINITY or cpu_limit <= current_hard:
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))
            print("✓ CPU limit setting works")
            # Reset to original
            resource.setrlimit(resource.RLIMIT_CPU, (current_soft, current_hard))
        else:
            print(f"✗ CPU limit too high: {cpu_limit} > {current_hard}")
    except Exception as e:
        print(f"✗ CPU limit failed: {e}")
    
    # Test file descriptor limit
    print("Testing file descriptor limit...")
    try:
        current_soft, current_hard = resource.getrlimit(resource.RLIMIT_NOFILE)
        print(f"Current NOFILE limit: soft={current_soft}, hard={current_hard}")
        
        fd_limit = 50
        if current_hard == resource.RLIM_INFINITY or fd_limit <= current_hard:
            resource.setrlimit(resource.RLIMIT_NOFILE, (fd_limit, fd_limit))
            print("✓ File descriptor limit setting works")
            # Reset to original
            resource.setrlimit(resource.RLIMIT_NOFILE, (current_soft, current_hard))
        else:
            print(f"✗ FD limit too high: {fd_limit} > {current_hard}")
    except Exception as e:
        print(f"✗ File descriptor limit failed: {e}")

if __name__ == "__main__":
    print("PyRunner preexec_fn Diagnostic Tool")
    print("=" * 50)
    
    # Check system information
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"PID: {os.getpid()}")
    
    # Check system limits
    check_system_limits()
    
    # Test individual limits
    test_individual_limits()
    
    # Test the full preexec_fn
    success = test_preexec_fn()
    
    if success:
        print("\n✓ All tests passed! preexec_fn should work correctly.")
    else:
        print("\n✗ Tests failed. preexec_fn has issues that need fixing.")