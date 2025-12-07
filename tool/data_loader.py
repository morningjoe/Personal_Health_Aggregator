"""
Data loading and normalization module.

This module handles:
- Loading sleep data from JSON
- Loading workout data from JSON
- Converting all timestamps to UTC
- Detecting day boundary crossings
- Comprehensive error handling for invalid data
"""

import json
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from tool.models import SleepRecord, WorkoutRecord


# Required fields for sleep and workout records
SLEEP_REQUIRED_FIELDS = {'sleep_start', 'sleep_end', 'duration_hours', 'quality_score'}
WORKOUT_REQUIRED_FIELDS = {'id', 'timestamp', 'tz', 'type', 'duration_min', 'calories'}


def validate_sleep_entry(entry: dict, index: int) -> None:
    """
    Validate that a sleep entry has all required fields.
    """
    missing_fields = SLEEP_REQUIRED_FIELDS - set(entry.keys())
    if missing_fields:
        raise ValueError(
            f"Sleep record {index}: Missing required fields: {', '.join(sorted(missing_fields))}. "
            f"Required: {', '.join(sorted(SLEEP_REQUIRED_FIELDS))}"
        )


def validate_workout_entry(entry: dict, index: int) -> None:
    """
    Validate that a workout entry has all required fields.
    """
    missing_fields = WORKOUT_REQUIRED_FIELDS - set(entry.keys())
    if missing_fields:
        raise ValueError(
            f"Workout record {index}: Missing required fields: {', '.join(sorted(missing_fields))}. "
            f"Required: {', '.join(sorted(WORKOUT_REQUIRED_FIELDS))}"
        )


def load_sleep_data(filepath: str) -> list[SleepRecord]:
    """
    Load sleep data from JSON file with comprehensive error handling.
    Skips invalid records and prints warnings for each skipped entry.
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Sleep data file not found: {filepath}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in sleep data file: {e}")

    # Check for 'records' key
    if 'records' not in data:
        raise KeyError("Sleep data JSON must contain 'records' key")
    
    if not isinstance(data['records'], list):
        raise TypeError(f"'records' must be a list, got {type(data['records']).__name__}")

    records = []
    skipped = []
    for idx, entry in enumerate(data['records']):
        try:
            # Validate required fields
            validate_sleep_entry(entry, idx)

            # Parse UTC timestamps (ISO 8601 format with Z suffix)
            try:
                sleep_start = datetime.fromisoformat(entry['sleep_start'].replace('Z', '+00:00'))
                sleep_end = datetime.fromisoformat(entry['sleep_end'].replace('Z', '+00:00'))
            except ValueError as e:
                raise ValueError(
                    f"Invalid timestamp format. Error: {e}"
                )

            # Validate numeric fields
            try:
                duration_hours = float(entry['duration_hours'])
                quality_score = int(entry['quality_score'])
                
                if duration_hours < 0 or duration_hours > 24:
                    raise ValueError(f"Duration must be between 0 and 24 hours, got {duration_hours}")
                if quality_score < 0 or quality_score > 100:
                    raise ValueError(f"Quality score must be between 0 and 100, got {quality_score}")
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid numeric values. {e}")

            # Use the wake-up date as the "day" for sleep attribution
            date_utc = sleep_end.date()

            records.append(SleepRecord(
                date_utc=date_utc,
                sleep_start_utc=sleep_start,
                sleep_end_utc=sleep_end,
                duration_hours=duration_hours,
                quality_score=quality_score
            ))

        except (KeyError, ValueError, TypeError) as e:
            skipped.append((idx, str(e)))

    # Print warnings for skipped records
    if skipped:
        print(f"  Warning: Skipped {len(skipped)} invalid sleep record(s):")
        for idx, error in skipped:
            print(f"    - Record {idx}: {error}")

    return records


def load_workout_data(filepath: str) -> list[WorkoutRecord]:
    """
    Load workout data from JSON file with comprehensive error handling.
    Skips invalid records and prints warnings for each skipped entry.
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Workout data file not found: {filepath}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in workout data file: {e}")

    # Check for 'workout_log' key
    if 'workout_log' not in data:
        raise KeyError("Workout data JSON must contain 'workout_log' key")
    
    if not isinstance(data['workout_log'], list):
        raise TypeError(f"'workout_log' must be a list, got {type(data['workout_log']).__name__}")

    records = []
    skipped = []
    for idx, entry in enumerate(data['workout_log']):
        try:
            # Validate required fields
            validate_workout_entry(entry, idx)

            # Validate and parse timezone
            try:
                local_tz = ZoneInfo(entry['tz'])
            except ZoneInfoNotFoundError:
                raise ValueError(
                    f"Invalid timezone '{entry['tz']}'. Use IANA timezone identifiers."
                )
            except KeyError:
                raise ValueError(f"'tz' field is required")

            # Parse timestamp
            try:
                local_dt = datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S')
            except ValueError as e:
                raise ValueError(
                    f"Invalid timestamp format. Error: {e}"
                )

            # Make it timezone-aware in local time
            local_dt_aware = local_dt.replace(tzinfo=local_tz)

            # Convert to UTC
            utc_dt = local_dt_aware.astimezone(ZoneInfo('UTC'))

            # Check if day boundary was crossed
            local_date = local_dt.date()
            utc_date = utc_dt.date()
            crossed_boundary = local_date != utc_date

            # Validate numeric fields
            try:
                duration_min = int(entry['duration_min'])
                calories = int(entry['calories'])
                
                if duration_min < 0 or duration_min > 1440:
                    raise ValueError(f"Duration must be between 0 and 1440 minutes, got {duration_min}")
                if calories < 0:
                    raise ValueError(f"Calories must be non-negative, got {calories}")
            except (ValueError, TypeError) as e:
                raise ValueError(f"Invalid numeric values. {e}")

            records.append(WorkoutRecord(
                id=str(entry['id']),
                timestamp_utc=utc_dt,
                date_utc=utc_date,
                original_timestamp=entry['timestamp'],
                original_timezone=entry['tz'],
                workout_type=str(entry['type']),
                duration_min=duration_min,
                calories=calories,
                crossed_day_boundary=crossed_boundary
            ))

        except (KeyError, ValueError, ZoneInfoNotFoundError, TypeError) as e:
            skipped.append((idx, str(e)))

    # Print warnings for skipped records
    if skipped:
        print(f"  Warning: Skipped {len(skipped)} invalid workout record(s):")
        for idx, error in skipped:
            print(f"    - Record {idx}: {error}")

    return records
