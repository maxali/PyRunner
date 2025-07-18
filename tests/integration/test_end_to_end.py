"""End-to-end integration tests for PyRunner"""

import pytest
import httpx
from tests.conftest import assert_success_response, assert_error_response


class TestRealWorldScenarios:
    """Test cases for real-world usage scenarios"""
    
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_data_science_workflow(self, api_client: httpx.AsyncClient):
        """Test complete data science workflow"""
        payload = {
            "code": """
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

# Generate sample data
np.random.seed(42)
data = np.random.normal(100, 15, 1000)

# Create DataFrame
df = pd.DataFrame({
    'values': data,
    'category': np.random.choice(['A', 'B', 'C'], 1000)
})

# Basic statistics
print(f"Data shape: {df.shape}")
print(f"Mean: {df['values'].mean():.2f}")
print(f"Std: {df['values'].std():.2f}")
print(f"Min: {df['values'].min():.2f}")
print(f"Max: {df['values'].max():.2f}")

# Group by category
grouped = df.groupby('category')['values'].mean()
print(f"\\nMean by category:")
for cat, mean in grouped.items():
    print(f"  {cat}: {mean:.2f}")

# Statistical test
statistic, p_value = stats.normaltest(df['values'])
print(f"\\nNormality test p-value: {p_value:.4f}")

# Correlation (with itself should be 1.0)
correlation = df['values'].corr(df['values'])
print(f"Self-correlation: {correlation:.4f}")

print("\\nData science workflow completed successfully!")
""",
            "timeout": 30,
            "memory_limit": 512
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "Data science workflow completed successfully!")
        assert "Data shape: (1000, 2)" in data["stdout"]
        assert "Mean:" in data["stdout"]
        assert "Self-correlation: 1.0000" in data["stdout"]
    
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_machine_learning_example(self, api_client: httpx.AsyncClient):
        """Test machine learning workflow"""
        payload = {
            "code": """
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

# Generate synthetic dataset
np.random.seed(42)
X = np.random.randn(100, 2)
y = 3 * X[:, 0] + 2 * X[:, 1] + np.random.randn(100) * 0.1

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
model = LinearRegression()
model.fit(X_train, y_train)

# Make predictions
y_pred = model.predict(X_test)

# Evaluate
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"Model coefficients: {model.coef_}")
print(f"Model intercept: {model.intercept_:.4f}")
print(f"Mean squared error: {mse:.4f}")
print(f"R² score: {r2:.4f}")

# Predict on a new sample
new_sample = np.array([[1, 2]])
prediction = model.predict(new_sample)
print(f"Prediction for [1, 2]: {prediction[0]:.4f}")

print("\\nMachine learning workflow completed!")
""",
            "timeout": 30,
            "memory_limit": 512
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "Machine learning workflow completed!")
        assert "Model coefficients:" in data["stdout"]
        assert "R² score:" in data["stdout"]
        assert "Prediction for [1, 2]:" in data["stdout"]
    
    @pytest.mark.integration
    async def test_mathematical_computation(self, api_client: httpx.AsyncClient):
        """Test complex mathematical computation"""
        payload = {
            "code": """
import math
import numpy as np
from scipy.special import gamma, factorial

# Mathematical constants and functions
print(f"π = {math.pi:.10f}")
print(f"e = {math.e:.10f}")
print(f"√2 = {math.sqrt(2):.10f}")

# Trigonometric functions
angle = math.pi / 4
print(f"\\nsin(π/4) = {math.sin(angle):.10f}")
print(f"cos(π/4) = {math.cos(angle):.10f}")
print(f"tan(π/4) = {math.tan(angle):.10f}")

# Logarithms
print(f"\\nln(e) = {math.log(math.e):.10f}")
print(f"log₁₀(100) = {math.log10(100):.10f}")

# Factorial and gamma function
n = 5
print(f"\\n{n}! = {factorial(n)}")
print(f"Γ({n}) = {gamma(n):.10f}")

# Series calculations
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

print(f"\\nFibonacci sequence (first 10):")
fib_sequence = [fibonacci(i) for i in range(10)]
print(fib_sequence)

# Prime number check
def is_prime(n):
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

primes = [i for i in range(2, 50) if is_prime(i)]
print(f"\\nPrimes up to 50: {primes}")

# Matrix operations
A = np.array([[1, 2], [3, 4]])
B = np.array([[5, 6], [7, 8]])

print(f"\\nMatrix A:\\n{A}")
print(f"Matrix B:\\n{B}")
print(f"A × B:\\n{np.dot(A, B)}")
print(f"det(A) = {np.linalg.det(A):.4f}")

print("\\nMathematical computation completed!")
""",
            "timeout": 30,
            "memory_limit": 512
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "Mathematical computation completed!")
        assert "π = 3.1415926536" in data["stdout"]
        assert "Fibonacci sequence" in data["stdout"]
        assert "Primes up to 50:" in data["stdout"]
        assert "det(A) = -2.0000" in data["stdout"]
    
    @pytest.mark.integration
    async def test_string_processing(self, api_client: httpx.AsyncClient):
        """Test string processing and text analysis"""
        payload = {
            "code": """
import re
from collections import Counter

# Sample text
text = '''
Python is a high-level, interpreted programming language with dynamic semantics.
Its high-level built-in data structures, combined with dynamic typing and dynamic binding,
make it very attractive for Rapid Application Development, as well as for use as a
scripting or glue language to connect existing components together.
'''

# Basic string operations
print(f"Original text length: {len(text)}")
print(f"Word count: {len(text.split())}")
print(f"Line count: {len(text.strip().split('\\n'))}")

# Clean and process text
cleaned = re.sub(r'[^a-zA-Z\\s]', '', text.lower())
words = cleaned.split()

# Word frequency analysis
word_freq = Counter(words)
print(f"\\nTotal unique words: {len(word_freq)}")
print(f"Most common words:")
for word, count in word_freq.most_common(10):
    print(f"  '{word}': {count}")

# Find specific patterns
python_mentions = len(re.findall(r'python', text, re.IGNORECASE))
print(f"\\n'Python' mentioned {python_mentions} times")

# Find all words starting with 'd'
d_words = [word for word in words if word.startswith('d')]
print(f"Words starting with 'd': {d_words}")

# Calculate average word length
avg_word_length = sum(len(word) for word in words) / len(words)
print(f"Average word length: {avg_word_length:.2f} characters")

# Text statistics
vowels = sum(1 for char in cleaned if char in 'aeiou')
consonants = sum(1 for char in cleaned if char.isalpha() and char not in 'aeiou')
print(f"\\nVowels: {vowels}")
print(f"Consonants: {consonants}")
print(f"Vowel/Consonant ratio: {vowels/consonants:.2f}")

print("\\nString processing completed!")
""",
            "timeout": 30,
            "memory_limit": 512
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "String processing completed!")
        assert "Word count:" in data["stdout"]
        assert "Most common words:" in data["stdout"]
        assert "Average word length:" in data["stdout"]
    
    @pytest.mark.integration
    async def test_algorithm_implementation(self, api_client: httpx.AsyncClient):
        """Test algorithm implementations"""
        payload = {
            "code": """
import heapq
from collections import deque

# Sorting algorithms
def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr

def merge_sort(arr):
    if len(arr) <= 1:
        return arr
    
    mid = len(arr) // 2
    left = merge_sort(arr[:mid])
    right = merge_sort(arr[mid:])
    
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    
    result.extend(left[i:])
    result.extend(right[j:])
    return result

# Test sorting algorithms
test_array = [64, 34, 25, 12, 22, 11, 90]
print(f"Original array: {test_array}")
print(f"Bubble sort: {bubble_sort(test_array.copy())}")
print(f"Merge sort: {merge_sort(test_array.copy())}")
print(f"Built-in sort: {sorted(test_array)}")

# Binary search
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    
    return -1

# Test binary search
sorted_array = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]
target = 11
result = binary_search(sorted_array, target)
print(f"\\nBinary search for {target} in {sorted_array}: index {result}")

# Graph algorithms (simple BFS)
def bfs(graph, start):
    visited = set()
    queue = deque([start])
    result = []
    
    while queue:
        node = queue.popleft()
        if node not in visited:
            visited.add(node)
            result.append(node)
            queue.extend(graph[node] - visited)
    
    return result

# Test BFS
graph = {
    'A': {'B', 'C'},
    'B': {'A', 'D', 'E'},
    'C': {'A', 'F'},
    'D': {'B'},
    'E': {'B', 'F'},
    'F': {'C', 'E'}
}

bfs_result = bfs(graph, 'A')
print(f"\\nBFS traversal from 'A': {bfs_result}")

# Dynamic programming (Fibonacci with memoization)
def fibonacci_dp(n, memo={}):
    if n in memo:
        return memo[n]
    if n <= 1:
        return n
    
    memo[n] = fibonacci_dp(n-1, memo) + fibonacci_dp(n-2, memo)
    return memo[n]

# Test DP
fib_result = [fibonacci_dp(i) for i in range(20)]
print(f"\\nFibonacci (DP) first 20: {fib_result}")

print("\\nAlgorithm implementation completed!")
""",
            "timeout": 30,
            "memory_limit": 512
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "Algorithm implementation completed!")
        assert "Bubble sort:" in data["stdout"]
        assert "Binary search for 11" in data["stdout"]
        assert "BFS traversal from 'A':" in data["stdout"]
        assert "Fibonacci (DP) first 20:" in data["stdout"]


