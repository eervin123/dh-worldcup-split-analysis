import pandas as pd
import re
import fitz  # PyMuPDF

filename = "data/leog_2025_dhi_me_results_tt.pdf"


def parse_timed_training_data_final(lines):
    data = []
    current_rider = {}
    run_number = 0
    collect_splits = False
    start_collecting = False  # Flag to start collecting data

    print("\n=== Debug: Examining text content ===")
    for i, line in enumerate(lines):
        line = line.strip()
        if "Nr Name / UCI MTB Team" in line:
            print(f"\nFound header at line {i}: {line}")
            start_collecting = True
            continue
        if not start_collecting:
            continue

        # Debug prints for potential split times
        if (
            re.match(r"^\d+\.\d+$", line)
            or re.match(r"\d+:\d+\.\d+$", line)
            or re.match(r"\+\d+\.\d+$", line)
        ):
            print(f"Potential split/speed at line {i}: {line}")
            print(f"Previous line: {lines[i-1].strip() if i > 0 else 'N/A'}")
            print(f"Next line: {lines[i+1].strip() if i < len(lines)-1 else 'N/A'}")

        if line.endswith(".") or (re.match(r"^\d+ [A-Z]", line) and not current_rider):
            # Resetting for a new rider entry
            if current_rider:
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
            print(f"\nProcessing rider: {parts[1]}")
        elif line.isupper():  # Handles team and nationality
            if any(ext in line for ext in ["TEAM", "FACTORY", "RACING", "GRAVITY"]):
                current_rider["Team"] = line
            else:
                current_rider["NAT"] = line
        elif re.match(r"^\d+\.\d+$", line):  # Handles speed for a run
            run_number += 1
            current_rider[f"Run{run_number}_Speed"] = line
            collect_splits = True
            current_rider[f"Run{run_number}_Splits"] = []  # Prepare to collect splits
            print(f"Found speed for run {run_number}: {line}")
        elif collect_splits and (
            re.match(r"\d+:\d+\.\d+$", line) or re.match(r"\d+\.\d+$", line)
        ):  # Captures splits
            current_rider[f"Run{run_number}_Splits"].append(line)
            print(f"Added split for run {run_number}: {line}")
        elif collect_splits and re.match(
            r"\+\d+\.\d+$", line
        ):  # Handles the delta time
            current_rider[f"Run{run_number}_Delta"] = line
            collect_splits = False  # Stop collecting splits for this run
            print(f"Finished splits for run {run_number}")

    # Append the last rider if not already appended
    if current_rider:
        data.append(current_rider)

    # Convert to DataFrame and filter entries with missing crucial data
    df = pd.DataFrame(data)
    df = df[
        df["Number"].notna() & df["Name"].notna()
    ]  # Ensure every entry has at least a number and a name
    return df


# Open the PDF and read its content
doc = fitz.open(filename)

all_text = []
for page in doc:
    text = page.get_text("text")
    all_text.extend(text.split("\n"))

# Parse the data directly from PDF text
df_timed_training_final = parse_timed_training_data_final(all_text)
print("\nFirst few entries of the parsed data:")
print(df_timed_training_final.head())
print("\nLast few entries of the parsed data:")
print(df_timed_training_final.tail())

# Print column names to verify data structure
print("\nColumns in the DataFrame:")
print(df_timed_training_final.columns.tolist())

# Print a sample row to see the split data
print("\nSample row with split data:")
sample_row = df_timed_training_final.iloc[0]
for col in df_timed_training_final.columns:
    print(f"{col}: {sample_row[col]}")
