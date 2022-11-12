import streamlit as st
from api_utils import get_notion_client
from datetime import datetime, timedelta
from sync_utils import sync_data_for_date
from notion_client.helpers import get_id
from config import APP_CONFIG

if __name__ == "__main__":
    oura_client =  ()
    notion = get_notion_client()
    db_id = get_id(APP_CONFIG["NOTION_DATABASE_PAGE"])
    notion_db = notion.databases.retrieve(db_id)
    
    st.header("Sync with notion")
    sync_date = st.date_input(
        "Sync date",
        value=datetime.now()
    )
    if st.button("Sync data for day"):
        sync_data_for_date(
            notion,
            db_id,
            oura_client,
            sync_date
        )
    if st.button("Sync data for week"):
        start_of_week = sync_date  - timedelta(days=sync_date.weekday() % 7)
        for i in range(7):
            sync_data_for_date(
                notion,
                db_id,
                oura_client,
                start_of_week + timedelta(days=i)
            )