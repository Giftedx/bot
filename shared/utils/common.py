import json
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, date
import uuid
import re
from pathlib import Path
import hashlib
import base64

def generate_uuid() -> str:
    """Generate a UUID4 string"""
    return str(uuid.uuid4())

def to_snake_case(name: str) -> str:
    """Convert a string to snake_case"""
    name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

def to_camel_case(name: str) -> str:
    """Convert a string to camelCase"""
    components = name.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])

class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles dates and complex objects"""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        return super().default(obj)

def json_dumps(obj: Any) -> str:
    """Serialize object to JSON string"""
    return json.dumps(obj, cls=JSONEncoder)

def json_loads(s: str) -> Any:
    """Deserialize JSON string to object"""
    return json.loads(s)

def hash_file(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
    """Calculate hash of a file"""
    hash_obj = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()

def base64_encode(data: Union[str, bytes]) -> str:
    """Encode data as base64"""
    if isinstance(data, str):
        data = data.encode()
    return base64.b64encode(data).decode()

def base64_decode(data: str) -> bytes:
    """Decode base64 data"""
    return base64.b64decode(data)

def truncate_string(s: str, max_length: int, suffix: str = '...') -> str:
    """Truncate a string to max_length characters"""
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix

def deep_merge(dict1: Dict, dict2: Dict) -> Dict:
    """Deep merge two dictionaries"""
    result = dict1.copy()
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def flatten_dict(d: Dict, parent_key: str = '', sep: str = '.') -> Dict:
    """Flatten a nested dictionary"""
    items: List = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def unflatten_dict(d: Dict, sep: str = '.') -> Dict:
    """Unflatten a dictionary with dot notation keys"""
    result: Dict = {}
    for key, value in d.items():
        parts = key.split(sep)
        target = result
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = value
    return result

def parse_duration(duration_str: str) -> Optional[int]:
    """Parse a duration string into seconds"""
    units = {
        's': 1,
        'm': 60,
        'h': 3600,
        'd': 86400,
        'w': 604800
    }
    
    match = re.match(r'^(\d+)([smhdw])$', duration_str)
    if not match:
        return None
        
    value, unit = match.groups()
    return int(value) * units[unit]

def format_duration(seconds: int) -> str:
    """Format a duration in seconds to a human-readable string"""
    intervals = [
        ('w', 604800),
        ('d', 86400),
        ('h', 3600),
        ('m', 60),
        ('s', 1)
    ]
    
    parts = []
    for unit, count in intervals:
        value = seconds // count
        if value:
            parts.append(f'{value}{unit}')
            seconds = seconds % count
            
    return ' '.join(parts) if parts else '0s'

def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """Split a list into chunks of specified size"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def retry_operation(operation: callable, max_attempts: int = 3, 
                   delay: float = 1.0, backoff: float = 2.0,
                   exceptions: tuple = (Exception,)) -> Any:
    """Retry an operation with exponential backoff"""
    import time
    
    attempt = 1
    while attempt <= max_attempts:
        try:
            return operation()
        except exceptions as e:
            if attempt == max_attempts:
                raise
            wait = delay * (backoff ** (attempt - 1))
            time.sleep(wait)
            attempt += 1 