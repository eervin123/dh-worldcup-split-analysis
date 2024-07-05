# Filename: utils.py
# Description: This file contains utility functions that are used in both timed_training.py and event_results.py.

import pandas as pd

def seconds_to_human_readable(seconds):
    if pd.isna(seconds):
        return "N/A"
    minutes = int(seconds // 60)
    seconds = seconds % 60
    return f"{minutes}:{seconds:05.2f}"

def clean_column_name(col_name):
    return (
        col_name.replace("Orig_", "")
        .replace("_", " ")
        .replace("Clean_", "")
        .replace("Time", "")
        .title()
        .strip()
    )

def convert_to_seconds(time_str):
    try:
        if pd.isna(time_str):
            return None
        if ":" in time_str:
            minutes, seconds = map(float, time_str.split(":"))
            return minutes * 60 + seconds
        return float(time_str)
    except ValueError:
        return None
