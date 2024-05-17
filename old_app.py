

import streamlit as st
import pandas as pd
import plotly.graph_objs as go

# Filenames to choose from
filenames = ["data/fwil_dhi_me_results_qr.csv", "data/fwil_dhi_me_results_semi.csv", "data/fwil_dhi_me_results_f.csv"]

# Configure the page
st.set_page_config(page_title="Downhill Mountain Bike World Cup Results", layout="wide")
st.title("Downhill Mountain Bike World Cup Results")
# Mapping of user-friendly names to file paths
file_mapping = {
    "Fort William Qualifications": "data/fwil_dhi_me_results_qr.csv",
    "Fort William Semi-Finals": "data/fwil_dhi_me_results_semi.csv",
    "Fort William Finals": "data/fwil_dhi_me_results_f.csv",
}
# File selection using user-friendly names
file_choice = st.selectbox("Select event results:", list(file_mapping.keys()))
df = pd.read_csv(file_mapping[file_choice])

# Display basic information
simple_df = df[["rank", "name", "team", "country", "final_time", "points"]]
simple_df.set_index("rank", inplace=True)
st.write(simple_df)

# Display split times and sectors
st.write(f"Splits and Sector Ranks")
splits_df = df[
    [
        "rank",
        "name",
        "final_time",
        "split_1",
        "split_2",
        "split_3",
        "split_4",
        "split_1_rank",
        "split_2_rank",
        "split_3_rank",
        "split_4_rank",
        "sector_1",
        "sector_2",
        "sector_3",
        "sector_4",
        "sector_5",
        "sector_1_rank",
        "sector_2_rank",
        "sector_3_rank",
        "sector_4_rank",
        "sector_5_rank",
    ]
].set_index("rank")
st.write(splits_df)
# Using columns to organize dropdowns
col1, col2 = st.columns(2)
with col1:
    n = st.selectbox(
        "Select a number of riders to create an average for comparison", [3, 5, 10, 20, 30]
    )
    selected_rider = st.selectbox(
        "Select a *primary* rider to compare", df["name"].unique(), index=0
    )

with col2:
    comparison_type = st.selectbox(
        "Select comparison type", ["Sector Times", "Split Times"]
    )
    second_rider = st.selectbox(
        "Select a *second* rider to compare", df["name"].unique(), index=1
    )

# ======================Data Processing==========================================================
# Convert split and sector times to timedelta
for column in [
    "split_1",
    "split_2",
    "split_3",
    "split_4",
    "sector_1",
    "sector_2",
    "sector_3",
    "sector_4",
    "sector_5",
]:
    df[column] = pd.to_timedelta("00:" + df[column], errors="coerce")
# Check if there are enough riders to compare to the 30th place
if len(df) < 30:
    index_location = len(df) - 1
else:
    index_location = 29
# Create the plots
if comparison_type == "Split Times":
    st.write("## Split Time Comparison")
    top_times_avg = df[["split_1", "split_2", "split_3", "split_4"]].head(n).mean()
    
    thirtieth_times = df[["split_1", "split_2", "split_3", "split_4"]].iloc[index_location]
    primary_rider_times = df[["split_1", "split_2", "split_3", "split_4"]].loc[
        df["name"].str.contains(selected_rider, case=False, na=False)
    ]
    secondary_rider_times = df[["split_1", "split_2", "split_3", "split_4"]].loc[
        df["name"].str.contains(second_rider, case=False, na=False)
    ]
else:
    st.write("## Sector Time Comparison")
    top_times_avg = (
        df[["sector_1", "sector_2", "sector_3", "sector_4", "sector_5"]].head(n).mean()
    )
    # TODO: Need to add error handling if fewer than 30 riders are present
    thirtieth_times = df[
        ["sector_1", "sector_2", "sector_3", "sector_4", "sector_5"]
    ].iloc[index_location]
    primary_rider_times = df[
        ["sector_1", "sector_2", "sector_3", "sector_4", "sector_5"]
    ].loc[df["name"].str.contains(selected_rider, case=False, na=False)]
    secondary_rider_times = df[
        ["sector_1", "sector_2", "sector_3", "sector_4", "sector_5"]
    ].loc[df["name"].str.contains(second_rider, case=False, na=False)]
# Calculate spread between top_times_avg and thirtieth_times and the tyler_times
spread_top_thirtieth = top_times_avg - thirtieth_times
if not primary_rider_times.empty:
    spread_primary_rider_vs_top_rider_avg = top_times_avg - primary_rider_times.iloc[0]
    spread_secondary_rider_vs_top_rider_avg = (
        top_times_avg - secondary_rider_times.iloc[0]
    )

# ======================Rider vs Rider Comparison===============================================

