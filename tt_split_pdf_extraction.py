import pandas as pd
import re
import fitz  # PyMuPDF

filename = "data/leog_2025_dhi_me_results_tt.pdf"


def parse_timed_training_data_final(lines):
    print("\n=== Starting parse_timed_training_data_final ===")
    print(f"Number of lines to process: {len(lines)}")
    data = []
    current_rider = {}
    run_number = 0
    collect_splits = False
    start_collecting = False  # Flag to start collecting data

    for line in lines:
        line = line.strip()
        if "Nr Name / UCI MTB Team" in line:  # This marks the start of rider data
            print(f"Found start marker: {line}")
            start_collecting = True
            continue
        if not start_collecting:
            continue

        if line.endswith(".") or (re.match(r"^\d+ [A-Z]", line) and not current_rider):
            # Resetting for a new rider entry
            if current_rider:
                print(f"Adding rider: {current_rider.get('Name', 'Unknown')}")
                data.append(current_rider.copy())
                current_rider = {}
                run_number = 0
                collect_splits = False
            current_rider["Rank"] = line[:-1] if line.endswith(".") else None
            continue

        if re.match(r"^\d+ [A-Z]", line):  # Captures the number and name
            parts = line.split(maxsplit=1)
            current_rider["Number"] = parts[0]
            current_rider["Name"] = parts[1]
            print(f"Processing rider: {parts[1]}")
        elif line.isupper():  # Handles team and nationality
            if any(ext in line for ext in ["TEAM", "FACTORY", "RACING", "GRAVITY"]):
                current_rider["Team"] = line
            else:
                current_rider["NAT"] = line
        elif re.match(r"^\d+:\d+\.\d+$", line):  # Handles split times
            if not collect_splits:
                run_number += 1
                collect_splits = True
                current_rider[f"Run{run_number}_Splits"] = []
            current_rider[f"Run{run_number}_Splits"].append(line)
            print(f"Added split: {line} for run {run_number}")
        elif re.match(r"^\d+\.\d+$", line):  # Handles final time
            if collect_splits:
                current_rider[f"Run{run_number}_Time"] = line
                collect_splits = False
                print(f"Added final time: {line} for run {run_number}")

    # Append the last rider if not already appended
    if current_rider:
        print(f"Adding final rider: {current_rider.get('Name', 'Unknown')}")
        data.append(current_rider)

    # Convert to DataFrame and filter entries with missing crucial data
    df = pd.DataFrame(data)
    print(f"\nInitial DataFrame shape: {df.shape}")
    df = df[
        df["Number"].notna() & df["Name"].notna()
    ]  # Ensure every entry has at least a number and a name
    print(f"DataFrame shape after filtering: {df.shape}")
    return df


# Open the PDF and read its content
print("\n=== Starting PDF Processing ===")
doc = fitz.open(filename)
print(f"PDF opened successfully. Number of pages: {len(doc)}")

all_text = []
for page in doc:
    text = page.get_text("text")
    all_text.extend(text.split("\n"))

print(f"Total lines extracted from PDF: {len(all_text)}")
print("=== Finished PDF Processing ===\n")

# Parse the data directly from PDF text
df_timed_training_final = parse_timed_training_data_final(all_text)

# Extract runs and splits into a new structure
print("\n=== Starting Run Data Extraction ===")
run_data = []
for _, row in df_timed_training_final.iterrows():
    for run in range(1, 6):  # Changed to 6 runs as per PDF format
        run_splits = row.get(f"Run{run}_Splits", [])
        if run_splits:
            # Get the last split time as the final time
            final_time = run_splits[-1] if run_splits else None
            run_entry = {
                "Number": row["Number"],
                "Name": row["Name"],
                "Run": run,
                "Splits": run_splits if isinstance(run_splits, list) else [],
                "Time": final_time,
            }
            run_data.append(run_entry)
            print(f"Added run {run} for {row['Name']} with {len(run_splits)} splits")

