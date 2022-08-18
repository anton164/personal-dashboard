import databutton as db
import streamlit as st
from config import APP_CONFIG
from oura import OuraClientDataFrame
from datetime import datetime, timedelta, date
from notion_client import Client as NotionClient
from notion_client.helpers import get_id
import pandas as pd
import numpy as np
import notion_df
notion_df.pandas()

# st.set_page_config(layout="wide")

COL_NAMES = {
    "fasting_hrs": "🍔 Fasting (hrs)",
    "sleep_hrs": "😴 Sleep time (hrs)",
    "activity_cals": "🔥 Cals",
    "activity_steps":  "🏃 Steps",
    # "french": "🇫🇷 French",
    "spanish": "🇪🇸 Spanish",
    "piano": "🎹 Piano",
    "weight": "Weight (kg)"
}

def get_oura_client():
    return OuraClientDataFrame(personal_access_token=APP_CONFIG["OURA_TOKEN"])

def get_notion_client():
    return NotionClient(auth=APP_CONFIG["NOTION_TOKEN"])

def date_to_page_name(date: datetime):
    return f"{date.strftime('%A')} ({date.strftime('%Y-%m-%d')})"


def find_notion_page_by_name(notion, name: str):
    query_results = notion.search(query=name)
    if len(query_results["results"]) == 0:
        return False
    else:
        for result in query_results["results"]:
            if result["properties"]["Name"]["title"][0]["plain_text"] == name:
                return result
    return False


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
    # st.write(activity_data)

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

def get_metrics(df_notion):
    return {
        "avg_steps": int(df_notion[[COL_NAMES["activity_steps"]]].fillna(0).mean().round(0)),
        "avg_sleep_hrs": float(df_notion[[COL_NAMES["sleep_hrs"]]].dropna().mean().round(2)),
        "avg_weight": float(df_notion[[COL_NAMES["weight"]]].dropna().mean().round(2)),
        "count_fasting_days": int(sum(pd.to_numeric(df_notion[COL_NAMES["fasting_hrs"]].fillna(0)) > 0)),
    }

@db.apps.streamlit("/app", name="Dashboard")
def dashboard():
    st.header("Anton's Data")
    oura_client = get_oura_client()
    st.write(oura_client.user_info())
    notion_tab, oura_tab, toggl_tab = st.tabs(["Synced (Notion)", "OURA", "Toggl"])
    
    notion_df = pd.read_notion(
        APP_CONFIG["NOTION_DATABASE_PAGE"], 
        api_key=APP_CONFIG["NOTION_TOKEN"]
    ).set_index("Date").sort_index(ascending=False)
    for col in [
        COL_NAMES["fasting_hrs"], 
        COL_NAMES["activity_steps"], 
        COL_NAMES["activity_cals"]
    ]:
        notion_df[col] = np.floor(notion_df[col]).astype("Int64")
    # selected_week = pd.to_datetime(datetime.now()).week
    notion_df["week_number"] = notion_df.index.map(lambda x: x.week)
    col1, col2 = notion_tab.columns(2)
    day_period = col1.selectbox("Period (days)", options=[7, 14, 28], index=0)
    selected_period = col2.selectbox("Selected Period", options=[0, 1, 2, 3], index=0)
    notion_df["period"] = notion_df.index.map(
        lambda x: abs((x - pd.to_datetime(date.today())).days) // day_period
    )
    df_selected_period = notion_df[
        (notion_df["period"] == selected_period)
        & (notion_df.index < pd.to_datetime(date.today()))
    ]
    df_prev_period = notion_df[
        notion_df["period"] == selected_period + 1
    ]
    notion_tab.subheader(f"From {df_selected_period.index.min().date()} to {df_selected_period.index.max().date()}")
    col1, col2 = notion_tab.columns(2)
    selected_period_metrics = get_metrics(df_selected_period)
    prev_period_metrics = get_metrics(df_prev_period)
    col1.metric(
        "Average steps per day",
        selected_period_metrics["avg_steps"],
        delta=selected_period_metrics["avg_steps"] - prev_period_metrics["avg_steps"]
    )
    col2.metric(
        "Average hours of sleep per day",
        selected_period_metrics["avg_sleep_hrs"],
        delta=round(selected_period_metrics["avg_sleep_hrs"] - prev_period_metrics["avg_sleep_hrs"], 2)
    )
    col1.metric(
        "Days of fasting",
        selected_period_metrics["count_fasting_days"],
        delta=selected_period_metrics["count_fasting_days"] - prev_period_metrics["count_fasting_days"]
    )
    col2.metric(
        "Average weight (kg)",
        selected_period_metrics["avg_weight"],
        delta=round(selected_period_metrics["avg_weight"] - prev_period_metrics["avg_weight"], 2)
    )
    notion_tab.write(df_selected_period["Tags"].value_counts())
    notion_tab.dataframe(
        df_selected_period[[
            "Tags",
            COL_NAMES["fasting_hrs"],
            COL_NAMES["sleep_hrs"],
            COL_NAMES["activity_steps"],
            COL_NAMES["activity_cals"],
            COL_NAMES["spanish"],
            COL_NAMES["piano"],
        ]],
        width=1000
    )
    notion_tab.line_chart(
        notion_df[[
            COL_NAMES["activity_steps"],
        ]]
    )
    notion_tab.line_chart(
        notion_df[[
            COL_NAMES["sleep_hrs"],
        ]]
    )
    start_date = oura_tab.date_input(
        "Start date",
        value=datetime.now() - timedelta(7)
    )
    sleep_df = oura_client.sleep_df(
        str(start_date)
    )
    oura_tab.write(sleep_df)

@db.apps.streamlit("/sync_debugger", name="Sync Debugger")
def sync_debugger():
    oura_client = get_oura_client()
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
        

@db.jobs.repeat_every(seconds=4 * 60 * 60)
def sync_data():
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