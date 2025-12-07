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
) -> dict[date, DailyAggregate]:
    """
    Merge sleep and workout data by UTC date.
    """
    daily_data = defaultdict(lambda: DailyAggregate(date_utc=None))

    # Add sleep data
    for sleep in sleep_records:
        day = sleep.date_utc
        daily_data[day].date_utc = day
        daily_data[day].sleep_hours = sleep.duration_hours
        daily_data[day].sleep_quality = sleep.quality_score

    # Add workout data
    for workout in workout_records:
        day = workout.date_utc
        daily_data[day].date_utc = day
        daily_data[day].workouts.append(workout)
        daily_data[day].total_calories += workout.calories
        daily_data[day].total_workout_minutes += workout.duration_min

    return dict(daily_data)


def calculate_correlations(daily_data: dict[date, DailyAggregate]) -> dict:
    """
    Calculate correlation metrics between sleep and exercise.
    """
    results = {}

    low_sleep_days = [
        d for d in daily_data.values()
        if d.sleep_hours is not None and d.sleep_hours < 6 and d.total_calories > 0
    ]

    good_sleep_days = [
        d for d in daily_data.values()
        if d.sleep_hours is not None and d.sleep_hours >= 7 and d.total_calories > 0
    ]

    if low_sleep_days:
        results['avg_calories_low_sleep'] = statistics.mean(
            [d.total_calories for d in low_sleep_days]
        )
        results['low_sleep_day_count'] = len(low_sleep_days)

    if good_sleep_days:
        results['avg_calories_good_sleep'] = statistics.mean(
            [d.total_calories for d in good_sleep_days]
        )
        results['good_sleep_day_count'] = len(good_sleep_days)

    days_with_sleep_data = [d for d in daily_data.values() if d.sleep_hours is not None]

    if days_with_sleep_data:
        low_sleep_with_workout = sum(
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
