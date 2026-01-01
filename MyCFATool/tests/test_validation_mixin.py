import unittest
from MyCFATool.core.validation import ValidationMixin, ValidationError


class TestValidationMixin(unittest.TestCase):
    """Test cases for ValidationMixin methods."""

    def setUp(self):
        self.mixin = ValidationMixin()

    def test_validate_numeric_valid_int(self):
        """Test validate_numeric with valid integer."""
        result = self.mixin.validate_numeric(5)
        self.assertEqual(result, 5.0)

    def test_validate_numeric_valid_float(self):
        """Test validate_numeric with valid float."""
        result = self.mixin.validate_numeric(5.5)
        self.assertEqual(result, 5.5)

    def test_validate_numeric_non_numeric_string(self):
        """Test validate_numeric with non-numeric string raises ValidationError."""
        with self.assertRaises(ValidationError) as cm:
            self.mixin.validate_numeric("not_a_number")
        self.assertIn("Value not_a_number is not numeric", str(cm.exception))

    def test_validate_numeric_non_numeric_list(self):
        """Test validate_numeric with list raises ValidationError."""
        with self.assertRaises(ValidationError) as cm:
            self.mixin.validate_numeric([1, 2, 3])
        self.assertIn("Value [1, 2, 3] is not numeric", str(cm.exception))

    def test_validate_numeric_min_val_violation(self):
        """Test validate_numeric with value below min_val raises ValidationError."""
        with self.assertRaises(ValidationError) as cm:
            self.mixin.validate_numeric(5, min_val=10)
        self.assertIn("Value 5.0 is below minimum 10", str(cm.exception))

    def test_validate_numeric_max_val_violation(self):
        """Test validate_numeric with value above max_val raises ValidationError."""
        with self.assertRaises(ValidationError) as cm:
            self.mixin.validate_numeric(15, max_val=10)
        self.assertIn("Value 15.0 is above maximum 10", str(cm.exception))

    def test_validate_numeric_at_min_boundary(self):
        """Test validate_numeric at minimum boundary."""
        result = self.mixin.validate_numeric(10, min_val=10)
        self.assertEqual(result, 10.0)

    def test_validate_numeric_at_max_boundary(self):
        """Test validate_numeric at maximum boundary."""
        result = self.mixin.validate_numeric(10, max_val=10)
        self.assertEqual(result, 10.0)

    def test_validate_numeric_with_range(self):
        """Test validate_numeric within valid range."""
        result = self.mixin.validate_numeric(7.5, min_val=5, max_val=10)
        self.assertEqual(result, 7.5)

    def test_validate_non_zero_valid_positive(self):
        """Test validate_non_zero with positive number."""
        result = self.mixin.validate_non_zero(5)
        self.assertEqual(result, 5)

    def test_validate_non_zero_valid_negative(self):
        """Test validate_non_zero with negative number."""
        result = self.mixin.validate_non_zero(-5)
        self.assertEqual(result, -5)

    def test_validate_non_zero_zero_int(self):
        """Test validate_non_zero with zero integer raises ValidationError."""
        with self.assertRaises(ValidationError) as cm:
            self.mixin.validate_non_zero(0)
        self.assertIn("Value 0 is zero or None", str(cm.exception))

    def test_validate_non_zero_zero_float(self):
        """Test validate_non_zero with zero float raises ValidationError."""
        with self.assertRaises(ValidationError) as cm:
            self.mixin.validate_non_zero(0.0)
        self.assertIn("Value 0.0 is zero or None", str(cm.exception))

    def test_validate_non_zero_none(self):
        """Test validate_non_zero with None raises ValidationError."""
        with self.assertRaises(ValidationError) as cm:
            self.mixin.validate_non_zero(None)
        self.assertIn("Value None is zero or None", str(cm.exception))

    def test_validate_date_format_valid(self):
        """Test validate_date_format with valid date string."""
        result = self.mixin.validate_date_format("2023-01-01")
        self.assertEqual(result, "2023-01-01")

    def test_validate_date_format_invalid_format(self):
        """Test validate_date_format with invalid format raises ValidationError."""
        with self.assertRaises(ValidationError) as cm:
            self.mixin.validate_date_format("01/01/2023")
        self.assertIn("Date string 01/01/2023 does not match format %Y-%m-%d", str(cm.exception))

    def test_validate_date_format_invalid_date(self):
        """Test validate_date_format with invalid date raises ValidationError."""
        with self.assertRaises(ValidationError) as cm:
            self.mixin.validate_date_format("2023-13-01")
        self.assertIn("Date string 2023-13-01 does not match format %Y-%m-%d", str(cm.exception))

    def test_validate_date_format_custom_format_valid(self):
        """Test validate_date_format with custom format."""
        result = self.mixin.validate_date_format("01/01/2023", "%m/%d/%Y")
        self.assertEqual(result, "01/01/2023")

    def test_validate_date_format_custom_format_invalid(self):
        """Test validate_date_format with custom format invalid."""
        with self.assertRaises(ValidationError) as cm:
            self.mixin.validate_date_format("2023-01-01", "%m/%d/%Y")
        self.assertIn("Date string 2023-01-01 does not match format %m/%d/%Y", str(cm.exception))

    def test_validate_required_fields_valid(self):
        """Test validate_required_fields with all required fields present."""
        data = {"field1": "value1", "field2": "value2"}
        result = self.mixin.validate_required_fields(data, ["field1", "field2"])
        self.assertEqual(result, data)

    def test_validate_required_fields_missing_one(self):
        """Test validate_required_fields with one missing field raises ValidationError."""
        data = {"field1": "value1"}
        with self.assertRaises(ValidationError) as cm:
            self.mixin.validate_required_fields(data, ["field1", "field2"])
        self.assertIn("Required field field2 is missing or None", str(cm.exception))

    def test_validate_required_fields_multiple_missing(self):
        """Test validate_required_fields with multiple missing fields."""
        data = {"field1": "value1"}
        with self.assertRaises(ValidationError) as cm:
            self.mixin.validate_required_fields(data, ["field1", "field2", "field3"])
        self.assertIn("Required field field2 is missing or None", str(cm.exception))
        self.assertIn("Required field field3 is missing or None", str(cm.exception))

    def test_validate_required_fields_none_value(self):
        """Test validate_required_fields with None value treated as missing."""
        data = {"field1": "value1", "field2": None}
        with self.assertRaises(ValidationError) as cm:
            self.mixin.validate_required_fields(data, ["field1", "field2"])
        self.assertIn("Required field field2 is missing or None", str(cm.exception))

    def test_validate_required_fields_empty_list(self):
        """Test validate_required_fields with empty required list."""
        data = {"field1": "value1"}
        result = self.mixin.validate_required_fields(data, [])
        self.assertEqual(result, data)


if __name__ == "__main__":
    unittest.main()