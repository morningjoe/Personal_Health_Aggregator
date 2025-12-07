# Personal Health Data Aggregator

A Python tool that merges health data from multiple sources (sleep and workout trackers) with different timezone formats. Automatically normalizes all data to UTC and handles edge cases like day boundary crossings.

## Features

- **Timezone-aware merging**: Converts local timestamps to UTC using Python's `zoneinfo`
- **Day boundary handling**: Correctly attributes workouts that cross midnight in different timezones
- **Correlation analysis**: Identifies patterns between sleep quality and exercise habits
- **JSON output**: Generates structured JSON with merged data for further analysis
- **CLI interface**: Flexible command-line options for custom workflows
- **Error handling**: Graceful, actionable error messages for invalid data

## Installation

### Requirements
- Python 3.9+
- `tzdata` package (for timezone support)

### Setup

```bash
cd Personal_Health_Aggregator
python -m venv .venv

# Activate (Windows)
.\.venv\Scripts\Activate.ps1
# Or (macOS/Linux)
source .venv/bin/activate

pip install tzdata
```

## Quick Start

### Basic Usage

```bash
# Use default files (data/sleep.json, data/workouts.json)
python main.py

# Show all analysis details
python main.py --verbose

# Custom file paths
python main.py --sleep my_sleep.json --workouts my_workouts.json --output result.json
```

### CLI Options

```
--sleep PATH              Path to sleep data JSON (default: data/sleep.json)
--workouts PATH           Path to workout data JSON (default: data/workouts.json)
--output PATH             Output JSON file path (default: merged_health_data.json)
--show-summary            Print human-readable summary
--show-boundaries         Show day boundary crossing analysis
--show-correlations       Show correlation analysis
--verbose                 Show all outputs (summary, boundaries, correlations)
```

## Data Format

### Sleep Data (`data/sleep.json`)

Sleep records must be in UTC with ISO 8601 format:

```json
{
  "records": [
    {
      "sleep_start": "2023-10-01T00:30:00Z",
      "sleep_end": "2023-10-01T08:30:00Z",
      "duration_hours": 8.0,
      "quality_score": 85
    }
  ]
}
```

**Required fields:** `sleep_start`, `sleep_end`, `duration_hours`, `quality_score`

**Validation rules:**
- Timestamps: ISO 8601 format with Z suffix (e.g., `2023-10-01T08:30:00Z`)
- `duration_hours`: 0-24 hours
- `quality_score`: 0-100

### Workout Data (`data/workouts.json`)

Workout records can be in any timezone (will be converted to UTC):

```json
{
  "workout_log": [
    {
      "id": "W001",
      "timestamp": "2023-10-01 08:30:00",
      "tz": "America/Los_Angeles",
      "type": "Running",
      "duration_min": 45,
      "calories": 420
    }
  ]
}
```

**Required fields:** `id`, `timestamp`, `tz`, `type`, `duration_min`, `calories`

**Validation rules:**
- Timestamps: Local time format (e.g., `2023-10-01 08:30:00`) without timezone
- `tz`: Valid IANA timezone identifier (see [IANA TZ Database](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones))
- `duration_min`: 0-1440 minutes
- `calories`: Non-negative integer

## Output Format

The generated `merged_health_data.json` contains:

```json
{
  "metadata": {
    "generated_at": "2023-10-07T12:34:56+00:00",
    "total_days": 7,
    "date_range": {"start": "2023-10-01", "end": "2023-10-07"}
  },
  "daily_data": [
    {
      "date_utc": "2023-10-01",
      "sleep": {"hours": 8.0, "quality_score": 85},
      "workouts": [
        {
          "id": "W001",
          "type": "Running",
          "duration_min": 45,
          "calories": 420,
          "timestamp_utc": "2023-10-01T08:30:00+00:00",
          "original_timestamp": "2023-10-01 08:30:00",
          "original_timezone": "America/Los_Angeles",
          "day_boundary_crossed": false
        }
      ],
      "daily_totals": {
        "total_calories": 420,
        "total_workout_minutes": 45,
        "workout_count": 1
      }
    }
  ],
  "correlations": {
    "low_sleep_days": {"count": 3, "avg_calories_burned": 457.0},
    "good_sleep_days": {"count": 3, "avg_calories_burned": 380.0},
    "day_boundary_crossings": 4
  }
}
```

