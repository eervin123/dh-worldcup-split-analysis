import pandas as pd
import re
import fitz  # PyMuPDF

filename = 'data/biel_dhi_me_results_tt.pdf'

def parse_timed_training_data_final(lines):
    data = []
    current_rider = {}
    run_number = 0
    collect_splits = False
    start_collecting = False  # Flag to start collecting data

    for line in lines:
        line = line.strip()
        if 'Nr Name / UCI MTB Team' in line:  # This marks the start of rider data
            start_collecting = True
            continue
        if not start_collecting:
            continue

        if line.endswith('.') or (re.match(r'^\d+ [A-Z]', line) and not current_rider):
            # Resetting for a new rider entry
            if current_rider:
                data.append(current_rider.copy())
                current_rider = {}
                run_number = 0
                collect_splits = False
            current_rider['Rank'] = line[:-1] if line.endswith('.') else None
            continue

        if re.match(r'^\d+ [A-Z]', line):  # Captures the number and name
            parts = line.split(maxsplit=1)
            current_rider['Number'] = parts[0]
            current_rider['Name'] = parts[1]
        elif line.isupper():  # Handles team and nationality
            if any(ext in line for ext in ['TEAM', 'FACTORY', 'RACING', 'GRAVITY']):
                current_rider['Team'] = line
            else:
                current_rider['NAT'] = line
        elif re.match(r'^\d+\.\d+$', line):  # Handles speed for a run
            run_number += 1
            current_rider[f'Run{run_number}_Speed'] = line
            collect_splits = True
            current_rider[f'Run{run_number}_Splits'] = []  # Prepare to collect splits
        elif collect_splits and (re.match(r'\d+:\d+\.\d+$', line) or re.match(r'\d+\.\d+$', line)):  # Captures splits
            current_rider[f'Run{run_number}_Splits'].append(line)
        elif collect_splits and re.match(r'\+\d+\.\d+$', line):  # Handles the delta time
            current_rider[f'Run{run_number}_Delta'] = line
            collect_splits = False  # Stop collecting splits for this run

    # Append the last rider if not already appended
    if current_rider:
        data.append(current_rider)

    # Convert to DataFrame and filter entries with missing crucial data
    df = pd.DataFrame(data)
    df = df[df['Number'].notna() & df['Name'].notna()]  # Ensure every entry has at least a number and a name
    return df

# Open the PDF and read its content

doc = fitz.open(filename)

all_text = []
for page in doc:
    text = page.get_text("text")
    all_text.extend(text.split('\n'))

# Parse the data directly from PDF text
df_timed_training_final = parse_timed_training_data_final(all_text)

# Extract runs and splits into a new structure
run_data = []
for _, row in df_timed_training_final.iterrows():
    for run in range(1, 4):
        run_splits = row.get(f'Run{run}_Splits', [])
        if run_splits:
            run_entry = {
                'Number': row['Number'],
                'Name': row['Name'],
                'Run': run,
                'Speed': row.get(f'Run{run}_Speed', None),
                'Splits': run_splits if isinstance(run_splits, list) else []
            }
            run_data.append(run_entry)

# Convert to DataFrame
df_runs = pd.DataFrame(run_data)

# Add original split times to the DataFrame
for i in range(5):  # Assuming max_splits is 5
    df_runs[f'Orig_Split_{i+1}_Time'] = df_runs['Splits'].apply(lambda x: x[i] if i < len(x) else None)

# Convert split times to seconds
def convert_to_seconds(split_time):
    if pd.isna(split_time):
        return None
    if ':' in split_time:
        minutes, seconds = map(float, split_time.split(':'))
        return minutes * 60 + seconds
    return float(split_time)

# Calculate and add cleaned split times to the DataFrame
for i in range(5):
    df_runs[f'Clean_Split_{i+1}_Time'] = df_runs[f'Orig_Split_{i+1}_Time'].apply(convert_to_seconds)

# Define function to calculate sector times
def calculate_sector_times(splits):
    sectors = []
    previous_split_time = 0
    for split in splits:
        # Convert split time to seconds
        split_time = convert_to_seconds(split)
        sector_time = split_time - previous_split_time if split_time is not None else None
        sectors.append(sector_time)
        previous_split_time = split_time if split_time is not None else previous_split_time
    return sectors

# Calculate and add sector times to the DataFrame
df_runs['Sector_Times'] = df_runs['Splits'].apply(lambda x: calculate_sector_times(x) if isinstance(x, list) else [])

# Ensure each run has 5 sectors
def pad_sector_times(sector_times):
    if len(sector_times) < 5:
        sector_times.extend([None] * (5 - len(sector_times)))
    return sector_times

df_runs['Sector_Times'] = df_runs['Sector_Times'].apply(pad_sector_times)

# Flatten the sector times into separate columns
for i in range(5):
    df_runs[f'Sector_{i+1}_Time'] = df_runs['Sector_Times'].apply(lambda x: x[i])

# Rank each split independently as integers, handling NaNs
for i in range(5):
    rank_col = f'Split_{i+1}_Rank'
    df_runs[rank_col] = df_runs[f'Clean_Split_{i+1}_Time'].rank(method='min', na_option='bottom')
    df_runs[rank_col] = df_runs[rank_col].fillna(df_runs[rank_col].max() + 1).astype(int)

# Rank each sector independently as integers, handling NaNs
for i in range(5):
    rank_col = f'Sector_{i+1}_Rank'
    df_runs[rank_col] = df_runs[f'Sector_{i+1}_Time'].rank(method='min', na_option='bottom')
    df_runs[rank_col] = df_runs[rank_col].fillna(df_runs[rank_col].max() + 1).astype(int)

# Convert speed to float for ranking and handle NaNs
df_runs['Speed'] = df_runs['Speed'].astype(float).fillna(0)  # Replace NaNs with a very small number (0)

# Rank speeds in descending order (higher speeds are better)
df_runs['Speed_Rank'] = df_runs['Speed'].rank(method='min', ascending=False, na_option='bottom')
df_runs['Speed_Rank'] = df_runs['Speed_Rank'].fillna(df_runs['Speed_Rank'].max() + 1).astype(int)

# Calculate cumulative times from each split to the finish
for i in range(4):  # Only up to Split 4
    df_runs[f'Cumulative_from_Split_{i+1}_Time'] = df_runs['Clean_Split_5_Time'] - df_runs[f'Clean_Split_{i+1}_Time']

# Rank cumulative times
for i in range(4):  # Only up to Split 4
    rank_col = f'Cumulative_from_Split_{i+1}_Rank'
    df_runs[rank_col] = df_runs[f'Cumulative_from_Split_{i+1}_Time'].rank(method='min', na_option='bottom')
    df_runs[rank_col] = df_runs[rank_col].fillna(df_runs[rank_col].max() + 1).astype(int)

# Save to CSV
# split filename and extension then replace extension with .csv
output_filename = filename.rsplit('.', 1)[0] + '.csv'
df_runs.to_csv(output_filename, index=False)

print(f'Data saved to {output_filename}')
