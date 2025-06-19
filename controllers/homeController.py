from flask import render_template, redirect, url_for, session, jsonify, request
from . import home_bp
from functools import wraps
from services.encdec import Encdec
from services.auth import Auth
from services.requestJson import ChatInfo
from services.aiAgent import AiAgent
import os, base64, json, uuid
from datetime import datetime
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('loginAccount') or not session.get('idAccount'):
            # Nếu người dùng chưa đăng nhập, chuyển hướng đến trang đăng nhập
            return redirect(url_for('home.login'))
        return f(*args, **kwargs)
    return decorated_function

# Login with Authentication mail google
@home_bp.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        # Kiểm tra thông tin đăng nhập
        account = Auth.search_email_password(request.form.get('email'), request.form.get('password'))
        if account:
            print(account)
            # Lưu thông tin người dùng vào session
            session['loginAccount'] = True
            session['idAccount'] = account['IDACCOUNT']
            session['emailAccount'] = account['EMAIL']
            session['fullnameAccount'] = account['FULLNAME']
            if 'IMG' in account and account['IMG']: session['imgAccount'] = account['IMG']  
            return redirect(url_for('home.index'))
        else:
            # Nếu thông tin đăng nhập không hợp lệ, hiển thị thông báo lỗi
            return render_template('login.html', error='Email hoặc mật khẩu không hợp lệ')
    return render_template('login.html')

# Route mặc đinh cho người dùng
@home_bp.route('/', methods=['POST', 'GET'])
@login_required
def index():
    get_chat_info_list = ChatInfo.get_chat_info_list(session.get('emailAccount'))
    return render_template('index.html', get_chat_info_list=get_chat_info_list)

@home_bp.route('/chat/<file_token>', methods=['POST', 'GET'])
@login_required
def chat(file_token):
    get_chat_info_list = ChatInfo.get_chat_info_list(session.get('emailAccount'))
    chat_content = ChatInfo.get_chat_content(session.get('emailAccount'), file_token)
    return render_template('index.html', get_chat_info_list=get_chat_info_list, chat_content=chat_content, file_token=file_token)

@home_bp.route('/messenger', methods=['POST'])
@login_required
def messenger():
    if request.method == 'POST':
        # Lấy dữ liệu từ request
        file_token = request.form.get('file_token')
        messageContent = request.form.get('messageContent') # Nội dung tin nhắn
        fileContent = request.files.get('fileContent')

        # Đường dẫn thư mục
        base_dir = os.path.dirname(__file__)
        listchats_dir = os.path.join(base_dir, '..', 'static', 'listchats')
        imgs_dir = os.path.join(base_dir, '..', 'static', 'imgs')
        pdfs_dir = os.path.join(base_dir, '..', 'static', 'pdfs')

        # Tạo thư mục nếu chưa có
        for folder in [listchats_dir, imgs_dir, pdfs_dir]:
            if not os.path.exists(folder):
                os.makedirs(folder)

        # Nếu chưa có file_token, tạo mới và tạo file JSON với cấu trúc mặc định
        if not file_token:
            title_content=AiAgent.ask_general(f"{messageContent}. Trả về tiêu đề cho nội dung trên. Chỉ trả về tiêu đề, không trả lời gì khác, cũng không cần chào hỏi gì tôi.")
            print(title_content)  
            file_token = str(uuid.uuid4())
            file_path = os.path.join(listchats_dir, f"{file_token}.json")
            data = {
                "id_email": session.get('emailAccount'),  # Hoặc lấy từ form tùy bạn
                "title": title_content['content'],
                "description": "Cuộc trò chuyện mới",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "chat": []
            }
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        else:
            file_path = os.path.join(listchats_dir, f"{file_token}.json")
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else: return jsonify({"status": "error", "message": "File token không tồn tại."}), 400

        # Xử lý message mới (ưu tiên lưu file nếu có rồi đến text)
        messages_to_add = []

        if fileContent:
            filename = fileContent.filename
            extension = os.path.splitext(filename)[1].lower()
            if extension in ['.png', '.jpg', '.jpeg', '.gif']:
                save_folder = imgs_dir
                web_folder = 'imgs'
            else:
                save_folder = pdfs_dir
                web_folder = 'pdfs'

            save_filename = f"{uuid.uuid4()}{extension}"
            save_path = os.path.join(save_folder, save_filename)
            fileContent.save(save_path)
            message_path = f"{web_folder}/{save_filename}"

            messages_to_add.append({
                "sender": "user",
                "message": message_path,
                "type": "image" if web_folder == 'imgs' else "file",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })

        if messageContent:
            messages_to_add.append({
                "sender": "user",
                "message": messageContent,
                "type": "text",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })
            
            messages_to_add.append({
                "sender": "bot",
                "message": AiAgent.ask_general(f"{save_path if fileContent else '' + messageContent}"),
                "type": "text",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })

        # Thêm tất cả message vào JSON
        if messages_to_add:
            data['chat'].extend(messages_to_add)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        # Trả về thông tin file_token và dữ liệu mới thêm
        return redirect(url_for('home.chat', file_token=file_token))

    return jsonify({"status": "error", "message": "Invalid request"}), 400

# Route check-log
# @home_bp.route('/check-log', methods=['POST'])
@home_bp.route('/check-log')
@login_required
def check_log():
    get_chat_info_list = ChatInfo.get_chat_info_list(session.get('emailAccount'))
    return render_template('jpt_payment_transaction.html', get_chat_info_list=get_chat_info_list)

# Route role_manager
@home_bp.route('/role_manager')
@login_required
def role_manager():
    get_chat_info_list = ChatInfo.get_chat_info_list(session.get('emailAccount'))
    all_users = Auth.get_all_users() # Lấy tất cả người dùng từ Google Sheet
    return render_template('role_manager.html', get_chat_info_list=get_chat_info_list, all_users=all_users)

# Route role_manager
@home_bp.route('/setting')
@login_required
def setting():
    
    #Lấy token từ json
    requestJsonDataSheet =ChatInfo.requestJsonDataSheet() 
    #lấy dữ liệu từ json bankref
    requestJsonBankref  = ChatInfo.requestJsonBankref()
    get_chat_info_list = ChatInfo.get_chat_info_list(session.get('emailAccount'))
    return render_template('setting.html', get_chat_info_list=get_chat_info_list,requestJsonDataSheet=requestJsonDataSheet)

# Route delete_chat
@home_bp.route('/chat-delete/<file_token>', methods=['POST', 'GET'])
@login_required
def chat_delete(file_token):
    get_chat_info_list = ChatInfo.get_chat_info_list(session.get('emailAccount'))
    file_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'listchats', f"{file_token}.json")
    
    if os.path.exists(file_path):
        os.remove(file_path)
        return redirect(url_for('home.index'))
    else:
        return jsonify({"status": "error", "message": "File không tồn tại"}), 404

# Route logout
@home_bp.route('/logout')
def logout():
    # Xóa session khi người dùng đăng xuất
    session.clear()
    return redirect(url_for('home.login'))
