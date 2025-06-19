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

    @staticmethod
    def get_all_users():
        try:
            SECRET_KEY_PASSWORD = os.getenv('SECRET_KEY_PASSWORD')
            ws = connGoogleSheets(os.getenv('SHEET_ACCOUNT_ID'), os.getenv('SHEET_ACCOUNT_ID_dataAccount'))
            records = ws.get_all_records() # Lấy tất cả các hàng dưới dạng list of dictionaries
            
            all_users_data = []
            for record in records:
                decrypted_record = {}
                # Giải mã tất cả các trường trong mỗi bản ghi
                for key, value in record.items():
                    try:
                        decrypted_record[key] = Encdec.decrypt_aes(value, SECRET_KEY_PASSWORD)
                    except Exception:
                        # Nếu giải mã thất bại (ví dụ: trường không phải là mã hóa), giữ nguyên giá trị gốc
                        decrypted_record[key] = value

                # Giả sử cột 'ROLES' chứa các vai trò được phân tách bằng dấu phẩy
                if 'ROLES' in decrypted_record and decrypted_record['ROLES']:
                    decrypted_record['roles'] = [role.strip() for role in decrypted_record['ROLES'].split(',')]
                else:
                    decrypted_record['roles'] = [] # Mặc định là một list trống nếu không có vai trò

                # Giả sử cột 'STATUS' chứa trạng thái (ví dụ: 'active', 'inactive')
                # Bạn có thể điều chỉnh logic này tùy thuộc vào cách bạn lưu trạng thái
                if 'STATUS' in decrypted_record and decrypted_record['STATUS'] == 'active':
                    decrypted_record['status'] = True
                else:
                    decrypted_record['status'] = False

                all_users_data.append(decrypted_record)
            return all_users_data
        except Exception as e:
            print(f"Error getting all users: {e}")
        return []
