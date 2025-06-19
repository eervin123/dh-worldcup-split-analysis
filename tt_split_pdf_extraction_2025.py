import pandas as pd
import re
import fitz  # PyMuPDF
import numpy as np

filename = "data/vdso_2025_dhi_me_results_tt.pdf"


def parse_timed_training_data_final(lines):
    print("\n=== Starting parse_timed_training_data_final ===")
    print(f"Number of lines to process: {len(lines)}")

    data = []
    rider_data = {}

    # Find the start of the results table
    start_index = -1
    for i, line in enumerate(lines):
        if "Nr Name / UCI MTB Team" in line:
            start_index = i
            print(f"Found start marker at line {i}: {line}")
            break

    if start_index == -1:
        print("Could not find start marker!")
        return data

    # Process lines after the start marker
    i = start_index + 1
    current_rider = None

    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Check if this is a new rider (starts with a number)
        rider_match = re.match(r"^(\d+)\.?\s*(.+?)\s*\(([A-Z]{3})\)", line)
        if rider_match:
            # Save previous rider data if exists
            if current_rider:
                data.append(current_rider)

            # Start new rider
            current_rider = {
                "Number": rider_match.group(1),
                "Name": rider_match.group(2).strip(),
                "NAT": rider_match.group(3),
                "Team": "",
                "Runs": {},
            }
            print(f"Found rider: {current_rider['Name']} ({current_rider['NAT']})")

            # Initialize runs
            for run_num in range(1, 6):
                current_rider["Runs"][run_num] = {
                    "splits": [],
                    "final_time": None,
                    "speed": None,
                    "valid": False,
                }

            # Look for team name on next line
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if (
                    next_line
                    and not re.match(r"^\d+\.?\s*", next_line)
                    and not re.match(r"^[A-Z]{3}$", next_line)
                ):
                    current_rider["Team"] = next_line
                    i += 1  # Skip the team line in next iteration

            i += 1
            continue

        # Check if this line contains a time (format like 0:46.519)
        time_match = re.match(r"^(\d+:\d+\.\d+)$", line)
        if time_match:
            # This is a split time, collect all consecutive times for this run
            run_splits = []
            run_speed = None
            run_num = 1

            # Find which run this belongs to by looking at the current state
            if current_rider:
                # Count how many runs we've already processed
                for r in range(1, 6):
                    if current_rider["Runs"][r]["splits"]:
                        run_num = r + 1
                    else:
                        break

            # Collect all consecutive times
            j = i
            while j < len(lines) and j < i + 10:  # Limit to avoid infinite loop
                current_line = lines[j].strip()

                # Check for time
                time_match = re.match(r"^(\d+:\d+\.\d+)$", current_line)
                if time_match:
                    run_splits.append(time_match.group(1))
                    j += 1
                    continue

                # Check for speed
                speed_match = re.search(r"(\d+\.\d+)kmh", current_line)
                if speed_match:
                    run_speed = float(speed_match.group(1))
                    j += 1
                    break

                # Check for dashes (invalid run)
                if current_line == "-" or all(c in "- " for c in current_line):
                    run_splits = []
                    j += 1
                    break

                # If we hit something else, stop collecting
                break

            # Store the run data
            if current_rider and run_num <= 5 and run_splits:
                current_rider["Runs"][run_num]["splits"] = run_splits
                current_rider["Runs"][run_num]["final_time"] = run_splits[-1]
                current_rider["Runs"][run_num]["speed"] = run_speed
                current_rider["Runs"][run_num]["valid"] = True
                print(
                    f"  Run {run_num}: {len(run_splits)} splits, final time: {run_splits[-1]}"
                )

            i = j
            continue

        # Check for speed on its own line
        speed_match = re.search(r"(\d+\.\d+)kmh", line)
        if speed_match and current_rider:
            # Find the current run and add speed
            for run_num in range(1, 6):
                if (
                    current_rider["Runs"][run_num]["splits"]
                    and not current_rider["Runs"][run_num]["speed"]
                ):
                    current_rider["Runs"][run_num]["speed"] = float(
                        speed_match.group(1)
                    )
                    break

        i += 1

    # Add the last rider
    if current_rider:
        data.append(current_rider)

    print(f"\nParsed {len(data)} riders")
    return data


