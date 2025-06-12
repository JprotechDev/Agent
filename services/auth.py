from google.oauth2.service_account import Credentials
from services.DataSheet.connect_googleSheet import connect_to_google_sheets as connGoogleSheets
from .encdec import Encdec
import pandas as pd
import os, base64, gspread
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()

class Auth:
    # Tìm kiếm Email, Password trong Google Sheets để login
    @staticmethod
    def search_email_password(email: str, password: str):
        try:
            SECRET_KEY_PASSWORD = os.getenv('SECRET_KEY_PASSWORD')
            ws = connGoogleSheets(os.getenv('SHEET_ACCOUNT_ID'), os.getenv('SHEET_ACCOUNT_ID_dataAccount'))
            cell = ws.find(Encdec.encrypt_aes(email, SECRET_KEY_PASSWORD), in_column=2)
            if cell and ws.cell(cell.row, 4).value == Encdec.encrypt_aes(password, SECRET_KEY_PASSWORD):
                data =  dict(zip(ws.row_values(1), ws.row_values(cell.row)))
                # Giải mã dữ liệu
                for key in data: data[key] = Encdec.decrypt_aes(data[key], SECRET_KEY_PASSWORD)
                return data
        except Exception as e:
            print(f"Error: {e}")
        return None
'''
print(Auth.search_email_password('6d796e6f6e636531323334356d7973616c743132333435363738393007d1104abf3ccf56d1ddd971845a66a7aeea7d7d67106d80ee59ad17fc88b88e6fe830ef', '6d796e6f6e636531323334356d7973616c74313233343536373839305f91563bb93cc956c9a0f56b3c0bdfd5e0d34877121c03e3')) 
'''
# print(Auth.search_email_password('20214044@eaut.edu.vn', 'jpt@2024'))