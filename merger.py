"""
Data merging and correlation analysis module.

This module handles:
- Merging sleep and workout data by date
- Calculating correlation metrics between sleep and exercise
"""

import statistics
from datetime import date
from collections import defaultdict
from tool.models import SleepRecord, WorkoutRecord, DailyAggregate


def merge_by_day(
    sleep_records: list[SleepRecord],
    workout_records: list[WorkoutRecord]
"""Compatibility shim re-exporting merger functions from `tool.merger`.

The real implementations live in `tool/merger.py`. Importing from the
top-level `merger` module still works for compatibility.
"""

from tool.merger import *  # noqa: F401,F403
            1 for d in days_with_sleep_data
            if d.sleep_hours < 6 and len(d.workouts) > 0
        )
        good_sleep_with_workout = sum(
            1 for d in days_with_sleep_data
            if d.sleep_hours >= 7 and len(d.workouts) > 0
        )

        total_low_sleep = sum(1 for d in days_with_sleep_data if d.sleep_hours < 6)
        total_good_sleep = sum(1 for d in days_with_sleep_data if d.sleep_hours >= 7)

        if total_low_sleep > 0:
            results['workout_rate_low_sleep'] = low_sleep_with_workout / total_low_sleep
        if total_good_sleep > 0:
            results['workout_rate_good_sleep'] = good_sleep_with_workout / total_good_sleep

    return results
