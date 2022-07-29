import databutton as db
import streamlit as st


@db.apps.streamlit("/app", name="My first app")
def my_first_app():
    st.title("My first app!")
    st.text("This is not doing much just yet...")   