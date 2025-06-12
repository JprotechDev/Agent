from google import genai
from google.genai import types
import re, textwrap, os
from dotenv import load_dotenv
import httpx

# Load biến môi trường
load_dotenv()

def format(text, width=100):
    """
        Extracts and summarizes content from a PDF file using Google's Gemini AI model.
        
        This function takes a PDF source (URL, file path, or raw bytes), reads its contents, 
        and sends it along with a user-defined prompt to the Gemini 2.0 Flash model for analysis or summarization. 
        It supports various input formats and automatically downloads the file if a URL is provided.
        
        Parameters:
        source (str | bytes): The input PDF source. It can be:
            - A URL pointing to a PDF file (will be downloaded)
            - A local file path to a PDF
            - Raw bytes of a PDF file
        prompt (str): The instruction or question to guide the AI's response regarding the PDF's content.

        Returns:
        str: The AI-generated response, formatted for terminal display, or an error message if something fails.
        
        Dependencies:
        - Requires `google.generativeai`, `httpx`, `python-dotenv`, and `beautifulsoup4`
        - Set the environment variable `GOOGLE_API_KEY` for Gemini API access
    """
    seen, out = set(), []
    for line in text.splitlines():
        line = line.strip()
        if not line or line in seen: continue
        seen.add(line)
        if re.match(r"^\d+\.\s", line): out.append(f"\n\033[1m{line}\033[0m")
        elif "**" in line:
            line = re.sub(r"\*\*(.+?)\*\*", lambda m: f"\033[1m{m.group(1)}\033[0m", line)
            out.append(textwrap.fill(line, width))
        elif line.startswith(("* ", "- ", "•")): out.append("  • " + line.lstrip("*•- "))
        else: out.append(textwrap.fill(line, width))
    return "\n".join(out)

def AgentPdf(source: str = None, prompt: str = None) -> str:
    '''
    Trích xuất và tóm tắt nội dung từ tệp PDF bằng mô hình AI Gemini của Google.
    Args:
        source (str | bytes): Nguồn PDF đầu vào. Có thể là:
            - Một URL trỏ đến tệp PDF (sẽ được tải xuống)
            - Đường dẫn cục bộ đến tệp PDF
            - Các byte thô của một tệp PDF
        prompt (str): Hướng dẫn hoặc câu hỏi để định hướng phản hồi của AI về nội dung PDF.
    Returns:
        str: Phản hồi do AI tạo ra, được định dạng để hiển thị trên thiết bị đầu cuối, hoặc thông báo lỗi nếu có điều gì đó không thành công.
    '''
    try:
        client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

        base_dir = os.path.dirname(__file__)
        static_dir = os.path.join(base_dir, '..', 'static', 'pdfs')
        # Tạo thư mục nếu chưa có
        if not os.path.exists(static_dir): os.makedirs(static_dir)

        # Nếu source là URL thì tải về
        if isinstance(source, str) and source.startswith("http"):
            filename = os.path.basename(source.split("?")[0])
            response = httpx.get(source)
            file_path = os.path.join(static_dir, filename)
            with open(file_path, "wb") as f: f.write(response.content)
            pdf_data = response.content
        # Nếu source là path tới file local
        elif isinstance(source, str) and os.path.isfile(source):
            with open(source, "rb") as f: pdf_data = f.read()
        # Nếu source là dữ liệu bytes
        elif isinstance(source, bytes): pdf_data = source
        else:
            return None

        res = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[types.Part.from_bytes(data=pdf_data, mime_type='application/pdf'), prompt]
        )
        return format(res.text)
    except Exception as e:
        return None

# Ví dụ dùng URL
print(AgentPdf(
    'https://discovery.ucl.ac.uk/id/eprint/10089234/1/343019_3_art_0_py4t4l_convrt.pdf',
    'Nội dung của nó?'
))