## Architecture

### Module Organization

| Module | Purpose |
|--------|---------|
| `main.py` | CLI entry point and orchestration |
| `models.py` | Data models (SleepRecord, WorkoutRecord, DailyAggregate) |
| `data_loader.py` | Data loading and normalization with validation |
| `merger.py` | Data aggregation and correlation analysis |
| `reporter.py` | Console output and JSON generation |

### Data Flow

```
main() → load_sleep_data() → merge_by_day() → generate_json_output() → save_json_output()
      ↓              ↓              ↓              ↓                    ↓
   argparse    load_workout_data()  calculate_correlations()   print_* functions
```

## Key Design Decisions

### Timezone Handling
- Uses Python's `zoneinfo` module for accurate DST handling and historical timezone data
- All timestamps normalized to UTC for consistent aggregation
- Original local timestamp and timezone preserved for reference

### Day Attribution
- Days are attributed based on UTC date
- Workouts that cross midnight (local to UTC) are flagged with `day_boundary_crossed`
- Sleep duration uses wake-up time (end time) as the reference day

### Correlation Analysis
- Compares low-sleep days (<6 hours) vs. good-sleep days (≥7 hours)
- Calculates average calories burned and workout frequency
- Identifies patterns in exercise habits based on sleep quality

## Error Handling

The application provides clear error messages for common issues:

### Timezone Validation Error
```
Data Validation Error: Invalid timezone 'BadZone'.
Use IANA timezone identifiers (e.g., 'America/Los_Angeles', 'Europe/London').
See: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
```

### Missing Required Fields Error
```
Data Validation Error: Sleep record 0: Missing required fields: quality_score.
Required: duration_hours, quality_score, sleep_end, sleep_start
```

### Invalid Numeric Values Error
```
Data Validation Error: Workout record 0: Invalid numeric values.
Duration must be between 0 and 1440 minutes, got -30
```

### Invalid Timestamp Format Error
```
Data Validation Error: Sleep record 0: Invalid timestamp format.
Expected ISO 8601 format (e.g., '2023-10-01T00:30:00Z').
```

## Edge Cases Handled

✅ **Day boundary crossings**: Workouts that cross midnight when converted to UTC
✅ **Multiple timezones**: Different devices reporting in different timezones
✅ **Missing data**: Days with only sleep or only workouts
✅ **DST transitions**: Automatic handling of Daylight Saving Time
✅ **Invalid timezones**: Clear error messages with resolution steps

## Troubleshooting

| Error | Solution |
|-------|----------|
| `FileNotFoundError` | Check file paths exist; use `--sleep` and `--workouts` options |
| `ModuleNotFoundError: tzdata` | Run `pip install tzdata` |
| `ZoneInfoNotFoundError` | Verify timezone strings (e.g., "America/Los_Angeles"); see [IANA TZ list](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones) |
| `KeyError: 'records'` | Sleep JSON must contain 'records' key; workout JSON must contain 'workout_log' key |

## Project Structure

```
Personal_Health_Aggregator/
├── main.py                      # CLI entry point
├── models.py                    # Data models
├── data_loader.py               # Data loading with validation
├── merger.py                    # Merging and correlation analysis
├── reporter.py                  # Reporting and output
├── data/
│   ├── sleep.json              # Sleep data source
│   └── workouts.json           # Workout data source
├── merged_health_data.json      # Generated output
└── README.md                    # This file
```

## Data Models

