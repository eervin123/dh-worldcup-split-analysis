import streamlit as st
import pandas as pd
from plot_helper import plot_results
from columns import preferred_columns, timedelta_columns

def show_time_trials():
    # Filename for time trials
    filename = "data/biel_dhi_me_results_tt.csv"

    st.title("Downhill Mountain Bike World Cup Time Trials")

    df = pd.read_csv(filename)

    # Function to clean column names for display
    def clean_column_name(col_name):
        return col_name.replace('Orig_', '').replace('_', ' ').replace('Time', '').title().strip()

    # Display basic information sorted by fastest speed
    simple_df = df[["Number", "Name", "Run", "Speed", "Speed_Rank"]].sort_values(by="Speed", ascending=False)
    st.write(simple_df.rename(columns=clean_column_name))

    # Display split times and sectors
    st.write("Splits and Sector Ranks")
    splits_df = df[preferred_columns].rename(columns=clean_column_name)
    st.write(splits_df)

    # Using columns to organize dropdowns
    col1, col2 = st.columns(2)
    with col1:
        n = st.selectbox(
            "Select a number of riders to create an average for comparison", [3, 5, 10, 20, 30]
        )
        selected_rider = st.selectbox(
            "Select a *primary* rider to compare", df["Name"].unique(), index=0
        )

    with col2:
        comparison_type = st.selectbox(
            "Select comparison type", ["Sector Times", "Split Times"]
        )
        second_rider = st.selectbox(
            "Select a *second* rider to compare", df["Name"].unique(), index=1
        )

    # ======================Data Processing==========================================================
    # Function to convert time strings to seconds
    def convert_to_seconds(time_str):
        if pd.isna(time_str):
            return None
        if ':' in time_str:
            minutes, seconds = map(float, time_str.split(':'))
            return minutes * 60 + seconds
        return float(time_str)

    # Convert Orig_Split_5_Time to seconds
    df['Orig_Split_5_Time'] = df['Orig_Split_5_Time'].apply(convert_to_seconds)

    # Filter for the best runs
    df['Best_Run'] = df.groupby('Name')['Orig_Split_5_Time'].transform('min')
    df_best_runs = df[df['Orig_Split_5_Time'] == df['Best_Run']]

    # Display the filtered DataFrame for debugging
    st.write("Best Runs DataFrame")
    st.write(df_best_runs[preferred_columns].rename(columns=clean_column_name))

    # Convert split and sector times to timedelta
    for column in timedelta_columns:
        df_best_runs[column] = pd.to_timedelta(df_best_runs[column], errors="coerce")

    # Check if there are enough riders to compare to the 30th place
    if len(df_best_runs) < 30:
        index_location = len(df_best_runs) - 1
    else:
        index_location = 29

    # Plot results for the best runs
    plot_results(df_best_runs, selected_rider, second_rider, n, comparison_type, index_location)

    # ====================== Hypothetical Best Runs Calculation ======================================
    # Calculate the best sector times for each rider
    best_sectors = df.groupby('Name').agg({
        'Sector_1_Time': 'min',
        'Sector_2_Time': 'min',
        'Sector_3_Time': 'min',
        'Sector_4_Time': 'min',
        'Sector_5_Time': 'min',
        'Speed': 'max'  # Get the maximum speed for the hypothetical run
    }).reset_index()

    # Create a new dataframe for the hypothetical best runs
    best_runs_data = []
    for _, row in best_sectors.iterrows():
        best_run = {
            'Number': df[df['Name'] == row['Name']]['Number'].iloc[0],
            'Name': row['Name'],
            'Run': 4,  # Hypothetical run number
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

    # Calculate cumulative times from each sector to the finish
    for i in range(1, 5):
        df_hypothetical_best[f'Cumulative_from_Sector_{i}_Time'] = df_hypothetical_best[[f'Sector_{j}_Time' for j in range(i, 6)]].sum(axis=1)

    # Rank the hypothetical best runs
    for i in range(1, 6):
        df_hypothetical_best[f'Split_{i}_Rank'] = df_hypothetical_best[f'Orig_Split_{i}_Time'].rank(method='min')
        df_hypothetical_best[f'Sector_{i}_Rank'] = df_hypothetical_best[f'Sector_{i}_Time'].rank(method='min')

    for i in range(1, 5):
        df_hypothetical_best[f'Cumulative_from_Sector_{i}_Rank'] = df_hypothetical_best[f'Cumulative_from_Sector_{i}_Time'].rank(method='min')

    # Calculate Speed_Rank for hypothetical runs
    df_hypothetical_best['Speed_Rank'] = df_hypothetical_best['Speed'].rank(method='min', ascending=False)

    # Add missing columns with NaNs to match preferred_columns
    missing_cols = set(preferred_columns) - set(df_hypothetical_best.columns)
    for col in missing_cols:
        df_hypothetical_best[col] = pd.NA

    # Calculate and add "Perfect Run Rank"
    df_hypothetical_best['Perfect_Run_Rank'] = df_hypothetical_best['Split_5_Rank']

    # Sort by Orig_Split_5_Time
    df_hypothetical_best = df_hypothetical_best.sort_values(by='Orig_Split_5_Time')

    # Reorder columns to place "Perfect Run Rank" next to "Name"
    columns_order = ['Number', 'Name', 'Perfect_Run_Rank', 'Speed', 'Speed_Rank'] + \
                    [col for col in preferred_columns if col not in ['Number', 'Name', 'Speed', 'Speed_Rank', 'Perfect_Run_Rank']]
    df_hypothetical_best = df_hypothetical_best[columns_order]

    # Display a clear title to indicate the start of hypothetical data
    st.title("Hypothetical Perfect Runs Analysis")
    st.write("The following analysis is based on the best sector times for each rider out of their three runs to compile a single best hypothetical run.")
    # Display the hypothetical best runs for debugging
    st.write("Hypothetical Perfect Runs DataFrame")
    st.write(df_hypothetical_best.rename(columns=clean_column_name))

    # Convert split and sector times to timedelta for plotting
    for column in timedelta_columns:
        df_hypothetical_best[column] = pd.to_timedelta(df_hypothetical_best[column], errors="coerce")

    # Plot results for the hypothetical best runs
    plot_results(df_hypothetical_best, selected_rider, second_rider, n, comparison_type, index_location)

# This function call would be part of the main script or within a Streamlit app setup
show_time_trials()
