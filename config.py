import json
import os

try:
    with open("secrets.json", "r") as f:
        APP_CONFIG = json.load(f)
except:
    APP_CONFIG = {
        "OURA_TOKEN": os.getenv("OURA_TOKEN"),
        "NOTION_TOKEN": os.getenv("NOTION_TOKEN"),
        "NOTION_DATABASE_PAGE": os.getenv("NOTION_DATABASE_PAGE")
    }

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