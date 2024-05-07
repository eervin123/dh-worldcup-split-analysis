import streamlit as st
import pandas as pd

filenames = ["data/fwil_dhi_me_results_qr.csv", "data/fwil_dhi_me_results_semi.csv"]



st.set_page_config(page_title="Downhill Mountain Bike World Cup Results", layout="wide")
st.title("Downhill Mountain Bike World Cup Results")
file_choice = st.selectbox("Select a file", filenames)
df = pd.read_csv(file_choice)

simple_df = df[["rank", "name", "team", "country", "final_time", "points"]]
simple_df.set_index("rank", inplace=True)
st.write(simple_df)

st.write("## Split Times")
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