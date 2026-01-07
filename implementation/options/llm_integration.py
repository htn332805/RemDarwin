"""
LLM Integration Layer for RemDarwin Options Trading System

This module provides AI-driven analysis for options trading decisions including
risk assessment, trade rationale generation, and market sentiment analysis.

Functions:
    assess_risk_with_llm: AI-driven risk assessment
    generate_trade_rationale: Natural language trade explanations
    calibrate_confidence: Confidence scoring system
    analyze_sentiment: Market sentiment analysis
    compare_historical_trades: Comparative historical analysis

Dependencies: openai, anthropic, datetime, json, logging
"""

import os
import json
import datetime
import logging
from typing import Dict, Optional, Tuple
import time

# Import LLM providers (optional dependencies)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


# Prompt Templates
RISK_ASSESSMENT_TEMPLATE = """
Analyze the following options trade for risk assessment:

TRADE DETAILS:
- Symbol: {symbol}
- Option Type: {option_type}
- Strike Price: ${strike_price}
- Expiration Date: {expiration_date}
- Days to Expiration: {days_to_expiration}
- Underlying Price: ${underlying_price}

GREEKS ANALYSIS:
- Delta: {delta}
- Gamma: {gamma}
- Theta: {theta}
- Vega: {vega}
- Rho: {rho}
- Implied Volatility: {implied_volatility}%

MARKET CONTEXT:
- Bid Price: ${bid}
- Ask Price: ${ask}
- Spread: ${spread}
- Volume: {volume}
- Open Interest: {open_interest}

Please provide a comprehensive risk assessment in the following JSON format:
{{
    "risk_level": "LOW|MEDIUM|HIGH|VERY_HIGH",
    "risk_score": 1-10,
    "key_risk_factors": ["factor1", "factor2", ...],
    "recommended_position_size": "percentage or dollar amount",
    "exit_strategy": "brief strategy description",
    "market_conditions_impact": "analysis of current conditions",
    "confidence_level": 0.0-1.0
}}
"""

TRADE_RATIONALE_TEMPLATE = """
Generate a comprehensive trade rationale for the following options position:

POSITION DETAILS:
- Symbol: {symbol}
- Strategy: {option_type} option
- Strike Price: ${strike_price}
- Expiration: {expiration_date}
- Entry Price: ${entry_price}
- Current Underlying: ${underlying_price}

QUANTITATIVE ANALYSIS:
- Delta: {delta} (directional exposure)
- Gamma: {gamma} (delta sensitivity)
- Theta: {theta} (time decay)
- Vega: {vega} (volatility sensitivity)
- Expected Return: {expected_return}%

MARKET CONTEXT:
- Implied Volatility: {implied_volatility}% (vs historical {historical_vol}%)
- Bid-Ask Spread: ${spread}
- Market Trend: {market_trend}

Please provide a detailed trade rationale explaining:
1. Why this trade was selected
2. Key quantitative factors supporting the position
3. Risk-reward analysis
4. Market timing considerations
5. Exit criteria and profit targets

Format as a coherent paragraph suitable for client reporting.
"""

SENTIMENT_ANALYSIS_TEMPLATE = """
Analyze market sentiment for {symbol} based on the following context:

CURRENT MARKET DATA:
- Stock Price: ${underlying_price}
- Recent Performance: {price_change}% over {time_period}
- Trading Volume: {volume} (vs average {avg_volume})
- Options Volume: {options_volume}

TECHNICAL INDICATORS:
- RSI: {rsi}
- MACD: {macd_signal}
- Moving Averages: {ma_analysis}

RECENT NEWS HEADLINES:
{news_headlines}

Please analyze the overall market sentiment and provide:
1. Sentiment classification (BULLISH|BEARISH|NEUTRAL)
2. Confidence score (0.0-1.0)
3. Key sentiment drivers
4. Expected volatility impact
5. Trading implications for options
"""

