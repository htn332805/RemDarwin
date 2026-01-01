from typing import Any, Dict, List, Optional
from datetime import datetime


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class ValidationMixin:
    """Mixin class providing common validation methods."""

    def validate_numeric(
        self,
        value: Any,
        min_val: Optional[float] = None,
        max_val: Optional[float] = None
    ) -> float:
        """Validate that value is numeric and within optional range."""
        if not isinstance(value, (int, float)):
            raise ValidationError(f"Value {value} is not numeric")
        numeric_value = float(value)
        if min_val is not None and numeric_value < min_val:
            raise ValidationError(f"Value {numeric_value} is below minimum {min_val}")
        if max_val is not None and numeric_value > max_val:
            raise ValidationError(f"Value {numeric_value} is above maximum {max_val}")
        return numeric_value

    def validate_non_zero(self, value: Any) -> Any:
        """Ensure value is not zero or None."""
        if value is None or value == 0:
            raise ValidationError(f"Value {value} is zero or None")
        return value

    def validate_date_format(
        self,
        date_str: str,
        format: str = "%Y-%m-%d"
    ) -> str:
        """Validate date string format."""
        try:
            datetime.strptime(date_str, format)
            return date_str
        except ValueError:
            raise ValidationError(f"Date string {date_str} does not match format {format}")

    def validate_required_fields(
        self,
        data: Dict[str, Any],
        required: List[str]
    ) -> Dict[str, Any]:
        """Check if required fields are present in the dict."""
        for field in required:
            if field not in data or data[field] is None:
                raise ValidationError(f"Required field {field} is missing or None")
        return data