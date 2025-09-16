# 💡 Basic Plugin Examples

Simple, practical examples to get you started with RAG Builder plugin development.

## 🚀 Quick Start Examples

### 1. **Hello World Plugin**

The simplest possible plugin to understand the basics.

```python
# plugins/hello_world.py

def hello(name: str = "World") -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"

def goodbye(name: str = "World") -> str:
    """Say goodbye to someone."""
    return f"Goodbye, {name}!"

# Test the plugin
if __name__ == "__main__":
    print(hello("RAG Builder"))  # Hello, RAG Builder!
    print(goodbye("RAG Builder"))  # Goodbye, RAG Builder!
```

**Usage via API:**
```bash
curl -X POST http://localhost:8000/api/call/hello \
  -H "Content-Type: application/json" \
  -d '{"args": ["Alice"]}'
# Response: {"success": true, "result": "Hello, Alice!"}
```

### 2. **Text Processing Plugin**

Basic text manipulation capabilities.

```python
# plugins/text_utils.py

import re
from typing import List

def clean_text(text: str) -> str:
    """Remove extra whitespace and normalize text."""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Strip leading/trailing whitespace
    return text.strip()

def count_words(text: str) -> int:
    """Count the number of words in text."""
    cleaned = clean_text(text)
    return len(cleaned.split()) if cleaned else 0

def count_characters(text: str, include_spaces: bool = True) -> int:
    """Count characters in text."""
    if include_spaces:
        return len(text)
    else:
        return len(text.replace(' ', ''))

def reverse_text(text: str) -> str:
    """Reverse the input text."""
    return text[::-1]

def to_title_case(text: str) -> str:
    """Convert text to title case."""
    return text.title()

def extract_numbers(text: str) -> List[int]:
    """Extract all numbers from text."""
    numbers = re.findall(r'\d+', text)
    return [int(num) for num in numbers]

def remove_punctuation(text: str) -> str:
    """Remove punctuation from text."""
    return re.sub(r'[^\w\s]', '', text)

# Example usage
if __name__ == "__main__":
    sample_text = "  Hello,   World!   This has 123 numbers and   extra   spaces.  "
    
    print(f"Original: '{sample_text}'")
    print(f"Cleaned: '{clean_text(sample_text)}'")
    print(f"Word count: {count_words(sample_text)}")
    print(f"Character count: {count_characters(sample_text)}")
    print(f"Numbers: {extract_numbers(sample_text)}")
    print(f"No punctuation: '{remove_punctuation(sample_text)}'")
```

### 3. **Math Operations Plugin**

Simple mathematical calculations and utilities.

```python
# plugins/math_utils.py

import math
from typing import List, Union

def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b

def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    return a - b

def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b

def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

def power(base: float, exponent: float) -> float:
    """Raise base to the power of exponent."""
    return base ** exponent

def square_root(number: float) -> float:
    """Calculate square root of a number."""
    if number < 0:
        raise ValueError("Cannot calculate square root of negative number")
    return math.sqrt(number)

def factorial(n: int) -> int:
    """Calculate factorial of n."""
    if n < 0:
        raise ValueError("Factorial is not defined for negative numbers")
    return math.factorial(n)

def sum_list(numbers: List[Union[int, float]]) -> Union[int, float]:
    """Calculate sum of a list of numbers."""
    return sum(numbers)

def average(numbers: List[Union[int, float]]) -> float:
    """Calculate average of a list of numbers."""
    if not numbers:
        raise ValueError("Cannot calculate average of empty list")
    return sum(numbers) / len(numbers)

def max_value(numbers: List[Union[int, float]]) -> Union[int, float]:
    """Find maximum value in a list."""
    if not numbers:
        raise ValueError("Cannot find max of empty list")
    return max(numbers)

def min_value(numbers: List[Union[int, float]]) -> Union[int, float]:
    """Find minimum value in a list."""
    if not numbers:
        raise ValueError("Cannot find min of empty list")
    return min(numbers)

def is_prime(n: int) -> bool:
    """Check if a number is prime."""
    if n < 2:
        return False
    for i in range(2, int(math.sqrt(n)) + 1):
        if n % i == 0:
            return False
    return True

# Example usage
if __name__ == "__main__":
    numbers = [1, 2, 3, 4, 5]
    
    print(f"Numbers: {numbers}")
    print(f"Sum: {sum_list(numbers)}")
    print(f"Average: {average(numbers)}")
    print(f"Max: {max_value(numbers)}")
    print(f"Min: {min_value(numbers)}")
    print(f"Is 17 prime? {is_prime(17)}")
    print(f"5! = {factorial(5)}")
```

### 4. **Data Validation Plugin**

