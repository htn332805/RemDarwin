"""
RemDarwin Prompt Engine - Jinja2 Template Integration for LLM Analysis

This module provides the core functionality for rendering LLM prompts using Jinja2 templates
with quantitative data injection for options trading decision support.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

import jinja2

logger = logging.getLogger(__name__)


@dataclass
class PromptVariables:
    """Structured data class for LLM prompt variables"""

    # Trade identification
    trade_id: str
    timestamp: str

    # Stock and position details
    stock_symbol: str
    stock_price: float
    strategy_type: str  # 'covered_call' or 'cash_secured_put'
    expiration_date: str
    strike_price: float
    option_premium: float
    option_premium_pct: float  # premium as percentage of stock price
    days_to_expiration: int

    # Market context
    market_regime: str  # 'bull', 'bear', 'sideways'
    regime_description: str
    volatility_environment: str  # 'low', 'normal', 'high', 'extreme'

    # Greeks
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float

    # Greeks interpretations
    delta_interpretation: str
    gamma_interpretation: str
    theta_interpretation: str
    vega_interpretation: str

    # Volatility analysis
    implied_volatility: float
    iv_percentile: str
    iv_timeframe: str
    realized_volatility: float
    rv_timeframe: str
    volatility_skew: float
    skew_interpretation: str
    term_structure_description: str

    # Fundamental data
    sector: str
    market_cap_billions: float
    beta: float
    dividend_yield: float
    pe_ratio: float
    performance_summary: str

    # Technical analysis
    trend_direction: str
    trend_strength: str
    support_levels: str
    resistance_levels: str
    volume_analysis: str
    relative_strength_vs_market: str

    # Scoring and risk
    quantitative_score: int
    risk_budget_pct: float
    investment_timeframe: str
    max_risk_tolerance: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for template rendering"""
        return asdict(self)


