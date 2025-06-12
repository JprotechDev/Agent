from google.oauth2.service_account import Credentials
import gspread, os
import pandas as pd

@staticmethod
def connect_to_google_sheets(spreadsheet_id: str, worksheet_name: str):
    """
    Kết nối tới Google Sheets và trả về worksheet.
    """
    credentials_path = r'D:\Agent_JPT-6_2_2025_Hoan-New\services\DataSheet\data\maildevjprotech-b13deed39d0e.json'
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    creds = Credentials.from_service_account_file(credentials_path, scopes=scope)
    gc = gspread.authorize(creds)
    worksheet = gc.open_by_key(spreadsheet_id).worksheet(worksheet_name)
    return worksheet