class TestComplexScenarios:
    """Test cases for complex usage scenarios"""
    
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_scientific_simulation(self, api_client: httpx.AsyncClient):
        """Test scientific simulation"""
        payload = {
            "code": """
import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint

# Simulate a simple pendulum
def pendulum(y, t, b, c):
    theta, z = y
    dydt = [z, -b*z - c*np.sin(theta)]
    return dydt

# Parameters
b = 0.25  # damping coefficient
c = 5.0   # gravitational constant

# Initial conditions
y0 = [np.pi - 0.1, 0.0]

# Time points
t = np.linspace(0, 10, 101)

# Solve ODE
sol = odeint(pendulum, y0, t, args=(b, c))

# Extract solutions
theta = sol[:, 0]
omega = sol[:, 1]

# Calculate energy
kinetic = 0.5 * omega**2
potential = c * (1 - np.cos(theta))
total_energy = kinetic + potential

print(f"Pendulum simulation results:")
print(f"Time range: {t[0]:.1f} to {t[-1]:.1f} seconds")
print(f"Initial angle: {y0[0]:.3f} radians ({np.degrees(y0[0]):.1f}°)")
print(f"Final angle: {theta[-1]:.3f} radians ({np.degrees(theta[-1]):.1f}°)")
print(f"Initial energy: {total_energy[0]:.6f}")
print(f"Final energy: {total_energy[-1]:.6f}")
print(f"Energy loss: {total_energy[0] - total_energy[-1]:.6f}")

# Find maximum displacement
max_angle = np.max(np.abs(theta))
max_time = t[np.argmax(np.abs(theta))]
print(f"Maximum displacement: {max_angle:.3f} radians at t={max_time:.1f}s")

# Calculate period (approximate)
zero_crossings = np.where(np.diff(np.sign(theta)))[0]
if len(zero_crossings) >= 2:
    period = 2 * (t[zero_crossings[1]] - t[zero_crossings[0]])
    print(f"Approximate period: {period:.3f} seconds")

print("\\nScientific simulation completed!")
""",
            "timeout": 30,
            "memory_limit": 512
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "Scientific simulation completed!")
        assert "Pendulum simulation results:" in data["stdout"]
        assert "Energy loss:" in data["stdout"]
        assert "Maximum displacement:" in data["stdout"]
    
    @pytest.mark.integration
    async def test_cryptography_and_hashing(self, api_client: httpx.AsyncClient):
        """Test cryptography and hashing operations"""
        payload = {
            "code": """
import hashlib
import hmac
import secrets
import base64

# Generate secure random data
secret_key = secrets.token_bytes(32)
message = b"Hello, PyRunner! This is a secret message."

print(f"Original message: {message.decode()}")
print(f"Secret key length: {len(secret_key)} bytes")

# Hash functions
md5_hash = hashlib.md5(message).hexdigest()
sha1_hash = hashlib.sha1(message).hexdigest()
sha256_hash = hashlib.sha256(message).hexdigest()
sha512_hash = hashlib.sha512(message).hexdigest()

print(f"\\nHash functions:")
print(f"MD5:    {md5_hash}")
print(f"SHA1:   {sha1_hash}")
print(f"SHA256: {sha256_hash}")
print(f"SHA512: {sha512_hash}")

# HMAC (Hash-based Message Authentication Code)
hmac_sha256 = hmac.new(secret_key, message, hashlib.sha256).hexdigest()
print(f"\\nHMAC-SHA256: {hmac_sha256}")

# Base64 encoding
message_b64 = base64.b64encode(message).decode()
decoded_message = base64.b64decode(message_b64)
print(f"\\nBase64 encoded: {message_b64}")
print(f"Decoded matches original: {decoded_message == message}")

# URL-safe base64
url_safe_b64 = base64.urlsafe_b64encode(message).decode()
print(f"URL-safe Base64: {url_safe_b64}")

# Generate random tokens
random_token = secrets.token_hex(16)
random_urlsafe = secrets.token_urlsafe(32)

print(f"\\nRandom tokens:")
print(f"Hex token (16 bytes): {random_token}")
print(f"URL-safe token (32 bytes): {random_urlsafe}")

# Simple password hashing (using multiple iterations)
def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_bytes(16)
    
    key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return salt + key

def verify_password(password, hashed):
    salt = hashed[:16]
    key = hashed[16:]
    return hmac.compare_digest(key, hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000))

# Test password hashing
password = "super_secret_password"
hashed_pw = hash_password(password)
is_valid = verify_password(password, hashed_pw)
is_invalid = verify_password("wrong_password", hashed_pw)

print(f"\\nPassword hashing test:")
print(f"Password verified correctly: {is_valid}")
print(f"Wrong password rejected: {not is_invalid}")

print("\\nCryptography and hashing completed!")
""",
            "timeout": 30,
            "memory_limit": 512
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        # hashlib is not in the allowed modules list, so this should fail
        assert_error_response(data, "hashlib")


class TestErrorRecovery:
    """Test cases for error recovery and edge cases"""
    
    @pytest.mark.integration
    async def test_partial_execution_with_error(self, api_client: httpx.AsyncClient):
        """Test partial execution before error"""
        payload = {
            "code": """
print("Starting execution...")

# Some successful operations
import math
result1 = math.sqrt(16)
print(f"Square root of 16: {result1}")

# Create some data
data = list(range(10))
print(f"Created list: {data}")

# This will cause an error
print("About to cause an error...")
x = 10 / 0  # Division by zero

# This should not execute
print("This should not appear")
""",
            "timeout": 30,
            "memory_limit": 512
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert "Starting execution..." in data["stdout"]
        assert "Square root of 16: 4.0" in data["stdout"]
        assert "About to cause an error..." in data["stdout"]
        assert "This should not appear" not in data["stdout"]
        assert "ZeroDivisionError" in data["stderr"]
    
    @pytest.mark.integration
    async def test_large_output_handling(self, api_client: httpx.AsyncClient):
        """Test handling of large output"""
        payload = {
            "code": """
# Generate large output
print("Starting large output test...")

for i in range(1000):
    print(f"Line {i:04d}: This is a test line with some content to make it longer")

print("Large output test completed!")
""",
            "timeout": 30,
            "memory_limit": 512
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "Large output test completed!")
        assert "Line 0000:" in data["stdout"]
        assert "Line 0999:" in data["stdout"]
        assert data["stdout"].count("Line") == 1000
    
    @pytest.mark.integration
    async def test_unicode_and_special_characters(self, api_client: httpx.AsyncClient):
        """Test unicode and special character handling"""
        payload = {
            "code": """
# Test various unicode characters
print("Testing unicode characters...")

# Basic Unicode
print("Hello 世界! 🌍")
print("Привет мир! 🇷🇺")
print("Hola mundo! 🇪🇸")
print("Bonjour le monde! 🇫🇷")

# Mathematical symbols
print("\\nMathematical symbols:")
print("∑ ∫ ∂ ∞ π α β γ δ ε")
print("≤ ≥ ≠ ≈ ∈ ∉ ∅ ∪ ∩")

# Special characters
print("\\nSpecial characters:")
print("Quotes: '' "" 「」 『』")
print("Arrows: ← → ↑ ↓ ↔ ↕")
print("Currency: $ € £ ¥ ₹ ₽")

# Emojis
print("\\nEmojis:")
print("Animals: 🐱 🐶 🐰 🐻 🐼")
print("Food: 🍕 🍔 🍟 🍦 🍰")
print("Objects: 📱 💻 🖥️ ⌨️ 🖱️")

# Test string operations with unicode
text = "Hello 世界! 🌍"
print(f"\\nString operations:")
print(f"Length: {len(text)}")
print(f"Upper: {text.upper()}")
print(f"Encoded: {text.encode('utf-8')}")

print("\\nUnicode test completed!")
""",
            "timeout": 30,
            "memory_limit": 512
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "Unicode test completed!")
        assert "Hello 世界! 🌍" in data["stdout"]
        assert "∑ ∫ ∂ ∞ π α β γ δ ε" in data["stdout"]
        assert "Animals: 🐱 🐶 🐰 🐻 🐼" in data["stdout"]
    
    @pytest.mark.integration
    async def test_complex_data_structures(self, api_client: httpx.AsyncClient):
        """Test complex data structures"""
        payload = {
            "code": """
from collections import defaultdict, deque, Counter
import json

print("Testing complex data structures...")

# Nested dictionaries
nested_dict = {
    'users': {
        'alice': {'age': 30, 'city': 'New York', 'hobbies': ['reading', 'swimming']},
        'bob': {'age': 25, 'city': 'San Francisco', 'hobbies': ['coding', 'gaming']},
        'charlie': {'age': 35, 'city': 'Chicago', 'hobbies': ['cooking', 'traveling']}
    },
    'metadata': {
        'created': '2023-01-01',
        'version': '1.0',
        'total_users': 3
    }
}

print(f"Nested dictionary structure created with {len(nested_dict['users'])} users")

# Complex list operations
matrix = [[i*j for j in range(1, 6)] for i in range(1, 6)]
print(f"\\nGenerated 5x5 multiplication matrix:")
for row in matrix:
    print(row)

# Set operations
set1 = {1, 2, 3, 4, 5}
set2 = {4, 5, 6, 7, 8}
print(f"\\nSet operations:")
print(f"Set 1: {set1}")
print(f"Set 2: {set2}")
print(f"Union: {set1 | set2}")
print(f"Intersection: {set1 & set2}")
print(f"Difference: {set1 - set2}")

# Advanced collections
dd = defaultdict(list)
dd['fruits'].extend(['apple', 'banana', 'orange'])
dd['vegetables'].extend(['carrot', 'broccoli', 'spinach'])
print(f"\\nDefaultdict: {dict(dd)}")

# Counter
text = "hello world hello python world"
word_count = Counter(text.split())
print(f"Word counter: {word_count}")

# Deque operations
dq = deque(maxlen=5)
for i in range(10):
    dq.append(i)
print(f"Deque (maxlen=5): {list(dq)}")

# Complex comprehensions
result = {
    'squares': [x**2 for x in range(10) if x % 2 == 0],
    'cubes': [x**3 for x in range(5)],
    'word_lengths': {word: len(word) for word in ['hello', 'world', 'python']}
}

print(f"\\nComplex comprehensions:")
for key, value in result.items():
    print(f"  {key}: {value}")

# JSON serialization
json_str = json.dumps(nested_dict, indent=2)
print(f"\\nJSON serialization successful: {len(json_str)} characters")

# Reconstruct from JSON
reconstructed = json.loads(json_str)
print(f"JSON deserialization successful: {reconstructed['metadata']['total_users']} users")

print("\\nComplex data structures test completed!")
""",
            "timeout": 30,
            "memory_limit": 512
        }
        response = await api_client.post("/run", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert_success_response(data, "Complex data structures test completed!")
        assert "Generated 5x5 multiplication matrix:" in data["stdout"]
        assert "Set operations:" in data["stdout"]
        assert "JSON serialization successful:" in data["stdout"]