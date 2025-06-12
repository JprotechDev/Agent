import imaplib, email
from email.header import decode_header
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from google import genai
import requests
import os
from datetime import datetime
import json

# Load biến môi trường
load_dotenv()

user, pwd = os.getenv('ADDRESS_EMAIL'), os.getenv('PASSWORD_EMAIL')
con = imaplib.IMAP4_SSL('imap.gmail.com'); con.login(user, pwd); con.select('Inbox')
search = lambda f, s=None, b=None: con.search(None, f'(FROM "{f}"' + (f' SINCE "{s}"' if s else '') + (f' BEFORE "{b}"' if b else '') + ')')[1]
get_emails = lambda ids: [con.fetch(num, '(RFC822)')[1] for num in ids[0].split()]
decode_mime = lambda s: ''.join([(b.decode(enc or 'utf-8') if isinstance(b, bytes) else b) for b, enc in decode_header(s)])

def extract(msg_raw):
    msg = email.message_from_bytes(msg_raw)
    subj, sender = decode_mime(msg.get('Subject', '')), msg.get('From', '')
    try: date = parsedate_to_datetime(msg.get('Date')).strftime('%Y-%m-%d %H:%M:%S')
    except: date = msg.get('Date', '')
    body = ""
    for part in (msg.walk() if msg.is_multipart() else [msg]):
        if part.get_filename(): continue
        payload = part.get_payload(decode=True)
        if not payload: continue
        text = payload.decode(part.get_content_charset() or 'utf-8', errors='replace')
        if part.get_content_type() == 'text/plain': body = text.strip(); break
        elif part.get_content_type() == 'text/html' and not body: body = BeautifulSoup(text, 'html.parser').get_text().strip()
    return subj, sender, date, body
def AiCheck(datacheck):
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    client = genai.Client(api_key=GOOGLE_API_KEY)
    prompt = (
        "You are a smart assistant. "
        "Extract only the available fields from the text. "
        "Display each on a single plain text line using the format FieldName: Value — for example, Sender name: NGUYEN VAN HOAN. "
        "Fields include: recipient name & account number, sender name, amount, transaction date, transaction content, bank, and status. "
        "Do not include labels like 'Field Name' or 'Value', and omit any missing fields. "
        f"Just show data and say nothing more. Input text:\n{datacheck}"
    )
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error: {str(e)}"

def AgentCheckMail(email_from:str, since_date:str, before_date:str):
    data = []
    ids = search(email_from, since_date, before_date)
    if not ids or not ids[0]:
        print(f"No emails found from {email_from} between {since_date} and {before_date}.")
        return json.dumps(data, indent=2, ensure_ascii=False)
    for msg in get_emails(ids)[::-1]:
        for part in msg:
            if isinstance(part, tuple):
                try:
                    s, f, d, b = extract(part[1])
                    datacheck = f"From: {f}\nDate: {d}\nSubject: {s}\nContent:\n{b}"
                    print("🔎 Checking email data:\n", datacheck)
                    Agent = AiCheck(datacheck)
                    print("💡 AI Extracted:\n", Agent)
                    data.append({"content": Agent})
                except Exception as e:
                    print(f"Error processing email: {e}")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    return json.dumps(data, indent=2, ensure_ascii=False)

# Gọi hàm kiểm tra email từ MB Bank
AgentCheckMail('hoang.luong@jprotech.com.vn', '01-Oct-2022', '10-Oct-2025')