Input validation and data quality checks.

```python
# plugins/data_validator.py

import re
from typing import Dict, Any, List
from datetime import datetime

def validate_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_phone(phone: str) -> bool:
    """Validate phone number format (US format)."""
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    # Check if it's 10 or 11 digits (with or without country code)
    return len(digits) in [10, 11]

def validate_url(url: str) -> bool:
    """Validate URL format."""
    pattern = r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
    return bool(re.match(pattern, url))

def validate_date(date_string: str, format_string: str = "%Y-%m-%d") -> bool:
    """Validate date string against a format."""
    try:
        datetime.strptime(date_string, format_string)
        return True
    except ValueError:
        return False

def validate_credit_card(card_number: str) -> Dict[str, Any]:
    """Validate credit card number using Luhn algorithm."""
    # Remove spaces and dashes
    card_number = re.sub(r'[\s-]', '', card_number)
    
    # Check if all characters are digits
    if not card_number.isdigit():
        return {"valid": False, "error": "Card number must contain only digits"}
    
    # Check length
    if len(card_number) < 13 or len(card_number) > 19:
        return {"valid": False, "error": "Card number must be 13-19 digits"}
    
    # Luhn algorithm
    def luhn_check(card_num):
        digits = [int(d) for d in card_num]
        for i in range(len(digits) - 2, -1, -2):
            digits[i] *= 2
            if digits[i] > 9:
                digits[i] -= 9
        return sum(digits) % 10 == 0
    
    # Determine card type
    card_type = "Unknown"
    if card_number.startswith('4'):
        card_type = "Visa"
    elif card_number.startswith('5') or card_number.startswith('2'):
        card_type = "Mastercard"
    elif card_number.startswith('3'):
        card_type = "American Express"
    
    is_valid = luhn_check(card_number)
    
    return {
        "valid": is_valid,
        "type": card_type,
        "masked": f"****-****-****-{card_number[-4:]}"
    }

def validate_password_strength(password: str) -> Dict[str, Any]:
    """Check password strength."""
    score = 0
    feedback = []
    
    # Length check
    if len(password) >= 8:
        score += 1
    else:
        feedback.append("Password should be at least 8 characters long")
    
    # Uppercase check
    if re.search(r'[A-Z]', password):
        score += 1
    else:
        feedback.append("Password should contain uppercase letters")
    
    # Lowercase check
    if re.search(r'[a-z]', password):
        score += 1
    else:
        feedback.append("Password should contain lowercase letters")
    
    # Number check
    if re.search(r'\d', password):
        score += 1
    else:
        feedback.append("Password should contain numbers")
    
    # Special character check
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1
    else:
        feedback.append("Password should contain special characters")
    
    # Strength levels
    if score >= 5:
        strength = "Very Strong"
    elif score >= 4:
        strength = "Strong"
    elif score >= 3:
        strength = "Medium"
    elif score >= 2:
        strength = "Weak"
    else:
        strength = "Very Weak"
    
    return {
        "strength": strength,
        "score": score,
        "max_score": 5,
        "feedback": feedback
    }

def validate_json_structure(data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
    """Validate if JSON data contains required fields."""
    missing_fields = []
    present_fields = []
    
    for field in required_fields:
        if field in data:
            present_fields.append(field)
        else:
            missing_fields.append(field)
    
    return {
        "valid": len(missing_fields) == 0,
        "missing_fields": missing_fields,
        "present_fields": present_fields,
        "completion_rate": len(present_fields) / len(required_fields)
    }

# Example usage
if __name__ == "__main__":
    # Test email validation
    print(f"Email valid: {validate_email('user@example.com')}")
    
    # Test phone validation
    print(f"Phone valid: {validate_phone('(555) 123-4567')}")
    
    # Test password strength
    password_check = validate_password_strength("MySecurePass123!")
    print(f"Password strength: {password_check}")
    
    # Test JSON validation
    data = {"name": "John", "email": "john@example.com"}
    required = ["name", "email", "age"]
    validation = validate_json_structure(data, required)
    print(f"JSON validation: {validation}")
```

### 5. **File Operations Plugin**

Basic file and directory operations.

