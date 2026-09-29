"""Utilities - JSON helpers, slug generation, etc."""
import json
import re
from typing import Any


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'-+', '-', text)
    return text.strip('-')


def format_json_field(value: Any) -> str:
    """Format a value as JSON string for storage."""
    if value is None:
        return "[]" if isinstance(value, list) else "{}"
    return json.dumps(value)


def parse_json_field(value: str, default: Any = None) -> Any:
    """Parse a JSON string field."""
    if not value:
        return default
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return default


def validate_slug(slug: str) -> bool:
    """Validate a slug format."""
    return bool(re.match(r'^[a-z0-9-]+$', slug))


def generate_slug(title: str, existing_slugs: list[str], index: int = None) -> str:
    """Generate a unique slug from a title."""
    base_slug = slugify(title)
    if index:
        base_slug = f"{base_slug}-{index}"
    if base_slug not in existing_slugs:
        return base_slug
    # Try with a number suffix
    counter = 2
    while True:
        candidate = f"{base_slug}-{counter}"
        if candidate not in existing_slugs:
            return candidate
        counter += 1


def sanitize_code(code: str, language: str) -> str:
    """Basic code sanitization."""
    # Remove null bytes
    code = code.replace('\x00', '')
    # Trim to max length
    max_length = 100000
    if len(code) > max_length:
        code = code[:max_length]
    return code.strip()


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def datetime_to_iso(dt) -> str:
    """Convert datetime to ISO format string."""
    if dt is None:
        return ""
    return dt.isoformat()
