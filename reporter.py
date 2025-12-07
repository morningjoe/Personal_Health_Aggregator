"""
Reporting and output functions module.
"""Compatibility shim re-exporting reporter functions from `tool.reporter`.

The real implementations live in `tool/reporter.py`. Importing from the
top-level `reporter` module still works for compatibility.
"""

from tool.reporter import *  # noqa: F401,F403
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

    Args:
        output: Dictionary to serialize to JSON
        filepath: Path where JSON file will be saved
    """
    with open(filepath, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"JSON output saved to: {filepath}")
