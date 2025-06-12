import imaplib, email
from email.header import decode_header
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup

user, password = 'a5k47hoan@gmail.com', 'ffdt cwlh fwyb sfbv'
imap_url = 'imap.gmail.com'
con = imaplib.IMAP4_SSL(imap_url)
con.login(user, password)
con.select('Inbox')

def search(from_email, since=None, before=None):
    criteria = f'(FROM "{from_email}"'
    if since:  criteria += f' SINCE "{since}"'
    if before: criteria += f' BEFORE "{before}"'
    criteria += ')'
    return con.search(None, criteria)[1]

def get_emails(ids): return [con.fetch(num, '(RFC822)')[1] for num in ids[0].split()]

def decode_mime(s): return ''.join([(b.decode(enc or 'utf-8') if isinstance(b, bytes) else b) for b, enc in decode_header(s)])

def extract_text(raw):
    msg = email.message_from_bytes(raw)
    subject = decode_mime(msg.get('Subject', ''))
    sender = msg.get('From', '')
    try: date = parsedate_to_datetime(msg.get('Date')).strftime('%Y-%m-%d %H:%M:%S')
    except: date = msg.get('Date', '')
    
    body = ""
    parts = msg.walk() if msg.is_multipart() else [msg]
    for part in parts:
        if part.get_filename(): continue
        payload = part.get_payload(decode=True)
        if not payload: continue
        content = payload.decode(part.get_content_charset() or 'utf-8', errors='replace')
        if part.get_content_type() == 'text/plain': body = content.strip(); break
        elif part.get_content_type() == 'text/html' and not body: body = BeautifulSoup(content, 'html.parser').get_text().strip()
    return subject, sender, date, body

# 🔍 Lọc email theo địa chỉ và khoảng thời gian
email_from = 'mbebanking@mbbank.com.vn'
since_date = '01-Oct-2022'   # định dạng: dd-Mon-yyyy
before_date = None           # ví dụ: '10-Oct-2022'

for msg in get_emails(search(email_from, since=since_date, before=before_date))[::-1]:
    for part in msg:
        if isinstance(part, tuple):
            try:
                subject, sender, date, body = extract_text(part[1])
                print("========== EMAIL ==========")
                print(f"📨 From   : {sender}")
                print(f"🕒 Date   : {date}")
                print(f"📝 Subject: {subject}")
                print(f"📄 Content:\n{body}")
                print("===========================\n")
            except Exception as e: print(f"Error: {e}")
