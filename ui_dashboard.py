import streamlit as st
from config import APP_CONFIG, COL_NAMES
from datetime import datetime, timedelta, date
import pandas as pd
import numpy as np
import notion_df
from api_utils import get_notion_client, get_oura_client

notion_df.pandas()

def get_metrics(df_notion):
    return {
        "avg_steps": int(df_notion[[COL_NAMES["activity_steps"]]].fillna(0).mean().round(0)),
        "avg_sleep_hrs": float(df_notion[[COL_NAMES["sleep_hrs"]]].dropna().mean().round(2)),
        "avg_weight": float(df_notion[[COL_NAMES["weight"]]].dropna().mean().round(2)),
        "count_fasting_days": int(sum(pd.to_numeric(df_notion[COL_NAMES["fasting_hrs"]].fillna(0)) > 0)),
    }


def render_dashboard():
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

if __name__ == "__main__":
    render_dashboard()