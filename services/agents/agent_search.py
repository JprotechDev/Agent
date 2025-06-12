from dotenv import load_dotenv
import os
import re
import textwrap
from google import genai

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

def AgentSearch(promt: str) -> str:
    """
    Gọi API Gemini và trả về kết quả thô (chưa xử lý).
    """
    try: 
        client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))
        response = client.models.generate_content(model="gemini-2.0-flash", contents=promt)
        return format_special_text(response.text.strip())
    except Exception as e:
        return f'Error: {e}'

if __name__ == "__main__":
    raw_response = AgentSearch("Giới thiệu cơ bản về Hồ Chí Minh, Việt Nam.")
    print(raw_response)
