# services/chat_suggestions.py

import os
import json
from collections import Counter
from typing import List, Dict

class ChatSuggestions:
    # Đường dẫn đến thư mục chứa các file chat JSON
    # Giả định thư mục services/ nằm trong cấu trúc của ứng dụng Flask
    # Đường dẫn sẽ là: project_root/static/listchats
    LISTCHATS_DIR = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), # services/
        '..', # project_root/
        'static', # static/
        'listchats' # listchats/
    )

    @staticmethod
    def _get_all_chat_files() -> List[str]:
        """Trả về danh sách các đường dẫn đầy đủ đến các tệp chat JSON."""
        if not os.path.exists(ChatSuggestions.LISTCHATS_DIR):
            return []
        
        json_files = []
        for filename in os.listdir(ChatSuggestions.LISTCHATS_DIR):
            if filename.endswith('.json'):
                json_files.append(os.path.join(ChatSuggestions.LISTCHATS_DIR, filename))
        return json_files

    @staticmethod
    def get_popular_suggestions(num_suggestions: int = 5) -> List[Dict[str, str]]:
        """
        Phân tích tất cả lịch sử chat và trả về các cụm từ phổ biến nhất.
        """
        all_messages_text = []
        for file_path in ChatSuggestions._get_all_chat_files():
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'chat' in data and isinstance(data['chat'], list):
                        for message_entry in data['chat']:
                            # Chỉ lấy tin nhắn từ người dùng (sender == "user")
                            # và chỉ tin nhắn dạng văn bản (type == "text")
                            if message_entry.get('sender') == 'user' and message_entry.get('type') == 'text':
                                message_content = message_entry.get('message', '').strip()
                                if message_content:
                                    all_messages_text.append(message_content)
            except Exception as e:
                print(f"Error processing chat file {file_path}: {e}")
                continue

        # Đếm tần suất xuất hiện của mỗi cụm từ
        message_counts = Counter(all_messages_text)

        # Lấy các cụm từ phổ biến nhất
        top_suggestions = []
        for text, count in message_counts.most_common(num_suggestions):
            top_suggestions.append({"text": text})
            
        return top_suggestions

    @staticmethod
    def update_suggestion_frequency(text: str):
        """
        Khi sử dụng file JSON cho lịch sử, việc "cập nhật tần suất" thực chất
        là việc ghi tin nhắn vào lịch sử chat. Các gợi ý sẽ được tính toán lại
        khi hàm get_popular_suggestions được gọi.
        Do đó, hàm này không cần thiết nếu bạn chỉ dùng lịch sử JSON để sinh gợi ý.
        Bạn có thể bỏ qua việc gọi hàm này trong homeController.py.
        Tôi sẽ giữ nó ở đây như một hàm rỗng để tránh lỗi nếu bạn quên xóa lời gọi.
        """
        pass