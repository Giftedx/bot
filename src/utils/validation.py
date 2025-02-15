"""Data validation utilities."""
from typing import Any, Dict, List, Optional, Type, Union
from dataclasses import dataclass, fields
import re
from datetime import datetime
from .exceptions import ValidationError
from .logger import get_logger

logger = get_logger(__name__)

@dataclass
class ValidationRule:
    """Validation rule definition."""
    field: str
    rule_type: str
    value: Any = None
    message: Optional[str] = None

class Validator:
    """Data model validator."""
    
    def __init__(self, rules: List[ValidationRule]):
        self.rules = rules
        
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against rules."""
        errors = []
        
        for rule in self.rules:
            try:
                self._validate_rule(rule, data)
            except ValidationError as e:
                errors.append(e)
        
        if errors:
            raise ValidationError(
                message="Validation failed",
                field="multiple",
                value=errors
            )
        
        return data
    
    def _validate_rule(self, rule: ValidationRule, data: Dict[str, Any]) -> None:
        """Validate a single rule."""
        value = data.get(rule.field)
        
        if rule.rule_type == "required" and value is None:
            raise ValidationError(
                message=rule.message or f"Field {rule.field} is required",
                field=rule.field
            )
            
        if value is None:
            return
            
        if rule.rule_type == "type":
            if not isinstance(value, rule.value):
                raise ValidationError(
                    message=rule.message or f"Field {rule.field} must be of type {rule.value.__name__}",
                    field=rule.field,
                    value=value
                )
                
        elif rule.rule_type == "regex":
            if not isinstance(value, str) or not re.match(rule.value, value):
                raise ValidationError(
                    message=rule.message or f"Field {rule.field} must match pattern {rule.value}",
                    field=rule.field,
                    value=value
                )
                
        elif rule.rule_type == "range":
            if not isinstance(value, (int, float)) or not (rule.value[0] <= value <= rule.value[1]):
                raise ValidationError(
                    message=rule.message or f"Field {rule.field} must be between {rule.value[0]} and {rule.value[1]}",
                    field=rule.field,
                    value=value
                )
                
        elif rule.rule_type == "length":
            if not hasattr(value, "__len__") or not (rule.value[0] <= len(value) <= rule.value[1]):
                raise ValidationError(
                    message=rule.message or f"Field {rule.field} length must be between {rule.value[0]} and {rule.value[1]}",
                    field=rule.field,
                    value=value
                )
                
        elif rule.rule_type == "enum":
            if value not in rule.value:
                raise ValidationError(
                    message=rule.message or f"Field {rule.field} must be one of {rule.value}",
                    field=rule.field,
                    value=value
                )

def validate_dataclass(instance: Any) -> None:
    """Validate a dataclass instance."""
    if not hasattr(instance, "__dataclass_fields__"):
        raise ValidationError("Object is not a dataclass instance")
        
    errors = []
    
    for field in fields(instance):
        value = getattr(instance, field.name)
        
        # Check required fields
        if not field.default and not field.default_factory and value is None:
            errors.append(
                ValidationError(
                    message=f"Field {field.name} is required",
                    field=field.name
                )
            )
            continue
            
        # Skip None values for optional fields
        if value is None:
            continue
            
        # Type checking
        try:
            if not isinstance(value, field.type):
                # Handle Union types
                if hasattr(field.type, "__origin__") and field.type.__origin__ is Union:
                    if not any(isinstance(value, t) for t in field.type.__args__):
                        errors.append(
                            ValidationError(
                                message=f"Field {field.name} must be one of types {field.type.__args__}",
                                field=field.name,
                                value=value
                            )
                        )
                else:
                    errors.append(
                        ValidationError(
                            message=f"Field {field.name} must be of type {field.type}",
                            field=field.name,
                            value=value
                        )
                    )
        except TypeError:
            logger.warning(f"Could not check type for field {field.name}")
    
    if errors:
        raise ValidationError(
            message="Dataclass validation failed",
            field="multiple",
            value=errors
        )

def validate_type(value: Any, expected_type: Type) -> None:
    """Validate value type."""
    if not isinstance(value, expected_type):
        raise ValidationError(
            message=f"Value must be of type {expected_type.__name__}",
            value=value
        )

def validate_datetime(value: str) -> datetime:
    """Validate and parse datetime string."""
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError) as e:
        raise ValidationError(
            message="Invalid datetime format",
            value=value,
            original_error=e
        ) 