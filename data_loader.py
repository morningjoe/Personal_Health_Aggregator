"""
Data loading and normalization module.

This module handles:
- Loading sleep data from JSON
- Loading workout data from JSON
- Converting all timestamps to UTC
- Detecting day boundary crossings
- Comprehensive error handling for invalid data
"""

"""Compatibility shim re-exporting data loader functions from `tool.data_loader`.

The real implementation lives in `tool/data_loader.py`. Importing from the
top-level `data_loader` module still works for compatibility.
"""

from tool.data_loader import *  # noqa: F401,F403


def validate_workout_entry(entry: dict, index: int) -> None:
    """
    Validate that a workout entry has all required fields.
    
    Args:
        entry: Dictionary representing a workout record
        index: Index of the record in the list (for error reporting)
        
    Raises:
        ValueError: If required fields are missing
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
    Sleep data is already in UTC, so minimal conversion needed.

    Args:
        filepath: Path to JSON file containing sleep records

    Returns:
        List of SleepRecord objects normalized to UTC

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
        ValueError: If required fields are missing or data is invalid
        TypeError: If 'records' key is missing or not a list
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
                    f"Sleep record {idx}: Invalid timestamp format. "
                    f"Expected ISO 8601 format (e.g., '2023-10-01T00:30:00Z'). Error: {e}"
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
                raise ValueError(f"Sleep record {idx}: Invalid numeric values. {e}")

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
            raise ValueError(f"Error processing sleep record {idx}: {e}")

    return records


def load_workout_data(filepath: str) -> list[WorkoutRecord]:
    """
    Load workout data from JSON file with comprehensive error handling.

    Converts workout timestamps from local time to UTC.
    Critical: Workout timestamps are in local time (e.g., PST).
    Converting to UTC may change the date!

    Example edge case:
    - Local: 2023-10-01 23:15:00 PST
    - UTC:   2023-10-02 06:15:00 UTC  <- Different day!

    Args:
        filepath: Path to JSON file containing workout records

    Returns:
        List of WorkoutRecord objects with timestamps converted to UTC

    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If JSON is invalid
        ValueError: If required fields are missing or timezone is invalid
        TypeError: If 'workout_log' key is missing or not a list
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
    for idx, entry in enumerate(data['workout_log']):
        try:
            # Validate required fields
            validate_workout_entry(entry, idx)

            # Validate and parse timezone
            try:
                local_tz = ZoneInfo(entry['tz'])
            except ZoneInfoNotFoundError:
                raise ValueError(
                    f"Workout record {idx}: Invalid timezone '{entry['tz']}'. "
                    f"Use IANA timezone identifiers (e.g., 'America/Los_Angeles', 'Europe/London'). "
                    f"See: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones"
                )
            except KeyError:
                raise ValueError(f"Workout record {idx}: 'tz' field is required")

            # Parse timestamp
            try:
                local_dt = datetime.strptime(entry['timestamp'], '%Y-%m-%d %H:%M:%S')
            except ValueError as e:
                raise ValueError(
                    f"Workout record {idx}: Invalid timestamp format. "
                    f"Expected format: 'YYYY-MM-DD HH:MM:SS' (e.g., '2023-10-01 08:30:00'). Error: {e}"
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
                
                if duration_min < 0 or duration_min > 1440:  # 1440 minutes = 24 hours
                    raise ValueError(f"Duration must be between 0 and 1440 minutes, got {duration_min}")
                if calories < 0:
                    raise ValueError(f"Calories must be non-negative, got {calories}")
            except (ValueError, TypeError) as e:
                raise ValueError(f"Workout record {idx}: Invalid numeric values. {e}")

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
            raise ValueError(f"Error processing workout record {idx}: {e}")

    return records