# Rider vs Rider Comparison with Incremental and Cumulative Spread on Secondary Axis
if not primary_rider_times.empty and not secondary_rider_times.empty:
    st.write("## Rider vs Rider Detailed Comparison")
    st.write(
        """The following plot shows the comparison between two selected 
        riders with incremental and cumulative spread on the secondary 
        axis. The dotted line represents the zero spread line. If the spread is 
        below the dotted line Rider 1 is catching Rider 2 and vice versa."""
    )
    fig_rider_vs_rider = go.Figure()

    # Primary Rider times
    fig_rider_vs_rider.add_trace(
        go.Bar(
            x=primary_rider_times.columns,
            y=primary_rider_times.iloc[0].dt.total_seconds(),
            name=selected_rider,
            marker_color="green",
        )
    )

    # Secondary Rider times
    fig_rider_vs_rider.add_trace(
        go.Bar(
            x=secondary_rider_times.columns,
            y=secondary_rider_times.iloc[0].dt.total_seconds(),
            name=second_rider,
            marker_color="red",
        )
    )

    # Calculate the incremental spread for each split
    spread_rider_vs_rider = primary_rider_times.iloc[0] - secondary_rider_times.iloc[0]

    # Adding incremental spread as a line plot on secondary y-axis
    fig_rider_vs_rider.add_trace(
        go.Scatter(
            x=spread_rider_vs_rider.index,
            y=spread_rider_vs_rider.dt.total_seconds(),
            name="Incremental Spread",
            mode="lines+markers",
            marker=dict(color="orange", size=10),
            yaxis="y2",
        )
    )

    # Calculate cumulative spread
    cumulative_spread = spread_rider_vs_rider.dt.total_seconds().cumsum()

    # Adding cumulative spread as a line plot on secondary y-axis
    fig_rider_vs_rider.add_trace(
        go.Scatter(
            x=cumulative_spread.index,
            y=cumulative_spread,
            name="Cumulative Spread",
            mode="lines+markers",
            marker=dict(color="purple", size=10),
            yaxis="y2",
        )
    )

    # Set up the layout for dual axes
    fig_rider_vs_rider.update_layout(
        title=f"{selected_rider} vs {second_rider} Comparison and Spreads",
        xaxis_title="Time Split",
        yaxis=dict(
            title="Time (seconds)",
            titlefont=dict(color="blue"),
            tickfont=dict(color="blue"),
        ),
        yaxis2=dict(
            title="Spread (seconds)",
            overlaying="y",
            side="right",
            titlefont=dict(color="purple"),
            tickfont=dict(color="purple"),
        ),
        shapes=[  # Add shapes
            dict(
                type="line",
                xref="paper",
                x0=0,
                x1=1,
                yref="y2",
                y0=0,
                y1=0,
                line=dict(color="gray", width=3, dash="dash"),
            )
        ],
    )

    st.plotly_chart(fig_rider_vs_rider, use_container_width=True)

# ================================================================================================
# Average of top riders vs 30th place and selected riders
st.write(f"## {comparison_type}")
st.write(f"#### Compare Top {n} avg vs {index_location+1}th Place vs Selected Riders")
fig = go.Figure()
fig.add_trace(
    go.Bar(
        x=top_times_avg.index,
        y=top_times_avg.dt.total_seconds(),
        name=f"Top {n} Avg",
        marker_color="blue",
    )
)
fig.add_trace(
    go.Bar(
        x=thirtieth_times.index,
        y=thirtieth_times.dt.total_seconds(),
        name=f"{index_location+1}th Place",
        marker_color="orange",
    )
)
if not primary_rider_times.empty:
    fig.add_trace(
        go.Bar(
            x=primary_rider_times.columns,
            y=primary_rider_times.iloc[0].dt.total_seconds(),
            name=selected_rider,
            marker_color="green",
        )
    )
if not secondary_rider_times.empty:
    fig.add_trace(
        go.Bar(
            x=secondary_rider_times.columns,
            y=secondary_rider_times.iloc[0].dt.total_seconds(),
            name=second_rider,
            marker_color="red",
        )
    )
fig.update_layout(
    title=f"Average {comparison_type} Comparison",
    xaxis_title="Time Split",
    yaxis_title="Time (seconds)",
    barmode="group",
)

st.plotly_chart(fig, use_container_width=True)

# Plot the spreads
fig_spread = go.Figure()
fig_spread.add_trace(
    go.Bar(
        x=spread_top_thirtieth.index,
        y=spread_top_thirtieth.dt.total_seconds(),
        name=f"{index_location+1}th Place",
        marker_color="orange",
    )
)
if not primary_rider_times.empty:
    fig_spread.add_trace(
        go.Bar(
            x=spread_primary_rider_vs_top_rider_avg.index,
            y=spread_primary_rider_vs_top_rider_avg.dt.total_seconds(),
            name=selected_rider,
            marker_color="green",
        )
    )
if not secondary_rider_times.empty:
    fig_spread.add_trace(
        go.Bar(
            x=spread_secondary_rider_vs_top_rider_avg.index,
            y=spread_secondary_rider_vs_top_rider_avg.dt.total_seconds(),
            name=second_rider,
            marker_color="red",
        )
    )

fig_spread.update_layout(
    title=f"Spread Comparison (Gap to Top {n} Avg)",
    xaxis_title="Time Split",
    yaxis_title="Time (seconds)",
    barmode="group",
)

st.plotly_chart(fig_spread, use_container_width=True)
