import fitz
import pandas as pd
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Union

logging.basicConfig(level=logging.DEBUG)

# Function to calculate sector times
def calculate_sector_times(split_times: List[str]) -> List[str]:
    sector_times = []
    previous_time = "0:00.000"
    for split_time in split_times:
        if split_time == "-":
            sector_times.append("N/A")
        else:
            try:
                time_format = "%M:%S.%f"
                start_time = datetime.strptime(previous_time, time_format)
                end_time = datetime.strptime(split_time, time_format)
                if end_time >= start_time:
                    delta = end_time - start_time
                    sector_times.append(str(delta)[2:])  # Skip "0:" part in "0:XX.XXX" string
                else:
                    logging.warning(f"End time {split_time} is earlier than start time {previous_time}. Appending 'N/A'.")
                    sector_times.append("N/A")
                previous_time = split_time
            except ValueError as e:
                logging.error(f"Error parsing time '{split_time}': {e}")
                sector_times.append("N/A")
    return sector_times

# Function to calculate the time for the final sector
def calculate_final_sector_time(final_time, split_4):
    if final_time not in ["DNF", "DNS", "N/A", "-"] and split_4 not in ["DNF", "DNS", "N/A", "-"]:
        final_time_dt = datetime.strptime(final_time, "%M:%S.%f")
        split_4_dt = datetime.strptime(split_4, "%M:%S.%f")
        delta = final_time_dt - split_4_dt
        return str(delta)[2:]  # Skip "0:" part in "0:XX.XXX" string
    return "N/A"

# Function to convert sector time into a timedelta for ranking
def rank_final_sector(sector_time):
    if sector_time not in ["N/A", "-"]:
        minutes, seconds = map(float, sector_time.split(':'))
        return timedelta(minutes=minutes, seconds=seconds)
    return timedelta.max

# Main function to process time and rank data
def process_time_and_rank_data(df):
    # Handle split times and ranks
    for i in range(4):
        split_col = f'split_{i+1}'
        df[split_col] = df['split_times'].apply(lambda x: x[i] if len(x) > i else 'N/A')
        df[f'{split_col}_rank'] = df['split_time_ranks'].apply(lambda x: x[i] if len(x) > i else 'N/A')

    # Handle sector times and ranks, allowing rankings for completed sectors even if DNF later
    for i in range(4):  # Assuming there are 4 sectors before the final one
        sector_col = f'sector_{i+1}'
        df[sector_col] = df['sector_times'].apply(lambda x: x[i] if i < len(x) else 'N/A')

        # Adjust the mask to only exclude times for this sector specifically
        mask = (df[sector_col] != 'N/A') & (df[sector_col] != '-')
        valid_times = df.loc[mask, sector_col]

        # Convert times to timedeltas and rank them
        timedeltas = valid_times.apply(lambda x: timedelta(minutes=int(x.split(":")[0]), seconds=float(x.split(":")[1])))
        df.loc[mask, f'{sector_col}_rank'] = timedeltas.rank(method='min').astype(int)

    # Special handling for the final sector
    df['sector_5'] = df.apply(
        lambda row: calculate_final_sector_time(row['final_time'], row['split_4']) if row['final_time'] not in ["DNF", "DNS"] else "N/A", axis=1)
    
    # Create a mask for valid final times, excluding 'DNF' from final time
    mask_final = df['sector_5'] != 'N/A'
    valid_final_times = df.loc[mask_final, 'sector_5']
    df.loc[mask_final, 'sector_5_rank'] = valid_final_times.apply(rank_final_sector).rank(method='min').astype(int)

    # Handle 'N/A' values for final sector rank
    df.loc[~mask_final, 'sector_5_rank'] = 'N/A'
    df['sector_5_rank'] = df['sector_5_rank'].apply(lambda x: int(x) if x != 'N/A' else x)

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

        line_start = line_start_num  # Starting from line 24, this might vary depending on the document format

        while line_start < len(lines):
            rider_info = lines[line_start : line_start + 20]

            if len(rider_info) < 19:
                break

            if rider_info[5].isdigit():  # No team case
                split_times = [s.split()[0] for s in rider_info[9:13]]
                split_time_ranks = [s.split()[-1].strip("()") for s in rider_info[9:13]]
                sector_times = calculate_sector_times(split_times)
                rider_data = {
                    "rank": rider_info[0].split()[0].replace(".", ""),
                    "protected": (
                        rider_info[0].split()[1]
                        if len(rider_info[0].split()) > 1
                        else ""
                    ),
                    "rider_number": rider_info[1].split()[0],
                    "name": " ".join(rider_info[1].split()[1:]),
                    "team": "N/A",
                    "uci_id": rider_info[5],
                    "country": rider_info[6],
                    "birth_year": rider_info[7],
                    "speed_trap": rider_info[8].split()[0],
                    "speed_trap_rank": rider_info[8].split()[-1].strip("()"),
                    "split_times": split_times,
                    "split_time_ranks": split_time_ranks,
                    "sector_times": sector_times,
                    "final_time": rider_info[13],
                    "gap": rider_info[17],
                    "points": rider_info[18],
                }
                next_offset = 19  # Proceed 19 elements forward for the next rider
            else:  # With team case
                split_times = [s.split()[0] for s in rider_info[10:14]]
                split_time_ranks = [
                    s.split()[-1].strip("()") for s in rider_info[10:14]
                ]
                sector_times = calculate_sector_times(split_times)
                rider_data = {
                    "rank": rider_info[0].split()[0].replace(".", ""),
                    "protected": (
                        rider_info[0].split()[1]
                        if len(rider_info[0].split()) > 1
                        else ""
                    ),
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
                    "gap": rider_info[18],
                    "points": rider_info[19] if len(rider_info) > 19 else "N/A",
                }
                next_offset = 20  # Proceed 20 elements forward for the next rider
            if rider_data["final_time"] == "DNF" or rider_data["final_time"] == "DNS":
                break
            riders_info.append(rider_data)
            line_start += next_offset

    return riders_info


def process_results(filename: str, line_start_num: int):
    """
    Process the results from a given PDF file starting from a specified line number.
    
    Parameters:
    filename (str): Path to the PDF file.
    line_start_num (int): Line number to start processing from.
    """
    file_prefix = filename.split(".")[0]  # Get prefix for output file
    riders_info = extract_rider_info_all_pages(filename, line_start_num)
    df = pd.DataFrame(riders_info)
    df = process_time_and_rank_data(df)
    df.to_csv(f"{file_prefix}.csv", index=False)
    print(f"The tail for filename {filename} is \n") 
    print(df.tail(10)) # Print the last 10 rows of the processed DataFrame

# Now use this function for both qualifications and semifinals
process_results("data/fwil_dhi_me_results_qr.pdf", 24)  # Qualifications
process_results("data/fwil_dhi_me_results_semi.pdf", 25)  # Semifinals
process_results("data/fwil_dhi_me_results_f.pdf", 24)  # Finals