class PromptEngine:
    """Jinja2 template engine for LLM prompt generation"""

    def __init__(self, template_dir: Optional[str] = None):
        """
        Initialize the prompt engine

        Args:
            template_dir: Directory containing Jinja2 templates (default: same as this file)
        """
        if template_dir is None:
            template_dir = Path(__file__).parent

        self.template_dir = Path(template_dir)
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            autoescape=False  # Safe for our use case
        )

        # Cache for loaded templates
        self._template_cache: Dict[str, jinja2.Template] = {}

        logger.info(f"PromptEngine initialized with template directory: {self.template_dir}")

    def load_template(self, template_name: str) -> jinja2.Template:
        """
        Load a Jinja2 template with caching

        Args:
            template_name: Name of the template file (e.g., 'prompt_template.jinja2')

        Returns:
            Compiled Jinja2 template
        """
        if template_name not in self._template_cache:
            try:
                template = self.env.get_template(template_name)
                self._template_cache[template_name] = template
                logger.debug(f"Loaded and cached template: {template_name}")
            except jinja2.TemplateNotFound:
                raise FileNotFoundError(f"Template not found: {template_name}")
            except jinja2.TemplateSyntaxError as e:
                raise ValueError(f"Template syntax error in {template_name}: {e}")

        return self._template_cache[template_name]

    def render_prompt(self, variables: PromptVariables, template_name: str = "prompt_template.jinja2") -> str:
        """
        Render a prompt using the provided variables

        Args:
            variables: PromptVariables instance with all required data
            template_name: Name of the template to use

        Returns:
            Rendered prompt string
        """
        template = self.load_template(template_name)

        try:
            rendered = template.render(**variables.to_dict())
            logger.debug(f"Successfully rendered prompt for trade_id: {variables.trade_id}")
            return rendered
        except jinja2.UndefinedError as e:
            raise ValueError(f"Undefined variable in template: {e}")
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            raise

    def validate_variables(self, variables: PromptVariables, strict: bool = True) -> bool:
        """
        Comprehensive validation of PromptVariables with length limits and data type checking

        Args:
            variables: PromptVariables to validate
            strict: If True, raise exceptions on validation failures. If False, return validation results.

        Returns:
            True if valid, raises exception if invalid (when strict=True)
        """
        validation_results = self._perform_comprehensive_validation(variables)

        if not validation_results["is_valid"]:
            if strict:
                error_messages = []
                for error in validation_results["errors"]:
                    error_messages.append(f"- {error}")
                raise ValueError(f"PromptVariables validation failed:\n" + "\n".join(error_messages))
            else:
                return False

        logger.debug(f"Variables validation passed for trade_id: {variables.trade_id}")
        return True

    def _perform_comprehensive_validation(self, variables: PromptVariables) -> Dict[str, Any]:
        """Perform comprehensive validation with detailed error reporting"""
        errors = []
        warnings = []

        # Required string fields validation with length limits
        string_limits = {
            'trade_id': (1, 50, "Trade identifier"),
            'stock_symbol': (1, 10, "Stock ticker symbol"),
            'strategy_type': (1, 20, "Strategy type (covered_call/cash_secured_put)"),
            'expiration_date': (8, 12, "Expiration date (YYYY-MM-DD format)"),
            'market_regime': (1, 15, "Market regime"),
            'regime_description': (10, 200, "Market regime description"),
            'volatility_environment': (1, 15, "Volatility environment"),
            'sector': (1, 50, "Company sector"),
            'trend_direction': (1, 15, "Trend direction"),
            'trend_strength': (1, 20, "Trend strength description"),
            'iv_timeframe': (1, 20, "IV timeframe"),
            'rv_timeframe': (1, 20, "RV timeframe"),
            'skew_interpretation': (1, 100, "Skew interpretation"),
            'term_structure_description': (1, 100, "Term structure description"),
            'performance_summary': (1, 200, "Company performance summary"),
            'support_levels': (1, 100, "Support levels"),
            'resistance_levels': (1, 100, "Resistance levels"),
            'volume_analysis': (1, 100, "Volume analysis"),
            'relative_strength_vs_market': (1, 100, "Relative strength description"),
            'investment_timeframe': (1, 50, "Investment timeframe"),
            # max_risk_tolerance handled separately as string
        }

        for field, (min_len, max_len, description) in string_limits.items():
            value = getattr(variables, field, "")
            if not isinstance(value, str):
                errors.append(f"{description} ({field}) must be a string, got {type(value).__name__}")
            elif not value.strip():
                errors.append(f"{description} ({field}) cannot be empty")
            elif len(value.strip()) < min_len:
                errors.append(f"{description} ({field}) is too short (minimum {min_len} characters)")
            elif len(value.strip()) > max_len:
                errors.append(f"{description} ({field}) is too long (maximum {max_len} characters)")
                # Truncate if too long (warning, not error)
                warnings.append(f"{description} ({field}) truncated to {max_len} characters")

        # Numeric field validations with ranges and types
        numeric_validations = {
            'stock_price': (0.01, 10000.0, float, "Stock price"),
            'strike_price': (0.01, 10000.0, float, "Strike price"),
            'option_premium': (0.0, 1000.0, float, "Option premium"),
            'option_premium_pct': (0.0, 50.0, float, "Option premium percentage"),
            'days_to_expiration': (1, 1000, int, "Days to expiration"),
            'delta': (-1.0, 1.0, float, "Delta"),
            'gamma': (-1.0, 1.0, float, "Gamma"),
            'theta': (-10.0, 10.0, float, "Theta"),
            'vega': (-5.0, 5.0, float, "Vega"),
            'rho': (-5.0, 5.0, float, "Rho"),
            'implied_volatility': (0.0, 5.0, float, "Implied volatility"),
            'realized_volatility': (0.0, 5.0, float, "Realized volatility"),
            'iv_percentile': (0.0, 100.0, (int, float), "IV percentile"),
            'volatility_skew': (-2.0, 2.0, float, "Volatility skew"),
            'market_cap_billions': (0.0, 10000.0, float, "Market cap (billions)"),
            'beta': (-5.0, 5.0, float, "Beta"),
            'dividend_yield': (0.0, 20.0, float, "Dividend yield"),
            'pe_ratio': (0.0, 500.0, (int, float), "P/E ratio"),
            'quantitative_score': (0, 100, (int, float), "Quantitative score"),
            'risk_budget_pct': (0.0, 100.0, float, "Risk budget percentage")
        }

        for field, (min_val, max_val, expected_type, description) in numeric_validations.items():
            value = getattr(variables, field)

            # Type checking
            if expected_type == (int, float):
                if not isinstance(value, (int, float)):
                    errors.append(f"{description} ({field}) must be numeric, got {type(value).__name__}")
                    continue
            elif not isinstance(value, expected_type):
                errors.append(f"{description} ({field}) must be {expected_type.__name__}, got {type(value).__name__}")
                continue

            # Range checking
            if isinstance(value, (int, float)) and not (min_val <= value <= max_val):
                errors.append(f"{description} ({field}) {value} is outside valid range [{min_val}, {max_val}]")

        # Special validations for categorical fields
        if variables.strategy_type not in ['covered_call', 'cash_secured_put']:
            errors.append(f"Strategy type must be 'covered_call' or 'cash_secured_put', got '{variables.strategy_type}'")

        if variables.market_regime not in ['bull', 'bear', 'sideways', 'volatile']:
            warnings.append(f"Market regime '{variables.market_regime}' is non-standard")

        if variables.volatility_environment not in ['low', 'normal', 'high', 'extreme']:
            warnings.append(f"Volatility environment '{variables.volatility_environment}' is non-standard")

        if variables.trend_direction not in ['upward', 'downward', 'sideways', 'volatile']:
            warnings.append(f"Trend direction '{variables.trend_direction}' is non-standard")

        # Greeks interpretation validations
        greek_interpretations = ['delta_interpretation', 'gamma_interpretation', 'theta_interpretation', 'vega_interpretation']
        for interp_field in greek_interpretations:
            value = getattr(variables, interp_field, "")
            if not isinstance(value, str) or len(value.strip()) < 3:
                errors.append(f"{interp_field} must be a descriptive string (minimum 3 characters)")
            elif len(value.strip()) > 100:
                warnings.append(f"{interp_field} is quite long, consider shortening")

        # Timestamp validation
        try:
            datetime.fromisoformat(variables.timestamp.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            errors.append(f"Invalid timestamp format: {variables.timestamp} (expected ISO format)")

        # Cross-field validations
        if variables.strike_price >= variables.stock_price * 1.5:
            warnings.append("Strike price is very high relative to stock price - consider risk implications")

        if variables.option_premium_pct > 10.0:
            warnings.append("Option premium percentage is quite high - verify pricing")

        if variables.days_to_expiration > 180:
            warnings.append("Expiration is quite far out - theta decay will be slower")

        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "field_count": len([f for f in variables.__dataclass_fields__.values() if getattr(variables, f.name) is not None])
        }

    def get_validation_report(self, variables: PromptVariables) -> Dict[str, Any]:
        """
        Get detailed validation report without raising exceptions

        Args:
            variables: PromptVariables to analyze

        Returns:
            Comprehensive validation report
        """
        return self._perform_comprehensive_validation(variables)

    def create_sample_variables(self) -> PromptVariables:
        """
        Create sample PromptVariables for testing

        Returns:
            Sample PromptVariables instance
        """
        return PromptVariables(
            trade_id="TEST_001",
            timestamp=datetime.utcnow().isoformat() + "Z",
            stock_symbol="AAPL",
            stock_price=150.25,
            strategy_type="covered_call",
            expiration_date="2024-02-16",
            strike_price=155.0,
            option_premium=2.50,
            option_premium_pct=1.66,  # 2.50 / 150.25 * 100
            days_to_expiration=45,
            market_regime="bull",
            regime_description="moderate bull market with tech sector leadership",
            volatility_environment="normal",
            delta=0.65,
            gamma=0.03,
            theta=-0.25,
            vega=-0.15,
            rho=0.08,
            delta_interpretation="moderately bullish position",
            gamma_interpretation="low convexity",
            theta_interpretation="time decay working against position",
            vega_interpretation="beneficial in rising vol environment",
            implied_volatility=0.22,
            iv_percentile=65.0,
            iv_timeframe="30-day",
            realized_volatility=0.18,
            rv_timeframe="30-day",
            volatility_skew=0.05,
            skew_interpretation="slightly bearish skew",
            term_structure_description="normal backwardation",
            sector="Technology",
            market_cap_billions=2.8,
            beta=1.2,
            dividend_yield=0.5,
            pe_ratio=28.5,
            performance_summary="up 15% YTD, outperforming market",
            trend_direction="upward",
            trend_strength="moderate",
            support_levels="$145, $142",
            resistance_levels="$158, $162",
            volume_analysis="above average volume on up days",
            relative_strength_vs_market="outperforming by 5%",
            quantitative_score=85,
            risk_budget_pct=2.0,
            investment_timeframe="4-6 weeks",
            max_risk_tolerance="5% of portfolio value"
        )


def main():
    """Main function for testing the prompt engine"""
    logging.basicConfig(level=logging.INFO)

    # Initialize engine
    engine = PromptEngine()

    # Create sample variables
    variables = engine.create_sample_variables()

    # Validate
    try:
        engine.validate_variables(variables)
        print("✅ Variables validation passed")
    except ValueError as e:
        print(f"❌ Validation failed: {e}")
        return

    # Render prompt
    try:
        prompt = engine.render_prompt(variables)
        print("✅ Prompt rendered successfully")
        print(f"Prompt length: {len(prompt)} characters")

        # Save to file for inspection
        with open("sample_prompt.txt", "w") as f:
            f.write(prompt)
        print("✅ Sample prompt saved to sample_prompt.txt")

    except Exception as e:
        print(f"❌ Rendering failed: {e}")


if __name__ == "__main__":
    main()