"""
Reporting and output functions module.

This module handles all display and output operations:
- Printing day boundary analysis
- Printing merged daily data
- Printing correlation analysis
- Generating JSON output
- Saving JSON to file
"""

import json
from datetime import datetime
from zoneinfo import ZoneInfo
from tool.models import WorkoutRecord


def print_day_boundary_analysis(workout_records: list[WorkoutRecord]):
    """Show which workouts crossed the day boundary during timezone conversion."""
    print("\n" + "=" * 70)
    print("DAY BOUNDARY ANALYSIS (Critical Edge Cases)")
    print("=" * 70)

    boundary_crossings = [w for w in workout_records if w.crossed_day_boundary]

    if boundary_crossings:
        print(f"\nFound {len(boundary_crossings)} workout(s) that crossed day boundary:\n")
        for w in boundary_crossings:
            local_date = datetime.strptime(w.original_timestamp, '%Y-%m-%d %H:%M:%S').date()
            print(f"  Workout: {w.id} ({w.workout_type})")
            print(f"    Local:  {w.original_timestamp} {w.original_timezone}")
            print(f"    UTC:    {w.timestamp_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC")
            print(f"    Local Date: {local_date} -> UTC Date: {w.date_utc}")
            print(f"    Attributed to {w.date_utc} (UTC day)\n")
    else:
        print("\nNo workouts crossed the day boundary.")


def print_merged_data(daily_data: dict):
    """Print the merged daily data in a readable format."""
    print("\n" + "=" * 70)
    print("MERGED DAILY HEALTH DATA (All times normalized to UTC)")
    print("=" * 70)

    for day in sorted(daily_data.keys()):
        data = daily_data[day]
        print(f"\n{day}")
        print("-" * 40)

        if data.sleep_hours is not None:
            print(f"  Sleep: {data.sleep_hours:.1f} hrs (quality: {data.sleep_quality}/100)")
        else:
            print("  Sleep: No data")

        if data.workouts:
            print(f"  Workouts: {len(data.workouts)}")
            for w in data.workouts:
                boundary_flag = " [day boundary crossed]" if w.crossed_day_boundary else ""
                print(f"      - {w.workout_type}: {w.calories} cal, {w.duration_min} min{boundary_flag}")
            print(f"  Total: {data.total_calories} calories, {data.total_workout_minutes} min")
        else:
            print("  Workouts: None")


def print_correlations(correlations: dict):
    """Print correlation analysis results."""
    print("\n" + "=" * 70)
    print("CORRELATION ANALYSIS")
    print("=" * 70)

    print("\nSleep vs Exercise Metrics:\n")

    if 'avg_calories_low_sleep' in correlations:
        print(f"  Days with < 6 hours sleep ({correlations['low_sleep_day_count']} days):")
        print(f"    Average calories burned: {correlations['avg_calories_low_sleep']:.0f}")

    if 'avg_calories_good_sleep' in correlations:
        print(f"\n  Days with >= 7 hours sleep ({correlations['good_sleep_day_count']} days):")
        print(f"    Average calories burned: {correlations['avg_calories_good_sleep']:.0f}")

    if 'avg_calories_low_sleep' in correlations and 'avg_calories_good_sleep' in correlations:
        diff = correlations['avg_calories_good_sleep'] - correlations['avg_calories_low_sleep']
        insight_text = f"Insight: {abs(diff):.0f} more calories burned on well-rested days" if diff > 0 else f"Insight: {abs(diff):.0f} fewer calories burned on well-rested days"
        print(f"\n  {insight_text}")


def generate_json_output(
    merged: dict,
    workout_records: list[WorkoutRecord],
    correlations: dict
) -> dict:
    """
    Generate a comprehensive JSON output with merged health data.
    """
    daily_list = []

    # Convert daily aggregates to JSON-serializable format
    for day in sorted(merged.keys()):
        data = merged[day]

        # Build workout list for this day
        workouts = []
        for workout in data.workouts:
            workouts.append({
                "id": workout.id,
                "type": workout.workout_type,
                "duration_min": workout.duration_min,
                "calories": workout.calories,
                "timestamp_utc": workout.timestamp_utc.isoformat(),
                "original_timestamp": workout.original_timestamp,
                "original_timezone": workout.original_timezone,
                "day_boundary_crossed": workout.crossed_day_boundary
            })

        daily_entry = {
            "date_utc": str(day),
            "sleep": {
                "hours": data.sleep_hours,
                "quality_score": data.sleep_quality
            } if data.sleep_hours is not None else None,
            "workouts": workouts,
            "daily_totals": {
                "total_calories": data.total_calories,
                "total_workout_minutes": data.total_workout_minutes,
                "workout_count": len(data.workouts)
            }
        }

        daily_list.append(daily_entry)

    # Build output structure
    output = {
        "metadata": {
            "generated_at": datetime.now(ZoneInfo('UTC')).isoformat(),
            "total_days": len(merged),
            "date_range": {
                "start": str(min(merged.keys())),
                "end": str(max(merged.keys()))
            }
        },
        "daily_data": daily_list,
        "correlations": {
            "low_sleep_days": {
                "count": correlations.get('low_sleep_day_count', 0),
                "avg_calories_burned": round(correlations.get('avg_calories_low_sleep', 0), 2)
            },
            "good_sleep_days": {
                "count": correlations.get('good_sleep_day_count', 0),
                "avg_calories_burned": round(correlations.get('avg_calories_good_sleep', 0), 2)
            },
            "day_boundary_crossings": len([w for w in workout_records if w.crossed_day_boundary])
        }
    }

    return output


def save_json_output(output: dict, filepath: str = 'merged_health_data.json'):
    """
    Save merged health data to a JSON file.
    """
    with open(filepath, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"JSON output saved to: {filepath}")
