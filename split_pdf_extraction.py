import fitz
from typing import List, Dict, Union
import pandas as pd
from datetime import datetime, timedelta

def extract_time_and_rank(data_string: str) -> (str, str):
    if "(" in data_string:
        time, rank = data_string.split()[0], data_string.split()[-1].strip("()")
        return time, rank
    else:
        return "N/A", "N/A"

def calculate_sector_times(split_times: List[str]) -> List[str]:
    sector_times = []
    previous_time = "0:00.000"

    for split_time in split_times:
        try:
            delta = datetime.strptime(split_time, "%M:%S.%f") - datetime.strptime(previous_time, "%M:%S.%f")
            sector_times.append(str(delta)[2:])  # Skip "0:" part in "0:XX.XXX" string
            previous_time = split_time
        except ValueError as e:
            sector_times.append("N/A")

    return sector_times

def extract_rider_info_all_pages(filename: str, table_start_line: int = 25) -> List[Dict[str, Union[str, List[str]]]]:
    doc = fitz.open(filename)
    riders_info = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        lines = text.split('\n')
        line_start = table_start_line

        while line_start < len(lines):
            rider_info = lines[line_start:line_start + 20]
            if len(rider_info) < 19:
                break

            # No team case
            if rider_info[5].isdigit():
                speed_trap, speed_trap_rank = extract_time_and_rank(rider_info[8])
                split_times, split_time_ranks = zip(*(extract_time_and_rank(s) for s in rider_info[9:13]))
                rider_data = {
                    'rank': rider_info[0].split()[0].replace('.', ''),
                    'protected': rider_info[0].split()[1] if len(rider_info[0].split()) > 1 else '',
                    'rider_number': rider_info[1].split()[0],
                    'name': ' '.join(rider_info[1].split()[1:]),
                    'team': 'N/A',
                    'uci_id': rider_info[5],
                    'country': rider_info[6],
                    'birth_year': rider_info[7],
                    'speed_trap': speed_trap,
                    'speed_trap_rank': speed_trap_rank,
                    'split_times': list(split_times),
                    'split_time_ranks': list(split_time_ranks),
                    'final_time': rider_info[13],
                    'gap': rider_info[17] if len(rider_info) > 17 else 'N/A',
                    'points': rider_info[18] if len(rider_info) > 18 else 'N/A'
                }
                next_offset = 19
            # With team case
            else:
                speed_trap, speed_trap_rank = extract_time_and_rank(rider_info[9])
                split_times, split_time_ranks = zip(*(extract_time_and_rank(s) for s in rider_info[10:14]))
                rider_data = {
                    'rank': rider_info[0].split()[0].replace('.', ''),
                    'protected': rider_info[0].split()[1] if len(rider_info[0].split()) > 1 else '',
                    'rider_number': rider_info[1].split()[0],
                    'name': ' '.join(rider_info[1].split()[1:]),
                    'team': rider_info[5],
                    'uci_id': rider_info[6],
                    'country': rider_info[7],
                    'birth_year': rider_info[8],
                    'speed_trap': speed_trap,
                    'speed_trap_rank': speed_trap_rank,
                    'split_times': list(split_times),
                    'split_time_ranks': list(split_time_ranks),
                    'final_time': rider_info[14],
                    'gap': rider_info[18] if len(rider_info) > 18 else 'N/A',
                    'points': rider_info[19] if len(rider_info) > 19 else 'N/A'
                }
                next_offset = 20

            if rider_data['final_time'] in ['DNF', 'DNS', 'DSQ']:
                line_start += next_offset
                continue

            sector_times = calculate_sector_times(rider_data['split_times'])
            rider_data['sector_times'] = sector_times
            riders_info.append(rider_data)
            line_start += next_offset

    return riders_info

def is_valid_time_format(time_str):
    try:
        datetime.strptime(time_str, "%M:%S.%f")
        return True
    except ValueError:
        return False

def is_invalid_entry(entry):
    invalid_terms = ['DNF', 'DNS', 'DSQ', '-', 'N/A', 'Average', 'YOB', 'In', 'Year', 'MACDERMID', 'GUIONNET', 'TRUMMER', 'RIESCO', 'SCHLEBES', 'DORVAL AM COMMENCAL']
    return any(term in entry for term in invalid_terms)

