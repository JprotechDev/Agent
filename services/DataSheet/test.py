from google.oauth2.service_account import Credentials
import gspread
import pandas as pd

# kết nối chương trình Python với Google Sheets
ss_cred_path = r'D:\Code\Python\AI\Agent_AI\JproChat\model-a5k47-0001-4022c4568150.json'
scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
creds = Credentials.from_service_account_file(ss_cred_path, scopes=scope)
gc = gspread.authorize(creds)

# Lấy dữ liệu xu hướng hiện có từ Sheet
spreadsheet_id = "1VNtJ1hAKZ8IvZQklGDV0OLE7vvJAzEfVD49kfkFNL_U"

# Kết nối book sheet
wks = gc.open_by_key(spreadsheet_id)

# Kết nối page sheet: PAYMENT_TRANSACTION_devTest
worksheet = wks.worksheet('PAYMENT_TRANSACTION_devTest')

# Lấy dữ liệu từ page sheet
df = pd.DataFrame(worksheet.get_all_records())
print(df)
print(f"Số dòng dữ liệu: {len(df)}")

'''
try:
    # Thêm sheet mới: test_sheet
    new_sheet = wks.add_worksheet('test_sheet', rows=1000, cols=26)

    # Đẩy dữ liệu từ page sheet PAYMENT_TRANSACTION_devTest sang test_sheet
    new_sheet.update([df.columns.values.tolist()] + df.values.tolist())
    print("Đẩy dữ liệu thành công")
except Exception as e:
    print(e)
'''

new_data = {
    'REQUEST_ID': ['REQ005'],
    'TRANSACTION ID': ['TXN1004'],
    'BANK ACCOUNT': ['111222333'],
    'BANK SHORT NAME': ['BIDV'],
    'TRANSACTION CONTENT': ['Thanh toán phí dịch vụ'],
    'INVOICE NO': ['INV004'],
    'CONTRACT_NO': ['CONT004'],
    'PROJECT ID': ['PRJ004'],
    'MONEY AMOUNT': [4300000],
    'TRANSACTION DATE': ['2024-05-13'],
    'SENDER': ['Pham Van D'],
    'RECEIVER': ['Công ty GHI']
}

# Update dữ liệu
df_append = pd.DataFrame(new_data)
for _, row in df_append.iterrows():
    worksheet.append_row(row.tolist(), value_input_option='USER_ENTERED')

print("Đã thêm dòng mới thành công!")

# Lấy dữ liệu ở dòng (hàng ngang) bất kì
row_data = worksheet.row_values(3) # Tính từ tiêu đề trở xuống theo số thứ tự  1, 2, 3
print(f"Dữ liệu ở dòng số 3\n{row_data}")

# Lấy dữ liệu ở cột dọc bất kì
column_data = worksheet.col_values(3)
print("Dữ liệu cột thứ 3:", column_data)

all_rows = worksheet.get_all_values()
last_row = all_rows[-1]  # Dòng cuối cùng có dữ liệu
print("Dữ liệu dòng cuối cùng:", last_row)

# theo tọa độ dòng dữ liệu
value = worksheet.cell(3, 2).value
print("Giá trị tại ô B3:", value)