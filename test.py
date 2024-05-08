import fitz
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Union

logging.basicConfig(level=logging.DEBUG)

def safe_parse_time(time_str):
    try:
        return datetime.strptime(time_str, "%M:%S.%f")
    except ValueError:
        return pd.NA

def calculate_delta_time(start, end):
    if pd.notna(start) and pd.notna(end) and end >= start:
        return str(end - start)[2:]
    return "N/A"

def calculate_sector_times(split_times: List[str]) -> List[str]:
    sector_times = []
    previous_time = safe_parse_time("0:00.000")
    for split_time in split_times:
        if split_time == "-":
            sector_times.append("N/A")
        else:
            current_time = safe_parse_time(split_time)
            delta_time = calculate_delta_time(previous_time, current_time)
            sector_times.append(delta_time)
            if pd.notna(current_time):
                previous_time = current_time
    return sector_times

def process_time_and_rank_data(df):
    for i in range(4):
        split_col = f'split_{i+1}'
        df[split_col] = df['split_times'].apply(lambda x: x[i] if len(x) > i else pd.NA)
        df[f'{split_col}_rank'] = df['split_time_ranks'].apply(lambda x: x[i] if len(x) > i else pd.NA)
        
        sector_col = f'sector_{i+1}'
        df[sector_col] = df['sector_times'].apply(lambda x: x[i] if i < len(x) else pd.NA)

    # Process the final sector if it exists
    if 'final_time' in df.columns and 'split_4' in df.columns:
        df['sector_5'] = df.apply(lambda row: calculate_delta_time(safe_parse_time(row['split_4']), safe_parse_time(row['final_time'])), axis=1)
    
    # Convert all sector times to timedeltas and rank
    for i in range(1, 6):  # Assuming there could be up to 5 sectors
        sector_col = f'sector_{i}'
        if sector_col in df.columns:
            df[f'{sector_col}_rank'] = df[sector_col].apply(lambda x: timedelta(minutes=int(x.split(":")[0]), seconds=float(x.split(":")[1])) if x not in ["N/A", pd.NA] else pd.NA).rank(method='min').astype('Int64').fillna(pd.NA)

    # Drop the original columns with lists
    df.drop(columns=['split_times', 'split_time_ranks', 'sector_times'], inplace=True)
    return df

def extract_rider_info_all_pages(filename, line_start_num):
    doc = fitz.open(filename)
    riders_info = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        lines = text.split("\n")
        line_start = line_start_num
        while line_start < len(lines):
            rider_info = lines[line_start:line_start+20]
            if len(rider_info) < 19:
                break
            split_times = [s.split()[0] for s in rider_info[9:13]]
            split_time_ranks = [s.split()[-1].strip("()") for s in rider_info[9:13]]
            sector_times = calculate_sector_times(split_times)
            rider_data = {
                "rank": rider_info[0].split()[0].replace(".", ""),
                "protected": rider_info[0].split()[1] if len(rider_info[0].split()) > 1 else "",
                "rider_number": rider_info[1].split()[0],
                "name": " ".join(rider_info[1].split()[1:]),
                "team": rider_info[5],
                "uci_id": rider_info[6],
                "country": rider_info[7],
                "birth_year": rider_info[8],
                "speed_trap": rider_info[9].split()[0],
                "speed_trap_rank": rider_info[9].split()[-1].strip("()"),
                "split_times": split_times,
                "split_time_ranks": split_time_ranks,
                "sector_times": sector_times,
                "final_time": rider_info[14],
                "gap": rider_info[17],
                "points": rider_info[18] if len(rider_info) > 19 else "N/A",
            }
            riders_info.append(rider_data)
            line_start += 20  # Adjust based on actual layout

    return riders_info

def process_results(filename: str, line_start_num: int):
    file_prefix = filename.split(".")[0]
    riders_info = extract_rider_info_all_pages(filename, line_start_num)
    df = pd.DataFrame(riders_info)
    df = process_time_and_rank_data(df)
    df.to_csv(f"{file_prefix}.csv", index=False)
    print(df.tail(10))

process_results("data/fwil_dhi_me_results_qr.pdf", 24)  # Qualifications
process_results("data/fwil_dhi_me_results_semi.pdf", 25)  # Semifinals
