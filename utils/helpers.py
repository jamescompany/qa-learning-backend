import hashlib
import random
import string
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import json


def generate_random_string(length: int = 32, chars: str = None) -> str:
    """Generate a random string of specified length"""
    if chars is None:
        chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def generate_slug(text: str, max_length: int = 50) -> str:
    """Generate a URL-friendly slug from text"""
    import re
    
    # Convert to lowercase
    slug = text.lower()
    
    # Replace spaces and special characters with hyphens
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    
    # Trim and limit length
    slug = slug.strip('-')[:max_length]
    
    return slug


def hash_string(text: str, algorithm: str = 'sha256') -> str:
    """Hash a string using specified algorithm"""
    hasher = hashlib.new(algorithm)
    hasher.update(text.encode('utf-8'))
    return hasher.hexdigest()


def format_datetime(dt: datetime, format: str = '%Y-%m-%d %H:%M:%S') -> str:
    """Format datetime to string"""
    if dt is None:
        return ''
    return dt.strftime(format)


def parse_datetime(date_string: str, format: str = '%Y-%m-%d %H:%M:%S') -> Optional[datetime]:
    """Parse string to datetime"""
    try:
        return datetime.strptime(date_string, format)
    except (ValueError, TypeError):
        return None


def time_ago(dt: datetime) -> str:
    """Convert datetime to human-readable time ago format"""
    if dt is None:
        return 'never'
    
    now = datetime.utcnow()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return 'just now'
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f'{minutes} minute{"s" if minutes > 1 else ""} ago'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours} hour{"s" if hours > 1 else ""} ago'
    elif seconds < 604800:
        days = int(seconds / 86400)
        return f'{days} day{"s" if days > 1 else ""} ago'
    elif seconds < 2592000:
        weeks = int(seconds / 604800)
        return f'{weeks} week{"s" if weeks > 1 else ""} ago'
    elif seconds < 31536000:
        months = int(seconds / 2592000)
        return f'{months} month{"s" if months > 1 else ""} ago'
    else:
        years = int(seconds / 31536000)
        return f'{years} year{"s" if years > 1 else ""} ago'


def format_file_size(size_bytes: int) -> str:
    """Format file size in bytes to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def truncate_text(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def remove_duplicates(items: List[Any]) -> List[Any]:
    """Remove duplicates from list while preserving order"""
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def deep_merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """Deep merge two dictionaries"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def safe_json_loads(json_string: str, default: Any = None) -> Any:
    """Safely parse JSON string with default value on error"""
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any, default: str = '{}') -> str:
    """Safely convert object to JSON string with default on error"""
    try:
        return json.dumps(obj, default=str)
    except (TypeError, ValueError):
        return default


def calculate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """Calculate estimated reading time in minutes"""
    word_count = len(text.split())
    minutes = max(1, round(word_count / words_per_minute))
    return minutes


def extract_hashtags(text: str) -> List[str]:
    """Extract hashtags from text"""
    import re
    hashtags = re.findall(r'#\w+', text)
    return [tag.lower() for tag in hashtags]


def extract_mentions(text: str) -> List[str]:
    """Extract @mentions from text"""
    import re
    mentions = re.findall(r'@\w+', text)
    return [mention.lower() for mention in mentions]


def mask_email(email: str) -> str:
    """Mask email address for privacy"""
    parts = email.split('@')
    if len(parts) != 2:
        return email
    
    username = parts[0]
    domain = parts[1]
    
    if len(username) <= 2:
        masked_username = '*' * len(username)
    else:
        masked_username = username[0] + '*' * (len(username) - 2) + username[-1]
    
    return f"{masked_username}@{domain}"


def is_valid_uuid(uuid_string: str) -> bool:
    """Check if string is a valid UUID"""
    import uuid
    try:
        uuid.UUID(uuid_string)
        return True
    except (ValueError, AttributeError):
        return False


def get_client_ip(request) -> str:
    """Extract client IP from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"