COMPARATIVE_ANALYSIS_TEMPLATE = """
Compare the current {symbol} {option_type} position with similar historical trades:

CURRENT TRADE:
- Strike: ${strike_price}
- Expiration: {expiration_date}
- Delta: {delta}
- Vega: {vega}
- Implied Volatility: {implied_volatility}%

SIMILAR HISTORICAL TRADES:
{historical_trades}

MARKET CONDITIONS:
- Current VIX: {current_vix}
- Historical VIX at trade time: {historical_vix}

Please provide comparative analysis including:
1. Performance patterns of similar trades
2. Key success factors identified
3. Risk factors that emerged
4. Recommended adjustments based on historical outcomes
5. Confidence level in current trade setup
"""


class LLMIntegrationLayer:
    """
    AI-powered analysis layer for options trading decisions.
    """

    def __init__(self, provider='openai', api_key=None, model='gpt-4'):
        """
        Initialize LLM integration with specified provider.

        Args:
            provider: 'openai' or 'anthropic'
            api_key: API key (if None, uses environment variables)
            model: Model name/version
        """
        self.provider = provider.lower()
        self.model = model
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour cache

        # Set API key
        if api_key:
            self.api_key = api_key
        else:
            if self.provider == 'openai':
                self.api_key = os.getenv('OPENAI_API_KEY')
            elif self.provider == 'anthropic':
                self.api_key = os.getenv('ANTHROPIC_API_KEY')
            else:
                raise ValueError(f"Unsupported provider: {provider}")

        if not self.api_key:
            raise ValueError(f"API key not found for provider {provider}")

        # Initialize client
        self.client = self._initialize_client()
        self.logger = logging.getLogger(__name__)

    def _initialize_client(self):
        """Initialize the appropriate LLM client."""
        if self.provider == 'openai' and OPENAI_AVAILABLE:
            return openai.OpenAI(api_key=self.api_key)
        elif self.provider == 'anthropic' and ANTHROPIC_AVAILABLE:
            return anthropic.Anthropic(api_key=self.api_key)
        else:
            raise ImportError(f"Required library for {self.provider} not available")

    def _get_cache_key(self, prompt: str, **kwargs) -> str:
        """Generate cache key from prompt and parameters."""
        key_data = {'prompt': prompt[:100], **kwargs}  # Limit prompt length
        return json.dumps(key_data, sort_keys=True)

    def _get_cached_response(self, cache_key: str) -> Optional[Dict]:
        """Retrieve cached response if valid."""
        if cache_key in self.cache:
            cached_time, response = self.cache[cache_key]
            if time.time() - cached_time < self.cache_ttl:
                return response
            else:
                del self.cache[cache_key]
        return None

    def _cache_response(self, cache_key: str, response: Dict):
        """Cache the response with timestamp."""
        self.cache[cache_key] = (time.time(), response)

    def _call_llm(self, prompt: str, **kwargs) -> Dict:
        """
        Make LLM API call with caching and error handling.

        Args:
            prompt: Formatted prompt text
            **kwargs: Additional parameters for prompt formatting

        Returns:
            Dict containing response and metadata
        """
        cache_key = self._get_cache_key(prompt, **kwargs)
        cached = self._get_cached_response(cache_key)
        if cached:
            self.logger.info("Using cached LLM response")
            return cached

        try:
            if self.provider == 'openai':
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=1000
                )
                content = response.choices[0].message.content

            elif self.provider == 'anthropic':
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=1000,
                    temperature=0.3,
                    messages=[{"role": "user", "content": prompt}]
                )
                content = response.content[0].text

            # Parse JSON if response looks like JSON
            try:
                if content.strip().startswith('{'):
                    result = json.loads(content)
                else:
                    result = {'text_response': content}
            except json.JSONDecodeError:
                result = {'text_response': content}

            # Add metadata
            result['_metadata'] = {
                'provider': self.provider,
                'model': self.model,
                'timestamp': datetime.datetime.utcnow().isoformat(),
                'cached': False
            }

            self._cache_response(cache_key, result)
            return result

        except Exception as e:
            self.logger.error(f"LLM API call failed: {e}")
            # Return fallback response
            return {
                'error': str(e),
                'fallback': True,
                '_metadata': {
                    'provider': self.provider,
                    'model': self.model,
                    'timestamp': datetime.datetime.utcnow().isoformat(),
                    'error': True
                }
            }


