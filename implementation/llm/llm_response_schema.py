"""
RemDarwin LLM Response Schema - JSON schema loader and utilities

This module provides utilities for loading and working with the LLM response JSON schema.
"""

import json
import os
from typing import Dict, Any
from pathlib import Path


def get_response_schema() -> Dict[str, Any]:
    """
    Load the LLM response JSON schema

    Returns:
        Dictionary containing the JSON schema
    """
    schema_path = Path(__file__).parent / "llm_response_schema.json"

    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
        return schema
    except FileNotFoundError:
        # Fallback to embedded schema if file not found
        return _get_embedded_schema()
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in schema file: {e}")


def _get_embedded_schema() -> Dict[str, Any]:
    """
    Fallback embedded schema if file cannot be loaded

    Returns:
        Basic schema structure
    """
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "RemDarwin LLM Trade Analysis Response Schema",
        "description": "Structured JSON schema for LLM responses in options trading decision support",
        "type": "object",
        "properties": {
            "trade_id": {"type": "string"},
            "timestamp": {"type": "string", "format": "date-time"},
            "analysis_confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
            "trade_rationale": {
                "type": "object",
                "properties": {
                    "primary_catalyst": {"type": "string"},
                    "market_context": {"type": "string"},
                    "narrative_summary": {"type": "string"}
                },
                "required": ["primary_catalyst", "market_context", "narrative_summary"]
            },
            "risk_assessment": {
                "type": "object",
                "properties": {
                    "overall_risk_level": {"type": "string", "enum": ["LOW", "MODERATE", "HIGH", "EXTREME"]},
                    "risk_factors": {"type": "array"}
                },
                "required": ["overall_risk_level", "risk_factors"]
            },
            "scenario_analysis": {
                "type": "object",
                "properties": {
                    "base_case": {"type": "object"}
                },
                "required": ["base_case"]
            },
            "recommendation": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["BUY", "SELL", "HOLD", "AVOID", "MONITOR"]},
                    "confidence_score": {"type": "number", "minimum": 0.0, "maximum": 1.0}
                },
                "required": ["action", "confidence_score"]
            }
        },
        "required": ["trade_id", "timestamp", "analysis_confidence", "trade_rationale", "risk_assessment", "scenario_analysis", "recommendation"]
    }


def validate_schema_compliance(data: Dict[str, Any]) -> bool:
    """
    Quick validation that data structure matches expected schema

    Args:
        data: Data to validate

    Returns:
        True if data has required top-level fields
    """
    required_fields = [
        "trade_id", "timestamp", "analysis_confidence",
        "trade_rationale", "risk_assessment", "scenario_analysis", "recommendation"
    ]

    return all(field in data for field in required_fields)


if __name__ == "__main__":
    # Test schema loading
    schema = get_response_schema()
    print(f"Schema loaded successfully with {len(schema.get('properties', {}))} properties")

    # Test validation
    test_data = {
        "trade_id": "TEST_001",
        "timestamp": "2024-01-01T00:00:00Z",
        "analysis_confidence": 0.8,
        "trade_rationale": {
            "primary_catalyst": "Test catalyst",
            "market_context": "Test context",
            "narrative_summary": "Test summary"
        },
        "risk_assessment": {
            "overall_risk_level": "MODERATE",
            "risk_factors": []
        },
        "scenario_analysis": {
            "base_case": {"probability": 0.5, "outcome_description": "Test"}
        },
        "recommendation": {
            "action": "BUY",
            "confidence_score": 0.8
        }
    }

    is_valid = validate_schema_compliance(test_data)
    print(f"Test data validation: {'PASS' if is_valid else 'FAIL'}")