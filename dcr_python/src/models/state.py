"""
App state management for DataFerns Traffic Reporter
"""
from typing import Optional, Dict, Any, List, Callable
import pandas as pd
from dataclasses import dataclass, field

@dataclass
class AppState:
    """Centralized state for the traffic analysis application"""
    _current_df: Optional[pd.DataFrame] = None
    _current_metadata: Dict[str, Any] = field(default_factory=dict)
    _listeners: List[Callable] = field(default_factory=list)

    @property
    def current_df(self) -> Optional[pd.DataFrame]:
        return self._current_df

    @property
    def current_metadata(self) -> Dict[str, Any]:
        return self._current_metadata

    def set_data(self, df: pd.DataFrame, metadata: Dict[str, Any]):
        """Update the current data and notify listeners"""
        self._current_df = df
        self._current_metadata = metadata
        self._notify_listeners()

    def subscribe(self, callback: Callable):
        """Subscribe to state changes"""
        self._listeners.append(callback)

    def _notify_listeners(self):
        """Notify all subscribers of data changes"""
        for listener in self._listeners:
            try:
                listener(self._current_df, self._current_metadata)
            except Exception as e:
                print(f"Error in state listener: {e}")

    def has_data(self) -> bool:
        """Check if data is loaded"""
        return self._current_df is not None and not self._current_df.empty
