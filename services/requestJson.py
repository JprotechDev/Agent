import os
import json

class ChatInfo:
    @staticmethod
    def get_chat_info_list(target_email):
        directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'listchats'))
        chat_info_list = []

        if not os.path.exists(directory):
            print(f"Thư mục không tồn tại: {directory}")
            return None

        for filename in os.listdir(directory):
            if filename.endswith(".json"):
                try:
                    with open(os.path.join(directory, filename), encoding='utf-8') as f:
                        data = json.load(f)
                    if data.get("id_email") == target_email:
                        chat_info_list.append({
                            "file_token": os.path.splitext(filename)[0],
                            "title": data.get("title", "Không có tiêu đề")
                        })
                except Exception as e:
                    print(f"Lỗi đọc file {filename}: {e}")

        return chat_info_list if chat_info_list else None

    @staticmethod
    def get_chat_content(target_email, target_filename):
        directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'listchats'))
        chat_content = []

        if not os.path.exists(directory):
            print(f"Thư mục không tồn tại: {directory}")
            return []

        for filename in os.listdir(directory):
            if filename.endswith(".json"):
                filepath = os.path.join(directory, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        file_basename = os.path.splitext(filename)[0]
                        if data.get("id_email") == target_email and file_basename == target_filename:
                            chat_content = data.get("chat", [])
                            break
                except Exception as e:
                    print(f"Lỗi đọc file {filename}: {e}")

        return chat_content  # Trả về list chứa nội dung chat

    @staticmethod
    def requestJsonDataSheet():
        # Đường dẫn đến file JSON
        directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'services', 'DataSheet', 'data', 'dataSheet.json'))

        if not os.path.exists(directory):
            print(f"File không tồn tại: {directory}")
            return []

        try:
            with open(directory, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except Exception as e:
            print(f"Lỗi đọc file {directory}: {e}")
            return []

        result = []

        for sheet_key, sheet_data in data.items():
            item = {
                "maneSheet": sheet_data.get("maneSheet"),
                "spreadsheet_id": sheet_data.get("spreadsheet_id"),
                "worksheet_name": sheet_data.get("worksheet_name", {})
            }
            result.append(item)

        return result

    @staticmethod
    def requestJsonBankref():
        directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'services', 'DataSheet', 'data', 'bank_ref.json'))

        if not os.path.exists(directory):
            print(f"File không tồn tại: {directory}")
            return {}

        try:
            with open(directory, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except Exception as e:
            print(f"Lỗi đọc file {directory}: {e}")
            return {}

        return data  # Trả về dict đúng định dạng dùng trong Jinja template

