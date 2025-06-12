from dotenv import load_dotenv
import os, json
import re
import textwrap
import httpx
from google import genai
from google.genai import types
from datetime import datetime
from services.DataSheet.connect_googleSheet import connect_to_google_sheets
#from DataSheet.connect_googleSheet import connect_to_google_sheets
import pandas as pd

# Load biến môi trường từ file .env
load_dotenv()

# Global variables (formerly instance variables)
API_KEY = os.getenv('GOOGLE_API_KEY')
if not API_KEY:
    raise ValueError("Bạn cần đặt biến môi trường GOOGLE_API_KEY")
CLIENT = genai.Client(api_key=API_KEY)

# Thư mục lưu trữ file PDF tải về tạm
STATIC_PDF_DIR = os.path.join(os.path.dirname(__file__), '..', 'static', 'pdfs')
if not os.path.exists(STATIC_PDF_DIR):
    os.makedirs(STATIC_PDF_DIR)

@staticmethod
def format_text(text, width=100):
    """
    Định dạng văn bản với:
    - In đậm tiêu đề số thứ tự (vd: 1. Tiêu đề)
    - In đậm markdown **text**
    - Thay dấu * hoặc - đầu dòng thành dấu bullet •
    """
    seen, out = set(), []
    for line in text.splitlines():
        line = line.strip()
        if not line or line in seen:
            continue
        seen.add(line)
        if re.match(r"^\d+\.\s", line):
            # In đậm tiêu đề số thứ tự
            out.append(f"\n\033[1m{line}\033[0m")
        elif "**" in line:
            # In đậm các đoạn markdown **text**
            line = re.sub(r"\*\*(.+?)\*\*", lambda m: f"\033[1m{m.group(1)}\033[0m", line)
            out.append(textwrap.fill(line, width))
        elif line.startswith(("* ", "- ", "•")):
            # Thay đầu dòng dấu * hoặc - thành bullet •
            out.append(" • " + line.lstrip("*•- "))
        else:
            out.append(textwrap.fill(line, width))
    return "\n".join(out)

class AiAgent:
    """
    Lớp đại diện trợ lý AI sử dụng Google Gemini.
    Tự động nhận diện nếu prompt có link PDF để gọi AgentPdf.
    """

    @staticmethod
    def wrap_text(text, width=100):
        return "\n".join(textwrap.wrap(text, width=width))

    @staticmethod
    def format_special_text(text: str) -> str:
        # Gọi hàm định dạng chung
        return format_text(text)

