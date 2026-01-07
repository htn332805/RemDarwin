"""
RemDarwin Decision Matrix - LLM + Quantitative Score Integration

This module implements the core decision matrix that combines quantitative scoring
(80% weight) with LLM interpretive analysis (20% weight) to provide final
trade recommendations for covered calls and cash-secured puts.
"""

import logging
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np

from .response_parser import ParsedResponse

logger = logging.getLogger(__name__)


@dataclass
class QuantitativeScore:
    """Container for quantitative scoring components"""
    total_score: float  # 0-100 scale
    greeks_score: float  # 0-100
    volatility_score: float  # 0-100
    fundamental_score: float  # 0-100
    technical_score: float  # 0-100
    risk_adjusted_score: float  # 0-100
    components: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "total_score": self.total_score,
            "greeks_score": self.greeks_score,
            "volatility_score": self.volatility_score,
            "fundamental_score": self.fundamental_score,
            "technical_score": self.technical_score,
            "risk_adjusted_score": self.risk_adjusted_score,
            "components": self.components
        }


@dataclass
class LLMScore:
    """Container for LLM analysis scoring"""
    confidence_score: float  # 0-1 scale from LLM
    action_recommendation: str  # BUY, SELL, HOLD, AVOID, MONITOR
    risk_level: str  # LOW, MODERATE, HIGH, EXTREME
    urgency_level: str  # IMMEDIATE, HIGH, MODERATE, LOW
    normalized_score: float  # 0-100 scale for matrix integration
    rationale_summary: str
    key_assumptions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "confidence_score": self.confidence_score,
            "action_recommendation": self.action_recommendation,
            "risk_level": self.risk_level,
            "urgency_level": self.urgency_level,
            "normalized_score": self.normalized_score,
            "rationale_summary": self.rationale_summary,
            "key_assumptions": self.key_assumptions
        }


@dataclass
class DecisionMatrixResult:
    """Final decision matrix output"""
    trade_id: str
    timestamp: str
    final_recommendation: str  # BUY, SELL, HOLD, AVOID, MONITOR
    composite_score: float  # 0-100 final score
    confidence_level: str  # HIGH, MEDIUM, LOW
    decision_category: str  # STRONG_BUY, BUY, HOLD, AVOID, STRONG_AVOID

    # Component scores
    quantitative_score: QuantitativeScore
    llm_score: LLMScore

    # Weighting breakdown
    quantitative_weight: float = 0.80
    llm_weight: float = 0.20

    # Decision logic
    score_breakdown: Dict[str, float] = field(default_factory=dict)
    decision_factors: List[str] = field(default_factory=list)
    risk_warnings: List[str] = field(default_factory=list)

    # Metadata
    processing_version: str = "1.0"
    processing_time: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "trade_id": self.trade_id,
            "timestamp": self.timestamp,
            "final_recommendation": self.final_recommendation,
            "composite_score": self.composite_score,
            "confidence_level": self.confidence_level,
            "decision_category": self.decision_category,
            "quantitative_score": self.quantitative_score.to_dict(),
            "llm_score": self.llm_score.to_dict(),
            "quantitative_weight": self.quantitative_weight,
            "llm_weight": self.llm_weight,
            "score_breakdown": self.score_breakdown,
            "decision_factors": self.decision_factors,
            "risk_warnings": self.risk_warnings,
            "processing_version": self.processing_version,
            "processing_time": self.processing_time
        }


