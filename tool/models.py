"""
Data models for the Personal Health Data Aggregator.

This module defines the data structures used throughout the application:
- SleepRecord: Normalized sleep session
- WorkoutRecord: Normalized workout session
- DailyAggregate: Merged daily health data
"""

from dataclasses import dataclass
from datetime import datetime, date
from typing import Optional


@dataclass
class SleepRecord:
    """Normalized sleep record."""
    date_utc: date
    sleep_start_utc: datetime
    sleep_end_utc: datetime
    duration_hours: float
    quality_score: int


@dataclass
class WorkoutRecord:
    """Normalized workout record."""
    id: str
    timestamp_utc: datetime
    date_utc: date  # The UTC date this workout is attributed to
    original_timestamp: str
    original_timezone: str
    workout_type: str
    duration_min: int
    calories: int
    crossed_day_boundary: bool  # Flag for edge case tracking


@dataclass
class DailyAggregate:
    """Merged daily health data."""
    date_utc: date
    sleep_hours: Optional[float] = None
    sleep_quality: Optional[int] = None
    workouts: list = None
    total_calories: int = 0
    total_workout_minutes: int = 0

    def __post_init__(self):
        if self.workouts is None:
            self.workouts = []
