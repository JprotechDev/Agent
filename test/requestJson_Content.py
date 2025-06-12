import os
import json

def get_chat_content(target_email, target_filename):
    directory = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'listchats'))
    chat_content = []

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

    return chat_content  # Trả về list dict chứa nội dung chat, rỗng nếu không tìm thấy

# Ví dụ gọi hàm
if __name__ == "__main__":
    email = "20214044@eaut.edu.vn"
    filename = "683950f2-7f00-8013-afba-98c58c284071"
    print(get_chat_content(email, filename))