```python
# plugins/file_utils.py

import os
import json
from typing import List, Dict, Any, Optional

def read_text_file(file_path: str, encoding: str = 'utf-8') -> str:
    """Read content from a text file."""
    try:
        with open(file_path, 'r', encoding=encoding) as file:
            return file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except Exception as e:
        raise Exception(f"Error reading file: {str(e)}")

def write_text_file(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
    """Write content to a text file."""
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding=encoding) as file:
            file.write(content)
        return True
    except Exception as e:
        raise Exception(f"Error writing file: {str(e)}")

def read_json_file(file_path: str) -> Dict[str, Any]:
    """Read and parse JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in file: {str(e)}")

def write_json_file(file_path: str, data: Dict[str, Any], indent: int = 2) -> bool:
    """Write data to JSON file."""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=indent, ensure_ascii=False)
        return True
    except Exception as e:
        raise Exception(f"Error writing JSON file: {str(e)}")

def list_files(directory_path: str, extension: Optional[str] = None) -> List[str]:
    """List files in a directory, optionally filtered by extension."""
    try:
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        files = []
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            if os.path.isfile(item_path):
                if extension is None or item.endswith(extension):
                    files.append(item)
        
        return sorted(files)
    except Exception as e:
        raise Exception(f"Error listing files: {str(e)}")

def get_file_info(file_path: str) -> Dict[str, Any]:
    """Get information about a file."""
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        stat = os.stat(file_path)
        
        return {
            "name": os.path.basename(file_path),
            "path": os.path.abspath(file_path),
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "is_file": os.path.isfile(file_path),
            "is_directory": os.path.isdir(file_path)
        }
    except Exception as e:
        raise Exception(f"Error getting file info: {str(e)}")

def file_exists(file_path: str) -> bool:
    """Check if a file exists."""
    return os.path.exists(file_path) and os.path.isfile(file_path)

def directory_exists(directory_path: str) -> bool:
    """Check if a directory exists."""
    return os.path.exists(directory_path) and os.path.isdir(directory_path)

def create_directory(directory_path: str) -> bool:
    """Create a directory (and parent directories if needed)."""
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        raise Exception(f"Error creating directory: {str(e)}")

def count_lines(file_path: str) -> int:
    """Count the number of lines in a text file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return sum(1 for _ in file)
    except Exception as e:
        raise Exception(f"Error counting lines: {str(e)}")

# Example usage
if __name__ == "__main__":
    # Test file operations
    test_file = "test_output.txt"
    test_content = "Hello, World!\nThis is a test file."
    
    # Write file
    write_text_file(test_file, test_content)
    print(f"File written: {test_file}")
    
    # Read file
    content = read_text_file(test_file)
    print(f"File content: {content}")
    
    # Get file info
    info = get_file_info(test_file)
    print(f"File info: {info}")
    
    # Count lines
    lines = count_lines(test_file)
    print(f"Line count: {lines}")
```

## 🧪 Testing Your Plugins

### Basic Test Examples

```python
# tests/test_basic_plugins.py

import pytest
from plugins.text_utils import clean_text, count_words, extract_numbers
from plugins.math_utils import add, divide, is_prime
from plugins.data_validator import validate_email, validate_password_strength

class TestTextUtils:
    def test_clean_text(self):
        assert clean_text("  hello   world  ") == "hello world"
        assert clean_text("") == ""
        assert clean_text("   ") == ""
    
    def test_count_words(self):
        assert count_words("hello world") == 2
        assert count_words("") == 0
        assert count_words("   ") == 0
        assert count_words("one") == 1
    
    def test_extract_numbers(self):
        assert extract_numbers("I have 5 apples and 10 oranges") == [5, 10]
        assert extract_numbers("No numbers here") == []
        assert extract_numbers("123 and 456") == [123, 456]

class TestMathUtils:
    def test_add(self):
        assert add(2, 3) == 5
        assert add(-1, 1) == 0
        assert add(0.1, 0.2) == pytest.approx(0.3)
    
    def test_divide(self):
        assert divide(10, 2) == 5
        assert divide(7, 2) == 3.5
        
        with pytest.raises(ValueError):
            divide(5, 0)
    
    def test_is_prime(self):
        assert is_prime(2) == True
        assert is_prime(17) == True
        assert is_prime(4) == False
        assert is_prime(1) == False

class TestDataValidator:
    def test_validate_email(self):
        assert validate_email("user@example.com") == True
        assert validate_email("invalid-email") == False
        assert validate_email("user@") == False
    
    def test_validate_password_strength(self):
        weak_result = validate_password_strength("123")
        assert weak_result["strength"] == "Very Weak"
        
        strong_result = validate_password_strength("StrongPass123!")
        assert strong_result["strength"] in ["Strong", "Very Strong"]

# Run tests with: pytest tests/test_basic_plugins.py -v
```

### API Testing Examples

