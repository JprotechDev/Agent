import os
import json

def get_chat_info_list(target_email):
    directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'listchats'))
    chat_info_list = []

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

# Ví dụ gọi hàm
'''if __name__ == "__main__":
    print(get_chat_info_list("20214044@eaut.edu.vn"))'''
