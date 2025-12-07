# Technical Documentation - Personal Health Data Aggregator

## Table of Contents
1. [Credits and Attribution](#credits-and-attribution)
2. [Architecture Overview](#architecture-overview)
3. [Data Models](#data-models)
4. [Function Reference](#function-reference)
5. [Timezone Handling](#timezone-handling)
6. [Edge Cases](#edge-cases)
7. [Testing Scenarios](#testing-scenarios)
8. [Implementation Details](#implementation-details)

---

## Credits and Attribution

### Development Contributions

This project is the result of collaborative development with clear separation between original design/architecture and implementation:

#### Development in conjunction with Copilot AI Assistant - Implementation Phase
- **Reporting functions**: Developed all console output functions (`print_day_boundary_analysis()`, `print_merged_data()`, `print_correlations()`)
- **CLI interface**: Built the argparse-based command-line interface with comprehensive help messages
- **Code modularization**: Refactored monolithic code into separate modules (models.py, data_loader.py, merger.py, reporter.py)
- **JSON output generation**: Created JSON serialization functions with proper datetime handling

#### Original Design/Drafting - Architecture Phase
- **Day boundary crossing detection**: Implemented the timezone conversion logic that detects when workout timestamps cross midnight
- **Input JSON schema**: Designed sleep.json and workouts.json formats with timezone support
- **Output JSON structure**: Defined the merged output format including metadata, daily data, and correlations
- **Merge algorithm**: Drafted the core logic for combining sleep and workout data by UTC date
- **Edge case analysis**: Identified critical test cases including:
  - Day boundary crossings (e.g., 11:15 PM local → next day UTC)
  - Multiple timezones in single dataset
  - Missing data (sleep without workouts, vice versa)
  - DST transitions
- **Data models**: Defined SleepRecord, WorkoutRecord, and DailyAggregate structures
- **Correlation metrics**: Specified what metrics to calculate and how to analyze them
- **Testing and validation**: Executed test cases and verified edge case handling
- **Test scenarios**: Created comprehensive test data with known edge cases
- **Library References**: Utilized zoneinfo, timezone, and datetime libraries, which are well established and safe for production


---

## Architecture Overview

The application follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────┐
│         CLI Interface (argparse)            │
├─────────────────────────────────────────────┤
│         Data Loading & Normalization        │
│  ├─ load_sleep_data()                       │
│  └─ load_workout_data()                     │
├─────────────────────────────────────────────┤
│         Data Merging & Processing           │
│  ├─ merge_by_day()                          │
│  └─ calculate_correlations()                │
├─────────────────────────────────────────────┤
│         Output Generation                   │
│  ├─ generate_json_output()                  │
│  └─ save_json_output()                      │
├─────────────────────────────────────────────┤
│         Reporting & Visualization           │
│  ├─ print_day_boundary_analysis()           │
│  ├─ print_merged_data()                     │
│  └─ print_correlations()                    │
└─────────────────────────────────────────────┘
```

### Control Flow

```
main()
  ├─> parse arguments
  ├─> load_sleep_data(args.sleep)
  ├─> load_workout_data(args.workouts)
  ├─> [conditional] print_day_boundary_analysis()
  ├─> merge_by_day()
  ├─> [conditional] print_merged_data()
  ├─> calculate_correlations()
  ├─> [conditional] print_correlations()
  ├─> generate_json_output()
  └─> save_json_output()
```

---

## Data Models

### SleepRecord (Dataclass)

Represents a single sleep session normalized to UTC.

```python
@dataclass
class SleepRecord:
    date_utc: date                    # UTC date of wake-up
    sleep_start_utc: datetime         # Start time in UTC
    sleep_end_utc: datetime           # End time in UTC
    duration_hours: float             # Total duration
    quality_score: int                # 0-100 quality rating
```

**Key Notes:**
- `date_utc` is based on wake-up time (sleep_end_utc.date()) 
- Timestamps are timezone-aware (UTC)
- Quality score should be 0-100

**Example:**
```python
SleepRecord(
    date_utc=date(2023, 10, 1),
    sleep_start_utc=datetime(2023, 10, 1, 0, 30, tzinfo=ZoneInfo('UTC')),
    sleep_end_utc=datetime(2023, 10, 1, 8, 30, tzinfo=ZoneInfo('UTC')),
    duration_hours=8.0,
    quality_score=85
)
```

### WorkoutRecord (Dataclass)

Represents a single workout normalized to UTC.

```python
@dataclass
class WorkoutRecord:
    id: str                          # Unique identifier
    timestamp_utc: datetime          # UTC timestamp
    date_utc: date                   # UTC date for attribution
    original_timestamp: str          # Original local time string
    original_timezone: str           # Original timezone (IANA format)
    workout_type: str                # Exercise type (Running, Yoga, etc.)
    duration_min: int                # Duration in minutes
    calories: int                    # Estimated calories burned
    crossed_day_boundary: bool       # Flag: day changed during conversion
```

**Key Notes:**
- `timestamp_utc` is the authoritative timestamp
- `crossed_day_boundary` indicates if local date ≠ UTC date
- Original values preserved for audit trail
- `date_utc` used for aggregation

**Example:**
```python
WorkoutRecord(
    id="W002",
    timestamp_utc=datetime(2023, 10, 2, 6, 15, tzinfo=ZoneInfo('UTC')),
    date_utc=date(2023, 10, 2),
    original_timestamp="2023-10-01 23:15:00",
    original_timezone="America/Los_Angeles",
    workout_type="Yoga",
    duration_min=30,
    calories=120,
    crossed_day_boundary=True
)
```

### DailyAggregate (Dataclass)

Represents merged data for a single UTC day.

```python
@dataclass
class DailyAggregate:
    date_utc: date                   # The UTC date
    sleep_hours: Optional[float]     # Total sleep duration
    sleep_quality: Optional[int]     # Sleep quality score
    workouts: list = None            # List of WorkoutRecord
    total_calories: int = 0          # Sum of all workout calories
    total_workout_minutes: int = 0   # Sum of all workout durations
```

**Key Notes:**
- Sleep data is optional (some days may have no sleep data)
- Workouts list contains WorkoutRecord objects
- Totals automatically accumulate as workouts are added

---

## Function Reference

### Data Loading Functions

#### `load_sleep_data(filepath: str) -> list[SleepRecord]`

Loads sleep data from a JSON file and normalizes to UTC. **Invalid records are skipped with warnings.**

**Input Format:**
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

**Process:**
1. Parse JSON file
2. For each record:
   - Validate required fields (sleep_start, sleep_end, duration_hours, quality_score)
   - Convert ISO 8601 timestamps to datetime objects
   - Validate numeric ranges (duration_hours: 0-24, quality_score: 0-100)
   - Use sleep_end date as the attribution date
   - If any validation fails: skip record and print warning
3. Return list of valid SleepRecord objects

**Skipped Records:**
Records are skipped and a warning is printed for:
- Missing required fields
- Invalid timestamp format (not ISO 8601 with Z suffix)
- Out-of-range values (duration_hours < 0 or > 24, quality_score < 0 or > 100)

**Example Output:**
```
  Loaded 12 sleep records (UTC)
  Warning: Skipped 1 invalid sleep record(s):
    - Record 9: Invalid numeric values. Quality score must be between 0 and 100, got 150
```

**Exceptions:**
- `FileNotFoundError` - File doesn't exist (execution stops)
- `json.JSONDecodeError` - Invalid JSON format (execution stops)
- `KeyError` - Missing 'records' key (execution stops)

---

#### `load_workout_data(filepath: str) -> list[WorkoutRecord]`

Loads workout data from JSON and converts from local time to UTC. **Invalid records are skipped with warnings.**

**Input Format:**
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

**Process:**
1. Parse JSON file
2. For each record:
   - Validate required fields (id, timestamp, tz, type, duration_min, calories)
   - Validate timezone (must be valid IANA identifier)
   - Parse local timestamp (format: YYYY-MM-DD HH:MM:SS)
   - Create timezone-aware datetime in local timezone
   - Convert to UTC using `astimezone()`
   - Validate numeric ranges (duration_min: 0-1440, calories: ≥ 0)
   - Compare local date vs UTC date (detect boundary crossing)
   - Create WorkoutRecord with all data
   - If any validation fails: skip record and print warning
3. Return list of valid WorkoutRecord objects

**Skipped Records:**
Records are skipped and a warning is printed for:
- Missing required fields
- Invalid timezone identifier (not in IANA database)
- Invalid timestamp format (not YYYY-MM-DD HH:MM:SS)
- Out-of-range numeric values (duration_min < 0 or > 1440, calories < 0)
- DST transition edge cases (non-existent local times during spring-forward)

**Example Output:**
```
  Warning: Skipped 5 invalid workout record(s):
    - Record 8: Invalid timezone 'Bad/Timezone'. Use IANA timezone identifiers.
    - Record 11: Missing required fields: tz. Required: calories, duration_min, id, timestamp, type, tz
    - Record 12: Invalid numeric values. Duration must be between 0 and 1440 minutes, got -10
    - Record 13: Invalid numeric values. Duration must be between 0 and 1440 minutes, got 2000
    - Record 15: Invalid timestamp format. Error: time data '2023/10/01 08:30' does not match format '%Y-%m-%d %H:%M:%S'
  Loaded 11 workout records (converted from local time)
```

**Exceptions:**
- `FileNotFoundError` - File doesn't exist (execution stops)
- `json.JSONDecodeError` - Invalid JSON format (execution stops)
- `KeyError` - Missing 'workout_log' key (execution stops)

---

### Data Processing Functions

#### `merge_by_day(sleep_records: list[SleepRecord], workout_records: list[WorkoutRecord]) -> dict[date, DailyAggregate]`

Aggregates sleep and workout data by UTC date.

**Algorithm:**
1. Create defaultdict with DailyAggregate objects
2. Iterate through sleep_records:
   - Get date from sleep_end_utc
   - Set sleep_hours and sleep_quality
3. Iterate through workout_records:
   - Get date from date_utc
   - Append to workouts list
   - Increment total_calories
   - Increment total_workout_minutes
4. Convert defaultdict to regular dict
5. Return sorted by date

**Output:**
```python
{
    date(2023, 10, 1): DailyAggregate(...),
    date(2023, 10, 2): DailyAggregate(...),
    ...
}
```

---

#### `calculate_correlations(daily_data: dict[date, DailyAggregate]) -> dict`

Analyzes sleep and exercise patterns.

**Metrics Calculated:**
1. **Low Sleep Days** (< 6 hours):
   - Count of days
   - Average calories burned
   - Workout frequency

2. **Good Sleep Days** (≥ 7 hours):
   - Count of days
   - Average calories burned
   - Workout frequency

3. **Differential Analysis:**
   - Compares metrics between low and good sleep

**Algorithm:**
1. Filter days by sleep duration
2. For each category:
   - Count days with workout data
   - Calculate mean of total_calories
   - Calculate workout frequency
3. Return dictionary with results

**Output:**
```python
{
    'avg_calories_low_sleep': 457.0,
    'low_sleep_day_count': 3,
    'avg_calories_good_sleep': 380.0,
    'good_sleep_day_count': 3,
    'workout_rate_low_sleep': 1.0,
    'workout_rate_good_sleep': 1.0
}
```

---

### Output Functions

#### `generate_json_output(merged: dict, workout_records: list[WorkoutRecord], correlations: dict) -> dict`

Creates a comprehensive JSON-serializable structure.

**Structure:**
```json
{
  "metadata": { ... },
  "daily_data": [ ... ],
  "correlations": { ... }
}
```

**Metadata:**
- `generated_at`: ISO 8601 timestamp
- `total_days`: Number of days in dataset
- `date_range`: Start and end dates

**Daily Data:**
- Sorted by date
- Includes sleep, workouts, and daily totals
- Flags day boundary crossings

**Correlations:**
- Low sleep metrics
- Good sleep metrics
- Total boundary crossing count

---

#### `save_json_output(output: dict, filepath: str = 'merged_health_data.json')`

Serializes and writes output to JSON file.

**Process:**
1. Open file for writing
2. Use `json.dump()` with 2-space indentation
3. Print success message
4. Auto-closes file

---

### Reporting Functions

#### `print_day_boundary_analysis(workout_records: list[WorkoutRecord])`

Displays workouts that crossed day boundaries during timezone conversion.

**Output Format:**
```
Found N workout(s) that crossed day boundary:

  Workout: ID (Type)
    Local:  YYYY-MM-DD HH:MM:SS Timezone
    UTC:    YYYY-MM-DD HH:MM:SS UTC
    Local Date: YYYY-MM-DD -> UTC Date: YYYY-MM-DD
    Attributed to YYYY-MM-DD (UTC day)
```

---

#### `print_merged_data(merged: dict[date, DailyAggregate])`

Displays human-readable daily aggregates.

**Output Format:**
```
📅 YYYY-MM-DD
  😴 Sleep: N hrs (quality: X/100)
  🏃 Workouts: N
      - Type: calories cal, duration min
  🔥 Total: calories calories, duration min
```

---

#### `print_correlations(correlations: dict)`

Displays sleep/exercise correlation analysis.

**Output Format:**
```
Days with < 6 hours sleep (N days):
  Average calories burned: X

Days with ≥ 7 hours sleep (N days):
  Average calories burned: X

💡 Insight: [difference] more/fewer calories on well-rested days
```

---

## Timezone Handling

### Why zoneinfo?

Python's `zoneinfo` module (PEP 615, Python 3.9+) provides:
- ✅ Accurate DST handling
- ✅ Historical timezone data
- ✅ No external dependencies (uses system tzdata)
- ✅ Built-in to standard library

### Conversion Process

For each workout:

```python
# 1. Parse local timestamp
local_dt = datetime.strptime(
    "2023-10-01 23:15:00",
    '%Y-%m-%d %H:%M:%S'
)

# 2. Add timezone awareness (local time)
local_tz = ZoneInfo('America/Los_Angeles')
local_dt_aware = local_dt.replace(tzinfo=local_tz)

# 3. Convert to UTC
utc_dt = local_dt_aware.astimezone(ZoneInfo('UTC'))

# 4. Check if date changed
local_date = local_dt.date()        # 2023-10-01
utc_date = utc_dt.date()           # 2023-10-02 (DIFFERENT!)
```

### Supported Timezones

Any IANA timezone identifier is supported:
- `America/Los_Angeles`
- `Europe/London`
- `Asia/Tokyo`
- `UTC`
- etc.

Reference: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

---

## Edge Cases

### 1. Day Boundary Crossing

**Example:**
- Local: 2023-10-01 23:15:00 PST
- UTC: 2023-10-02 06:15:00 (8 hours ahead)
- Workout attributed to 2023-10-02

**Handling:**
- Detected by comparing local_date != utc_date
- Flagged with `crossed_day_boundary = True`
- Shown in visual output with ⚠️
- Included in correlations count

### 2. Missing Sleep Data

**Scenario:** Workout exists but no sleep data for that day

**Handling:**
- `daily_data[day].sleep_hours` remains `None`
- Sleep block shown as "😫 Sleep: No data"
- Correlations exclude days without sleep data

### 3. Missing Workout Data

**Scenario:** Sleep exists but no workouts for that day

**Handling:**
- `daily_data[day].workouts` is empty list
- Shown as "🏃 Workouts: None"
- Totals show 0 calories and 0 minutes

### 4. Multiple Workouts Same Day

**Scenario:** Multiple workouts on same UTC date

**Handling:**
- All appended to `workouts` list
- Totals correctly summed
- Each displayed separately in output

## Included Test Files

The repository includes several test JSON files useful for exercising validation
paths and edge-case behavior. Use these when developing or when validating
changes to loaders and merging logic.

- `data/sleep_invalid.json` — Mixed valid + invalid sleep records (out-of-range
  duration, missing fields, malformed timestamps, future dates).
- `data/workouts_invalid.json` — Mixed valid + invalid workout records
  (invalid timezone, missing `tz`, negative / excessively large durations,
  malformed timestamps).
- `data/workouts_multipletz.json` — Valid workout records reported in multiple
  timezones (America/Los_Angeles, Europe/London, Asia/Tokyo, UTC) for
  cross-timezone and day-boundary testing.
- `data/sleep_edgecases.json` — Valid sleep edge cases (zero duration, maximum
  quality score, cross-year sleep) for verifying aggregation and correlation
  logic.

Example commands:

```powershell
# Exercise invalid test sets (shows skipped records and warnings)
python main.py --sleep data/sleep_invalid.json --workouts data/workouts_invalid.json --verbose

# Test multi-timezone behavior and boundary crossings
python main.py --sleep data/sleep.json --workouts data/workouts_multipletz.json --show-boundaries

# Test edge-case sleep records
python main.py --sleep data/sleep_edgecases.json --workouts data/workouts.json --show-summary
```

### 5. Invalid Timezone

**Scenario:** Timezone string "America/Los_Angel" (typo)

**Handling:**
- Record is **skipped** with a warning
- Warning displays: `Invalid timezone 'America/Los_Angel'. Use IANA timezone identifiers.`
- Processing continues with remaining valid records
- Final summary includes count of skipped records

**Example Output:**
```
Warning: Skipped 1 invalid workout record(s):
  - Record 8: Invalid timezone 'Bad/Timezone'. Use IANA timezone identifiers.
Loaded 11 workout records (converted from local time)
```

### 6. DST Transitions

**Scenario:** Daylight Saving Time change (e.g., spring forward on March 12, 2 AM → 3 AM)

**Handling:**
- If a timestamp refers to a non-existent time during DST transition:
  - Record is **skipped** with a warning
  - Warning displays: `Invalid timestamp format. Error: [specific zoneinfo error]`
- Valid times during DST transitions are automatically converted correctly
- UTC conversion is always accurate

### 7. Missing Required Fields

**Scenario:** Workout record missing `tz` field

**Handling:**
- Record is **skipped** with a warning
- Warning displays: `Missing required fields: tz. Required: calories, duration_min, id, timestamp, type, tz`
- Processing continues with valid records

### 8. Invalid Numeric Values

**Scenario:** Negative duration (`duration_min: -10`) or exceeding limits (`duration_min: 2000`)

**Handling:**
- Record is **skipped** with a warning
- Warning displays: `Invalid numeric values. Duration must be between 0 and 1440 minutes, got 2000`
- Processing continues with valid records

### 9. Bad Timestamp Format

**Scenario:** Timestamp with wrong format (`2023/10/01 08:30` instead of `2023-10-01 08:30:00`)

**Handling:**
- Record is **skipped** with a warning
- Warning displays: `Invalid timestamp format. Error: time data '2023/10/01 08:30' does not match format '%Y-%m-%d %H:%M:%S'`
- Processing continues with valid records

---

## Testing Scenarios

### Test Case 1: Simple Day (No Boundary Crossing)

**Input:**
- Sleep: Oct 1, 0:30-8:30 UTC (8 hours)
- Workout: Oct 1, 8:30 PST (16:30 UTC)

**Expected:**
- Both attributed to Oct 1
- Sleep: 8 hours, quality N
- Workout: 1 entry, X calories
- No boundary warning

### Test Case 2: Late Evening Workout (Boundary Crossing)

**Input:**
- Sleep: Oct 1, 0:30-8:30 UTC
- Workout: Oct 1 23:15 PST (Oct 2 06:15 UTC)

**Expected:**
- Workout attributed to Oct 2
- Boundary crossing flag = True
- Oct 1: only sleep
- Oct 2: sleep + workout + ⚠️ warning

### Test Case 3: Multiple Workouts Single Day

**Input:**
- Sleep: Oct 1, 0:30-8:30 UTC
- Workout 1: Oct 1, 8:30 PST (420 cal)
- Workout 2: Oct 1, 17:30 PST (550 cal)

**Expected:**
- Both workouts on Oct 1
- Daily total: 970 calories
- 2 entries in workouts list

### Test Case 4: No Sleep Data

**Input:**
- Workout: Oct 1, 8:30 PST
- (No sleep data for Oct 1)

**Expected:**
- Daily aggregate created
- sleep_hours = None
- Workout data present
- Correlation analysis excludes this day

### Test Case 5: DST Transition

**Input:**
- Spring forward: March 12, 2023 (2 AM → 3 AM)
- Workout: March 12, 1:30 AM PST (not valid during transition)

**Expected:**
- ValueError raised during parsing
- Error caught in main()
- User informed to check timestamp

---

## Implementation Details

### Memory Efficiency

The implementation is designed for reasonable dataset sizes:
- Sleep records typically ~365/year
- Workout records typically ~365-1000/year
- All data loaded into memory (acceptable for personal data)

For larger datasets, consider:
- Database backend (SQLite, PostgreSQL)
- Streaming/chunked processing
- Separate correlation analysis module

### Error Handling Strategy

```python
try:
    # Load and process data
except FileNotFoundError as e:
    # File path issues
    print(f"❌ Error: {e}")
    return 1
except Exception as e:
    # Unexpected errors
    print(f"❌ Unexpected error: {e}")
    return 1
```

**Exit Codes:**
- `0` - Success
- `1` - File or processing error

### JSON Serialization

Challenges with datetime serialization:

```python
# ❌ This fails
json.dump(datetime_obj)  # TypeError

# ✅ This works
json.dump(datetime_obj.isoformat())  # String format
```

Solution: Convert all datetime objects to ISO 8601 strings before JSON output.


## Future Enhancements

### 1. Database Backend

Replace JSON with SQLite:
```python
import sqlite3
cursor.execute("INSERT INTO workouts VALUES (...)")
```

Benefits:
- Better for large datasets
- Query flexibility
- Historical tracking

