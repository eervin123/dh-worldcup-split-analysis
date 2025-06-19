import pandas as pd
import re
import fitz  # PyMuPDF
import numpy as np

filename = "data/vdso_2025_dhi_me_results_tt.pdf"


def parse_timed_training_data_final(lines):
    data = []
    current_rider = None
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Look for rider number and name
        number_match = re.match(r"^(\d+)\s+(.+)$", line)
        if number_match:
            # Save previous rider data if exists
            if current_rider:
                data.append(current_rider)

            # Initialize new rider
            current_rider = {
                "Number": number_match.group(1),
                "Name": number_match.group(2),
                "Runs": {
                    run: {
                        "splits": [],
                        "final_time": None,
                        "speed": None,
                        "valid": False,
                    }
                    for run in range(1, 6)
                },
            }
            print(f"\nProcessing rider: {current_rider['Name']}")
            i += 1
            continue

        # Look for speed (indicates start of a new run)
        speed_match = re.search(r"(\d+\.\d+)kmh", line)
        if speed_match and current_rider:
            # Find next available run slot
            run_num = 1
            while run_num <= 5 and current_rider["Runs"][run_num]["valid"]:
                run_num += 1

            if run_num <= 5:  # Only process if we haven't exceeded max runs
                current_rider["Runs"][run_num]["speed"] = float(speed_match.group(1))
                print(f"  Found speed for run {run_num}: {speed_match.group(1)}kmh")

                # Look for splits starting from the next line
                splits = []
                j = i + 1
                while (
                    j < len(lines) and j < i + 15
                ):  # Limit search to avoid infinite loop
                    split_line = lines[j].strip()

                    # Valid split time format
                    if re.match(r"^\d+:\d+\.\d+$", split_line):
                        splits.append(split_line)
                        j += 1
                    # Skip dashes or empty lines
                    elif split_line == "-" or not split_line:
                        j += 1
                    # Stop if we hit another speed or rider
                    elif re.search(r"kmh", split_line) or re.match(
                        r"^\d+\s+[A-Z]", split_line
                    ):
                        break
                    else:
                        break

                # Only store run data if we found valid splits
                if splits:
                    # Check if this is a 'Best' column artifact: all splits are identical and match a previous final time
                    is_best_column = False
                    if len(splits) > 1 and len(set(splits)) == 1:
                        for prev_run in range(1, run_num):
                            prev_final = current_rider["Runs"][prev_run]["final_time"]
                            if prev_final and prev_final == splits[0]:
                                is_best_column = True
                                break
                    if is_best_column:
                        print(f"  Skipping 'Best' column artifact for run {run_num}")
                        i = j
                        continue
                    # ... existing duplicate detection logic ...
                    is_duplicate = False
                    for prev_run in range(1, run_num):
                        if current_rider["Runs"][prev_run]["splits"] == splits:
                            is_duplicate = True
                            break
                    if not is_duplicate:
                        current_rider["Runs"][run_num]["splits"] = splits
                        current_rider["Runs"][run_num]["final_time"] = splits[-1]
                        current_rider["Runs"][run_num]["valid"] = True
                        print(
                            f"  Run {run_num}: {len(splits)} splits, final time: {splits[-1]}"
                        )
                    else:
                        print(f"  Skipping duplicate run {run_num}")
                i = j
                continue

        # Look for split times that might not have speed (for runs without speed data)
        if re.match(r"^\d+:\d+\.\d+$", line) and current_rider:
            # Check if this is part of an existing run or a new run
            # Find next available run slot
            run_num = 1
            while run_num <= 5 and current_rider["Runs"][run_num]["valid"]:
                run_num += 1

            if run_num <= 5:  # Only process if we haven't exceeded max runs
                # Collect splits for this run
                splits = []
                j = i
                while (
                    j < len(lines) and j < i + 15
                ):  # Limit search to avoid infinite loop
                    split_line = lines[j].strip()

                    # Valid split time format
                    if re.match(r"^\d+:\d+\.\d+$", split_line):
                        splits.append(split_line)
                        j += 1
                    # Skip dashes or empty lines
                    elif split_line == "-" or not split_line:
                        j += 1
                    # Stop if we hit another speed or rider
                    elif re.search(r"kmh", split_line) or re.match(
                        r"^\d+\s+[A-Z]", split_line
                    ):
                        break
                    else:
                        break

                # Only store run data if we found valid splits and they're not duplicates
                if splits:
                    # Check if this is a 'Best' column artifact: all splits are identical and match a previous final time
                    is_best_column = False
                    if len(splits) > 1 and len(set(splits)) == 1:
                        for prev_run in range(1, run_num):
                            prev_final = current_rider["Runs"][prev_run]["final_time"]
                            if prev_final and prev_final == splits[0]:
                                is_best_column = True
                                break
                    if is_best_column:
                        print(f"  Skipping 'Best' column artifact for run {run_num}")
                        i = j
                        continue
                    # ... existing duplicate detection logic ...
                    is_duplicate = False
                    for prev_run in range(1, run_num):
                        if current_rider["Runs"][prev_run]["splits"] == splits:
                            is_duplicate = True
                            break
                    if not is_duplicate:
                        current_rider["Runs"][run_num]["splits"] = splits
                        current_rider["Runs"][run_num]["final_time"] = splits[-1]
                        current_rider["Runs"][run_num]["valid"] = True
                        print(
                            f"  Run {run_num}: {len(splits)} splits, final time: {splits[-1]}"
                        )
                    else:
                        print(f"  Skipping duplicate run {run_num}")

                i = j
                continue

        i += 1

    # Add the last rider
    if current_rider:
        data.append(current_rider)

    print(f"\nParsed {len(data)} riders")
    return data


# Helper functions
def convert_time_to_seconds(split_time):
    if pd.isna(split_time):
        return None
    if ":" in split_time:
        minutes, seconds = map(float, split_time.split(":"))
        return minutes * 60 + seconds
    return float(split_time)


def calculate_sector_times(splits):
    sectors = []
    previous_split_time = 0
    for split in splits:
        # Convert split time to seconds
        split_time = convert_time_to_seconds(split)
        if split_time is not None:
            sector_time = split_time - previous_split_time
            sectors.append(sector_time)
            previous_split_time = split_time
        else:
            sectors.append(None)
    return sectors


# Main processing
print("=== Starting PDF Processing ===")
doc = fitz.open(filename)

# Process all pages, not just the first one
all_lines = []
for page_num in range(len(doc)):
    page = doc[page_num]
    text = page.get_text("text")  # Correct PyMuPDF API call
    lines = text.split("\n")
    print(f"Processing page {page_num + 1}: {len(lines)} lines")
    all_lines.extend(lines)

print(f"Total lines across all pages: {len(all_lines)}")

# Parse the data from all pages
rider_data = parse_timed_training_data_final(all_lines)

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

# After DataFrame creation, add a 'Best' column for each rider
if not df_timed_training_final.empty:
    best_times = (
        df_timed_training_final[df_timed_training_final["Time"].notna()]
        .groupby("Number")["Final_Time_Seconds"]
        .min()
        .reset_index()
    )
    best_times = best_times.rename(columns={"Final_Time_Seconds": "Best"})
    df_timed_training_final = df_timed_training_final.merge(
        best_times, on="Number", how="left"
    )

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
