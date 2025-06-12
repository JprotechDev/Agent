'''
from dotenv import load_dotenv
import os
import re
import textwrap
from google import genai
from datetime import datetime
# Load biến môi trường
load_dotenv()

def wrap_text(text, width=100):
    return "\n".join(textwrap.wrap(text, width=width))

def format_special_text(text: str) -> str:
    """
    Xử lý định dạng đặc biệt cho từng dòng:
    - In đậm tiêu đề dạng số thứ tự (1. ...)
    - In đậm markdown **text**
    - Thay dấu * hoặc - đầu dòng thành dấu bullet •
    """
    lines = text.splitlines()
    seen_lines = set()
    formatted_lines = []
    for line in lines:
        line = line.strip()
        if not line or line in seen_lines:
            continue
        seen_lines.add(line)

        # In đậm các tiêu đề dạng số thứ tự: 1. ABC, 2. XYZ:
        if re.match(r"^\d+\.\s", line):
            formatted_lines.append(f"\n\033[1m{line}\033[0m")
        # In đậm dòng có định dạng markdown: **text**
        elif "**" in line:
            bold_line = re.sub(r"\*\*(.+?)\*\*", lambda m: f"\033[1m{m.group(1)}\033[0m", line)
            formatted_lines.append(wrap_text(bold_line))
        # In bullet đầu dòng bằng dấu `•`, `-`, `*`
        elif line.startswith("*  ") or line.startswith("- "):
            formatted_lines.append("  • " + line[2:].strip())
        elif line.startswith("•"):
            formatted_lines.append("  • " + line[1:].strip())
        else:
            formatted_lines.append(wrap_text(line))

    result = "\n".join(formatted_lines)
    return result.replace('*   ', '  - ')

def ask(prompt):
    key = os.getenv('GOOGLE_API_KEY')
    try:
        return format_special_text(genai.Client(api_key=key).models.generate_content(model="gemini-2.0-flash", contents= f"You are a smart assistant. Your name is JproChat. Please reply in the national language I am using with the following prompt: {prompt}").text)
    except Exception as e:
        return str(e)
    
def ask_time(prompt: str) -> str:
    key = os.getenv('GOOGLE_API_KEY')
    try:
        return format_special_text(genai.Client(api_key=key).models.generate_content(model="gemini-2.0-flash", contents= f"You are a smart assistant. Your name is JproChat. Please reply in the national language I am using with the following prompt: {prompt} (Current time: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")})").text)
    except Exception as e:
        return str(e)

def detect_task_type(prompt: str) -> str:
    """
    Gọi AI để tự nhận diện loại task từ prompt.
    Ví dụ, trả về "time" nếu là hỏi về thời gian,
    "general" nếu là câu hỏi bình thường.
    """
    key = os.getenv('GOOGLE_API_KEY')
    try:
        client = genai.Client(api_key=key)
        detection_prompt = f"""
            You are a helpful AI assistant that classifies user's query into one of these types:
            - time (if user is asking about current time or date)
            - general (for general questions)

            Classify the following query strictly as "time" or "general":
            Query: "{prompt}"
            Answer with only the type word.
            """
        resp = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=detection_prompt.strip()
        )
        task_type = resp.text.strip().lower()
        if task_type in ["time", "general"]:
            return task_type
        return "general"  # Mặc định là general nếu không rõ
    except Exception:
        return "general"

def ask_general(prompt: str) -> str:
    """
    Hàm chính nhận prompt, tự nhận diện task rồi gọi hàm phù hợp.
    """
    task = detect_task_type(prompt)
    if task == "time": return ask_time(prompt)
    else: return ask(prompt)

# Ví dụ sử dụng
if __name__ == "__main__":
    while True:
        user_input = input("Bạn: ")
        if user_input.lower() in ["exit", "quit"]:
            break
        response = ask_general(user_input)
        print(f"JproChat: {response}")
'''
from dotenv import load_dotenv
import os
import re
import textwrap
from google import genai
from datetime import datetime

# Load biến môi trường
load_dotenv()

class AiAgentFunctionCalling:
    """
    AiAgent sử dụng Gemini với Function Calling (tools) để xử lý yêu cầu của người dùng.
    """

    def __init__(self):
        self.api_key = os.getenv('GOOGLE_API_KEY')
        self.client = genai.Client(api_key=self.api_key)

        # Định nghĩa tools (function) cho Gemini
        self.functions = [
            {
                "name": "get_current_time",
                "description": "Trả về thời gian hiện tại.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_general_info",
                "description": "Trả lời câu hỏi tổng quát của người dùng.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "Câu hỏi tổng quát của người dùng."
                        }
                    },
                    "required": ["query"]
                }
            }
        ]

    def wrap_text(self, text, width=100):
        return "\n".join(textwrap.wrap(text, width=width))

    def format_special_text(self, text: str) -> str:
        lines = text.splitlines()
        seen_lines = set()
        formatted_lines = []
        for line in lines:
            line = line.strip()
            if not line or line in seen_lines:
                continue
            seen_lines.add(line)

            if re.match(r"^\d+\.\s", line):
                formatted_lines.append(f"\n\033[1m{line}\033[0m")
            elif "**" in line:
                bold_line = re.sub(r"\*\*(.+?)\*\*", lambda m: f"\033[1m{m.group(1)}\033[0m", line)
                formatted_lines.append(self.wrap_text(bold_line))
            elif line.startswith("*  ") or line.startswith("- "):
                formatted_lines.append("  • " + line[2:].strip())
            elif line.startswith("•"):
                formatted_lines.append("  • " + line[1:].strip())
            else:
                formatted_lines.append(self.wrap_text(line))

        result = "\n".join(formatted_lines)
        return result.replace('*   ', '  - ')

    # Hàm để xử lý gọi hàm từ function calling
    def handle_function_call(self, function_call):
        if function_call["name"] == "get_current_time":
            now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            return {"content": f"Bây giờ là {now}"}
        elif function_call["name"] == "get_general_info":
            query = function_call["args"]["query"]
            # Gọi Gemini trả lời câu hỏi
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"You are a smart assistant. Your name is JproChat. Please reply in the national language with this prompt: {query}"
            )
            return {"content": response.text}
        else:
            return {"content": "Xin lỗi, tôi không hiểu yêu cầu của bạn."}

    def ask_general(self, prompt: str) -> str:
        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=prompt,
                tools=self.functions
            )

            if hasattr(response, 'function_call'):
                # Nếu AI chọn gọi hàm
                result = self.handle_function_call(response.function_call)
                return self.format_special_text(result["content"])
            else:
                # Nếu AI chỉ trả về text
                return self.format_special_text(response.text)

        except Exception as e:
            return str(e)

# Ví dụ sử dụng
if __name__ == "__main__":
    agent = AiAgentFunctionCalling()
    print(agent.ask_general("Hi, bạn có thể cho tôi biết bây giờ là mấy giờ không?"))