# Xử lý nhận diện các ngân hàng trong giao dịch
    @staticmethod
    def detect_task_type(prompt: str) -> str:
        """
        Nhận diện loại câu hỏi:
        - time: hỏi về thời gian, ngày tháng
        - general: các câu hỏi chung khác
        - payment_transaction: hỏi về hoá đơn giao dịch, thanh toán
        - find_tax_transactions: hỏi về hoá đơn giao dịch thuế
        Gọi AI để tự nhận diện loại task từ prompt.
        """
        try:
            detection_prompt = f"""
                You are a helpful AI assistant that classifies user's query into one of these types:
                - time: This label is only used when the user requests information about the current time or date, for example: "What time is it now?" or "What date is today?".
                - general: This label applies to questions or requests not related to financial or tax transactions, such as questions about general knowledge, usage instructions, or technical support.
                - payment_transaction: This label is strictly for cases where the user mentions or requests details about a payment transaction, for example: "I made a payment on date X, please check for me," or "Retrieve my payment transaction information."
                - find_tax_transactions: This label is used only when the user requests a lookup or details about tax transactions, for example: "Check my tax information for last month," or "I want to see my tax transactions."
                
                Classify the following query strictly as "time" or "general" or "payment_transaction" or "find_tax_transactions":
                Query: "{prompt}"
                Answer with only the type word.
                """
            resp = CLIENT.models.generate_content(
                model="gemini-2.0-flash",
                contents=detection_prompt.strip()
            )
            task_type = resp.text.strip().lower()
            print(f"Detected task type: {task_type}")  # debug output
            if task_type in ["time", "general", "payment_transaction", "find_tax_transactions"]:
                return task_type
            return "general"
        except Exception:
            return "general"

    @staticmethod
    def ask(prompt: str) -> dict:
        """
        Gửi câu hỏi chung cho model AI. Trả về dict kiểu {"type": "text", "content": "..."}
        """
        try:
            response = CLIENT.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"You are a smart assistant. Your name is JproChat. Please reply in the national language I am using with the following prompt: {prompt}"
            )
            formatted = AiAgent.format_special_text(response.text)
            return {"type": "text", "content": formatted}
        except Exception as e:
            return {"type": "text", "content": f"Lỗi khi gọi AI: {e}"}

    @staticmethod
    def askTITLE(prompt: str) -> dict:
        """
        Gửi câu hỏi chung cho model AI. Trả về dict kiểu {"type": "text", "content": "..."}
        """
        try:
            response = CLIENT.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"You are a smart assistant. Your name is JproChat. Please reply in the national language I am using with the following prompt: {prompt}"
            )
            formatted = AiAgent.format_special_text(response.text)
            return {"type": "text", "content": formatted}
        except Exception as e:
            return {"type": "text", "content": f"Lỗi khi gọi AI: {e}"}

    @staticmethod
    def ask_time(prompt: str) -> str:
        """
        Gửi câu hỏi liên quan thời gian cho model AI kèm thời gian hiện tại.
        """
        try:
            now_str = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            response = CLIENT.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"You are a smart assistant. Please reply in the national language I am using with the following prompt: {prompt} (Current time: {now_str})"
            )
            return AiAgent.format_special_text(response.text)
        except Exception as e:
            return f"Lỗi khi gọi AI thời gian: {e}"

    @staticmethod
    def find_tax_transactions(prompt: str) -> dict:
        '''
        Tìm kiếm hóa đơn trong Google Sheets "TAX_TRANSACTION" dựa trên prompt.
        Sử dụng Google Gemini để trích xuất các trường dữ liệu có cấu trúc từ prompt.
        Trả về dict {"type": "table", "data": [...]}
        '''

        key_to_col = {
            "request_id": "REQUEST_ID",
            "contract_no": "CONTRACT_NO",
            "serial_no": "SERIAL NO",
            "invoice_no": "INVOICE NO",
            "invoice_signal": "INVOICE SIGNAL",
            "invoice_date": "INVOICE DATE",
            "invoice_description": "INVOICE DESCRIPTION",
            "buyer": "BUYER",
            "seller": "SELLER",
            "invoice_amount_wo_vat": "INVOICE AMOUNT_WO VAT",
            "vat_amount": "VAT AMOUNT",
            "total_amount": "TOTAL AMOUNT",
            "push_date": "PUSH_DATE"
        }

        system_prompt = """
            Extract structured fields from the following text. Return ONLY valid JSON (no extra text) with keys:
            - request_id
            - contract_no
            - serial_no
            - invoice_no
            - invoice_signal
            - invoice_date: format YYYY-MM-DD
            - invoice_description: Default null
            - buyer
            - seller
            - invoice_amount_wo_vat
            - vat_amount
            - total_amount
            - push_date: format YYYY-MM-DD
            If a field is not mentioned, return null.
            Strictly return valid JSON only.
        """

        try:
            response = CLIENT.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"{system_prompt}\nPrompt: {prompt}"
            )
            raw_text = response.text
            print("Gemini response:", raw_text)
            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if not match:
                print("Không tìm thấy JSON trong response")
                return {"type": "table", "data": []}
            structured_data = json.loads(match.group())

        except Exception as e:
            print("Lỗi gọi Gemini:", e)
            return {"type": "table", "data": []}

        # Đọc dữ liệu từ Google Sheets
        worksheet = connect_to_google_sheets(
            "1VNtJ1hAKZ8IvZQklGDV0OLE7vvJAzEfVD49kfkFNL_U",
            "TAX_TRANSACTION"
        )
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)

        # Lọc dữ liệu theo các trường từ AI
        for key, value in structured_data.items():
            if value is not None and value != '' and key in key_to_col:
                col = key_to_col[key]
                if col not in df.columns:
                    continue
                try:
                    if key in ['invoice_amount_wo_vat', 'vat_amount', 'total_amount']:
                        df = df[df[col].astype(float) == float(value)]
                    elif key in ['invoice_date', 'push_date']:
                        df = df[df[col].astype(str).str.strip() == str(value).strip()]
                    else:
                        df = df[df[col].astype(str).str.contains(str(value), case=False, na=False)]
                except Exception as e:
                    print(f"Lỗi khi lọc theo {key}: {e}")
                    continue

        if df.empty:
            return {"type": "table", "data": []}

        return {
            "type": "table",
            "data": df.reset_index(drop=True).to_dict(orient="records")
        }

    @staticmethod
    def AgentPdf(source: str = None, prompt: str = None) -> dict:
        """
        Xử lý PDF từ URL, file local hoặc bytes.
        Trả về kết quả dạng {"type": "text", "content": "..."}
        """
        try:
            # Xử lý nguồn dữ liệu PDF
            if isinstance(source, str) and source.startswith("http"):
                # Tải file PDF từ URL
                filename = os.path.basename(source.split("?")[0])
                response = httpx.get(source, timeout=30.0)
                if response.status_code != 200:
                    return {"type": "text", "content": f"Lỗi tải file PDF: HTTP {response.status_code}"}
                file_path = os.path.join(STATIC_PDF_DIR, filename)
                with open(file_path, "wb") as f:
                    f.write(response.content)
                pdf_data = response.content

            elif isinstance(source, str) and os.path.isfile(source):
                # Đọc từ file local
                with open(source, "rb") as f:
                    pdf_data = f.read()

            elif isinstance(source, bytes):
                pdf_data = source

            else:
                return {"type": "text", "content": "Nguồn PDF không hợp lệ"}

            # Gọi Google Gemini với dữ liệu PDF
            res = CLIENT.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Part.from_bytes(data=pdf_data, mime_type='application/pdf'),
                    prompt or ""
                ]
            )
            formatted = AiAgent.format_special_text(res.text)
            return {"type": "text", "content": formatted}

        except Exception as e:
            return {"type": "text", "content": f"Lỗi khi xử lý PDF: {e}"}

    @staticmethod
    def find_transactions(prompt: str) -> dict:
        '''
        Tìm kiếm giao dịch trong Google Sheets dựa trên prompt.
        Sử dụng Google Gemini để trích xuất các trường dữ liệu có cấu trúc từ prompt.
        Trả về dict dạng {"type": "table", "data": [...]}
        '''

        # Bản đồ key -> tên cột
        key_to_col = {
            "request_id": "REQUEST_ID",
            "transaction_id": "TRANSACTION ID",
            "bank_account": "BANK ACCOUNT",
            "bank_short_name": "BANK SHORT NAME",
            "transaction_content": "TRANSACTION CONTENT",
            "invoice_no": "INVOICE NO",
            "contract_no": "CONTRACT_NO",
            "project_id": "PROJECT ID",
            "money_amount": "MONEY AMOUNT",
            "transaction_date": "TRANSACTION DATE",
            "sender": "SENDER",
            "receiver": "RECEIVER",
            "status": "STATUS",
            "push_date": "PUSH_DATE"
        }

        # Prompt cho Gemini
        system_prompt = """
            Extract structured fields from the following text. Return ONLY valid JSON (no extra text) with keys:
            - request_id
            - transaction_id
            - bank_account: the bank account number
            - bank_short_name: Short name of the bank. Examples: VCB (Vietcombank), BIDV (Ngân hàng Đầu tư và Phát triển Việt Nam), CTG (VietinBank), TCB (Techcombank), ACB (Ngân hàng Á Châu), STB (Sacombank), MB (MB Bank), TPB (TPBank), VIB (Ngân hàng Quốc Tế), MSB (Ngân hàng Hàng Hải), SCB (Ngân hàng Sài Gòn), LPB (LienVietPostBank), HDB (HDBank), EIB (Eximbank), DAB (DongABank), NAB (Nam A Bank), BVB (Ngân hàng Bảo Việt), BAB (Bac A Bank), AGR (Agribank), PVcomBank (Ngân hàng Đại Chúng Việt Nam), ABB (An Bình Bank), SHB (Ngân hàng Sài Gòn Hà Nội), VAB (VietABank), VPB (VPBank), OCB (OceanBank), GPB (GPBank), PGB (PG Bank), HLBVN (Hong Leong Bank Vietnam), PBVN (Public Bank Vietnam), Woori Bank (Woori Vietnam), CIMB (CIMB Vietnam), Shinhan Bank (Shinhan Vietnam), Standard Chartered (Standard Chartered Vietnam), HSBC (HSBC Vietnam), UOB (UOB Vietnam).
            - transaction_content: null
            - invoice_no: the invoice number
            - contract_no: the contract number
            - project_id
            - money_amount: the amount of money in the transaction
            - transaction_date: the date of the transaction in YYYY-MM-DD format
            - sender: the sender's name
            - receiver: the receiver's name
            - status: the status of the transaction (e.g., "success", "pending", "failed")
            - push_date: the date when the transaction was pushed in YYYY-MM-DD format
            If a field is not mentioned, return null.
            Strictly no extra text, just pure JSON.
        """

        try:
            response = CLIENT.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"{system_prompt}\nPrompt: {prompt}"
            )
            raw_text = response.text
            print("Response from Gemini:", raw_text)

            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if not match:
                print("Không tìm thấy JSON trong response")
                return {"type": "table", "data": []}
            structured_data = json.loads(match.group())

        except Exception as e:
            print("Lỗi gọi Gemini:", e)
            return {"type": "table", "data": []}

        # Lấy dữ liệu từ Google Sheets
        worksheet = connect_to_google_sheets(
            "1VNtJ1hAKZ8IvZQklGDV0OLE7vvJAzEfVD49kfkFNL_U",
            "PAYMENT_TRANSACTION_devTest"
        )
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)

        # Lọc dữ liệu theo kết quả từ AI
        for key, value in structured_data.items():
            if value is not None and value != '' and key in key_to_col:
                col = key_to_col[key]
                if col not in df.columns:
                    continue
                if key == 'money_amount' or col == 'MONEY AMOUNT':
                    try:
                        df = df[df[col].astype(float) == float(value)]
                    except:
                        continue
                elif col in ['TRANSACTION DATE', 'PUSH_DATE', 'BANK ACCOUNT', 'BANK SHORT NAME']:
                    df = df[df[col].astype(str).str.strip() == str(value).strip()]
                else:
                    df = df[df[col].astype(str).str.contains(str(value), case=False, na=False)]

        # Trả kết quả
        if df.empty:
            return {
                "type": "table",
                "data": []
            }

        return {
            "type": "table",
            "data": df.reset_index(drop=True).to_dict(orient="records")
        }

    @staticmethod
    def ask_general(prompt: str) -> str:
        """
        Hàm chính xử lý input người dùng:
        - Nếu prompt có link PDF (URL), gọi AgentPdf
        - Nếu không, nhận diện task (time/general) rồi gọi hàm tương ứng
        """
        # Tự động kiểm tra nếu prompt có link PDF thì gọi AgentPdf
        url_match = re.search(r'https?://[^\s]+\.pdf', prompt, re.IGNORECASE)
        if url_match:
            pdf_url = url_match.group(0)
            # Tách prompt để chỉ lấy phần hỏi thực sự (bỏ URL)
            prompt_without_url = prompt.replace(pdf_url, "").strip()
            if not prompt_without_url:
                prompt_without_url = "Hãy tóm tắt nội dung của PDF này."
            return AiAgent.AgentPdf(source=pdf_url, prompt=prompt_without_url)

        # Nếu không phải link PDF, nhận diện task để gọi ask hoặc ask_time
        task = AiAgent.detect_task_type(prompt)
        print(f"Detected task type: {task}")
        if task == "time":
            return AiAgent.ask_time(prompt)
        elif task == "payment_transaction":
            return AiAgent.find_transactions(prompt)
        elif task == "find_tax_transactions":
            return AiAgent.find_tax_transactions(prompt)
        else:
            return AiAgent.ask(prompt)