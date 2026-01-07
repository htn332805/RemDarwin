"""
RemDarwin LLM Output Normalizer - Confidence scaling and sentiment polarity conversion

This module provides sophisticated normalization of LLM analysis outputs,
including confidence score calibration, sentiment polarity conversion,
and institutional-grade quality assessment.
"""

import logging
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
import re

logger = logging.getLogger(__name__)


@dataclass
class NormalizedLLMOutput:
    """Container for normalized LLM analysis results"""
    original_confidence: float  # Raw confidence from LLM (0-1)
    normalized_confidence: float  # Calibrated confidence (0-1)
    action_polarity: float  # Sentiment polarity (-1 to +1, where +1 = strong buy signal)
    risk_adjustment: float  # Risk-based adjustment factor
    quality_score: float  # Overall output quality assessment (0-1)
    calibrated_score: float  # Final score for decision matrix (0-100)

    # Analysis components
    action_strength: float  # Strength of recommended action (0-1)
    risk_perception: str  # Perceived risk level
    reasoning_quality: float  # Quality of reasoning (0-1)
    scenario_coverage: float  # Coverage of different scenarios (0-1)

    # Metadata
    normalization_method: str
    calibration_factors: Dict[str, float] = field(default_factory=dict)
    quality_flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "original_confidence": self.original_confidence,
            "normalized_confidence": self.normalized_confidence,
            "action_polarity": self.action_polarity,
            "risk_adjustment": self.risk_adjustment,
            "quality_score": self.quality_score,
            "calibrated_score": self.calibrated_score,
            "action_strength": self.action_strength,
            "risk_perception": self.risk_perception,
            "reasoning_quality": self.reasoning_quality,
            "scenario_coverage": self.scenario_coverage,
            "normalization_method": self.normalization_method,
            "calibration_factors": self.calibration_factors,
            "quality_flags": self.quality_flags
        }