```bash
#!/bin/bash
# test_api.sh - Test plugin APIs

echo "Testing basic plugins via API..."

# Test text utilities
echo "Testing clean_text..."
curl -X POST http://localhost:8000/api/call/clean_text \
  -H "Content-Type: application/json" \
  -d '{"args": ["  hello   world  "]}'

echo -e "\n\nTesting count_words..."
curl -X POST http://localhost:8000/api/call/count_words \
  -H "Content-Type: application/json" \
  -d '{"args": ["hello beautiful world"]}'

# Test math utilities
echo -e "\n\nTesting add..."
curl -X POST http://localhost:8000/api/call/add \
  -H "Content-Type: application/json" \
  -d '{"args": [5, 3]}'

echo -e "\n\nTesting is_prime..."
curl -X POST http://localhost:8000/api/call/is_prime \
  -H "Content-Type: application/json" \
  -d '{"args": [17]}'

# Test data validation
echo -e "\n\nTesting validate_email..."
curl -X POST http://localhost:8000/api/call/validate_email \
  -H "Content-Type: application/json" \
  -d '{"args": ["user@example.com"]}'

echo -e "\n\nDone!"
```

## 📊 Plugin Usage Examples

### Combining Multiple Plugins

```python
# plugins/text_processor_combo.py

from . import text_utils, data_validator

def process_user_input(text: str, validate_emails: bool = False) -> dict:
    """Process user input with cleaning and optional email validation."""
    
    # Clean the text
    cleaned_text = text_utils.clean_text(text)
    
    # Get basic statistics
    word_count = text_utils.count_words(cleaned_text)
    char_count = text_utils.count_characters(cleaned_text)
    numbers = text_utils.extract_numbers(cleaned_text)
    
    result = {
        "original_text": text,
        "cleaned_text": cleaned_text,
        "word_count": word_count,
        "character_count": char_count,
        "numbers_found": numbers
    }
    
    # Optional email validation
    if validate_emails:
        # Simple email extraction (basic pattern)
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        potential_emails = re.findall(email_pattern, text)
        
        validated_emails = []
        for email in potential_emails:
            is_valid = data_validator.validate_email(email)
            validated_emails.append({
                "email": email,
                "valid": is_valid
            })
        
        result["emails"] = validated_emails
    
    return result

# Example usage
if __name__ == "__main__":
    sample_input = """
    Hello! Please contact us at support@example.com or invalid-email.
    We have 100 products and 50 customers.
    """
    
    result = process_user_input(sample_input, validate_emails=True)
    print(json.dumps(result, indent=2))
```

### Error Handling Best Practices

```python
# plugins/robust_plugin.py

import logging
from typing import Union, Dict, Any

# Set up logging
logger = logging.getLogger(__name__)

def safe_divide(a: float, b: float) -> Dict[str, Any]:
    """Safely divide two numbers with comprehensive error handling."""
    try:
        # Input validation
        if not isinstance(a, (int, float)):
            return {
                "success": False,
                "error": "First argument must be a number",
                "error_type": "TypeError"
            }
        
        if not isinstance(b, (int, float)):
            return {
                "success": False,
                "error": "Second argument must be a number", 
                "error_type": "TypeError"
            }
        
        # Division by zero check
        if b == 0:
            return {
                "success": False,
                "error": "Cannot divide by zero",
                "error_type": "ZeroDivisionError"
            }
        
        # Perform calculation
        result = a / b
        
        # Log successful operation
        logger.info(f"Division successful: {a} / {b} = {result}")
        
        return {
            "success": True,
            "result": result,
            "operation": f"{a} / {b}"
        }
        
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error in safe_divide: {str(e)}")
        
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "error_type": type(e).__name__
        }

def process_list_safely(items: list, operation: str = "sum") -> Dict[str, Any]:
    """Safely process a list of numbers."""
    try:
        # Input validation
        if not isinstance(items, list):
            return {
                "success": False,
                "error": "Input must be a list"
            }
        
        if len(items) == 0:
            return {
                "success": False,
                "error": "List cannot be empty"
            }
        
        # Validate all items are numbers
        for i, item in enumerate(items):
            if not isinstance(item, (int, float)):
                return {
                    "success": False,
                    "error": f"Item at index {i} is not a number: {item}"
                }
        
        # Perform operation
        if operation == "sum":
            result = sum(items)
        elif operation == "average":
            result = sum(items) / len(items)
        elif operation == "max":
            result = max(items)
        elif operation == "min":
            result = min(items)
        else:
            return {
                "success": False,
                "error": f"Unknown operation: {operation}"
            }
        
        return {
            "success": True,
            "result": result,
            "operation": operation,
            "input_count": len(items)
        }
        
    except Exception as e:
        logger.error(f"Error in process_list_safely: {str(e)}")
        return {
            "success": False,
            "error": f"Processing error: {str(e)}"
        }
```

These basic plugin examples provide a solid foundation for understanding RAG Builder plugin development. Start with these simple patterns and gradually build more complex functionality as you become comfortable with the framework.