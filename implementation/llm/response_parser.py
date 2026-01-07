"""
RemDarwin Response Parser - LLM Output Processing and Validation

This module provides comprehensive utilities for parsing LLM responses,
validating structured outputs, extracting confidence scores, and handling
various response formats with robust error handling.
"""

import json
import logging
import re
from typing import Dict, Any, Optional, Union, Tuple, List
from dataclasses import dataclass, asdict
from datetime import datetime
import jsonschema

from .llm_response_schema import get_response_schema

logger = logging.getLogger(__name__)


@dataclass
class ParsedResponse:
    """Structured representation of parsed LLM response"""
    raw_response: str
    parsed_json: Optional[Dict[str, Any]]
    is_valid: bool
    validation_errors: List[str]
    confidence_score: Optional[float]
    processing_time: float
    parse_method: str  # 'direct_json', 'json_extraction', 'structured_parse'
    metadata: Dict[str, Any]


class LLMResponseParser:
    """
    Advanced parser for LLM responses with multiple extraction strategies

    Supports:
    - Direct JSON parsing
    - JSON extraction from markdown/text
    - Structured data validation
    - Confidence score extraction
    - Error recovery and fallback parsing
    """

    def __init__(self, schema_path: Optional[str] = None):
        """
        Initialize the response parser

        Args:
            schema_path: Path to JSON schema file for validation
        """
        self.schema = get_response_schema() if schema_path is None else self._load_schema(schema_path)
        self.validator = jsonschema.Draft7Validator(self.schema)

        # Compilation patterns for JSON extraction
        self.json_patterns = [
            re.compile(r'```json\s*(.*?)\s*```', re.DOTALL),  # ```json ... ```
            re.compile(r'```\s*(.*?)\s*```', re.DOTALL),       # ``` ... ```
            re.compile(r'\{.*\}', re.DOTALL),                  # Raw JSON object
        ]

        logger.info("LLM Response Parser initialized with validation schema")

    def _load_schema(self, schema_path: str) -> Dict[str, Any]:
        """Load JSON schema from file"""
        try:
            with open(schema_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load schema from {schema_path}: {e}")
            return {}

    def parse_response(self, response_text: str, timeout: float = 5.0) -> ParsedResponse:
        """
        Parse LLM response with multiple strategies

        Args:
            response_text: Raw response text from LLM
            timeout: Maximum parsing time in seconds

        Returns:
            ParsedResponse object with structured data
        """
        start_time = datetime.now()

        # Strategy 1: Direct JSON parsing
        parsed = self._try_direct_json(response_text)
        if parsed.is_valid:
            parsed.parse_method = 'direct_json'
            parsed.processing_time = (datetime.now() - start_time).total_seconds()
            return parsed

        # Strategy 2: Extract JSON from markdown/text
        parsed = self._extract_json_from_text(response_text)
        if parsed.is_valid:
            parsed.parse_method = 'json_extraction'
            parsed.processing_time = (datetime.now() - start_time).total_seconds()
            return parsed

        # Strategy 3: Structured parsing with fallbacks
        parsed = self._structured_parse_with_fallbacks(response_text)
        parsed.parse_method = 'structured_parse'
        parsed.processing_time = (datetime.now() - start_time).total_seconds()
        return parsed

    def _try_direct_json(self, text: str) -> ParsedResponse:
        """Attempt direct JSON parsing"""
        try:
            parsed_json = json.loads(text.strip())
            is_valid, errors = self._validate_json(parsed_json)
            confidence = self._extract_confidence_score(parsed_json)

            return ParsedResponse(
                raw_response=text,
                parsed_json=parsed_json if is_valid else None,
                is_valid=is_valid,
                validation_errors=errors,
                confidence_score=confidence,
                processing_time=0.0,
                parse_method='',
                metadata={'direct_parse': True}
            )
        except json.JSONDecodeError:
            return ParsedResponse(
                raw_response=text,
                parsed_json=None,
                is_valid=False,
                validation_errors=['Invalid JSON format'],
                confidence_score=None,
                processing_time=0.0,
                parse_method='',
                metadata={'direct_parse': False}
            )

    def _extract_json_from_text(self, text: str) -> ParsedResponse:
        """Extract JSON from markdown or mixed text content"""
        for pattern in self.json_patterns:
            matches = pattern.findall(text)
            for match in matches:
                try:
                    # Clean up the extracted text
                    cleaned = self._clean_extracted_json(match)
                    parsed_json = json.loads(cleaned)

                    is_valid, errors = self._validate_json(parsed_json)
                    confidence = self._extract_confidence_score(parsed_json)

                    if is_valid:
                        return ParsedResponse(
                            raw_response=text,
                            parsed_json=parsed_json,
                            is_valid=True,
                            validation_errors=[],
                            confidence_score=confidence,
                            processing_time=0.0,
                            parse_method='',
                            metadata={'extraction_pattern': pattern.pattern, 'extracted_text': match}
                        )
                except (json.JSONDecodeError, TypeError):
                    continue

        # No valid JSON found
        return ParsedResponse(
            raw_response=text,
            parsed_json=None,
            is_valid=False,
            validation_errors=['No valid JSON found in response'],
            confidence_score=None,
            processing_time=0.0,
            parse_method='',
            metadata={'extraction_attempts': len(self.json_patterns)}
        )

    def _structured_parse_with_fallbacks(self, text: str) -> ParsedResponse:
        """
        Parse semi-structured response with fallback strategies

        This handles cases where LLM provides structured but not perfectly formatted JSON
        """
        try:
            # Try to extract key components using regex and heuristics
            parsed_data = self._heuristic_structured_parse(text)
            is_valid, errors = self._validate_json(parsed_data)
            confidence = self._extract_confidence_score(parsed_data)

            return ParsedResponse(
                raw_response=text,
                parsed_json=parsed_data if is_valid else None,
                is_valid=is_valid,
                validation_errors=errors,
                confidence_score=confidence,
                processing_time=0.0,
                parse_method='',
                metadata={'heuristic_parse': True, 'fallback_used': True}
            )
        except Exception as e:
            return ParsedResponse(
                raw_response=text,
                parsed_json=None,
                is_valid=False,
                validation_errors=[f'Heuristic parsing failed: {str(e)}'],
                confidence_score=None,
                processing_time=0.0,
                parse_method='',
                metadata={'heuristic_parse': False, 'error': str(e)}
            )

    def _clean_extracted_json(self, text: str) -> str:
        """Clean extracted JSON text"""
        # Remove common formatting issues
        cleaned = text.strip()

        # Fix trailing commas
        cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)

        # Fix missing quotes on keys
        # This is a simple heuristic - more complex parsing would be needed for robustness
        cleaned = re.sub(r'(\w+):', r'"\1":', cleaned)

        return cleaned

    def _heuristic_structured_parse(self, text: str) -> Dict[str, Any]:
        """
        Heuristic parsing for semi-structured LLM responses

        This is a fallback for when JSON parsing fails but the response
        contains structured information that can be extracted.
        """
        parsed = {
            "trade_id": self._extract_field(text, r'trade[_-]id["\s:]*([^"\s,}]*)'),
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "analysis_confidence": self._extract_confidence_from_text(text),
            "trade_rationale": self._extract_trade_rationale(text),
            "risk_assessment": self._extract_risk_assessment(text),
            "scenario_analysis": self._extract_scenario_analysis(text),
            "recommendation": self._extract_recommendation(text)
        }

        return parsed

    def _extract_field(self, text: str, pattern: str, default: Any = None) -> Any:
        """Extract a field using regex pattern"""
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip('"\'') if match else default

    def _extract_confidence_from_text(self, text: str) -> float:
        """Extract confidence score from text using heuristics"""
        # Look for explicit confidence scores
        confidence_patterns = [
            r'confidence["\s:]*([0-9.]+)',
            r'([0-9.]+)%?\s*confidence',
            r'confidence\s*score["\s:]*([0-9.]+)',
        ]

        for pattern in confidence_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    score = float(match.group(1))
                    return min(score, 1.0) if score > 1 else score
                except ValueError:
                    continue

        # Default confidence based on text analysis
        return 0.5

    def _extract_trade_rationale(self, text: str) -> Dict[str, Any]:
        """Extract trade rationale section"""
        return {
            "primary_catalyst": self._extract_section(text, "rationale|catalyst", 200),
            "market_context": self._extract_section(text, "market|context", 200),
            "fundamental_factors": self._extract_list_items(text, "fundamental|factor"),
            "technical_factors": self._extract_list_items(text, "technical|factor"),
            "narrative_summary": self._extract_section(text, "summary|narrative", 300)
        }

    def _extract_risk_assessment(self, text: str) -> Dict[str, Any]:
        """Extract risk assessment section"""
        return {
            "overall_risk_level": self._extract_risk_level(text),
            "risk_factors": self._extract_risk_factors(text),
            "maximum_drawdown_estimate": self._extract_percentage(text, "drawdown|max.*loss"),
            "tail_risk_assessment": self._extract_section(text, "tail.*risk|extreme", 200)
        }

    def _extract_scenario_analysis(self, text: str) -> Dict[str, Any]:
        """Extract scenario analysis section"""
        return {
            "base_case": self._extract_scenario(text, "base|expected", 0.5),
            "bull_case": self._extract_scenario(text, "bull|upside|optimistic", 0.3),
            "bear_case": self._extract_scenario(text, "bear|downside|pessimistic", 0.2)
        }

    def _extract_recommendation(self, text: str) -> Dict[str, Any]:
        """Extract recommendation section"""
        return {
            "action": self._extract_action(text),
            "confidence_score": self._extract_confidence_from_text(text),
            "position_sizing_guidance": self._extract_section(text, "position.*size|sizing", 100),
            "urgency_level": self._extract_urgency(text),
            "key_assumptions": self._extract_list_items(text, "assumption|assumes")
        }

    def _extract_section(self, text: str, keywords: str, max_length: int = 500) -> str:
        """Extract a section of text based on keywords"""
        # Simple heuristic - find sentences containing keywords
        sentences = re.split(r'[.!?]+', text)
        relevant_sentences = []

        for sentence in sentences:
            if re.search(keywords, sentence, re.IGNORECASE):
                relevant_sentences.append(sentence.strip())

        result = '. '.join(relevant_sentences[:3])  # Limit to 3 sentences
        return result[:max_length] if len(result) > max_length else result

    def _extract_list_items(self, text: str, keywords: str) -> List[str]:
        """Extract list items from text"""
        # Look for bullet points or numbered lists
        items = re.findall(r'[-*•]\s*([^-\n]*?)(?=\n|$)', text)
        if not items:
            # Fallback: split on keywords
            sections = re.split(f'{keywords}.*?:', text, flags=re.IGNORECASE)
            if len(sections) > 1:
                items = [s.strip() for s in sections[1].split('\n') if s.strip()][:5]

        return [item.strip() for item in items if item.strip()][:10]  # Limit to 10 items

    def _extract_risk_level(self, text: str) -> str:
        """Extract risk level from text"""
        risk_keywords = {
            'LOW': ['low', 'minimal', 'small'],
            'MODERATE': ['moderate', 'medium', 'reasonable'],
            'HIGH': ['high', 'significant', 'substantial'],
            'EXTREME': ['extreme', 'severe', 'catastrophic']
        }

        text_lower = text.lower()
        for level, keywords in risk_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return level

        return 'MODERATE'  # Default

    def _extract_risk_factors(self, text: str) -> List[Dict[str, Any]]:
        """Extract risk factors with assessment"""
        risk_texts = self._extract_list_items(text, 'risk|danger|threat')

        factors = []
        for risk_text in risk_texts[:5]:  # Limit to 5
            # Simple heuristic assessment
            if any(word in risk_text.lower() for word in ['high', 'severe', 'critical']):
                probability, impact = 'HIGH', 'HIGH'
            elif any(word in risk_text.lower() for word in ['medium', 'moderate']):
                probability, impact = 'MEDIUM', 'MEDIUM'
            else:
                probability, impact = 'LOW', 'LOW'

            factors.append({
                'factor': risk_text,
                'probability': probability,
                'impact': impact,
                'mitigation_strategy': 'Monitor closely and adjust position as needed'
            })

        return factors

    def _extract_percentage(self, text: str, keywords: str) -> Optional[float]:
        """Extract percentage value from text"""
        match = re.search(fr'{keywords}.*?([0-9.]+)%', text, re.IGNORECASE)
        return float(match.group(1)) if match else None

    def _extract_scenario(self, text: str, keywords: str, default_prob: float) -> Dict[str, Any]:
        """Extract scenario information"""
        scenario_text = self._extract_section(text, keywords, 300)
        probability = self._extract_percentage(text, f'{keywords}.*?probability|chance') or default_prob

        return {
            'probability': probability,
            'outcome_description': scenario_text,
            'expected_return': self._extract_percentage(text, f'{keywords}.*?return|gain|loss') or 0.0
        }

    def _extract_action(self, text: str) -> str:
        """Extract recommended action"""
        actions = ['BUY', 'SELL', 'HOLD', 'AVOID', 'MONITOR']

        text_upper = text.upper()
        for action in actions:
            if action in text_upper:
                return action

        # Default based on sentiment
        if 'positive' in text.lower() or 'bullish' in text.lower():
            return 'BUY'
        elif 'negative' in text.lower() or 'bearish' in text.lower():
            return 'AVOID'
        else:
            return 'MONITOR'

    def _extract_urgency(self, text: str) -> str:
        """Extract urgency level"""
        if any(word in text.lower() for word in ['immediate', 'urgent', 'quickly', 'now']):
            return 'IMMEDIATE'
        elif any(word in text.lower() for word in ['soon', 'prompt', 'timely']):
            return 'HIGH'
        elif any(word in text.lower() for word in ['wait', 'monitor', 'watch']):
            return 'LOW'
        else:
            return 'MODERATE'

    def _validate_json(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate JSON against schema

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        try:
            self.validator.validate(data)
            return True, []
        except jsonschema.ValidationError as e:
            errors.append(str(e))
            return False, errors
        except Exception as e:
            errors.append(f'Validation error: {str(e)}')
            return False, errors

    def _extract_confidence_score(self, data: Dict[str, Any]) -> Optional[float]:
        """Extract confidence score from validated JSON"""
        try:
            confidence = data.get('analysis_confidence')
            if isinstance(confidence, (int, float)):
                return min(max(confidence, 0.0), 1.0)
            confidence = data.get('recommendation', {}).get('confidence_score')
            if isinstance(confidence, (int, float)):
                return min(max(confidence, 0.0), 1.0)
        except (KeyError, TypeError):
            pass
        return None


def create_response_parser(schema_path: Optional[str] = None) -> LLMResponseParser:
    """
    Factory function to create response parser

    Args:
        schema_path: Optional path to custom schema

    Returns:
        Configured response parser
    """
    return LLMResponseParser(schema_path)


# Example usage
if __name__ == "__main__":
    parser = create_response_parser()

    # Test with sample response
    sample_response = '''
    Based on my analysis, I recommend BUY with high confidence.

    Trade Rationale:
    - Primary catalyst is strong earnings growth
    - Market context is bullish with tech sector leadership

    Risk Assessment:
    - Overall risk level: MODERATE
    - Key risks: volatility, interest rate changes

    Recommendation:
    - Action: BUY
    - Confidence: 0.85
    '''

    parsed = parser.parse_response(sample_response)
    print(f"Parse successful: {parsed.is_valid}")
    print(f"Confidence: {parsed.confidence_score}")
    print(f"Method: {parsed.parse_method}")
    if parsed.parsed_json:
        print(f"Extracted action: {parsed.parsed_json.get('recommendation', {}).get('action')}")