# Convert to DataFrame
df_runs = pd.DataFrame(run_data)
print(f"\nRun DataFrame shape: {df_runs.shape}")
print("=== Finished Run Data Extraction ===\n")

# Add original split times to the DataFrame
print("\n=== Starting Split Time Processing ===")
for i in range(5):  # Assuming max_splits is 5
    df_runs[f"Orig_Split_{i+1}_Time"] = df_runs["Splits"].apply(
        lambda x: x[i] if i < len(x) else None
    )


# Convert split times to seconds
def convert_to_seconds(split_time):
    if pd.isna(split_time):
        return None
    if ":" in split_time:
        minutes, seconds = map(float, split_time.split(":"))
        return minutes * 60 + seconds
    return float(split_time)


# Calculate and add cleaned split times to the DataFrame
for i in range(5):
    df_runs[f"Clean_Split_{i+1}_Time"] = df_runs[f"Orig_Split_{i+1}_Time"].apply(
        convert_to_seconds
    )


# Define function to calculate sector times
def calculate_sector_times(splits):
    sectors = []
    previous_split_time = 0
    for split in splits:
        # Convert split time to seconds
        split_time = convert_to_seconds(split)
        if split_time is not None:
            sector_time = split_time - previous_split_time
            sectors.append(sector_time)
            previous_split_time = split_time
        else:
            sectors.append(None)
    return sectors


# Calculate and add sector times to the DataFrame
df_runs["Sector_Times"] = df_runs["Splits"].apply(
    lambda x: calculate_sector_times(x) if isinstance(x, list) else []
)


# Ensure each run has 5 sectors
def pad_sector_times(sector_times):
    if len(sector_times) < 5:
        sector_times.extend([None] * (5 - len(sector_times)))
    return sector_times


df_runs["Sector_Times"] = df_runs["Sector_Times"].apply(pad_sector_times)

# Flatten the sector times into separate columns
for i in range(5):
    df_runs[f"Sector_{i+1}_Time"] = df_runs["Sector_Times"].apply(lambda x: x[i])

print(f"Final DataFrame shape: {df_runs.shape}")
print("=== Finished Split Time Processing ===\n")

# Rank each split independently as integers, handling NaNs
print("\n=== Starting Ranking Calculations ===")
for i in range(5):
    rank_col = f"Split_{i+1}_Rank"
    df_runs[rank_col] = df_runs[f"Clean_Split_{i+1}_Time"].rank(
        method="min", na_option="bottom"
    )
    df_runs[rank_col] = (
        df_runs[rank_col].fillna(df_runs[rank_col].max() + 1).astype(int)
    )

# Rank each sector independently as integers, handling NaNs
for i in range(5):
    rank_col = f"Sector_{i+1}_Rank"
    df_runs[rank_col] = df_runs[f"Sector_{i+1}_Time"].rank(
        method="min", na_option="bottom"
    )
    df_runs[rank_col] = (
        df_runs[rank_col].fillna(df_runs[rank_col].max() + 1).astype(int)
    )

# Convert time to float for ranking and handle NaNs
df_runs["Time"] = df_runs["Time"].apply(convert_to_seconds)  # Convert time to seconds
df_runs["Time"] = df_runs["Time"].fillna(
    float("inf")
)  # Replace NaNs with infinity for ranking

# Rank times in ascending order (lower times are better)
df_runs["Time_Rank"] = df_runs["Time"].rank(method="min", na_option="bottom")
df_runs["Time_Rank"] = (
    df_runs["Time_Rank"].fillna(df_runs["Time_Rank"].max() + 1).astype(int)
)

