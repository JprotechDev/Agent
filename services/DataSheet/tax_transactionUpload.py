from connect_googleSheet import connect_to_google_sheets
from gspread.exceptions import APIError, WorksheetNotFound, SpreadsheetNotFound
from google.auth.exceptions import GoogleAuthError
import pandas as pd
import datetime

def get_worksheet(spreadsheet_id: str = None, worksheet_name: str = None):
    """
    Kết nối và trả về worksheet từ Google Sheets dựa vào spreadsheet ID và tên worksheet.

    Args:
        spreadsheet_id (str): ID của Google Spreadsheet (lấy từ URL).
        worksheet_name (str): Tên của worksheet cần truy cập trong spreadsheet.

    Returns:
        gspread.Worksheet: Đối tượng worksheet đã kết nối, có thể thao tác như đọc, ghi, v.v.
    """
    return connect_to_google_sheets(spreadsheet_id, worksheet_name)

def check_tax_dup(invoice_no: str, serial_no: str, worksheet) -> bool:
    """
    Kiểm tra xem bản ghi với INVOICE_NO và SERIAL_NO đã tồn tại trong worksheet thuế hay chưa.

    Args:
        invoice_no (str): Mã số hóa đơn cần kiểm tra trùng lặp.
        serial_no (str): Số serial của hóa đơn cần kiểm tra trùng lặp.
        worksheet (gspread.Worksheet): Đối tượng worksheet đã kết nối.

    Returns:
        bool:
            - True nếu đã tồn tại bản ghi trùng.
            - False nếu chưa có bản ghi.
    """
    if invoice_no and serial_no:
        df = pd.DataFrame(worksheet.get_all_records())
        duplicate = df[
            (df['INVOICE NO'].astype(str).str.strip() == invoice_no.strip()) &
            (df['SERIAL NO'].astype(str).str.strip() == serial_no.strip())
        ]
        return not duplicate.empty
    return False

def upload_tax_data(worksheet, request_id: str = '', contract_no: str = '', serial_no: str = '', invoice_no: str = '',
                    invoice_signal: str = '', invoice_date: str = '', invoice_description: str = '',
                    buyer: str = '', seller: str = '', invoice_amount_wo_vat: str = '',
                    vat_amount: str = '', total_amount: str = ''):
    try:
        column_order = [
            'REQUEST_ID', 'CONTRACT_NO', 'SERIAL NO', 'INVOICE NO',
            'INVOICE SIGNAL', 'INVOICE DATE', 'INVOICE DESCRIPTION',
            'BUYER', 'SELLER', 'INVOICE AMOUNT_WO VAT',
            'VAT AMOUNT', 'TOTAL AMOUNT', 'PUSH_DATE'
        ]
        new_data = {
            'REQUEST_ID': request_id,
            'CONTRACT_NO': contract_no,
            'SERIAL NO': serial_no,
            'INVOICE NO': invoice_no,
            'INVOICE SIGNAL': invoice_signal,
            'INVOICE DATE': invoice_date,
            'INVOICE DESCRIPTION': invoice_description,
            'BUYER': buyer,
            'SELLER': seller,
            'INVOICE AMOUNT_WO VAT': invoice_amount_wo_vat,
            'VAT AMOUNT': vat_amount,
            'TOTAL AMOUNT': total_amount,
            'PUSH_DATE': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        df_append = pd.DataFrame([new_data], columns=column_order)  # Đảm bảo đúng thứ tự cột

        rows_to_append = df_append.values.tolist()
        worksheet.append_rows(rows_to_append, value_input_option='USER_ENTERED')

        print(f"Tax data pushed successfully: {invoice_no} - {serial_no}")
    except SpreadsheetNotFound:
        print("Không tìm thấy Spreadsheet.")
    except WorksheetNotFound:
        print("Không tìm thấy Worksheet.")
    except APIError as e:
        print(f"API Error: {e}")
    except GoogleAuthError:
        print("Lỗi xác thực với Google.")
    except Exception as e:
        print(f"Lỗi khác: {e}")


worksheet = get_worksheet(
    spreadsheet_id="1VNtJ1hAKZ8IvZQklGDV0OLE7vvJAzEfVD49kfkFNL_U",
    worksheet_name="TAX_TRANSACTION"
)

upload_tax_data(
    worksheet,
    request_id="REQ001",
    contract_no="C123",
    serial_no="SR002",
    invoice_no="INV002",
    invoice_signal="AA/23E",
    invoice_date="2025-05-13",
    invoice_description="Thanh toán phần mềm quản lý",
    buyer="Công ty ABC",
    seller="Công ty XYZ",
    invoice_amount_wo_vat="10000000",
    vat_amount="1000000",
    total_amount="11000000"
)