### SleepRecord
```python
date_utc: date              # UTC date of wake-up
sleep_start_utc: datetime   # Start time in UTC
sleep_end_utc: datetime     # End time in UTC
duration_hours: float       # Total duration (0-24)
quality_score: int          # Quality rating (0-100)
```

### WorkoutRecord
```python
id: str                     # Unique identifier
timestamp_utc: datetime     # UTC timestamp
date_utc: date              # UTC date for attribution
original_timestamp: str     # Original local time
original_timezone: str      # IANA timezone identifier
workout_type: str           # Exercise type
duration_min: int           # Duration in minutes (0-1440)
calories: int               # Calories burned (≥0)
crossed_day_boundary: bool  # Flag if local date ≠ UTC date
```

### DailyAggregate
```python
date_utc: date              # The UTC date
sleep_hours: Optional[float]   # Total sleep duration
sleep_quality: Optional[int]   # Sleep quality score
workouts: list              # List of WorkoutRecord objects
total_calories: int         # Sum of all calories
total_workout_minutes: int  # Sum of all durations
```

## Timezone Examples

### Day Boundary Crossing

**Scenario:** Late evening workout in Pacific timezone
```
Local:    2023-10-01 23:15:00 America/Los_Angeles
UTC:      2023-10-02 06:15:00 UTC
Result:   Workout attributed to 2023-10-02 (different day!)
```

### Valid Timezone Identifiers

- `America/Los_Angeles` - US Pacific
- `America/New_York` - US Eastern
- `Europe/London` - UK
- `Asia/Tokyo` - Japan
- `UTC` or `Etc/UTC` - Coordinated Universal Time

See complete list: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

## Function Reference

### Data Loading

**`load_sleep_data(filepath: str) -> list[SleepRecord]`**
- Loads and validates sleep records from JSON
- Parses ISO 8601 UTC timestamps
- Raises `ValueError` for invalid data

**`load_workout_data(filepath: str) -> list[WorkoutRecord]`**
- Loads and validates workout records from JSON
- Converts local timestamps to UTC
- Detects day boundary crossings
- Raises `ValueError` for invalid timezone or data

### Data Processing

**`merge_by_day(sleep_records, workout_records) -> dict[date, DailyAggregate]`**
- Aggregates sleep and workout data by UTC date
- Returns dictionary sorted by date

**`calculate_correlations(daily_data) -> dict`**
- Analyzes sleep and exercise patterns
- Returns metrics for low-sleep and good-sleep days

### Output

**`generate_json_output(merged, workout_records, correlations) -> dict`**
- Creates JSON-serializable output structure with metadata, daily data, and correlations

**`save_json_output(output, filepath)`**
- Writes JSON output to file with 2-space indentation

### Reporting

**`print_day_boundary_analysis(workout_records)`**
- Displays workouts that crossed day boundaries

**`print_merged_data(merged)`**
- Displays human-readable daily aggregates

**`print_correlations(correlations)`**
- Displays sleep/exercise correlation analysis

## Future Enhancements

- [ ] Database backend (SQLite/PostgreSQL)
- [ ] Web dashboard visualization
- [ ] Configuration file support (.yaml/.ini)
- [ ] Advanced correlation metrics (Pearson, Spearman)
- [ ] Weekly/monthly aggregation
- [ ] Support for additional data sources (Fitbit, Apple Health, Whoop)

## Credits and Attribution

**Claude (AI Assistant):**
- Day boundary crossing detection logic
- Reporting functions and CLI interface
- Code modularization and refactoring
- JSON output generation
- Error handling and validation

**Original Design/Architecture:**
- Input/output JSON schemas
- Merge algorithm and daily aggregation strategy
- Edge cases identification and test scenarios
- Data model definitions
- Correlation metrics specification

This is collaborative development with clear separation between architectural design and implementation.

## License

MIT License

## Author

Jonathan (morningjoe)

## Support

For issues or questions, verify your input files match the data format requirements and check timezone identifiers against the [IANA TZ Database](https://en.wikipedia.org/wiki/List_of_tz_database_time_zones).
