import pandas as pd
from google import genai
import json
import re
from DataSheet.connect_googleSheet import connect_to_google_sheets

class AIAgent:

    # Tìm kiếm giao dịch trong Google Sheets dựa trên prompt
    def find_transactions(self, prompt: str) -> pd.DataFrame:
        '''
        Tìm kiếm giao dịch trong Google Sheets dựa trên prompt.
        Sử dụng Google Gemini để trích xuất các trường dữ liệu có cấu trúc từ prompt.
        Trả về DataFrame chứa các giao dịch phù hợp.
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

        client = genai.Client(api_key="AIzaSyC8BMMSq5kms0_3rd9Fvl_dRI3WZ1IDbZc")

        system_prompt = """
            Extract structured fields from the following text. Return ONLY valid JSON (no extra text) with keys:
            - request_id
            - transaction_id
            - bank_account: the bank account number
            - bank_short_name: Short name of the bank. Examples: VCB (Vietcombank), BIDV (Ngân hàng Đầu tư và Phát triển Việt Nam), CTG (VietinBank), TCB (Techcombank), ACB (Ngân hàng Á Châu), STB (Sacombank), MB (MB Bank), TPB (TPBank), VIB (Ngân hàng Quốc Tế), MSB (Ngân hàng Hàng Hải), SCB (Ngân hàng Sài Gòn), LPB (LienVietPostBank), HDB (HDBank), EIB (Eximbank), DAB (DongABank), NAB (Nam A Bank), BVB (Ngân hàng Bảo Việt), BAB (Bac A Bank), AGR (Agribank), PVcomBank (Ngân hàng Đại Chúng Việt Nam), ABB (An Bình Bank), SHB (Ngân hàng Sài Gòn Hà Nội), VAB (VietABank), VPB (VPBank), OCB (OceanBank), GPB (GPBank), PGB (PG Bank), HLBVN (Hong Leong Bank Vietnam), PBVN (Public Bank Vietnam), Woori Bank (Woori Vietnam), CIMB (CIMB Vietnam), Shinhan Bank (Shinhan Vietnam), Standard Chartered (Standard Chartered Vietnam), HSBC (HSBC Vietnam), UOB (UOB Vietnam).
            - transaction_content: the content of the transaction
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
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"{system_prompt}\nPrompt: {prompt}"
            )
            raw_text = response.text
            
            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if not match:
                print("Không tìm thấy JSON trong response")
                return None
            structured_data = json.loads(match.group())

        except Exception as e:
            print("Lỗi gọi Gemini:", e)
            return None

        # Lấy dữ liệu từ Google Sheets
        worksheet = connect_to_google_sheets("1VNtJ1hAKZ8IvZQklGDV0OLE7vvJAzEfVD49kfkFNL_U", "PAYMENT_TRANSACTION_devTest")
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
        # Nếu không có kết quả, trả về DataFrame rỗng
        if df.empty:
            return None
        return df.reset_index(drop=True)
    
    # Tìm kiếm hóa đơn trong Google Sheets TAX_TRANSACTION
    def find_tax_transactions(self, prompt: str) -> pd.DataFrame:
        '''
        Tìm kiếm hóa đơn trong Google Sheets TAX_TRANSACTION dựa trên prompt.
        Sử dụng Google Gemini để trích xuất các trường dữ liệu có cấu trúc từ prompt.
        Trả về DataFrame chứa các hóa đơn phù hợp.
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

        client = genai.Client(api_key="AIzaSyC8BMMSq5kms0_3rd9Fvl_dRI3WZ1IDbZc")

        system_prompt = """
            Extract structured fields from the following text. Return ONLY valid JSON (no extra text) with keys:
            - request_id
            - contract_no: the contract number
            - serial_no: the serial number of the invoice
            - invoice_no: the invoice number
            - invoice_signal: the signal of the invoice 
            - invoice_date: format YYYY-MM-DD (Purchase date or invoice date)
            - invoice_description: 
            - buyer: the buyer's name
            - seller: the seller's name
            - invoice_amount_wo_vat: amount as number
            - vat_amount: amount as number
            - total_amount: amount as number
            - push_date: format YYYY-MM-DD
            If a field is not mentioned, return null.
            Strictly no extra text, just pure JSON.
        """

        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=f"{system_prompt}\nPrompt: {prompt}"
            )
            raw_text = response.text
            print("Response from Gemini:", raw_text)
            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if not match:
                print("Không tìm thấy JSON trong response")
                return None
            structured_data = json.loads(match.group())

        except Exception as e:
            print("Lỗi gọi Gemini:", e)
            return None

        worksheet = connect_to_google_sheets("1VNtJ1hAKZ8IvZQklGDV0OLE7vvJAzEfVD49kfkFNL_U", "TAX_TRANSACTION")
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)

        for key, value in structured_data.items():
            if value is not None and value != '' and key in key_to_col:
                col = key_to_col[key]
                if col not in df.columns:
                    continue
                if key in ['invoice_amount_wo_vat', 'vat_amount', 'total_amount']:
                    try:
                        df = df[df[col].astype(float) == float(value)]
                    except:
                        continue
                elif col in ['INVOICE DATE', 'PUSH_DATE']:
                    df = df[df[col].astype(str).str.strip() == str(value).strip()]
                else:
                    df = df[df[col].astype(str).str.contains(str(value), case=False, na=False)]

        if df.empty: return None
        return df.reset_index(drop=True)

if __name__ == "__main__":
    agent = AIAgent()
    while True:
        user_input = input("Bạn: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            break
        transactions = agent.find_tax_transactions(user_input)
        if transactions is not None:
            print("Kết quả giao dịch:")
            print(transactions.to_string(index=False))
        else:
            print("Không tìm thấy giao dịch nào phù hợp.")