class LLMOutputNormalizer:
    """
    Advanced normalizer for LLM analysis outputs with institutional-grade calibration

    Features:
    - Confidence score normalization and calibration
    - Action sentiment polarity analysis
    - Risk-based adjustments
    - Quality assessment and flagging
    - Historical performance calibration
    """

    def __init__(self):
        # Confidence calibration curves (sigmoid-based for institutional conservatism)
        self.confidence_calibration = {
            "base_curve": self._sigmoid_calibration,
            "conservative_curve": self._conservative_calibration,
            "aggressive_curve": self._aggressive_calibration
        }

        # Action polarity mappings (sentiment analysis for trade actions)
        self.action_polarity_map = {
            "BUY": 1.0,      # Strong positive signal
            "SELL": -1.0,    # Strong negative signal
            "HOLD": 0.0,     # Neutral
            "AVOID": -0.8,   # Strong negative but not full sell
            "MONITOR": -0.2  # Slightly negative, watch closely
        }

        # Risk level adjustment factors
        self.risk_adjustments = {
            "LOW": 1.0,      # No adjustment for low risk
            "MODERATE": 0.9, # Slight reduction for moderate risk
            "HIGH": 0.7,     # Significant reduction for high risk
            "EXTREME": 0.4   # Major reduction for extreme risk
        }

        # Quality assessment weights
        self.quality_weights = {
            "reasoning_completeness": 0.3,
            "scenario_analysis": 0.25,
            "risk_assessment": 0.25,
            "action_justification": 0.2
        }

        # Historical calibration data (would be loaded from performance database)
        self.historical_calibration = {
            "mean_confidence_offset": 0.05,  # Historical mean adjustment
            "confidence_volatility": 0.15,   # Confidence score volatility
            "quality_threshold": 0.7         # Minimum quality score
        }

        logger.info("LLM Output Normalizer initialized with institutional calibration parameters")

    def normalize_output(self, llm_response: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> NormalizedLLMOutput:
        """
        Normalize complete LLM analysis output

        Args:
            llm_response: Parsed LLM response dictionary
            context: Optional context information (market regime, etc.)

        Returns:
            Fully normalized LLM output
        """
        # Extract core components
        original_confidence = self._extract_confidence(llm_response)
        action = self._extract_action(llm_response)
        risk_level = self._extract_risk_level(llm_response)

        # Apply normalization pipeline
        normalized_confidence = self._normalize_confidence(original_confidence, context)
        action_polarity = self._calculate_action_polarity(action, llm_response)
        risk_adjustment = self._calculate_risk_adjustment(risk_level)

        # Quality assessment
        quality_score = self._assess_output_quality(llm_response)
        quality_flags = self._generate_quality_flags(llm_response, quality_score)

        # Action strength analysis
        action_strength = self._assess_action_strength(llm_response)

        # Scenario coverage
        scenario_coverage = self._assess_scenario_coverage(llm_response)

        # Reasoning quality
        reasoning_quality = self._assess_reasoning_quality(llm_response)

        # Risk perception
        risk_perception = risk_level

        # Final calibrated score for decision matrix (0-100 scale)
        calibrated_score = self._calculate_calibrated_score(
            normalized_confidence, action_polarity, risk_adjustment, quality_score
        )

        # Calibration factors for transparency
        calibration_factors = {
            "confidence_normalization": normalized_confidence / max(original_confidence, 0.01),
            "action_polarity": action_polarity,
            "risk_adjustment": risk_adjustment,
            "quality_multiplier": quality_score
        }

        return NormalizedLLMOutput(
            original_confidence=original_confidence,
            normalized_confidence=normalized_confidence,
            action_polarity=action_polarity,
            risk_adjustment=risk_adjustment,
            quality_score=quality_score,
            calibrated_score=calibrated_score,
            action_strength=action_strength,
            risk_perception=risk_perception,
            reasoning_quality=reasoning_quality,
            scenario_coverage=scenario_coverage,
            normalization_method="institutional_calibrated",
            calibration_factors=calibration_factors,
            quality_flags=quality_flags
        )

    def _extract_confidence(self, response: Dict[str, Any]) -> float:
        """Extract confidence score from LLM response"""
        # Try multiple possible locations for confidence
        confidence_sources = [
            response.get("analysis_confidence"),
            response.get("recommendation", {}).get("confidence_score"),
            response.get("confidence"),
            0.5  # Default fallback
        ]

        for conf in confidence_sources:
            if isinstance(conf, (int, float)) and 0 <= conf <= 1:
                return float(conf)

        # Fallback: try to parse from text
        return self._extract_confidence_from_text(str(response))

    def _extract_action(self, response: Dict[str, Any]) -> str:
        """Extract recommended action from LLM response"""
        recommendation = response.get("recommendation", {})
        action = recommendation.get("action", "").upper()

        # Validate action
        if action in self.action_polarity_map:
            return action

        # Fallback to text analysis
        text = str(response).upper()
        if "BUY" in text and "SELL" not in text:
            return "BUY"
        elif "SELL" in text:
            return "SELL"
        elif "AVOID" in text:
            return "AVOID"
        elif "MONITOR" in text:
            return "MONITOR"
        else:
            return "HOLD"

    def _extract_risk_level(self, response: Dict[str, Any]) -> str:
        """Extract risk level assessment"""
        risk_assessment = response.get("risk_assessment", {})
        risk_level = risk_assessment.get("overall_risk_level", "MODERATE").upper()

        if risk_level in self.risk_adjustments:
            return risk_level

        return "MODERATE"  # Default

    def _normalize_confidence(self, confidence: float, context: Optional[Dict[str, Any]] = None) -> float:
        """
        Normalize confidence score using institutional calibration

        Applies conservative calibration curve with market context adjustments
        """
        # Base calibration using conservative curve
        calibrated = self._conservative_calibration(confidence)

        # Apply historical calibration offset
        calibrated += self.historical_calibration["mean_confidence_offset"]

        # Apply market context adjustment if available
        if context:
            market_regime = context.get("market_regime", "").lower()
            if "bear" in market_regime:
                calibrated *= 0.9  # Reduce confidence in bear markets
            elif "high_volatility" in market_regime:
                calibrated *= 0.85  # More conservative in high vol

        # Apply quality-based adjustment (lower quality = lower confidence)
        quality_adjustment = min(1.0, calibrated * 1.1) if calibrated > 0.7 else calibrated

        return max(0.0, min(1.0, quality_adjustment))

    def _sigmoid_calibration(self, x: float) -> float:
        """Sigmoid calibration curve (balanced)"""
        return 1 / (1 + np.exp(-6 * (x - 0.5)))

    def _conservative_calibration(self, x: float) -> float:
        """Conservative calibration curve (reduces high confidence)"""
        # More conservative: sigmoid with lower asymptote
        sigmoid = 1 / (1 + np.exp(-5 * (x - 0.6)))
        return sigmoid * 0.9  # Cap at 90%

    def _aggressive_calibration(self, x: float) -> float:
        """Aggressive calibration curve (amplifies confidence)"""
        return 1 / (1 + np.exp(-7 * (x - 0.4)))

    def _calculate_action_polarity(self, action: str, response: Dict[str, Any]) -> float:
        """Calculate sentiment polarity of recommended action"""
        base_polarity = self.action_polarity_map.get(action, 0.0)

        # Adjust based on urgency level
        urgency = response.get("recommendation", {}).get("urgency_level", "MODERATE")
        urgency_multipliers = {
            "IMMEDIATE": 1.2,
            "HIGH": 1.1,
            "MODERATE": 1.0,
            "LOW": 0.9
        }

        multiplier = urgency_multipliers.get(urgency.upper(), 1.0)
        adjusted_polarity = base_polarity * multiplier

        return max(-1.0, min(1.0, adjusted_polarity))

    def _calculate_risk_adjustment(self, risk_level: str) -> float:
        """Calculate risk-based adjustment factor"""
        return self.risk_adjustments.get(risk_level, 0.8)

    def _assess_output_quality(self, response: Dict[str, Any]) -> float:
        """Assess overall quality of LLM output"""
        scores = []

        # Reasoning completeness
        rationale = response.get("trade_rationale", {})
        rationale_completeness = sum([
            bool(rationale.get("primary_catalyst")),
            bool(rationale.get("market_context")),
            bool(rationale.get("narrative_summary")),
            len(rationale.get("fundamental_factors", [])) > 0,
            len(rationale.get("technical_factors", [])) > 0
        ]) / 5.0
        scores.append(rationale_completeness * self.quality_weights["reasoning_completeness"])

        # Scenario analysis quality
        scenario = response.get("scenario_analysis", {})
        scenario_quality = sum([
            bool(scenario.get("base_case")),
            bool(scenario.get("bull_case") or scenario.get("bear_case")),
            isinstance(scenario.get("base_case", {}).get("probability"), (int, float))
        ]) / 3.0
        scores.append(scenario_quality * self.quality_weights["scenario_analysis"])

        # Risk assessment quality
        risk = response.get("risk_assessment", {})
        risk_quality = sum([
            bool(risk.get("overall_risk_level")),
            len(risk.get("risk_factors", [])) > 0,
            bool(risk.get("tail_risk_assessment"))
        ]) / 3.0
        scores.append(risk_quality * self.quality_weights["risk_assessment"])

        # Action justification
        recommendation = response.get("recommendation", {})
        action_justification = sum([
            bool(recommendation.get("action")),
            isinstance(recommendation.get("confidence_score"), (int, float)),
            bool(recommendation.get("position_sizing_guidance"))
        ]) / 3.0
        scores.append(action_justification * self.quality_weights["action_justification"])

        return sum(scores)

    def _generate_quality_flags(self, response: Dict[str, Any], quality_score: float) -> List[str]:
        """Generate quality flags and warnings"""
        flags = []

        if quality_score < self.historical_calibration["quality_threshold"]:
            flags.append("LOW_QUALITY_OUTPUT")

        # Check for missing critical components
        if not response.get("trade_rationale", {}).get("primary_catalyst"):
            flags.append("MISSING_PRIMARY_CATALYST")

        if not response.get("scenario_analysis", {}).get("base_case"):
            flags.append("MISSING_BASE_CASE")

        if not response.get("risk_assessment", {}).get("risk_factors"):
            flags.append("MISSING_RISK_FACTORS")

        # Check for unrealistic confidence
        confidence = self._extract_confidence(response)
        if confidence > 0.95:
            flags.append("OVERCONFIDENT_OUTPUT")
        elif confidence < 0.1:
            flags.append("UNDERCONFIDENT_OUTPUT")

        return flags

    def _assess_action_strength(self, response: Dict[str, Any]) -> float:
        """Assess strength of recommended action"""
        recommendation = response.get("recommendation", {})
        confidence = recommendation.get("confidence_score", 0.5)
        urgency = recommendation.get("urgency_level", "MODERATE")

        # Base strength from confidence
        strength = confidence

        # Adjust for urgency
        if urgency == "IMMEDIATE":
            strength *= 1.2
        elif urgency == "HIGH":
            strength *= 1.1
        elif urgency == "LOW":
            strength *= 0.9

        return min(1.0, strength)

    def _assess_scenario_coverage(self, response: Dict[str, Any]) -> float:
        """Assess coverage of different market scenarios"""
        scenario = response.get("scenario_analysis", {})

        coverage = sum([
            bool(scenario.get("base_case")),
            bool(scenario.get("bull_case")),
            bool(scenario.get("bear_case"))
        ]) / 3.0

        return coverage

    def _assess_reasoning_quality(self, response: Dict[str, Any]) -> float:
        """Assess quality of reasoning and analysis"""
        rationale = response.get("trade_rationale", {})

        # Check for substantive content
        factors_present = sum([
            len(rationale.get("fundamental_factors", [])) > 0,
            len(rationale.get("technical_factors", [])) > 0,
            bool(rationale.get("primary_catalyst")),
            bool(rationale.get("market_context")),
            bool(rationale.get("narrative_summary"))
        ])

        return factors_present / 5.0

    def _calculate_calibrated_score(self, normalized_confidence: float,
                                  action_polarity: float, risk_adjustment: float,
                                  quality_score: float) -> float:
        """
        Calculate final calibrated score for decision matrix (0-100 scale)

        Combines all normalized factors into final score
        """
        # Base score from confidence and polarity
        base_score = (normalized_confidence + (action_polarity + 1) / 2) / 2

        # Apply risk adjustment
        risk_adjusted_score = base_score * risk_adjustment

        # Apply quality multiplier
        quality_adjusted_score = risk_adjusted_score * quality_score

        # Convert to 0-100 scale
        final_score = quality_adjusted_score * 100

        return max(0.0, min(100.0, final_score))

    def _extract_confidence_from_text(self, text: str) -> float:
        """Extract confidence score from unstructured text"""
        patterns = [
            r'confidence.*?([0-9.]+)%?',
            r'([0-9.]+).*?confidence',
            r'confident.*?([0-9.]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    score = float(match.group(1))
                    if score > 1:  # Convert percentages
                        score /= 100
                    return max(0.0, min(1.0, score))
                except ValueError:
                    continue

        return 0.5  # Default neutral confidence

    def calibrate_from_historical_data(self, historical_data: List[Dict[str, Any]]) -> None:
        """
        Calibrate normalization parameters from historical performance data

        Args:
            historical_data: List of historical LLM outputs with actual outcomes
        """
        if not historical_data:
            return

        # Analyze historical confidence vs. actual performance
        # This would implement machine learning calibration
        # For now, just update basic statistics

        confidences = [self._extract_confidence(item) for item in historical_data]
        if confidences:
            self.historical_calibration["mean_confidence_offset"] = np.mean(confidences) - 0.5
            self.historical_calibration["confidence_volatility"] = np.std(confidences)

        logger.info("Calibration updated from historical data")


def create_llm_normalizer() -> LLMOutputNormalizer:
    """
    Factory function to create LLM output normalizer

    Returns:
        Configured LLMOutputNormalizer instance
    """
    return LLMOutputNormalizer()


if __name__ == "__main__":
    # Test the normalizer
    normalizer = create_llm_normalizer()

    # Sample LLM response
    test_response = {
        "analysis_confidence": 0.85,
        "recommendation": {
            "action": "BUY",
            "confidence_score": 0.85,
            "urgency_level": "HIGH",
            "position_sizing_guidance": "2-3% of portfolio"
        },
        "risk_assessment": {
            "overall_risk_level": "MODERATE",
            "risk_factors": [
                {"factor": "Market volatility", "probability": "MEDIUM", "impact": "HIGH"}
            ]
        },
        "trade_rationale": {
            "primary_catalyst": "Strong earnings momentum",
            "market_context": "Bull market with tech leadership",
            "fundamental_factors": ["Revenue growth", "Margin expansion"],
            "technical_factors": ["Breakout above resistance"],
            "narrative_summary": "Company shows consistent growth"
        },
        "scenario_analysis": {
            "base_case": {"probability": 0.6, "outcome_description": "Steady growth"},
            "bull_case": {"probability": 0.3, "outcome_description": "Strong breakout"},
            "bear_case": {"probability": 0.1, "outcome_description": "Profit taking"}
        }
    }

    # Normalize
    normalized = normalizer.normalize_output(test_response)

    print(f"Original Confidence: {normalized.original_confidence:.2f}")
    print(f"Normalized Confidence: {normalized.normalized_confidence:.2f}")
    print(f"Action Polarity: {normalized.action_polarity:.2f}")
    print(f"Risk Adjustment: {normalized.risk_adjustment:.2f}")
    print(f"Quality Score: {normalized.quality_score:.2f}")
    print(f"Calibrated Score: {normalized.calibrated_score:.1f}")
    print(f"Quality Flags: {normalized.quality_flags}")