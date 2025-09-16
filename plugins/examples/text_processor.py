"""
Example: Text Processing Plugin - No manifest needed, just Python
"""

import re
from typing import Dict, List, Any


def clean_text(text: str) -> str:
    """Remove extra whitespace and normalize text"""
    return ' '.join(text.split())


def count_words(text: str) -> int:
    """Count words in text"""
    return len(text.split())


def extract_emails(text: str) -> List[str]:
    """Extract email addresses from text"""
    pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    return re.findall(pattern, text)


def analyze_text(text: str) -> Dict[str, Any]:
    """Comprehensive text analysis"""
    return {
        "word_count": count_words(text),
        "char_count": len(text),
        "line_count": text.count('\n') + 1,
        "emails": extract_emails(text),
        "cleaned_text": clean_text(text)
    }


# Framework will auto-discover all these functions as capabilities!