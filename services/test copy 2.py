import pandas as pd
from google import genai
import json
import re
from DataSheet.connect_googleSheet import connect_to_google_sheets

class AIAgent:

    # Khởi tạo client tại thời điểm gọi hàm (tránh phải __init__)
    def PAYMENT_TRANSACTION(self, **kwargs) -> pd.DataFrame:
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
        worksheet = connect_to_google_sheets("1VNtJ1hAKZ8IvZQklGDV0OLE7vvJAzEfVD49kfkFNL_U", "PAYMENT_TRANSACTION_devTest")
        records = worksheet.get_all_records()
        df = pd.DataFrame(records)

        for key, value in kwargs.items():
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
        return df.reset_index(drop=True)

    def ai_find_transactions(self, prompt: str) -> pd.DataFrame:
        client = genai.Client(api_key="AIzaSyC8BMMSq5kms0_3rd9Fvl_dRI3WZ1IDbZc")

        system_prompt = """
            Extract structured fields from the following text. Return ONLY valid JSON (no extra text) with keys:
            - request_id
            - transaction_id
            - bank_account: the bank account number
            - bank_short_name: the short name of the bank
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
            print("Raw AI response:", raw_text)  # debug

            match = re.search(r"\{.*\}", raw_text, re.DOTALL)
            if not match:
                print("Không tìm thấy JSON trong response")
                return pd.DataFrame()
            json_str = match.group()
            structured_data = json.loads(json_str)

        except Exception as e:
            print("Lỗi gọi Gemini:", e)
            return pd.DataFrame()

        return self.PAYMENT_TRANSACTION(**structured_data)

if __name__ == "__main__":
    agent = AIAgent()
    prompt = "Tìm giao dịch với số tài khoản 111222338"
    df = agent.ai_find_transactions(prompt)
    print(df)
