import json

with open("secrets.json", "r") as f:
    APP_CONFIG = json.load(f)

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