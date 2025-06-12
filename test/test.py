import imaplib, email
from email.header import decode_header
from email.utils import parsedate_to_datetime
from bs4 import BeautifulSoup

user, pwd = 'a5k47hoan@gmail.com', 'ffdt cwlh fwyb sfbv'
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

# Thông tin lọc
email_from = 'mbebanking@mbbank.com.vn'
since_date, before_date = '01-Oct-2022', None

for msg in get_emails(search(email_from, since_date, before_date))[::-1]:
    for part in msg:
        if isinstance(part, tuple):
            try:
                s, f, d, b = extract(part[1])
                print("========== EMAIL ==========")
                print(f"📨 From   : {f}\n🕒 Date   : {d}\n📝 Subject: {s}\n📄 Content:\n{b}")
                print("===========================\n")
            except Exception as e: print(f"Error: {e}")
