import streamlit as st
from config import APP_CONFIG, COL_NAMES
from oura import OuraClientDataFrame
from datetime import datetime, timedelta, date
from notion_client import Client as NotionClient
from notion_client.helpers import get_id
from api_utils import date_to_page_name, find_notion_page_by_name, get_oura_client, get_notion_client

def sync_daily_data():
    oura_client = get_oura_client()
    notion = get_notion_client()
    db_id = get_id(APP_CONFIG["NOTION_DATABASE_PAGE"])
    # sync today
    sync_data_for_date(
        notion,
        db_id,
        oura_client,
        datetime.now().date()
    )
    # sync yesterday
    sync_data_for_date(
        notion,
        db_id,
        oura_client,
        datetime.now().date() - timedelta(days=1) 
    )


def sync_data_for_date(
    notion: NotionClient, 
    db_id: str,
    oura_client: OuraClientDataFrame,
    date: date
):
    # Get data from Oura
    sleep_data = oura_client.sleep_df(
        date.strftime('%Y-%m-%d')
    )
    activity_data = oura_client.activity_df(
        date.strftime('%Y-%m-%d')
    )

    try:
        sleep_data = sleep_data.loc[date]
        sleep_hours = round(sleep_data["total_in_hrs"], 2)
    except:
        st.write(f"Missing sleep data for {date}")
        sleep_hours = None
    
    try:
        activity_data = activity_data.loc[date]
        activity_steps = int(activity_data["steps"])
        activity_cals = int(activity_data["cal_total"])
    except:
        st.write(f"Missing activity data for {date}")
        activity_steps = None
        activity_cals = None
    
    # Get or create page in Notion
    page_name = date_to_page_name(date)
    st.write("Syncing...", page_name)
    existing_page = find_notion_page_by_name(notion, page_name)
    if existing_page:
        st.write("Page exists, updating!")
        notion.pages.update(
            existing_page["id"],
            properties={
                COL_NAMES["sleep_hrs"]: {
                    "number": sleep_hours
                },
                COL_NAMES["activity_steps"]: {
                    "number": activity_steps
                },
                COL_NAMES["activity_cals"]: {
                    "number": activity_cals
                }
            }
        )
        st.write("Page updated!")
    else:
        st.write(notion.pages.create(parent={
                "type": "database_id",
                "database_id": db_id
            },
            properties={
               "Name": {
                    "title": [
                        {
                            "text": {
                                "content": page_name
                            }
                        }
                    ]
                },
                "Date": {
                    "date": {
                        "start": date.isoformat()
                    }
                },
                COL_NAMES["sleep_hrs"]: {
                    "number": sleep_hours
                },
               COL_NAMES["activity_steps"]: {
                    "number": activity_steps
                },
                COL_NAMES["activity_cals"]: {
                    "number": activity_cals
                }
            }
        ))
        st.write("Page created")
