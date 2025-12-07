# Error Handling Implementation

## Overview

The application now includes comprehensive error handling for data validation and timezone issues. This ensures users receive clear, actionable error messages when their input data is invalid.

## Error Types Handled

### 1. Timezone Validation Error
**When it occurs:** Invalid IANA timezone identifier in workout data

**Error message example:**
```
Data Validation Error: Error processing workout record 0: Workout record 0: Invalid timezone 'BadZone'. 
Use IANA timezone identifiers (e.g., 'America/Los_Angeles', 'Europe/London'). 
See: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
```

**Fields affected:** `tz` in workout records

**Resolution:** Use valid IANA timezone identifiers from the IANA Time Zone Database

---

### 2. Missing Required Fields Error
**When it occurs:** Required fields are missing from records in the JSON input

**Error message example (sleep data):**
```
Data Validation Error: Error processing sleep record 0: Sleep record 0: Missing required fields: quality_score. 
Required: duration_hours, quality_score, sleep_end, sleep_start
```

**Error message example (workout data):**
```
Data Validation Error: Error processing workout record 0: Workout record 0: Missing required fields: tz. 
Required: calories, duration_min, id, timestamp, type, tz
```

**Sleep required fields:** `sleep_start`, `sleep_end`, `duration_hours`, `quality_score`

**Workout required fields:** `id`, `timestamp`, `tz`, `type`, `duration_min`, `calories`

---

### 3. Invalid Numeric Values Error
**When it occurs:** Numeric fields are out of valid ranges or have invalid formats

**Error message examples:**
```
Data Validation Error: Error processing sleep record 0: Sleep record 0: Invalid numeric values. 
Quality score must be between 0 and 100, got 150

Data Validation Error: Error processing workout record 0: Workout record 0: Invalid numeric values. 
Duration must be between 0 and 1440 minutes, got -30
```

**Field validation rules:**

Sleep records:
- `duration_hours`: Float, must be between 0 and 24
- `quality_score`: Integer, must be between 0 and 100

Workout records:
- `duration_min`: Integer, must be between 0 and 1440 (24 hours)
- `calories`: Integer, must be non-negative

---

### 4. Invalid Timestamp Format Error
**When it occurs:** Timestamps don't match expected formats

**Error message examples:**

Sleep data (ISO 8601 format):
```
Data Validation Error: Error processing sleep record 0: Sleep record 0: Invalid timestamp format. 
Expected ISO 8601 format (e.g., '2023-10-01T00:30:00Z'). Error: ...
```

Workout data (local time format):
```
Data Validation Error: Error processing workout record 0: Workout record 0: Invalid timestamp format. 
Expected format: 'YYYY-MM-DD HH:MM:SS' (e.g., '2023-10-01 08:30:00'). Error: ...
```

**Format specifications:**
- Sleep timestamps: ISO 8601 with Z suffix (UTC) - e.g., `2023-10-01T00:30:00Z`
- Workout timestamps: Local time without timezone - e.g., `2023-10-01 08:30:00`

---

### 5. File and Structure Errors
**When it occurs:** Files don't exist or JSON structure is invalid

**Error message examples:**
```
File Error: Sleep data file not found: data/sleep.json
   Check that the input files exist and paths are correct.

Data Structure Error: Workout data JSON must contain 'workout_log' key
   The JSON file structure is invalid.
   Sleep data must contain 'records' key, workout data must contain 'workout_log' key.
```

**Requirements:**
- Sleep data JSON must have `records` key containing a list
- Workout data JSON must have `workout_log` key containing a list

---

## Example: Creating Valid Input Files

### Valid Sleep Data
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

**Notes:**
- Timestamps must be in UTC with 'Z' suffix (ISO 8601)
- Quality score must be 0-100
- Duration must be 0-24 hours

### Valid Workout Data
```json
{
  "workout_log": [
    {
      "id": 1,
      "timestamp": "2023-10-01 08:30:00",
      "tz": "America/Los_Angeles",
      "type": "Running",
      "duration_min": 45,
      "calories": 420
    }
  ]
}
```

**Notes:**
- Timestamps are in local time (no timezone suffix)
- Timezone must be valid IANA identifier
- Duration must be 0-1440 minutes
- Calories must be non-negative

---

## Error Handling Flow

```
User runs: python main.py --workouts invalid.json

1. Main tries to load workout data
2. data_loader.load_workout_data() catches error
3. Validation error is raised with clear message
4. main() catches ValueError
5. User sees formatted error message with resolution steps
6. Application exits with code 1
```

---

## Testing Error Scenarios

### Test 1: Invalid Timezone
```bash
# Create a test file with bad timezone
python -c "
import json, tempfile
data = {'workout_log': [{'id': 1, 'timestamp': '2023-10-01 08:30:00', 'tz': 'BadZone', 'type': 'Run', 'duration_min': 30, 'calories': 300}]}
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    json.dump(data, f); print(f.name)
"

# Run with the test file
python main.py --workouts <temp_file>
```

### Test 2: Missing Required Field
```bash
# Create a test file with missing 'tz' field
python -c "
import json, tempfile
data = {'workout_log': [{'id': 1, 'timestamp': '2023-10-01 08:30:00', 'type': 'Run', 'duration_min': 30, 'calories': 300}]}
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    json.dump(data, f); print(f.name)
"

# Run with the test file
python main.py --workouts <temp_file>
```

### Test 3: Invalid Quality Score
```bash
# Create a test file with quality score > 100
python -c "
import json, tempfile
data = {'records': [{'sleep_start': '2023-10-01T00:30:00Z', 'sleep_end': '2023-10-01T08:30:00Z', 'duration_hours': 8.0, 'quality_score': 150}]}
with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
    json.dump(data, f); print(f.name)
"

# Run with the test file
python main.py --sleep <temp_file>
```

---

## Validation Functions

### `validate_sleep_entry(entry: dict, index: int) -> None`
Checks that a sleep record has all required fields.
- Raises `ValueError` with list of missing fields

### `validate_workout_entry(entry: dict, index: int) -> None`
Checks that a workout record has all required fields.
- Raises `ValueError` with list of missing fields

---

## Implementation Details

**File:** `data_loader.py`

**Key changes:**
1. Added `ZoneInfoNotFoundError` import for timezone validation
2. Added constants defining required fields for each data type
3. Added `validate_sleep_entry()` and `validate_workout_entry()` functions
4. Enhanced `load_sleep_data()` with:
   - File existence and JSON format validation
   - Required fields validation
   - Timestamp format validation
   - Numeric value range validation
5. Enhanced `load_workout_data()` with:
   - File existence and JSON format validation
   - Required fields validation
   - Timezone validation (ZoneInfoNotFoundError handling)
   - Timestamp format validation
   - Numeric value range validation

**File:** `main.py`

**Key changes:**
1. Enhanced exception handling in `main()`:
   - Separate handlers for `FileNotFoundError`, `KeyError`/`TypeError`, `ValueError`
   - Specific error messages for each error type
   - User-friendly guidance on how to fix problems

---

## Best Practices for Users

1. **Always validate your input files before running the aggregator**
2. **Use IANA timezone identifiers** - check the list at https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
3. **Ensure all required fields are present** - check documentation for field requirements
4. **Keep values within valid ranges** - sleep quality 0-100, durations positive
5. **Use correct timestamp formats**:
   - Sleep: ISO 8601 with Z suffix (e.g., `2023-10-01T08:30:00Z`)
   - Workouts: Local time without timezone (e.g., `2023-10-01 08:30:00`)

