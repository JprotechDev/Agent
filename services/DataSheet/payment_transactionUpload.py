from connect_googleSheet import connect_to_google_sheets
from gspread.exceptions import APIError, WorksheetNotFound, SpreadsheetNotFound
from google.auth.exceptions import GoogleAuthError
import pandas as pd
import datetime

def get_worksheet(spreadsheet_id:str=None, worksheet_name:str=None):
    """
    Kết nối và trả về worksheet từ Google Sheets dựa vào spreadsheet ID và tên worksheet.

    Args:
        spreadsheet_id (str): ID của Google Spreadsheet (lấy từ URL).
        worksheet_name (str): Tên của worksheet cần truy cập trong spreadsheet.

    Returns:
        gspread.Worksheet: Đối tượng worksheet đã kết nối, có thể thao tác như đọc, ghi, v.v.
    """
    return connect_to_google_sheets(spreadsheet_id, worksheet_name)

def checkdup(INVOICE_NO: str, SERIAL_NO: str, worksheet) -> bool:
    """
    Kiểm tra xem bản ghi với INVOICE_NO và SERIAL_NO đã tồn tại trong Google Sheet hay chưa.

    Args:
        INVOICE_NO (str): Mã số hóa đơn cần kiểm tra trùng lặp.
        SERIAL_NO (str): Số serial của hóa đơn cần kiểm tra trùng lặp.
        worksheet (gspread.Worksheet): Đối tượng worksheet đã kết nối đến Google Sheet.

    Returns:
        bool: 
            - True nếu đã tồn tại bản ghi trùng lặp (INVOICE_NO và SERIAL_NO).
            - False nếu chưa tồn tại bản ghi trùng.
    """
    if INVOICE_NO and SERIAL_NO:
        df = pd.DataFrame(worksheet.get_all_records())
        # Nếu là dữ liệu mới thì sẽ không kiểm tra
        if ('INVOICE NO' not in df.columns or df['INVOICE NO'].dropna().empty or
            'SERIAL NO' not in df.columns or df['SERIAL NO'].dropna().empty):
            return False
        
        duplicate = df[
            (df['INVOICE NO'].astype(str).str.strip() == INVOICE_NO.strip()) &
            (df['SERIAL NO'].astype(str).str.strip() == SERIAL_NO.strip())
        ]
        return True
    return False

def uploaddata(worksheet, request_id: str = '', transaction_id: str = '', bank_account: str = '',
               bank_short_name: str = '', transaction_content: str = '', invoice_no: str = '',
               serial_no: str = '', contract_no: str = '', project_id: str = '', money_amount: str = '', 
               transaction_date: str = '', sender: str = '', receiver: str = ''):
    """
    Upload một dòng dữ liệu giao dịch lên Google Sheet nếu chưa tồn tại bản ghi trùng lặp.

    Args:
        worksheet: Đối tượng worksheet (gspread.Worksheet) đã được kết nối.
        request_id (str): Mã yêu cầu từ hệ thống gọi API.
        transaction_id (str): Mã giao dịch ngân hàng.
        bank_account (str): Số tài khoản ngân hàng.
        bank_short_name (str): Tên viết tắt của ngân hàng (ví dụ: 'VCB', 'ACB').
        transaction_content (str): Nội dung chuyển khoản từ ngân hàng.
        invoice_no (str): Mã số hóa đơn.
        serial_no (str): Số serial của hóa đơn.
        contract_no (str): Số hợp đồng liên quan đến giao dịch.
        project_id (str): Mã dự án hoặc hệ thống liên quan.
        money_amount (str): Số tiền giao dịch.
        transaction_date (str): Ngày giao dịch (định dạng yyyy-mm-dd hoặc tương đương).
        sender (str): Tên người chuyển khoản.
        receiver (str): Tên người nhận tiền.
    
    Returns:
        Data push successful or Data push failed
    """
    try:
        if checkdup(invoice_no, serial_no, worksheet) == False:
            new_data = {
                'REQUEST_ID': request_id, 'TRANSACTION ID': transaction_id, 'BANK ACCOUNT': bank_account,
                'BANK SHORT NAME': bank_short_name, 'TRANSACTION CONTENT': transaction_content,
                'INVOICE NO': invoice_no, 'SERIAL NO': serial_no, 'CONTRACT_NO': contract_no,
                'PROJECT ID': project_id, 'MONEY AMOUNT': money_amount, 'TRANSACTION DATE': transaction_date,
                'SENDER': sender, 'RECEIVER': receiver,
                'PUSH DATE': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            df_append = pd.DataFrame([new_data])
            for _, row in df_append.iterrows():
                worksheet.append_row(row.tolist(), value_input_option='USER_ENTERED')
            print(f"Data push successful: INVOICE NO({invoice_no}) - SERIAL NO({serial_no})")
        else: print("Payment data already exists.")
    except SpreadsheetNotFound: print("Không tìm thấy Spreadsheet.")
    except WorksheetNotFound: print("Không tìm thấy Worksheet.")
    except APIError as e: print(f"API Error: {e}")
    except GoogleAuthError: print("Lỗi xác thực với Google.")
    except Exception as e: print(f"Lỗi khác: {e}")

# Gọi thử
worksheet = get_worksheet(spreadsheet_id = "1VNtJ1hAKZ8IvZQklGDV0OLE7vvJAzEfVD49kfkFNL_U",worksheet_name = "PAYMENT_TRANSACTION_devTest")
uploaddata(worksheet, invoice_no='INV001', serial_no='SR001')