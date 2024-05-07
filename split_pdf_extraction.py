# %%
import fitz
import pandas as pd
import logging
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)

filename = "data/fwil_dhi_me_results_qr.pdf"

# %% [markdown]
# still need to work on dnf's and dns's

# %%

filename = "data/fwil_dhi_me_results_qr.pdf"


def calculate_sector_times_and_ranks(split_times, split_time_ranks):
    sector_times = []
    sector_time_ranks = []

    previous_time = "0:00.000"
    for i, split_time in enumerate(split_times):
        # Handle missing split times
        if split_time == "-":
            sector_times.append("-")
            sector_time_ranks.append("-")
        else:
            # Calculate the sector time
            time_format = "%M:%S.%f"
            delta = datetime.strptime(split_time, time_format) - datetime.strptime(
                previous_time, time_format
            )
            sector_times.append(str(delta)[2:])  # Skip "0:" part in "0:XX.XXX" string
            previous_time = split_time

            # Assign the rank
            sector_time_ranks.append(split_time_ranks[i])

    return sector_times, sector_time_ranks


def extract_rider_info_all_pages(filename):
    doc = fitz.open(filename)
    riders_info = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        lines = text.split("\n")

        line_start = 24  # Starting from line 24, this might vary depending on the document format

        while line_start < len(lines):
            rider_info = lines[line_start : line_start + 20]

            if len(rider_info) < 19:
                break

            if rider_info[5].isdigit():  # No team case
                split_times = [s.split()[0] for s in rider_info[9:13]]
                split_time_ranks = [s.split()[-1].strip("()") for s in rider_info[9:13]]
                sector_times, sector_time_ranks = calculate_sector_times_and_ranks(
                    split_times, split_time_ranks
                )
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
                    "sector_time_ranks": sector_time_ranks,
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
                sector_times, sector_time_ranks = calculate_sector_times_and_ranks(
                    split_times, split_time_ranks
                )
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
                    "sector_time_ranks": sector_time_ranks,
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


# Example usage
riders_info = extract_rider_info_all_pages(filename)
# riders_info[125:135]  # display a slice of the extracted data

# Convert data to DataFrame
df = pd.DataFrame(riders_info)

# Generate split columns
for i in range(4):
    df[f"split_{i+1}"] = df["split_times"].apply(
        lambda x: x[i] if len(x) > i else "N/A"
    )
    df[f"split_{i+1}_rank"] = df["split_time_ranks"].apply(
        lambda x: x[i] if len(x) > i else "N/A"
    )
    df[f"sector_{i+1}"] = df["sector_times"].apply(
        lambda x: x[i] if len(x) > i else "N/A"
    )
    df[f"sector_{i+1}_rank"] = df["sector_time_ranks"].apply(
        lambda x: x[i] if len(x) > i else "N/A"
    )

# Drop the original columns with lists
df.drop(
    columns=["split_times", "split_time_ranks", "sector_times", "sector_time_ranks"],
    inplace=True,
)

# Display the DataFrame
df.to_csv("data/fwil_dhi_me_results_qr.csv", index=False)
