import streamlit as st
from time_trials import show_time_trials
from event_results import show_event_results

# Page navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Event Results", "Time Trials"])

if page == "Event Results":
    show_event_results()
else:
    show_time_trials()