class DecisionMatrixEngine:
    """
    Core engine for combining quantitative and LLM scores

    Implements the 80/20 weighting scheme with sophisticated normalization,
    risk adjustment, and decision threshold calibration.
    """

    def __init__(self,
                 quantitative_weight: float = 0.80,
                 llm_weight: float = 0.20,
                 risk_adjustment_factor: float = 0.15,
                 enable_dynamic_weighting: bool = True,
                 confidence_threshold_high: float = 0.8,
                 confidence_threshold_low: float = 0.3):
        """
        Initialize the decision matrix engine

        Args:
            quantitative_weight: Weight for quantitative scoring (default 0.80)
            llm_weight: Weight for LLM scoring (default 0.20)
            risk_adjustment_factor: Risk adjustment multiplier (default 0.15)
        """
        if abs(quantitative_weight + llm_weight - 1.0) > 0.001:
            raise ValueError("Quantitative and LLM weights must sum to 1.0")

        self.base_quantitative_weight = quantitative_weight
        self.base_llm_weight = llm_weight
        self.risk_adjustment_factor = risk_adjustment_factor
        self.enable_dynamic_weighting = enable_dynamic_weighting
        self.confidence_threshold_high = confidence_threshold_high
        self.confidence_threshold_low = confidence_threshold_low

        # Initialize current weights (may be modified dynamically)
        self.quantitative_weight = quantitative_weight
        self.llm_weight = llm_weight

        # Decision thresholds (calibrated for institutional risk tolerance)
        self.decision_thresholds = {
            "STRONG_BUY": 85.0,      # High conviction trades
            "BUY": 70.0,             # Standard buy signals
            "HOLD": 55.0,            # Neutral/monitor zone
            "AVOID": 40.0,           # Below average opportunities
            "STRONG_AVOID": 25.0     # High risk or poor setups
        }

        # Risk level multipliers
        self.risk_multipliers = {
            "LOW": 1.0,
            "MODERATE": 0.9,
            "HIGH": 0.7,
            "EXTREME": 0.4
        }

        # Weighting override configurations
        self.weighting_overrides = {
            "high_confidence_boost": 0.1,  # Boost LLM weight when confidence > threshold
            "low_confidence_penalty": 0.1,  # Reduce LLM weight when confidence < threshold
            "extreme_market_volatility": 0.15,  # Adjust weights in high vol environments
            "earnings_season_adjustment": 0.05,  # Adjust during earnings periods
        }

        logger.info(f"DecisionMatrixEngine initialized with {quantitative_weight:.2f}/{llm_weight:.2f} weighting "
                   f"(dynamic: {enable_dynamic_weighting})")

    def calculate_dynamic_weights(self,
                                quantitative_score: QuantitativeScore,
                                llm_score: LLMScore,
                                context: Optional[Dict[str, Any]] = None) -> Tuple[float, float, Dict[str, Any]]:
        """
        Calculate dynamic weights based on confidence, market conditions, and override rules

        Args:
            quantitative_score: Quantitative scoring results
            llm_score: LLM scoring results
            context: Optional market context information

        Returns:
            Tuple of (quantitative_weight, llm_weight, adjustment_metadata)
        """
        if not self.enable_dynamic_weighting:
            return self.base_quantitative_weight, self.base_llm_weight, {"dynamic_adjustment": False}

        adjustment_metadata = {
            "dynamic_adjustment": True,
            "adjustments_applied": [],
            "original_weights": {
                "quantitative": self.base_quantitative_weight,
                "llm": self.base_llm_weight
            }
        }

        # Start with base weights
        quant_weight = self.base_quantitative_weight
        llm_weight = self.base_llm_weight

        # Confidence-based adjustments
        confidence_adjustment = self._calculate_confidence_adjustment(llm_score.confidence_score)
        if confidence_adjustment != 0:
            quant_weight -= confidence_adjustment
            llm_weight += confidence_adjustment
            adjustment_metadata["adjustments_applied"].append("confidence_based")
            adjustment_metadata["confidence_adjustment"] = confidence_adjustment

        # Market condition adjustments
        if context:
            market_adjustment = self._calculate_market_adjustment(context, llm_score)
            if market_adjustment != 0:
                quant_weight += market_adjustment
                llm_weight -= market_adjustment
                adjustment_metadata["adjustments_applied"].append("market_condition")
                adjustment_metadata["market_adjustment"] = market_adjustment

        # Risk-based adjustments
        risk_adjustment = self._calculate_risk_based_adjustment(llm_score, quantitative_score)
        if risk_adjustment != 0:
            quant_weight += risk_adjustment
            llm_weight -= risk_adjustment
            adjustment_metadata["adjustments_applied"].append("risk_based")
            adjustment_metadata["risk_adjustment"] = risk_adjustment

        # Ensure weights sum to 1.0 and stay within bounds
        quant_weight, llm_weight = self._normalize_weights(quant_weight, llm_weight)

        # Apply any active weight overrides
        quant_weight, llm_weight = self._apply_weight_override(quant_weight, llm_weight)
        if self._weight_override and self._weight_override["active"]:
            adjustment_metadata["adjustments_applied"].append("manual_override")

        adjustment_metadata["final_weights"] = {
            "quantitative": quant_weight,
            "llm": llm_weight
        }

        return quant_weight, llm_weight, adjustment_metadata

    def set_weight_override(self, quantitative_weight: Optional[float] = None,
                           llm_weight: Optional[float] = None,
                           duration_minutes: int = 60) -> Dict[str, Any]:
        """
        Manually override weighting ratios for a specified duration

        Args:
            quantitative_weight: Override quantitative weight (0.0-1.0)
            llm_weight: Override LLM weight (0.0-1.0)
            duration_minutes: How long the override lasts

        Returns:
            Override confirmation metadata
        """
        if quantitative_weight is not None and llm_weight is not None:
            if abs(quantitative_weight + llm_weight - 1.0) > 0.001:
                raise ValueError("Override weights must sum to 1.0")
        elif quantitative_weight is not None:
            llm_weight = 1.0 - quantitative_weight
        elif llm_weight is not None:
            quantitative_weight = 1.0 - llm_weight
        else:
            raise ValueError("Must specify at least one weight to override")

        # Apply bounds checking
        quantitative_weight = max(0.0, min(1.0, quantitative_weight))
        llm_weight = max(0.0, min(1.0, llm_weight))

        # Store override
        from datetime import datetime, timedelta
        self._weight_override = {
            "quantitative_weight": quantitative_weight,
            "llm_weight": llm_weight,
            "start_time": datetime.now(),
            "end_time": datetime.now() + timedelta(minutes=duration_minutes),
            "active": True
        }

        logger.warning(f"Weight override applied: {quantitative_weight:.2f}/{llm_weight:.2f} "
                      f"for {duration_minutes} minutes")

        return {
            "override_applied": True,
            "quantitative_weight": quantitative_weight,
            "llm_weight": llm_weight,
            "expires_at": self._weight_override["end_time"].isoformat(),
            "duration_minutes": duration_minutes
        }

    def clear_weight_override(self) -> bool:
        """Clear any active weight override"""
        if hasattr(self, '_weight_override'):
            self._weight_override = None
            logger.info("Weight override cleared")
            return True
        return False

    def get_weight_override_status(self) -> Dict[str, Any]:
        """Get current weight override status"""
        if not hasattr(self, '_weight_override') or not self._weight_override:
            return {"active": False}

        override = self._weight_override
        now = datetime.now()
        is_expired = now > override["end_time"]

        if is_expired:
            self.clear_weight_override()
            return {"active": False, "expired": True}

        return {
            "active": override["active"],
            "quantitative_weight": override["quantitative_weight"],
            "llm_weight": override["llm_weight"],
            "expires_at": override["end_time"].isoformat(),
            "minutes_remaining": max(0, int((override["end_time"] - now).total_seconds() / 60))
        }

    def _apply_weight_override(self, quant_weight: float, llm_weight: float) -> Tuple[float, float]:
        """Apply any active weight override"""
        if hasattr(self, '_weight_override') and self._weight_override and self._weight_override["active"]:
            override = self._weight_override
            now = datetime.now()

            if now <= override["end_time"]:
                return override["quantitative_weight"], override["llm_weight"]
            else:
                # Override expired
                self.clear_weight_override()

        return quant_weight, llm_weight

    def _calculate_confidence_adjustment(self, confidence: float) -> float:
        """Calculate weight adjustment based on LLM confidence"""
        if confidence >= self.confidence_threshold_high:
            # High confidence - boost LLM weight
            return self.weighting_overrides["high_confidence_boost"]
        elif confidence <= self.confidence_threshold_low:
            # Low confidence - reduce LLM weight
            return -self.weighting_overrides["low_confidence_penalty"]
        else:
            # Medium confidence - no adjustment
            return 0.0

    def _calculate_market_adjustment(self, context: Dict[str, Any], llm_score: LLMScore) -> float:
        """Calculate weight adjustment based on market conditions"""
        adjustment = 0.0

        # Volatility adjustment
        market_volatility = context.get("volatility_regime", "").lower()
        if "high" in market_volatility or "extreme" in market_volatility:
            # In high volatility, rely more on quantitative models
            adjustment += self.weighting_overrides["extreme_market_volatility"]

        # Earnings season adjustment
        is_earnings_season = context.get("is_earnings_season", False)
        if is_earnings_season:
            # During earnings season, be more conservative with LLM
            adjustment += self.weighting_overrides["earnings_season_adjustment"]

        # Market regime adjustment
        market_regime = context.get("market_regime", "").lower()
        if "bear" in market_regime and llm_score.confidence_score < 0.7:
            # In bear markets with uncertain LLM, boost quantitative weight
            adjustment += 0.05

        return adjustment

    def _calculate_risk_based_adjustment(self, llm_score: LLMScore, quant_score: QuantitativeScore) -> float:
        """Calculate weight adjustment based on risk assessments"""
        adjustment = 0.0

        # If LLM shows high risk but quantitative shows low risk, boost quantitative
        llm_risk_level = llm_score.risk_perception.lower()
        quant_risk_score = quant_score.risk_adjusted_score

        if "high" in llm_risk_level or "extreme" in llm_risk_level:
            if quant_risk_score > 70:  # Quantitative says it's not that risky
                adjustment += 0.08  # Boost quantitative weight
            elif quant_risk_score < 40:  # Both agree it's risky
                adjustment += 0.03  # Slight boost to quantitative for confirmation

        # Quality-based adjustment
        if llm_score.quality_score < 0.6:
            # Low quality LLM output - reduce its weight
            adjustment += 0.05

        return adjustment

    def _normalize_weights(self, quant_weight: float, llm_weight: float) -> Tuple[float, float]:
        """Ensure weights sum to 1.0 and stay within reasonable bounds"""
        total = quant_weight + llm_weight

        if abs(total - 1.0) < 0.001:
            # Already normalized
            pass
        else:
            # Renormalize
            quant_weight = quant_weight / total
            llm_weight = llm_weight / total

        # Apply bounds (prevent any weight from going below 0.1 or above 0.9)
        quant_weight = max(0.1, min(0.9, quant_weight))
        llm_weight = max(0.1, min(0.9, llm_weight))

        # Final normalization to ensure exact sum of 1.0
        total = quant_weight + llm_weight
        quant_weight = quant_weight / total
        llm_weight = llm_weight / total

        return quant_weight, llm_weight

    def process_decision(self,
                        trade_id: str,
                        quantitative_score: QuantitativeScore,
                        llm_response: ParsedResponse) -> DecisionMatrixResult:
        """
        Process a complete decision using both quantitative and LLM inputs

        Args:
            trade_id: Unique trade identifier
            quantitative_score: Quantitative scoring results
            llm_response: Parsed LLM analysis response

        Returns:
            Complete decision matrix result
        """
        start_time = datetime.now()

        # Extract LLM score
        llm_score = self._extract_llm_score(llm_response)

        # Calculate dynamic weights based on scores and context
        self.quantitative_weight, self.llm_weight, weight_metadata = self.calculate_dynamic_weights(
            quantitative_score, llm_score, {"market_regime": "normal"}  # Default context
        )

        # Calculate composite score with dynamic weights
        composite_score = self._calculate_composite_score(quantitative_score, llm_score)

        # Determine final recommendation
        final_recommendation, decision_category, confidence_level = self._determine_recommendation(
            composite_score, llm_score
        )

        # Apply any decision overrides
        final_recommendation, override_metadata = self._apply_decision_override(
            trade_id, final_recommendation, composite_score
        )

        # Build decision factors and risk warnings
        decision_factors = self._build_decision_factors(quantitative_score, llm_score)
        risk_warnings = self._build_risk_warnings(quantitative_score, llm_score)

        # Create result
        result = DecisionMatrixResult(
            trade_id=trade_id,
            timestamp=datetime.utcnow().isoformat() + "Z",
            final_recommendation=final_recommendation,
            composite_score=composite_score,
            confidence_level=confidence_level,
            decision_category=decision_category,
            quantitative_score=quantitative_score,
            llm_score=llm_score,
            quantitative_weight=self.quantitative_weight,
            llm_weight=self.llm_weight,
            score_breakdown={
                "quantitative_contribution": quantitative_score.total_score * self.quantitative_weight,
                "llm_contribution": llm_score.normalized_score * self.llm_weight,
                "risk_adjustment": self._calculate_risk_adjustment(llm_score),
                "dynamic_weighting": weight_metadata
            },
            decision_factors=decision_factors,
            risk_warnings=risk_warnings,
            processing_time=(datetime.now() - start_time).total_seconds()
        )

        # Add override metadata to result
        result.override_metadata = override_metadata

        logger.info(f"Decision processed for {trade_id}: {decision_category} ({composite_score:.1f})")
        return result

    def _extract_llm_score(self, llm_response: ParsedResponse) -> LLMScore:
        """
        Extract and normalize LLM score from parsed response

        Args:
            llm_response: Parsed LLM response

        Returns:
            Normalized LLM score
        """
        if not llm_response.is_valid or not llm_response.parsed_json:
            # Fallback for invalid LLM responses
            return LLMScore(
                confidence_score=0.5,
                action_recommendation="MONITOR",
                risk_level="MODERATE",
                urgency_level="MODERATE",
                normalized_score=50.0,
                rationale_summary="LLM analysis unavailable or invalid",
                key_assumptions=["Unable to parse LLM response"]
            )

        data = llm_response.parsed_json

        # Extract core fields with fallbacks
        confidence = data.get('analysis_confidence', 0.5)

        recommendation = data.get('recommendation', {})
        action = recommendation.get('action', 'MONITOR')
        risk_level = data.get('risk_assessment', {}).get('overall_risk_level', 'MODERATE')
        urgency = recommendation.get('urgency_level', 'MODERATE')

        # Normalize confidence to 0-100 scale
        normalized_score = self._normalize_llm_score(confidence, action, risk_level)

        # Extract rationale
        rationale_parts = []
        if 'trade_rationale' in data:
            rationale_parts.extend([
                data['trade_rationale'].get('primary_catalyst', ''),
                data['trade_rationale'].get('narrative_summary', '')
            ])

        rationale_summary = '. '.join(filter(None, rationale_parts)) or "Analysis completed"

        # Extract key assumptions
        assumptions = recommendation.get('key_assumptions', [])

        return LLMScore(
            confidence_score=confidence,
            action_recommendation=action,
            risk_level=risk_level,
            urgency_level=urgency,
            normalized_score=normalized_score,
            rationale_summary=rationale_summary,
            key_assumptions=assumptions
        )

    def _normalize_llm_score(self, confidence: float, action: str, risk_level: str) -> float:
        """
        Normalize LLM confidence to 0-100 scale based on action and risk

        Args:
            confidence: Raw confidence score (0-1)
            action: Recommended action
            risk_level: Risk assessment level

        Returns:
            Normalized score (0-100)
        """
        # Base score from confidence
        base_score = confidence * 100

        # Action modifiers
        action_modifiers = {
            "BUY": 10,      # Positive bias for buy recommendations
            "SELL": -10,    # Negative bias for sell recommendations
            "HOLD": 0,      # Neutral
            "AVOID": -20,   # Strong negative bias
            "MONITOR": -5   # Slight negative bias
        }

        # Risk adjustment
        risk_modifier = 0
        if risk_level in self.risk_multipliers:
            # Higher risk reduces the score
            risk_modifier = (1 - self.risk_multipliers[risk_level]) * -20

        # Apply modifiers
        final_score = base_score + action_modifiers.get(action, 0) + risk_modifier

        # Clamp to valid range
        return max(0.0, min(100.0, final_score))

    def _calculate_composite_score(self,
                                 quant_score: QuantitativeScore,
                                 llm_score: LLMScore) -> float:
        """
        Calculate weighted composite score

        Args:
            quant_score: Quantitative scoring results
            llm_score: LLM scoring results

        Returns:
            Composite score (0-100)
        """
        # Base weighted score
        quant_contribution = quant_score.total_score * self.quantitative_weight
        llm_contribution = llm_score.normalized_score * self.llm_weight

        base_score = quant_contribution + llm_contribution

        # Risk adjustment
        risk_adjustment = self._calculate_risk_adjustment(llm_score)

        # Apply risk adjustment (can be positive or negative)
        final_score = base_score + risk_adjustment

        # Clamp to valid range
        return max(0.0, min(100.0, final_score))

    def _calculate_risk_adjustment(self, llm_score: LLMScore) -> float:
        """
        Calculate risk-based score adjustment

        Args:
            llm_score: LLM scoring results

        Returns:
            Score adjustment value
        """
        if llm_score.risk_level not in self.risk_multipliers:
            return 0.0

        risk_multiplier = self.risk_multipliers[llm_score.risk_level]

        # Calculate adjustment based on deviation from neutral risk
        # High risk reduces score, low risk can slightly increase it
        if risk_multiplier < 1.0:
            adjustment = (1.0 - risk_multiplier) * self.risk_adjustment_factor * -100
        elif risk_multiplier > 1.0:
            adjustment = (risk_multiplier - 1.0) * self.risk_adjustment_factor * 100
        else:
            adjustment = 0.0

        return adjustment

    def _determine_recommendation(self,
                                composite_score: float,
                                llm_score: LLMScore) -> Tuple[str, str, str]:
        """
        Determine final recommendation based on composite score

        Args:
            composite_score: Calculated composite score
            llm_score: LLM scoring results

        Returns:
            Tuple of (recommendation, category, confidence_level)
        """
        # Determine category based on thresholds
        if composite_score >= self.decision_thresholds["STRONG_BUY"]:
            category = "STRONG_BUY"
            recommendation = "BUY"
            confidence = "HIGH"
        elif composite_score >= self.decision_thresholds["BUY"]:
            category = "BUY"
            recommendation = "BUY"
            confidence = "MEDIUM"
        elif composite_score >= self.decision_thresholds["HOLD"]:
            category = "HOLD"
            recommendation = llm_score.action_recommendation
            confidence = "MEDIUM"
        elif composite_score >= self.decision_thresholds["AVOID"]:
            category = "AVOID"
            recommendation = "AVOID"
            confidence = "LOW"
        else:
            category = "STRONG_AVOID"
            recommendation = "AVOID"
            confidence = "LOW"

        # Override based on LLM urgency for high-confidence cases
        if llm_score.confidence_score > 0.8 and llm_score.urgency_level == "IMMEDIATE":
            if category in ["BUY", "STRONG_BUY"]:
                recommendation = "BUY"
                confidence = "HIGH"
            elif category in ["AVOID", "STRONG_AVOID"]:
                recommendation = "AVOID"
                confidence = "HIGH"

        return recommendation, category, confidence

    def _build_decision_factors(self,
                              quant_score: QuantitativeScore,
                              llm_score: LLMScore) -> List[str]:
        """
        Build list of key decision factors

        Args:
            quant_score: Quantitative scoring
            llm_score: LLM scoring

        Returns:
            List of decision factor descriptions
        """
        factors = []

        # Quantitative factors
        if quant_score.greeks_score > 80:
            factors.append("Strong Greeks profile")
        elif quant_score.greeks_score < 40:
            factors.append("Weak Greeks profile")

        if quant_score.volatility_score > 75:
            factors.append("Favorable volatility positioning")
        elif quant_score.volatility_score < 35:
            factors.append("Unfavorable volatility positioning")

        # LLM factors
        if llm_score.confidence_score > 0.8:
            factors.append("High LLM confidence in analysis")
        elif llm_score.confidence_score < 0.4:
            factors.append("Low LLM confidence in analysis")

        if llm_score.risk_level == "LOW":
            factors.append("Low assessed risk level")
        elif llm_score.risk_level == "EXTREME":
            factors.append("Extreme assessed risk level")

        # Add primary catalyst if available
        if llm_score.rationale_summary:
            factors.append(f"Primary catalyst: {llm_score.rationale_summary[:100]}...")

        return factors[:5]  # Limit to 5 most important factors

    def set_decision_override(self, trade_id: str, override_decision: str,
                             reason: str, duration_minutes: int = 60) -> Dict[str, Any]:
        """
        Manually override decision logic for a specific trade or all trades

        Args:
            trade_id: Specific trade ID or "*" for all trades
            override_decision: Override decision ("BUY", "SELL", "HOLD", "AVOID")
            reason: Reason for override
            duration_minutes: Override duration

        Returns:
            Override confirmation metadata
        """
        if override_decision not in ["BUY", "SELL", "HOLD", "AVOID"]:
            raise ValueError("Override decision must be BUY, SELL, HOLD, or AVOID")

        from datetime import datetime, timedelta

        if not hasattr(self, '_decision_overrides'):
            self._decision_overrides = {}

        override_key = trade_id if trade_id != "*" else "GLOBAL"
        self._decision_overrides[override_key] = {
            "decision": override_decision,
            "reason": reason,
            "start_time": datetime.now(),
            "end_time": datetime.now() + timedelta(minutes=duration_minutes),
            "active": True
        }

        logger.warning(f"Decision override set for {trade_id}: {override_decision} "
                      f"({reason}) for {duration_minutes} minutes")

        return {
            "override_applied": True,
            "trade_id": trade_id,
            "override_decision": override_decision,
            "reason": reason,
            "expires_at": self._decision_overrides[override_key]["end_time"].isoformat()
        }

    def get_decision_override(self, trade_id: str) -> Optional[Dict[str, Any]]:
        """Get active decision override for a trade"""
        if not hasattr(self, '_decision_overrides'):
            return None

        overrides = self._decision_overrides
        now = datetime.now()

        # Check specific trade override first
        if trade_id in overrides:
            override = overrides[trade_id]
            if override["active"] and now <= override["end_time"]:
                return override
            elif now > override["end_time"]:
                # Expired
                override["active"] = False

        # Check global override
        if "GLOBAL" in overrides:
            override = overrides["GLOBAL"]
            if override["active"] and now <= override["end_time"]:
                return override
            elif now > override["end_time"]:
                override["active"] = False

        return None

    def clear_decision_override(self, trade_id: str) -> bool:
        """Clear decision override for a specific trade or global"""
        if hasattr(self, '_decision_overrides') and trade_id in self._decision_overrides:
            self._decision_overrides[trade_id]["active"] = False
            logger.info(f"Decision override cleared for {trade_id}")
            return True
        return False

    def _apply_decision_override(self, trade_id: str, original_decision: str,
                                composite_score: float) -> Tuple[str, Dict[str, Any]]:
        """Apply any active decision override"""
        override = self.get_decision_override(trade_id)
        if override:
            override_metadata = {
                "override_applied": True,
                "original_decision": original_decision,
                "original_score": composite_score,
                "override_decision": override["decision"],
                "override_reason": override["reason"],
                "expires_at": override["end_time"].isoformat()
            }
            return override["decision"], override_metadata

        return original_decision, {"override_applied": False}

    def _build_risk_warnings(self,
                           quant_score: QuantitativeScore,
                           llm_score: LLMScore) -> List[str]:
        """
        Build list of risk warnings

        Args:
            quant_score: Quantitative scoring
            llm_score: LLM scoring

        Returns:
            List of risk warning descriptions
        """
        warnings = []

        # Risk-based warnings
        if llm_score.risk_level in ["HIGH", "EXTREME"]:
            warnings.append(f"High risk level: {llm_score.risk_level}")

        if quant_score.risk_adjusted_score < 40:
            warnings.append("Poor risk-adjusted quantitative score")

        if llm_score.confidence_score < 0.3:
            warnings.append("Low LLM confidence may indicate analysis uncertainty")

        # Greeks warnings
        if quant_score.greeks_score < 30:
            warnings.append("Poor Greeks alignment increases risk")

        # Volatility warnings
        if quant_score.volatility_score < 25:
            warnings.append("Unfavorable volatility environment")

        return warnings[:3]  # Limit to 3 most critical warnings

    def calibrate_thresholds(self,
                           historical_performance: List[Dict[str, Any]],
                           target_accuracy: float = 0.75) -> Dict[str, float]:
        """
        Calibrate decision thresholds based on historical performance

        Args:
            historical_performance: List of historical decision outcomes
            target_accuracy: Target accuracy for calibration

        Returns:
            Updated threshold dictionary
        """
        # This would implement machine learning-based threshold calibration
        # For now, return current thresholds
        logger.info("Threshold calibration would be implemented with historical data")
        return self.decision_thresholds.copy()


