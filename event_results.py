# Filename: event_results.py
# Description: This file contains the code to display the event results for the Downhill Mountain Bike World Cup.

import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from columns import event_columns, split_sector_display_columns, split_columns, sector_columns, clean_column_name

def load_data(file_path):
    try:
        return pd.read_csv(file_path)
    except FileNotFoundError:
        st.error("File not found. Please check the file path.")
    except pd.errors.EmptyDataError:
        st.error("The selected file is empty. Please select another file.")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")
        return None

def show_event_results():
    file_mapping = {
        "Fort William Qualifications": "data/fwil_dhi_me_results_qr.csv",
        "Fort William Semi-Finals": "data/fwil_dhi_me_results_semi.csv",
        "Fort William Finals": "data/fwil_dhi_me_results_f.csv",
        "Biel Qualifications": "data/biel_dhi_me_results_qr.csv",
        "Biel Semi-Finals": "data/biel_dhi_me_results_semi.csv",
        "Biel Finals": "data/biel_dhi_me_results_f.csv",
        "Leogang Qualifications": "data/leog_dhi_me_results_qr.csv",
        "Leogang Semi-Finals": "data/leog_dhi_me_results_semi.csv",
        "Leogang Finals": "data/leog_dhi_me_results_f.csv",
        "Val di Sole Qualifications": "data/vdso_dhi_me_results_qr.csv",
        "Val di Sole Semi-Finals": "data/vdso_dhi_me_results_semi.csv",
        "Val di Sole Finals": "data/vdso_dhi_me_results_f.csv",
        "Les Gets Qualifications": "data/gets_dhi_me_results_qr.csv",
        "Les Gets Semi-Finals": "data/gets_dhi_me_results_semi.csv",
    }

    st.title("Downhill Mountain Bike World Cup Event Results")

    file_choice = st.selectbox("Select event results:", list(file_mapping.keys()), key='event_results_select')
    df = load_data(file_mapping[file_choice])
    if df is None:
        return

    simple_df = df[event_columns]
    simple_df.set_index("rank", inplace=True)
    st.dataframe(simple_df.rename(columns=clean_column_name), hide_index=True)

    st.write("Splits and Sector Ranks")
    splits_df = df[split_sector_display_columns].set_index("rank")
    st.dataframe(splits_df.rename(columns=clean_column_name), hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        n = st.selectbox(
            "Select a number of riders to create an average for comparison",
            [3, 5, 10, 20, 30],
            key='number_of_riders_select'
        )
        selected_rider = st.selectbox(
            "Select a *primary* rider to compare", df["name"].unique(), index=0, key='primary_rider_select'
        )

    with col2:
        comparison_type = st.selectbox(
            "Select comparison type", ["Sector Times", "Split Times"], key='comparison_type_select'
        )
        second_rider = st.selectbox(
            "Select a *second* rider to compare", df["name"].unique(), index=1, key='second_rider_select'
        )

    columns_to_convert = split_columns + sector_columns
    for column in columns_to_convert:
        df[column] = pd.to_timedelta("00:" + df[column], errors="coerce")

    index_location = min(len(df), 30) - 1

    if comparison_type == "Split Times":
        st.write("## Split Time Comparison")
        top_times_avg = df[split_columns].head(n).mean()
        thirtieth_times = df[split_columns].iloc[index_location]
        primary_rider_times = df[split_columns].loc[df["name"].str.contains(selected_rider, case=False, na=False)]
        secondary_rider_times = df[split_columns].loc[df["name"].str.contains(second_rider, case=False, na=False)]
    else:
        st.write("## Sector Time Comparison")
        top_times_avg = df[sector_columns].head(n).mean()
        thirtieth_times = df[sector_columns].iloc[index_location]
        primary_rider_times = df[sector_columns].loc[df["name"].str.contains(selected_rider, case=False, na=False)]
        secondary_rider_times = df[sector_columns].loc[df["name"].str.contains(second_rider, case=False, na=False)]

    spread_top_thirtieth = top_times_avg - thirtieth_times
    spread_primary_rider_vs_top_rider_avg = top_times_avg - primary_rider_times.iloc[0] if not primary_rider_times.empty else None
    spread_secondary_rider_vs_top_rider_avg = top_times_avg - secondary_rider_times.iloc[0] if not secondary_rider_times.empty else None

    if not primary_rider_times.empty and not secondary_rider_times.empty:
        st.write("## Rider vs Rider Detailed Comparison")
        fig_rider_vs_rider = go.Figure()

        fig_rider_vs_rider.add_trace(go.Bar(x=primary_rider_times.columns, y=primary_rider_times.iloc[0].dt.total_seconds(), name=selected_rider, marker_color="green"))
        fig_rider_vs_rider.add_trace(go.Bar(x=secondary_rider_times.columns, y=secondary_rider_times.iloc[0].dt.total_seconds(), name=second_rider, marker_color="red"))

        spread_rider_vs_rider = primary_rider_times.iloc[0] - secondary_rider_times.iloc[0]
        fig_rider_vs_rider.add_trace(go.Scatter(x=spread_rider_vs_rider.index, y=spread_rider_vs_rider.dt.total_seconds(), name="Incremental Spread", mode="lines+markers", marker=dict(color="orange", size=10), yaxis="y2"))
        cumulative_spread = spread_rider_vs_rider.dt.total_seconds().cumsum()
        fig_rider_vs_rider.add_trace(go.Scatter(x=cumulative_spread.index, y=cumulative_spread, name="Cumulative Spread", mode="lines+markers", marker=dict(color="purple", size=10), yaxis="y2"))

        fig_rider_vs_rider.update_layout(title=f"{selected_rider} vs {second_rider} Comparison and Spreads", xaxis_title="Time Split", yaxis=dict(title="Time (seconds)", titlefont=dict(color="blue"), tickfont=dict(color="blue")), yaxis2=dict(title="Spread (seconds)", overlaying="y", side="right", titlefont=dict(color="purple"), tickfont=dict(color="purple")), shapes=[dict(type="line", xref="paper", x0=0, x1=1, yref="y2", y0=0, y1=0, line=dict(color="gray", width=3, dash="dash"))])

        st.plotly_chart(fig_rider_vs_rider, use_container_width=True)

    st.write(f"## {comparison_type}")
    st.write(f"#### Compare Top {n} avg vs {index_location+1}th Place vs Selected Riders")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=top_times_avg.index, y=top_times_avg.dt.total_seconds(), name=f"Top {n} Avg", marker_color="blue"))
    fig.add_trace(go.Bar(x=thirtieth_times.index, y=thirtieth_times.dt.total_seconds(), name=f"{index_location+1}th Place", marker_color="orange"))
    if not primary_rider_times.empty:
        fig.add_trace(go.Bar(x=primary_rider_times.columns, y=primary_rider_times.iloc[0].dt.total_seconds(), name=selected_rider, marker_color="green"))
    if not secondary_rider_times.empty:
        fig.add_trace(go.Bar(x=secondary_rider_times.columns, y=secondary_rider_times.iloc[0].dt.total_seconds(), name=second_rider, marker_color="red"))
    fig.update_layout(title=f"Average {comparison_type} Comparison", xaxis_title="Time Split", yaxis_title="Time (seconds)", barmode="group")

    st.plotly_chart(fig, use_container_width=True)

    fig_spread = go.Figure()
    fig_spread.add_trace(go.Bar(x=spread_top_thirtieth.index, y=spread_top_thirtieth.dt.total_seconds(), name=f"{index_location+1}th Place", marker_color="orange"))
    if spread_primary_rider_vs_top_rider_avg is not None:
        fig_spread.add_trace(go.Bar(x=spread_primary_rider_vs_top_rider_avg.index, y=spread_primary_rider_vs_top_rider_avg.dt.total_seconds(), name=selected_rider, marker_color="green"))
    if spread_secondary_rider_vs_top_rider_avg is not None:
        fig_spread.add_trace(go.Bar(x=spread_secondary_rider_vs_top_rider_avg.index, y=spread_secondary_rider_vs_top_rider_avg.dt.total_seconds(), name=second_rider, marker_color="red"))

    fig_spread.update_layout(title=f"Spread Comparison (Gap to Top {n} Avg)", xaxis_title="Time Split", yaxis_title="Time (seconds)", barmode="group")

    st.plotly_chart(fig_spread, use_container_width=True)
