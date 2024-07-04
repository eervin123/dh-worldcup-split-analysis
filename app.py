import streamlit as st
from timed_training import show_timed_training
from event_results import show_event_results

""" Downhill Mountain Bike World Cup Results 
This app displays the results from the Downhill Mountain Bike World Cup events.
This can be viewed at dhworldcup.streamlit.app
"""

# Initialize session state if not already done
if 'page' not in st.session_state:
    st.session_state.page = "Event Results"

# Page navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Event Results", "Timed Training"], index=0 if st.session_state.page == "Event Results" else 1, key='navigation')

# Update session state
st.session_state.page = page

# Show the appropriate page
if st.session_state.page == "Event Results":
    show_event_results()
else:
    show_timed_training()