def assess_risk_with_llm(llm_layer: LLMIntegrationLayer, trade_data: Dict) -> Dict:
    """
    AI-driven risk assessment for options trades.

    Args:
        llm_layer: Initialized LLM integration layer
        trade_data: Dictionary with trade details and Greeks

    Returns:
        Dict with risk assessment results
    """
    prompt = RISK_ASSESSMENT_TEMPLATE.format(**trade_data)

    response = llm_layer._call_llm(prompt, symbol=trade_data.get('symbol'))

    # Validate and structure response
    if 'error' in response:
        return {
            'risk_level': 'UNKNOWN',
            'risk_score': 5,
            'key_risk_factors': ['API Error'],
            'recommended_position_size': 'Conservative',
            'exit_strategy': 'Monitor closely',
            'confidence_level': 0.5,
            'error': response['error']
        }

    # Extract structured data if available
    try:
        risk_assessment = {
            'risk_level': response.get('risk_level', 'MEDIUM'),
            'risk_score': response.get('risk_score', 5),
            'key_risk_factors': response.get('key_risk_factors', []),
            'recommended_position_size': response.get('recommended_position_size', 'Standard'),
            'exit_strategy': response.get('exit_strategy', 'Monitor Greeks'),
            'market_conditions_impact': response.get('market_conditions_impact', 'Standard market conditions'),
            'confidence_level': response.get('confidence_level', 0.8)
        }
    except Exception as e:
        llm_layer.logger.warning(f"Failed to parse risk assessment response: {e}")
        risk_assessment = {
            'risk_level': 'MEDIUM',
            'risk_score': 5,
            'key_risk_factors': ['Response parsing error'],
            'recommended_position_size': 'Standard',
            'exit_strategy': 'Monitor closely',
            'confidence_level': 0.5
        }

    return risk_assessment


def generate_trade_rationale(llm_layer: LLMIntegrationLayer, trade_data: Dict) -> str:
    """
    Generate natural language trade rationale.

    Args:
        llm_layer: Initialized LLM integration layer
        trade_data: Dictionary with trade details

    Returns:
        String containing trade rationale
    """
    prompt = TRADE_RATIONALE_TEMPLATE.format(**trade_data)

    response = llm_layer._call_llm(prompt, symbol=trade_data.get('symbol'))

    if 'error' in response:
        return f"Trade rationale generation failed: {response['error']}. This {trade_data.get('option_type', 'option')} position at strike ${trade_data.get('strike_price', 'N/A')} was selected based on quantitative analysis of Greeks and market conditions."

    return response.get('text_response', 'Trade rationale could not be generated.')


def calibrate_confidence(llm_layer: LLMIntegrationLayer, historical_performance: Dict) -> float:
    """
    Calibrate confidence based on historical LLM accuracy.

    Args:
        llm_layer: Initialized LLM integration layer
        historical_performance: Dict with historical accuracy metrics

    Returns:
        Float confidence score (0.0-1.0)
    """
    # Simple calibration based on recent performance
    recent_accuracy = historical_performance.get('recent_accuracy', 0.8)
    sample_size = historical_performance.get('sample_size', 100)

    # Apply domain-specific adjustments
    if llm_layer.provider == 'openai':
        base_confidence = 0.85
    elif llm_layer.provider == 'anthropic':
        base_confidence = 0.82
    else:
        base_confidence = 0.7

    # Adjust based on historical performance
    confidence = base_confidence * recent_accuracy

    # Adjust based on sample size (more data = higher confidence)
    if sample_size < 50:
        confidence *= 0.9
    elif sample_size > 500:
        confidence *= 1.05

    return min(1.0, max(0.0, confidence))


