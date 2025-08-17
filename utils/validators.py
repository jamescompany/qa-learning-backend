import re
from typing import Optional
from email_validator import validate_email, EmailNotValidError


def validate_email_address(email: str) -> tuple[bool, Optional[str]]:
    """Validate email address format"""
    try:
        validate_email(email)
        return True, None
    except EmailNotValidError as e:
        return False, str(e)


def validate_username(username: str) -> tuple[bool, Optional[str]]:
    """Validate username format"""
    if len(username) < 3:
        return False, "Username must be at least 3 characters long"
    
    if len(username) > 50:
        return False, "Username must be at most 50 characters long"
    
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"
    
    return True, None


def validate_phone_number(phone: str) -> tuple[bool, Optional[str]]:
    """Validate phone number format"""
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)\+]', '', phone)
    
    # Check if it's all digits
    if not cleaned.isdigit():
        return False, "Phone number must contain only digits"
    
    # Check length (between 10 and 15 digits)
    if len(cleaned) < 10 or len(cleaned) > 15:
        return False, "Phone number must be between 10 and 15 digits"
    
    return True, None


def validate_url(url: str) -> tuple[bool, Optional[str]]:
    """Validate URL format"""
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )
    
    if not url_pattern.match(url):
        return False, "Invalid URL format"
    
    return True, None


def sanitize_html(html: str) -> str:
    """Remove potentially dangerous HTML tags and attributes"""
    # Simple HTML sanitization (for production, use a library like bleach)
    dangerous_tags = ['script', 'style', 'iframe', 'object', 'embed', 'form']
    dangerous_attrs = ['onclick', 'onload', 'onerror', 'onmouseover']
    
    sanitized = html
    
    # Remove dangerous tags
    for tag in dangerous_tags:
        sanitized = re.sub(f'<{tag}[^>]*>.*?</{tag}>', '', sanitized, flags=re.IGNORECASE | re.DOTALL)
        sanitized = re.sub(f'<{tag}[^>]*/?>', '', sanitized, flags=re.IGNORECASE)
    
    # Remove dangerous attributes
    for attr in dangerous_attrs:
        sanitized = re.sub(f'{attr}="[^"]*"', '', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(f"{attr}='[^']*'", '', sanitized, flags=re.IGNORECASE)
    
    return sanitized


def validate_file_extension(filename: str, allowed_extensions: list[str]) -> bool:
    """Check if file extension is allowed"""
    if '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in allowed_extensions


def validate_file_size(file_size: int, max_size: int) -> bool:
    """Check if file size is within limit"""
    return 0 < file_size <= max_size