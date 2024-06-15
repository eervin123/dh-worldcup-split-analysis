import streamlit as st
from time_trials import show_time_trials
from event_results import show_event_results

# Page navigation
st.sidebar.title("Navigation")
if 'page' not in st.session_state:
    st.session_state.page = "Event Results"

page = st.sidebar.radio("Go to", ["Event Results", "Time Trials"], index=0 if st.session_state.page == "Event Results" else 1)

# Update session state
st.session_state.page = page

if st.session_state.page == "Event Results":
    show_event_results()
else:
    show_time_trials()
