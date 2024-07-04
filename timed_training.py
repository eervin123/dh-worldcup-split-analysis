import streamlit as st
import pandas as pd
from plot_helper import plot_results
from columns import preferred_columns, timedelta_columns

def show_timed_training():
    # Filenames to choose from
    filenames = ["data/fwil_dhi_me_results_tt.csv", "data/leog_dhi_me_results_tt.csv", "data/biel_dhi_me_results_tt.csv", "data/vdso_dhi_me_results_tt.csv", "data/gets_dhi_me_results_tt.csv"]

    # Mapping of user-friendly names to file paths
    file_mapping = {
        "Fort William Time Training": "data/fwil_dhi_me_results_tt.csv",
        "Leogang Time Training": "data/leog_dhi_me_results_tt.csv",
        "Biel Time Training": "data/biel_dhi_me_results_tt.csv",
        "Val di Sole Time Training": "data/vdso_dhi_me_results_tt.csv",
        "Les Gets Time Training": "data/gets_dhi_me_results_tt.csv", 
        
    }

    st.title("Downhill Mountain Bike World Cup Time Training Results")
    file_choice = st.selectbox("Select event results:", list(file_mapping.keys()), key='timed_training_file_select')
    df = pd.read_csv(file_mapping[file_choice])

    def clean_column_name(col_name):
        return col_name.replace('Orig_', '').replace('_', ' ').replace('Clean_', '').replace('Time', '').title().strip()
    
    def convert_to_seconds(time_str):
        try:
            if pd.isna(time_str):
                return None
            if ':' in time_str:
                minutes, seconds = map(float, time_str.split(':'))
                return minutes * 60 + seconds
            return float(time_str)
        except ValueError:
            return None

    def seconds_to_human_readable(seconds):
        if pd.isna(seconds):
            return "N/A"
        minutes = int(seconds // 60)
        seconds = seconds % 60
        return f"{minutes}:{seconds:05.2f}"

    simple_df = df[["Number", "Name", "Run", "Speed", "Speed_Rank", "Orig_Split_5_Time"]]
    simple_df['Orig_Split_5_Time'] = simple_df['Orig_Split_5_Time'].apply(convert_to_seconds)
    simple_df = simple_df.dropna(subset=["Orig_Split_5_Time"])
    simple_df = simple_df.sort_values(by="Orig_Split_5_Time", ascending=True).reset_index(drop=True)
    simple_df['Orig_Split_5_Time'] = simple_df['Orig_Split_5_Time'].apply(seconds_to_human_readable)
    simple_df['Rank'] = simple_df.index + 1
    simple_df = simple_df[["Rank", "Number", "Name", "Run", "Speed", "Speed_Rank", "Orig_Split_5_Time"]]
    
    st.dataframe(simple_df.rename(columns={"Orig_Split_5_Time": "Final Time"}), hide_index=True)
    st.write("Splits and Sector Ranks")
    splits_df = df[preferred_columns].rename(columns=clean_column_name)
    st.dataframe(splits_df, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        n = st.selectbox("Select a number of riders to create an average for comparison", [3, 5, 10, 20, 30], key='timed_training_num_riders_select')
        selected_rider = st.selectbox("Select a *primary* rider to compare", df["Name"].unique(), index=0, key='timed_training_primary_rider_select')

    with col2:
        comparison_type = st.selectbox("Select comparison type", ["Sector Times", "Split Times"], key='timed_training_comparison_type_select')
        second_rider = st.selectbox("Select a *second* rider to compare", df["Name"].unique(), index=1, key='timed_training_second_rider_select')

    df['Orig_Split_5_Time'] = df['Orig_Split_5_Time'].apply(convert_to_seconds)
    df['Best_Run'] = df.groupby('Name')['Orig_Split_5_Time'].transform('min')
    df_best_runs = df[df['Orig_Split_5_Time'] == df['Best_Run']].sort_values(by='Best_Run').reset_index(drop=True)
    df_best_runs['Rank'] = df_best_runs.index + 1
    df_best_runs = df_best_runs[["Rank"] + df_best_runs.columns[:-1].tolist()]

    new_columns = ["Rank"] + preferred_columns
    missing_cols = set(new_columns) - set(df_best_runs.columns)
    for col in missing_cols:
        df_best_runs[col] = pd.NA
    st.write("Best Runs DataFrame")
    st.dataframe(df_best_runs[new_columns].rename(columns=clean_column_name), hide_index=True)

    for column in timedelta_columns:
        df_best_runs[column] = pd.to_timedelta(df_best_runs[column], errors="coerce")

    if len(df_best_runs) < 30:
        index_location = len(df_best_runs) - 1
    else:
        index_location = 29

    plot_results(df_best_runs, selected_rider, second_rider, n, comparison_type, index_location)

    best_sectors = df.groupby('Name').agg({
        'Sector_1_Time': 'min',
        'Sector_2_Time': 'min',
        'Sector_3_Time': 'min',
        'Sector_4_Time': 'min',
        'Sector_5_Time': 'min',
        'Speed': 'max'
    }).reset_index()

    best_runs_data = []
    for _, row in best_sectors.iterrows():
        best_run = {
            'Number': df[df['Name'] == row['Name']]['Number'].iloc[0],
            'Name': row['Name'],
            'Run': 4,
            'Sector_1_Time': row['Sector_1_Time'],
            'Sector_2_Time': row['Sector_2_Time'],
            'Sector_3_Time': row['Sector_3_Time'],
            'Sector_4_Time': row['Sector_4_Time'],
            'Sector_5_Time': row['Sector_5_Time'],
            'Speed': row['Speed']
        }
        best_run['Orig_Split_1_Time'] = best_run['Sector_1_Time']
        best_run['Orig_Split_2_Time'] = best_run['Sector_1_Time'] + best_run['Sector_2_Time']
        best_run['Orig_Split_3_Time'] = best_run['Orig_Split_2_Time'] + best_run['Sector_3_Time']
        best_run['Orig_Split_4_Time'] = best_run['Orig_Split_3_Time'] + best_run['Sector_4_Time']
        best_run['Orig_Split_5_Time'] = best_run['Orig_Split_4_Time'] + best_run['Sector_5_Time']
        best_runs_data.append(best_run)

    df_hypothetical_best = pd.DataFrame(best_runs_data)

    for i in range(1, 5):
        df_hypothetical_best[f'Cumulative_from_Sector_{i}_Time'] = df_hypothetical_best[[f'Sector_{j}_Time' for j in range(i, 6)]].sum(axis=1)

    for i in range(1, 6):
        df_hypothetical_best[f'Split_{i}_Rank'] = df_hypothetical_best[f'Orig_Split_{i}_Time'].rank(method='min')
        df_hypothetical_best[f'Sector_{i}_Rank'] = df_hypothetical_best[f'Sector_{i}_Time'].rank(method='min')

    for i in range(1, 5):
        df_hypothetical_best[f'Cumulative_from_Sector_{i}_Rank'] = df_hypothetical_best[f'Cumulative_from_Sector_{i}_Time'].rank(method='min')

    df_hypothetical_best['Speed_Rank'] = df_hypothetical_best['Speed'].rank(method='min', ascending=False)

    missing_cols = set(preferred_columns) - set(df_hypothetical_best.columns)
    for col in missing_cols:
        df_hypothetical_best[col] = pd.NA

    df_hypothetical_best['Perfect_Run_Rank'] = df_hypothetical_best['Split_5_Rank']
    df_hypothetical_best = df_hypothetical_best.sort_values(by='Orig_Split_5_Time')

    columns_order = ['Perfect_Run_Rank', 'Number', 'Name', 'Speed', 'Speed_Rank'] + \
                    [col for col in preferred_columns if col not in ['Number', 'Name', 'Speed', 'Speed_Rank', 'Perfect_Run_Rank']]
    df_hypothetical_best = df_hypothetical_best[columns_order]

    # Convert all relevant time columns to human-readable format
    time_columns = [col for col in df_hypothetical_best.columns if 'Time' in col or 'Split' in col or 'Sector' in col]
    for col in time_columns:
        df_hypothetical_best[col] = df_hypothetical_best[col].apply(seconds_to_human_readable)

    st.title("Hypothetical Perfect Runs Analysis")
    st.write("The following analysis is based on the best sector times for each rider out of their three runs to compile a single best hypothetical run.")
    st.write("Hypothetical Perfect Runs DataFrame")
    st.dataframe(df_hypothetical_best.rename(columns=clean_column_name), hide_index=True)

    for column in timedelta_columns:
        df_hypothetical_best[column] = pd.to_timedelta(df_hypothetical_best[column], errors="coerce")

    plot_results(df_hypothetical_best, selected_rider, second_rider, n, comparison_type, index_location)

show_timed_training()