def create_decision_matrix(quantitative_weight: float = 0.80,
                          llm_weight: float = 0.20) -> DecisionMatrixEngine:
    """
    Factory function to create decision matrix engine

    Args:
        quantitative_weight: Weight for quantitative scoring
        llm_weight: Weight for LLM scoring

    Returns:
        Configured decision matrix engine
    """
    return DecisionMatrixEngine(
        quantitative_weight=quantitative_weight,
        llm_weight=llm_weight
    )


if __name__ == "__main__":
    # Example usage
    engine = create_decision_matrix()

    # Mock quantitative score
    quant_score = QuantitativeScore(
        total_score=78.5,
        greeks_score=82.0,
        volatility_score=75.0,
        fundamental_score=80.0,
        technical_score=76.0,
        risk_adjusted_score=79.0
    )

    # Mock LLM response
    mock_llm_data = {
        "analysis_confidence": 0.85,
        "recommendation": {
            "action": "BUY",
            "confidence_score": 0.85,
            "urgency_level": "HIGH",
            "key_assumptions": ["Market conditions favorable", "Earnings beat expected"]
        },
        "risk_assessment": {
            "overall_risk_level": "MODERATE"
        },
        "trade_rationale": {
            "primary_catalyst": "Strong earnings momentum",
            "narrative_summary": "Company showing consistent growth with positive analyst sentiment"
        }
    }

    from .response_parser import ParsedResponse
    mock_response = ParsedResponse(
        raw_response='{"mock": "data"}',
        parsed_json=mock_llm_data,
        is_valid=True,
        validation_errors=[],
        confidence_score=0.85,
        processing_time=0.1,
        parse_method="direct_json",
        metadata={}
    )

    # Process decision
    result = engine.process_decision("TEST_TRADE_001", quant_score, mock_response)

    print(f"Final Recommendation: {result.final_recommendation}")
    print(f"Composite Score: {result.composite_score:.1f}")
    print(f"Decision Category: {result.decision_category}")
    print(f"Confidence Level: {result.confidence_level}")
    print(f"Decision Factors: {result.decision_factors}")
    print(f"Risk Warnings: {result.risk_warnings}")