# Calculate cumulative times from each split to the finish
for i in range(4):  # Only up to Split 4
    df_runs[f"Cumulative_from_Split_{i+1}_Time"] = (
        df_runs["Time"] - df_runs[f"Clean_Split_{i+1}_Time"]
    )
    # Add rank for each cumulative time
    df_runs[f"Cumulative_from_Split_{i+1}_Rank"] = df_runs[
        f"Cumulative_from_Split_{i+1}_Time"
    ].rank(method="min", na_option="bottom")
    df_runs[f"Cumulative_from_Split_{i+1}_Rank"] = (
        df_runs[f"Cumulative_from_Split_{i+1}_Rank"]
        .fillna(df_runs[f"Cumulative_from_Split_{i+1}_Rank"].max() + 1)
        .astype(int)
    )

# Calculate speed (assuming course length is 2.5km - adjust if needed)
COURSE_LENGTH = 2.5  # in kilometers
df_runs["Speed"] = (COURSE_LENGTH / (df_runs["Time"] / 3600)).round(3)  # Speed in km/h

# Rank speeds in descending order (higher speeds are better)
# First replace inf values with NaN
df_runs["Speed"] = df_runs["Speed"].replace([float("inf"), float("-inf")], float("nan"))
# Then rank, handling NaN values appropriately
df_runs["Speed_Rank"] = df_runs["Speed"].rank(
    method="min", ascending=False, na_option="bottom"
)
df_runs["Speed_Rank"] = (
    df_runs["Speed_Rank"].fillna(df_runs["Speed_Rank"].max() + 1).astype(int)
)

# Clean up the DataFrame for output
output_columns = [
    "Number",
    "Name",
    "Run",
    "Time",
    "Time_Rank",
    "Speed",
    "Speed_Rank",
    "Splits",
    "Sector_Times",
    "Orig_Split_1_Time",
    "Orig_Split_2_Time",
    "Orig_Split_3_Time",
    "Orig_Split_4_Time",
    "Orig_Split_5_Time",
    "Clean_Split_1_Time",
    "Clean_Split_2_Time",
    "Clean_Split_3_Time",
    "Clean_Split_4_Time",
    "Clean_Split_5_Time",
    "Split_1_Rank",
    "Split_2_Rank",
    "Split_3_Rank",
    "Split_4_Rank",
    "Split_5_Rank",
    "Sector_1_Time",
    "Sector_2_Time",
    "Sector_3_Time",
    "Sector_4_Time",
    "Sector_5_Time",
    "Sector_1_Rank",
    "Sector_2_Rank",
    "Sector_3_Rank",
    "Sector_4_Rank",
    "Sector_5_Rank",
    "Cumulative_from_Split_1_Time",
    "Cumulative_from_Split_2_Time",
    "Cumulative_from_Split_3_Time",
    "Cumulative_from_Split_4_Time",
    "Cumulative_from_Split_1_Rank",
    "Cumulative_from_Split_2_Rank",
    "Cumulative_from_Split_3_Rank",
    "Cumulative_from_Split_4_Rank",
]


# Convert times back to M:SS.mmm format for display
def format_time(time_value):
    if pd.isna(time_value):
        return None
    if isinstance(time_value, str):
        return time_value  # Already in correct format
    minutes = int(time_value // 60)
    remaining_seconds = time_value % 60
    return f"{minutes}:{remaining_seconds:06.3f}"


# Format the time column
df_runs["Time"] = df_runs["Time"].apply(format_time)

# Format split times
for i in range(5):
    df_runs[f"Orig_Split_{i+1}_Time"] = df_runs[f"Orig_Split_{i+1}_Time"].apply(
        format_time
    )

# Format sector times (keep as seconds)
df_runs["Sector_Times"] = df_runs["Sector_Times"].apply(
    lambda x: [f"{t:.3f}" if t is not None else None for t in x]
)

# Format splits (keep as M:SS.mmm)
df_runs["Splits"] = df_runs["Splits"].apply(
    lambda x: [format_time(convert_to_seconds(t)) if t is not None else None for t in x]
)

df_output = df_runs[output_columns].copy()

# Save the results
output_file = "data/leog_2025_dhi_me_results_tt.csv"
df_output.to_csv(output_file, index=False)
print(f"\nData saved to {output_file}")