def convert_time_to_seconds(time_str):
    """Convert time string like '3:41.976' to seconds"""
    if not time_str or time_str == "None":
        return None

    # Handle format like "3:41.976" or "0:46.519"
    parts = time_str.split(":")
    if len(parts) == 2:
        minutes = int(parts[0])
        seconds = float(parts[1])
        return minutes * 60 + seconds

    return None


def calculate_sector_times(splits):
    """Calculate sector times from split times"""
    if not splits or len(splits) < 2:
        return []

    sector_times = []
    for i in range(len(splits) - 1):
        current_split = convert_time_to_seconds(splits[i])
        next_split = convert_time_to_seconds(splits[i + 1])

        if current_split is not None and next_split is not None:
            sector_time = next_split - current_split
            sector_times.append(sector_time)
        else:
            sector_times.append(None)

    return sector_times


# Main processing
print("=== Starting PDF Processing ===")
doc = fitz.open(filename)
page = doc[0]
text = page.get_text("text")
lines = text.split("\n")

# Parse the data
rider_data = parse_timed_training_data_final(lines)

# Convert to DataFrame format
df_data = []
for rider in rider_data:
    for run_num in range(1, 6):
        run_data = rider["Runs"][run_num]

        if not run_data["valid"]:
            continue

        # Calculate sector times
        sector_times = calculate_sector_times(run_data["splits"])

        # Convert splits to seconds
        split_seconds = [convert_time_to_seconds(split) for split in run_data["splits"]]
        final_time_seconds = convert_time_to_seconds(run_data["final_time"])

        row = {
            "Number": rider["Number"],
            "Name": rider["Name"],
            "Run": run_num,
            "Splits": run_data["splits"],
            "Time": run_data["final_time"],
            "Speed": run_data["speed"] or 0.0,
            "Final_Time_Seconds": final_time_seconds,
        }

        # Add split times
        for i, split in enumerate(run_data["splits"], 1):
            row[f"Orig_Split_{i}_Time"] = split
            row[f"Clean_Split_{i}_Time"] = convert_time_to_seconds(split)

        # Add sector times
        for i, sector_time in enumerate(sector_times, 1):
            row[f"Sector_{i}_Time"] = sector_time

        df_data.append(row)

df_timed_training_final = pd.DataFrame(df_data)

# Calculate ranks and additional metrics
print("\n=== Calculating Ranks and Metrics ===")

# Calculate ranks for each metric
metrics_to_rank = []
for i in range(1, 6):
    metrics_to_rank.extend([f"Clean_Split_{i}_Time", f"Sector_{i}_Time"])

for metric in metrics_to_rank:
    if metric in df_timed_training_final.columns:
        rank_col = metric.replace("_Time", "_Rank")
        df_timed_training_final[rank_col] = df_timed_training_final[metric].rank(
            method="min", na_option="bottom"
        )

# Speed rank
df_timed_training_final["Speed_Rank"] = df_timed_training_final["Speed"].rank(
    method="min", ascending=False, na_option="bottom"
)

# Calculate cumulative times
for i in range(1, 5):
    cumulative_col = f"Cumulative_from_Split_{i}_Time"
    df_timed_training_final[cumulative_col] = df_timed_training_final.apply(
        lambda row: sum(row[f"Clean_Split_{j}_Time"] or 0 for j in range(i + 1, 6)),
        axis=1,
    )

    cumulative_rank_col = f"Cumulative_from_Split_{i}_Rank"
    df_timed_training_final[cumulative_rank_col] = df_timed_training_final[
        cumulative_col
    ].rank(method="min", na_option="bottom")

# Overall rank based on final time
df_timed_training_final["Overall_Rank"] = df_timed_training_final[
    "Final_Time_Seconds"
].rank(method="min", na_option="bottom")

# Total time (same as final time)
df_timed_training_final["Total_Time"] = df_timed_training_final["Final_Time_Seconds"]

print(f"Created DataFrame with {len(df_timed_training_final)} rows")
print(f"Columns: {list(df_timed_training_final.columns)}")

# Save to CSV
output_filename = filename.replace(".pdf", ".csv")
df_timed_training_final.to_csv(output_filename, index=False)
print(f"Saved to {output_filename}")

# Show some sample data
print("\n=== Sample Data ===")
print(
    df_timed_training_final[
        ["Number", "Name", "Run", "Time", "Speed", "Overall_Rank"]
    ].head(10)
)

doc.close()
