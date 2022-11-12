import streamlit as st
from ui_dashboard import render_dashboard
from ui_sync_debugger import render_sync_debugger

if 'count' not in st.session_state:
    st.session_state.count = 0

def render():
    pages = {
        "Dashboard": render_dashboard,
        "Sync Debugger": render_sync_debugger
    }

    st.sidebar.title("Personal Data Tracker")
    selected_page = st.sidebar.radio("Select a page", options=list(pages.keys()))

    pages[selected_page]()


if __name__ == "__main__":
    render()