def validate_and_clean_data(df):
    valid_rows = []
    for _, row in df.iterrows():
        if (is_valid_time_format(row["final_time"]) and is_valid_time_format(row["split_4"]) and
                not is_invalid_entry(row["final_time"]) and not is_invalid_entry(row["split_4"])):
            valid_rows.append(row)
    return pd.DataFrame(valid_rows)

def process_results(filename: str, table_start_line: int):
    # Generate DataFrame
    riders_info = extract_rider_info_all_pages(filename, table_start_line)
    df = pd.DataFrame(riders_info)
    for i in range(4):
        df[f'split_{i+1}'] = df['split_times'].apply(lambda x: x[i] if len(x) > i else 'N/A')
        df[f'split_{i+1}_rank'] = df['split_time_ranks'].apply(lambda x: x[i] if len(x) > i else 'N/A')
        df[f'sector_{i+1}'] = df['sector_times'].apply(lambda x: x[i] if len(x) > i else 'N/A')

    # Debugging: Print problematic sector times
    print("Sector times with issues:")
    print(df[['sector_1', 'sector_2', 'sector_3', 'sector_4', 'final_time', 'split_4']].head(20))

    # Additional Debugging for final sector times
    for i, row in df.iterrows():
        final_time = row["final_time"]
        split_4 = row["split_4"]
        if not is_valid_time_format(final_time) or is_invalid_entry(final_time):
            print(f"Invalid final time format at index {i}: {final_time}")
        if not is_valid_time_format(split_4) or is_invalid_entry(split_4):
            print(f"Invalid split_4 time format at index {i}: {split_4}")

    # Validate and clean the data
    df = validate_and_clean_data(df)

    # Drop rows with invalid final_time or split_4 before ranking
    df = df[df.apply(lambda row: is_valid_time_format(row["final_time"]) and is_valid_time_format(row["split_4"]), axis=1)]

    # Further remove rows with any invalid sector times
    for i in range(4):
        df = df[df.apply(lambda row: is_valid_time_format(row[f'sector_{i+1}']), axis=1)]

    # Rank the sector times correctly
    for i in range(4):
        df[f'sector_{i+1}_rank'] = df[f'sector_{i+1}'].apply(
            lambda x: timedelta(minutes=int(x.split(":")[0]), seconds=float(x.split(":")[1]))
            if is_valid_time_format(x) else timedelta.max
        ).rank(method="min").astype(int)

    # Handle the final sector (sector_5)
    def calculate_final_sector(row):
        try:
            final_time = datetime.strptime(row["final_time"], "%M:%S.%f")
            split_4 = datetime.strptime(row["split_4"], "%M:%S.%f")
            return str(final_time - split_4)[2:]
        except Exception as e:
            return "N/A"

    df[f'sector_5'] = df.apply(calculate_final_sector, axis=1)

    df[f'sector_5_rank'] = df[f'sector_5'].apply(
        lambda x: timedelta(minutes=int(x.split(":")[0]), seconds=float(x.split(":")[1]))
        if is_valid_time_format(x) else timedelta.max
    ).rank(method="min").astype(int)

    # Ensure there are no infinity values in the ranking columns
    for i in range(1, 6):
        sector_col = f'sector_{i}_rank'
        if sector_col in df.columns:
            df[sector_col] = df[sector_col].replace([float('inf'), -float('inf')], 0)

    # Drop columns only if they exist
    columns_to_drop = ['split_times', 'split_time_ranks', 'sector_times']
    df.drop(columns=[col for col in columns_to_drop if col in df.columns], inplace=True)

    file_prefix = filename.split('/')[-1].split('.')[0]
    csv_path = f'data/{file_prefix}.csv'
    df.to_csv(csv_path, index=False)

    print(f"Processed {filename} and saved to {csv_path}")

# Process files

process_results('data/fwil_dhi_me_results_qr.pdf', 24)
process_results('data/fwil_dhi_me_results_semi.pdf', 25)
process_results('data/fwil_dhi_me_results_f.pdf', 24)
process_results('data/biel_dhi_me_results_qr.pdf', 24)
process_results('data/biel_dhi_me_results_semi.pdf', 25)
process_results('data/biel_dhi_me_results_f.pdf', 24)
process_results('data/leog_dhi_me_results_qr.pdf', 24)
process_results('data/leog_dhi_me_results_semi.pdf', 25)
process_results('data/leog_dhi_me_results_f.pdf', 24)
process_results('data/vdso_dhi_me_results_qr.pdf', 24)
process_results('data/vdso_dhi_me_results_semi.pdf', 25)
