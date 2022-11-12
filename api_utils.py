from oura import OuraClientDataFrame
from notion_client import Client as NotionClient
from config import APP_CONFIG
from datetime import datetime

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
