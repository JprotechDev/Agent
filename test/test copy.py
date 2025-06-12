import imaplib, email
from email.header import decode_header
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup  # pip install beautifulsoup4

user = 'a5k47hoan@gmail.com'
password = 'ffdt cwlh fwyb sfbv'
imap_url = 'imap.gmail.com'

# Kết nối IMAP
con = imaplib.IMAP4_SSL(imap_url)
con.login(user, password)
con.select('Inbox')

def search(key, value): return con.search(None, key, f'"{value}"')[1]

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
        charset = part.get_content_charset() or 'utf-8'
        content = payload.decode(charset, errors='replace')
        if part.get_content_type() == 'text/plain': body = content.strip(); break
        elif part.get_content_type() == 'text/html' and not body: body = BeautifulSoup(content, 'html.parser').get_text().strip()
    return subject, sender, date, body

# Lọc và in email
for msg in get_emails(search('FROM', 'mbebanking@mbbank.com.vn'))[::-1]:
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
