split_sector_columns = [
    "Number", "Name", "Run", "Speed", "Speed_Rank", "Orig_Split_1_Time", "Orig_Split_2_Time",
    "Orig_Split_3_Time", "Orig_Split_4_Time", "Orig_Split_5_Time", "Split_1_Rank", "Split_2_Rank",
    "Split_3_Rank", "Split_4_Rank", "Split_5_Rank", "Sector_1_Time", "Sector_2_Time",
    "Sector_3_Time", "Sector_4_Time", "Sector_5_Time", "Sector_1_Rank", "Sector_2_Rank",
    "Sector_3_Rank", "Sector_4_Rank", "Sector_5_Rank", "Cumulative_from_Split_1_Time",
    "Cumulative_from_Split_2_Time", "Cumulative_from_Split_3_Time", "Cumulative_from_Split_4_Time",
    "Cumulative_from_Split_1_Rank", "Cumulative_from_Split_2_Rank", "Cumulative_from_Split_3_Rank",
    "Cumulative_from_Split_4_Rank"
]

timedelta_columns = [
    "Orig_Split_1_Time", "Orig_Split_2_Time", "Orig_Split_3_Time", "Orig_Split_4_Time",
    "Orig_Split_5_Time", "Sector_1_Time", "Sector_2_Time", "Sector_3_Time", "Sector_4_Time",
    "Sector_5_Time", "Cumulative_from_Split_1_Time", "Cumulative_from_Split_2_Time",
    "Cumulative_from_Split_3_Time", "Cumulative_from_Split_4_Time"
]

preferred_columns = split_sector_columns

event_columns = [
    "rank", "name", "team", "country", "final_time", "points"
]

split_sector_display_columns = [
    "rank", "name", "final_time", "split_1", "split_2", "split_3", "split_4",
    "split_1_rank", "split_2_rank", "split_3_rank", "split_4_rank", "sector_1",
    "sector_2", "sector_3", "sector_4", "sector_5", "sector_1_rank", "sector_2_rank",
    "sector_3_rank", "sector_4_rank", "sector_5_rank"
]

split_columns = ["split_1", "split_2", "split_3", "split_4"]
sector_columns = ["sector_1", "sector_2", "sector_3", "sector_4", "sector_5"]

def clean_column_name(col_name):
    return col_name.replace("_", " ").replace(" Time", "")
