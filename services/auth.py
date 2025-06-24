# auth.py

from google.oauth2.service_account import Credentials
from services.DataSheet.connect_googleSheet import connect_to_google_sheets as connGoogleSheets
from .encdec import Encdec
import pandas as pd
import os, base64, gspread
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()

class Auth:
    @staticmethod
    def search_email_password(email: str, password: str):
        try:
            SECRET_KEY_PASSWORD = os.getenv('SECRET_KEY_PASSWORD')
            ws = connGoogleSheets(os.getenv('SHEET_ACCOUNT_ID'), os.getenv('SHEET_ACCOUNT_ID_dataAccount'))
            cell = ws.find(Encdec.encrypt_aes(email, SECRET_KEY_PASSWORD), in_column=2)
            if cell and ws.cell(cell.row, 4).value == Encdec.encrypt_aes(password, SECRET_KEY_PASSWORD):
                data =  dict(zip(ws.row_values(1), ws.row_values(cell.row)))
                for key in data: data[key] = Encdec.decrypt_aes(data[key], SECRET_KEY_PASSWORD)
                return data
        except Exception as e:
            print(f"Error in search_email_password: {e}")
        return None

    @staticmethod
    def get_all_users():
        try:
            SECRET_KEY_PASSWORD = os.getenv('SECRET_KEY_PASSWORD')
            ws = connGoogleSheets(os.getenv('SHEET_ACCOUNT_ID'), os.getenv('SHEET_ACCOUNT_ID_dataAccount'))
            
            all_values = ws.get_all_values()
            headers = [h.strip() for h in all_values[0]] 
            
            all_users_data = []
            for row in all_values[1:]:
                if not any(cell.strip() for cell in row):
                    continue

                record = dict(zip(headers, row))
                decrypted_record = {}
                is_valid_user = False 

                for key, value in record.items():
                    try:
                        decrypted_record[key] = Encdec.decrypt_aes(value, SECRET_KEY_PASSWORD)
                        if key == 'EMAIL' and decrypted_record[key]:
                            is_valid_user = True
                    except Exception:
                        decrypted_record[key] = value
                
                if is_valid_user:
                    if 'ROLES' in decrypted_record and decrypted_record['ROLES']:
                        decrypted_record['roles'] = [role.strip() for role in decrypted_record['ROLES'].split(',')]
                    else:
                        decrypted_record['roles'] = []

                    if 'STATUS' in decrypted_record and decrypted_record['STATUS'] == 'active':
                        decrypted_record['status'] = True
                    else:
                        decrypted_record['status'] = False

                    all_users_data.append(decrypted_record)
            return all_users_data
        except Exception as e:
            print(f"Error getting all users: {e}")
        return []

    @staticmethod
    def find_user_by_email(email: str):
        try:
            SECRET_KEY_PASSWORD = os.getenv('SECRET_KEY_PASSWORD')
            ws = connGoogleSheets(os.getenv('SHEET_ACCOUNT_ID'), os.getenv('SHEET_ACCOUNT_ID_dataAccount'))
            
            encrypted_email = Encdec.encrypt_aes(email, SECRET_KEY_PASSWORD)
            cell = ws.find(encrypted_email, in_column=2)
            
            if cell:
                row_values = ws.row_values(cell.row)
                headers = ws.row_values(1)
                
                user_data = dict(zip(headers, row_values))
                decrypted_user_data = {}
                for key, value in user_data.items():
                    try:
                        decrypted_user_data[key] = Encdec.decrypt_aes(value, SECRET_KEY_PASSWORD)
                    except Exception:
                        decrypted_user_data[key] = value
                
                if 'ROLES' in decrypted_user_data and decrypted_user_data['ROLES']:
                    decrypted_user_data['roles'] = [role.strip() for role in decrypted_user_data['ROLES'].split(',')]
                else:
                    decrypted_user_data['roles'] = []

                return decrypted_user_data
            return None
        except Exception as e:
            print(f"Error finding user by email: {e}")
            return None

    @staticmethod
    def add_new_user(id_account: str, fullname: str, email: str, password: str, img: str = '', roles: list = None, status: str = 'active'):
        try:
            SECRET_KEY_PASSWORD = os.getenv('SECRET_KEY_PASSWORD')
            ws = connGoogleSheets(os.getenv('SHEET_ACCOUNT_ID'), os.getenv('SHEET_ACCOUNT_ID_dataAccount'))

            if Auth.find_user_by_email(email):
                return False, "Email đã tồn tại."

            encrypted_id_account = Encdec.encrypt_aes(id_account, SECRET_KEY_PASSWORD)
            encrypted_fullname = Encdec.encrypt_aes(fullname, SECRET_KEY_PASSWORD)
            encrypted_email = Encdec.encrypt_aes(email, SECRET_KEY_PASSWORD)
            encrypted_password = Encdec.encrypt_aes(password, SECRET_KEY_PASSWORD)
            encrypted_img = Encdec.encrypt_aes(img, SECRET_KEY_PASSWORD) if img else Encdec.encrypt_aes("", SECRET_KEY_PASSWORD)
            
            roles_string = ','.join(sorted(roles)) if roles else ''
            encrypted_roles = Encdec.encrypt_aes(roles_string, SECRET_KEY_PASSWORD)
            
            encrypted_status = Encdec.encrypt_aes(status, SECRET_KEY_PASSWORD)

            headers = ws.row_values(1)
            
            new_row_data = {
                'IDACCOUNT': encrypted_id_account,
                'EMAIL': encrypted_email,
                'FULLNAME': encrypted_fullname,
                'PASSWORD': encrypted_password,
                'IMG': encrypted_img,
                'ROLES': encrypted_roles,
                'STATUS': encrypted_status,
            }
            
            row_to_append = [new_row_data.get(header, Encdec.encrypt_aes("", SECRET_KEY_PASSWORD)) for header in headers]

            ws.append_row(row_to_append)
            return True, "Người dùng đã được thêm thành công!"
        except Exception as e:
            print(f"Error adding new user: {e}")
            return False, f"Lỗi khi thêm người dùng: {e}"

    @staticmethod
    def update_user_role(email: str, role: str, add: bool):
        try:
            SECRET_KEY_PASSWORD = os.getenv('SECRET_KEY_PASSWORD')
            ws = connGoogleSheets(os.getenv('SHEET_ACCOUNT_ID'), os.getenv('SHEET_ACCOUNT_ID_dataAccount'))
            
            encrypted_email = Encdec.encrypt_aes(email, SECRET_KEY_PASSWORD)
            cell = ws.find(encrypted_email, in_column=2)
            
            if cell:
                row_index = cell.row
                # Giả định cột ROLES là cột thứ 6 (chỉ số 5)
                current_roles_encrypted = ws.cell(row_index, 6).value 
                
                current_roles_decrypted = Encdec.decrypt_aes(current_roles_encrypted, SECRET_KEY_PASSWORD) if current_roles_encrypted else ""
                roles_list = [r.strip() for r in current_roles_decrypted.split(',')] if current_roles_decrypted else []
                
                if add and role not in roles_list:
                    roles_list.append(role)
                elif not add and role in roles_list:
                    roles_list.remove(role)
                
                new_roles_string = ','.join(sorted(list(set(roles_list)))) # Loại bỏ trùng lặp và sắp xếp
                new_roles_encrypted = Encdec.encrypt_aes(new_roles_string, SECRET_KEY_PASSWORD)
                
                ws.update_cell(row_index, 6, new_roles_encrypted)
                return True
            return False
        except Exception as e:
            print(f"Error updating user role: {e}")
            return False

    @staticmethod
    def toggle_user_status(email: str):
        try:
            SECRET_KEY_PASSWORD = os.getenv('SECRET_KEY_PASSWORD')
            ws = connGoogleSheets(os.getenv('SHEET_ACCOUNT_ID'), os.getenv('SHEET_ACCOUNT_ID_dataAccount'))
            
            encrypted_email = Encdec.encrypt_aes(email, SECRET_KEY_PASSWORD)
            cell = ws.find(encrypted_email, in_column=2)
            
            if cell:
                row_index = cell.row
                # Giả định cột STATUS là cột thứ 7 (chỉ số 6)
                current_status_encrypted = ws.cell(row_index, 7).value 
                
                current_status_decrypted = Encdec.decrypt_aes(current_status_encrypted, SECRET_KEY_PASSWORD) if current_status_encrypted else ""
                
                new_status = 'inactive' if current_status_decrypted == 'active' else 'active'
                new_status_encrypted = Encdec.encrypt_aes(new_status, SECRET_KEY_PASSWORD)
                
                ws.update_cell(row_index, 7, new_status_encrypted)
                return True
            return False
        except Exception as e:
            print(f"Error toggling user status: {e}")
            return False

    @staticmethod
    def delete_user(email: str):
        try:
            SECRET_KEY_PASSWORD = os.getenv('SECRET_KEY_PASSWORD')
            ws = connGoogleSheets(os.getenv('SHEET_ACCOUNT_ID'), os.getenv('SHEET_ACCOUNT_ID_dataAccount'))
            
            encrypted_email = Encdec.encrypt_aes(email, SECRET_KEY_PASSWORD)
            cell = ws.find(encrypted_email, in_column=2)
            
            if cell:
                ws.delete_rows(cell.row)
                return True
            return False
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
            
