# filters.py - Advanced filtering system for risk management dashboard
"""
FilterManager class for customizable views and filters allowing traders and risk managers
to focus on subsets of data (specific underlyings, sectors, brokers).
"""

import sqlite3
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime, date
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class FilterManager:
    """
    Manages filtering logic for dashboard views.
    Supports symbol, sector, broker filtering with AND/OR logic.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._filter_cache = {}
        self._last_update = None

    def get_available_symbols(self) -> List[Dict[str, str]]:
        """Get all available underlying symbols for filtering."""
        return self._get_cached_filter_options('symbols', """
            SELECT DISTINCT symbol FROM risk_monitoring
            WHERE symbol IS NOT NULL AND symbol != ''
            ORDER BY symbol
        """, 'symbol')

    def get_available_sectors(self) -> List[Dict[str, str]]:
        """Get all available sectors for filtering."""
        # For now, return predefined sectors since sector data may not be in risk_monitoring
        sectors = ['Technology', 'Healthcare', 'Financials', 'Consumer', 'Energy',
                  'Industrials', 'Materials', 'Utilities', 'Real Estate', 'Communication']
        return [{'label': sector, 'value': sector} for sector in sectors]

    def get_available_brokers(self) -> List[Dict[str, str]]:
        """Get all available brokers/contra-parties for filtering."""
        # TODO: Implement broker data retrieval from positions table
        brokers = ['Interactive Brokers', 'TD Ameritrade', 'E*TRADE', 'Fidelity', 'Charles Schwab']
        return [{'label': broker, 'value': broker} for broker in brokers]

    def _get_cached_filter_options(self, cache_key: str, query: str, column: str,
                                 max_age_seconds: int = 300) -> List[Dict[str, str]]:
        """Get filter options with caching to avoid repeated DB queries."""

        # Check cache validity
        now = datetime.now()
        if (self._last_update and
            (now - self._last_update).total_seconds() < max_age_seconds and
            cache_key in self._filter_cache):
            return self._filter_cache[cache_key]

        # Query database
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

            options = [{'label': row[0], 'value': row[0]} for row in rows if row[0]]

            # Cache results
            self._filter_cache[cache_key] = options
            self._last_update = now

            return options

        except Exception as e:
            logger.warning(f"Error getting {cache_key} options: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def apply_filters(self, data: pd.DataFrame, filter_state: Dict[str, Any]) -> pd.DataFrame:
        """
        Apply filters to dashboard data.
        Supports configurable AND/OR logic across filter types.
        """
        if not filter_state or not isinstance(data, pd.DataFrame):
            return data

        logic = filter_state.get('logic', 'AND')
        filtered_data = data.copy()

        # Create filter masks for each type
        masks = []

        # Symbol filtering
        symbols = filter_state.get('symbols', [])
        if symbols and 'symbol' in filtered_data.columns:
            symbol_mask = filtered_data['symbol'].isin(symbols)
            masks.append(symbol_mask)

        # Sector filtering
        sectors = filter_state.get('sectors', [])
        if sectors and 'sector' in filtered_data.columns:
            sector_mask = filtered_data['sector'].isin(sectors)
            masks.append(sector_mask)

        # Broker filtering
        brokers = filter_state.get('brokers', [])
        if brokers and 'broker' in filtered_data.columns:
            broker_mask = filtered_data['broker'].isin(brokers)
            masks.append(broker_mask)

        # Date range filtering
        date_masks = []
        start_date = filter_state.get('start_date')
        end_date = filter_state.get('end_date')

        if start_date and 'timestamp' in filtered_data.columns:
            try:
                start_dt = pd.to_datetime(start_date)
                start_mask = pd.to_datetime(filtered_data['timestamp']) >= start_dt
                date_masks.append(start_mask)
            except Exception as e:
                logger.warning(f"Error filtering by start date: {e}")

        if end_date and 'timestamp' in filtered_data.columns:
            try:
                end_dt = pd.to_datetime(end_date)
                end_mask = pd.to_datetime(filtered_data['timestamp']) <= end_dt
                date_masks.append(end_mask)
            except Exception as e:
                logger.warning(f"Error filtering by end date: {e}")

        # Combine date masks (always AND for date ranges)
        if date_masks:
            date_combined = date_masks[0]
            for mask in date_masks[1:]:
                date_combined &= mask
            masks.append(date_combined)

        # Apply combined filter logic
        if masks:
            if logic == 'AND':
                # All conditions must be true
                combined_mask = masks[0]
                for mask in masks[1:]:
                    combined_mask &= mask
            elif logic == 'OR':
                # Any condition can be true
                combined_mask = masks[0]
                for mask in masks[1:]:
                    combined_mask |= mask
            else:
                # Default to AND
                combined_mask = masks[0]
                for mask in masks[1:]:
                    combined_mask &= mask

            filtered_data = filtered_data[combined_mask]

        logger.info(f"Applied {logic} filters: {len(data)} -> {len(filtered_data)} records")
        return filtered_data

    def combine_filters(self, filter_state: Dict[str, Any], new_filters: Dict[str, Any],
                       logic: str = 'AND') -> Dict[str, Any]:
        """
        Combine multiple filter sets with specified logic (AND/OR).
        For dashboard use, typically AND logic across filter types.
        """
        combined = filter_state.copy()

        if logic == 'AND':
            # AND logic: intersect all filter lists
            for key, values in new_filters.items():
                if key in combined and isinstance(combined[key], list) and isinstance(values, list):
                    combined[key] = list(set(combined[key]) & set(values))
                else:
                    combined[key] = values
        elif logic == 'OR':
            # OR logic: union all filter lists
            for key, values in new_filters.items():
                if key in combined and isinstance(combined[key], list) and isinstance(values, list):
                    combined[key] = list(set(combined[key]) | set(values))
                else:
                    combined[key] = values

        return combined

    def save_filter_preset(self, name: str, filter_state: Dict[str, Any]) -> bool:
        """Save a filter combination as a named preset."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create presets table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS filter_presets (
                    name TEXT PRIMARY KEY,
                    filters TEXT,
                    created_at TEXT
                )
            """)

            import json
            cursor.execute("""
                INSERT OR REPLACE INTO filter_presets (name, filters, created_at)
                VALUES (?, ?, ?)
            """, (name, json.dumps(filter_state), datetime.now().isoformat()))

            conn.commit()
            logger.info(f"Saved filter preset: {name}")
            return True

        except Exception as e:
            logger.error(f"Error saving filter preset {name}: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def load_filter_preset(self, name: str) -> Optional[Dict[str, Any]]:
        """Load a saved filter preset."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT filters FROM filter_presets WHERE name = ?", (name,))
            row = cursor.fetchone()

            if row:
                import json
                return json.loads(row[0])

        except Exception as e:
            logger.error(f"Error loading filter preset {name}: {e}")
        finally:
            if conn:
                conn.close()

        return None

    def get_filter_presets(self) -> List[str]:
        """Get list of saved filter preset names."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT name FROM filter_presets ORDER BY name")
            rows = cursor.fetchall()

            return [row[0] for row in rows]

        except Exception as e:
            logger.error(f"Error getting filter presets: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def reset_filters(self) -> Dict[str, Any]:
        """Return empty filter state (reset)."""
        return {
            'symbols': [],
            'sectors': [],
            'brokers': [],
            'start_date': None,
            'end_date': None
        }

    def validate_filters(self, filter_state: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate filter state for consistency and safety."""
        # Check date range validity
        start_date = filter_state.get('start_date')
        end_date = filter_state.get('end_date')

        if start_date and end_date:
            try:
                start = pd.to_datetime(start_date)
                end = pd.to_datetime(end_date)
                if start > end:
                    return False, "Start date cannot be after end date"
            except Exception as e:
                return False, f"Invalid date format: {e}"

        # Check for reasonable limits to prevent performance issues
        for key in ['symbols', 'sectors', 'brokers']:
            values = filter_state.get(key, [])
            if len(values) > 1000:  # Arbitrary limit
                return False, f"Too many {key} selected (max 1000)"

        return True, "Filters valid"