def analyze_sentiment(llm_layer: LLMIntegrationLayer, market_data: Dict) -> Dict:
    """
    Analyze market sentiment for options implications.

    Args:
        llm_layer: Initialized LLM integration layer
        market_data: Dictionary with market data and news

    Returns:
        Dict with sentiment analysis
    """
    prompt = SENTIMENT_ANALYSIS_TEMPLATE.format(**market_data)

    response = llm_layer._call_llm(prompt, symbol=market_data.get('symbol'))

    if 'error' in response:
        return {
            'sentiment': 'NEUTRAL',
            'confidence': 0.5,
            'key_drivers': ['API Error'],
            'volatility_impact': 'Unknown',
            'trading_implications': 'Monitor market conditions'
        }

    # Structure response
    try:
        sentiment_analysis = {
            'sentiment': response.get('sentiment', 'NEUTRAL'),
            'confidence': response.get('confidence', 0.7),
            'key_drivers': response.get('key_drivers', []),
            'volatility_impact': response.get('volatility_impact', 'Moderate'),
            'trading_implications': response.get('trading_implications', 'Standard options strategy')
        }
    except Exception as e:
        llm_layer.logger.warning(f"Failed to parse sentiment response: {e}")
        sentiment_analysis = {
            'sentiment': 'NEUTRAL',
            'confidence': 0.5,
            'key_drivers': ['Response parsing error'],
            'volatility_impact': 'Unknown',
            'trading_implications': 'Monitor developments'
        }

    return sentiment_analysis


def compare_historical_trades(llm_layer: LLMIntegrationLayer, current_trade: Dict, historical_trades: list) -> Dict:
    """
    Compare current trade with similar historical trades.

    Args:
        llm_layer: Initialized LLM integration layer
        current_trade: Current trade details
        historical_trades: List of similar historical trades

    Returns:
        Dict with comparative analysis
    """
    # Format historical trades for prompt
    hist_formatted = "\n".join([
        f"- {trade.get('date', 'Unknown')}: {trade.get('outcome', 'Unknown outcome')}"
        for trade in historical_trades[:5]  # Limit to 5 examples
    ])

    prompt_data = {
        **current_trade,
        'historical_trades': hist_formatted
    }

    prompt = COMPARATIVE_ANALYSIS_TEMPLATE.format(**prompt_data)

    response = llm_layer._call_llm(prompt, symbol=current_trade.get('symbol'))

    if 'error' in response:
        return {
            'performance_patterns': 'Unable to analyze due to API error',
            'success_factors': ['Historical analysis unavailable'],
            'risk_factors': ['API connectivity issues'],
            'recommended_adjustments': ['Monitor trade closely'],
            'confidence_level': 0.5
        }

    # Structure response
    try:
        comparison = {
            'performance_patterns': response.get('performance_patterns', 'Mixed historical results'),
            'success_factors': response.get('key_success_factors', []),
            'risk_factors': response.get('risk_factors', []),
            'recommended_adjustments': response.get('recommended_adjustments', ['Standard position management']),
            'confidence_level': response.get('confidence_level', 0.7)
        }
    except Exception as e:
        llm_layer.logger.warning(f"Failed to parse comparison response: {e}")
        comparison = {
            'performance_patterns': 'Analysis unavailable',
            'success_factors': ['Unable to determine'],
            'risk_factors': ['Response parsing error'],
            'recommended_adjustments': ['Use standard risk management'],
            'confidence_level': 0.5
        }

    return comparison


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Example usage (requires API keys)
    try:
        llm = LLMIntegrationLayer(provider='openai', model='gpt-3.5-turbo')

        # Test risk assessment
        sample_trade = {
            'symbol': 'AAPL',
            'option_type': 'call',
            'strike_price': 150,
            'expiration_date': '2024-03-15',
            'days_to_expiration': 45,
            'underlying_price': 145,
            'delta': 0.65,
            'gamma': 0.03,
            'theta': -0.02,
            'vega': 0.15,
            'rho': 0.08,
            'implied_volatility': 25,
            'bid': 4.50,
            'ask': 4.75,
            'spread': 0.25,
            'volume': 1250,
            'open_interest': 5000
        }

        risk = assess_risk_with_llm(llm, sample_trade)
        print("Risk Assessment:", json.dumps(risk, indent=2))

    except Exception as e:
        print(f"LLM integration test failed: {e}")