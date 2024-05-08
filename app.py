import streamlit as st
import pandas as pd
import plotly.graph_objs as go

# Filenames to choose from
filenames = ["data/fwil_dhi_me_results_qr.csv", "data/fwil_dhi_me_results_semi.csv"]

# Configure the page
st.set_page_config(page_title="Downhill Mountain Bike World Cup Results", layout="wide")
st.title("Downhill Mountain Bike World Cup Results")

# File selection
file_choice = st.selectbox("Select a file", filenames)
df = pd.read_csv(file_choice)



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

# Select n and type of times to compare
n = st.selectbox("Select a number of riders create an average for comparison", [3, 5, 10, 20, 30])
comparison_type = st.selectbox("Select comparison type", ["Sector Times", "Split Times"])
# Select riders to compare, default to first and second riders
selected_rider = st.selectbox("Select a *primary* rider to compare", df["name"].unique(), index=0 )
second_rider = st.selectbox("Select a *second* rider to compare", df["name"].unique(), index=1)
# Convert split and sector times to timedelta
for column in ["split_1", "split_2", "split_3", "split_4",
               "sector_1", "sector_2", "sector_3", "sector_4", "sector_5"]:
    df[column] = pd.to_timedelta("00:" + df[column], errors='coerce')

# Create the plots
if comparison_type == "Split Times":
    st.write("## Split Time Comparison")
    top_times_avg = df[["split_1", "split_2", "split_3", "split_4"]].head(n).mean()
    thirtieth_times = df[["split_1", "split_2", "split_3", "split_4"]].iloc[29]
    primary_rider_times = df[["split_1", "split_2", "split_3", "split_4"]].loc[df["name"].str.contains(selected_rider, case=False, na=False)]
    secondary_rider_times = df[["split_1", "split_2", "split_3", "split_4"]].loc[df["name"].str.contains(second_rider, case=False, na=False)]
else:
    st.write("## Sector Time Comparison")
    top_times_avg = df[["sector_1", "sector_2", "sector_3", "sector_4", "sector_5"]].head(n).mean()
    thirtieth_times = df[["sector_1", "sector_2", "sector_3", "sector_4", "sector_5"]].iloc[29]
    primary_rider_times = df[["sector_1", "sector_2", "sector_3", "sector_4", "sector_5"]].loc[df["name"].str.contains(selected_rider, case=False, na=False)]
    secondary_rider_times = df[["sector_1", "sector_2", "sector_3", "sector_4", "sector_5"]].loc[df["name"].str.contains(second_rider, case=False, na=False)]
# Calculate spread between top_times_avg and thirtieth_times and the tyler_times
spread_top_thirtieth = top_times_avg - thirtieth_times
if not primary_rider_times.empty:
    spread_primary_rider_vs_top_rider_avg = top_times_avg - primary_rider_times.iloc[0]
    spread_secondary_rider_vs_top_rider_avg = top_times_avg - secondary_rider_times.iloc[0]


# Plot the selected times
fig = go.Figure()
fig.add_trace(go.Bar(
    x=top_times_avg.index,
    y=top_times_avg.dt.total_seconds(),
    name=f'Top {n} Avg',
    marker_color='blue'
))
fig.add_trace(go.Bar(
    x=thirtieth_times.index,
    y=thirtieth_times.dt.total_seconds(),
    name='30th Place',
    marker_color='orange'
))
if not primary_rider_times.empty:
    fig.add_trace(go.Bar(
        x=primary_rider_times.columns,
        y=primary_rider_times.iloc[0].dt.total_seconds(),
        name=selected_rider,
        marker_color='green'
    ))
if not secondary_rider_times.empty:
    fig.add_trace(go.Bar(
        x=secondary_rider_times.columns,
        y=secondary_rider_times.iloc[0].dt.total_seconds(),
        name=second_rider,
        marker_color='red'
    ))
fig.update_layout(
    title=f"Average {comparison_type} Comparison",
    xaxis_title="Time Split",
    yaxis_title="Time (seconds)",
    barmode='group'
)

st.plotly_chart(fig, use_container_width=True)

# Plot the spreads
fig_spread = go.Figure()
fig_spread.add_trace(go.Bar(
    x=spread_top_thirtieth.index,
    y=spread_top_thirtieth.dt.total_seconds(),
    name=f'30th Place',
    marker_color='orange'
))
if not primary_rider_times.empty:
    fig_spread.add_trace(go.Bar(
        x=spread_primary_rider_vs_top_rider_avg.index,
        y=spread_primary_rider_vs_top_rider_avg.dt.total_seconds(),
        name=selected_rider,
        marker_color='green'
    ))
if not secondary_rider_times.empty:
    fig_spread.add_trace(go.Bar(
        x=spread_secondary_rider_vs_top_rider_avg.index,
        y=spread_secondary_rider_vs_top_rider_avg.dt.total_seconds(),
        name=second_rider,
        marker_color='red'
    ))
    
fig_spread.update_layout(
    title=f"Spread Comparison (Gap to Top {n} Avg)",
    xaxis_title="Time Split",
    yaxis_title="Time (seconds)",
    barmode='group'
)

st.plotly_chart(fig_spread, use_container_width=True)

# Rider vs Rider Comparison
if not primary_rider_times.empty and not secondary_rider_times.empty:
    st.write("## Rider vs Rider Comparison")
    fig_rider_vs_rider = go.Figure()
    fig_rider_vs_rider.add_trace(go.Bar(
        x=primary_rider_times.columns,
        y=primary_rider_times.iloc[0].dt.total_seconds(),
        name=selected_rider,
        marker_color='green'
    ))
    fig_rider_vs_rider.add_trace(go.Bar(
        x=secondary_rider_times.columns,
        y=secondary_rider_times.iloc[0].dt.total_seconds(),
        name=second_rider,
        marker_color='red'
    ))
    
    fig_rider_vs_rider.update_layout(
        title=f"{selected_rider} vs {second_rider} Comparison",
        xaxis_title="Rider",
        yaxis_title="Time (seconds)"
    )
    st.plotly_chart(fig_rider_vs_rider, use_container_width=True)
    
    # Rider vs Rider Comparison Spread
    spread_rider_vs_rider = primary_rider_times.iloc[0] - secondary_rider_times.iloc[0]
    fig_rider_vs_rider_spread = go.Figure()
    fig_rider_vs_rider_spread.add_trace(go.Bar(
        x=spread_rider_vs_rider.index,
        y=spread_rider_vs_rider.dt.total_seconds(),
        name=f'{selected_rider} - {second_rider}',
        marker_color='purple'
    ))
    fig_rider_vs_rider_spread.update_layout(
        title=f"{selected_rider} vs {second_rider} Spread",
        xaxis_title="Time Split",
        yaxis_title="Time (seconds)"
    )
    st.plotly_chart(fig_rider_vs_rider_spread, use_container_width=True)
    
    # Plot the cumulative time gap between the primary and secondary riders
    fig_cumulative_gap = go.Figure()
    cumulative_gap = primary_rider_times.iloc[0] - secondary_rider_times.iloc[0]
    fig_cumulative_gap.add_trace(go.Scatter(
        x=cumulative_gap.index,
        y=cumulative_gap.dt.total_seconds().cumsum(),
        mode='lines+markers',
        name=f'Cumulative Gap',
        marker_color='purple'
    ))
    fig_cumulative_gap.update_layout(
        title=f"Cumulative Gap between {selected_rider} and {second_rider}",
        xaxis_title="Time Split",
        yaxis_title="Cumulative Time Gap (seconds)"
    )
    st.plotly_chart(fig_cumulative_gap, use_container_width=True)