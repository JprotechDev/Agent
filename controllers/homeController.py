from flask import render_template, redirect, url_for, session, jsonify, request, send_file
from . import home_bp
from functools import wraps
from services.encdec import Encdec
from services.auth import Auth
from services.requestJson import ChatInfo
from services.aiAgent import AiAgent
from services.chat_suggestions import ChatSuggestions
import os, base64, json, uuid
from datetime import datetime
from dotenv import load_dotenv

# Load biến môi trường từ file .env
load_dotenv()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('loginAccount') or not session.get('idAccount'):
            return redirect(url_for('home.login'))
        return f(*args, **kwargs)
    return decorated_function

# Login with Authentication mail google
@home_bp.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        account = Auth.search_email_password(request.form.get('email'), request.form.get('password'))
        if account:
            print(account)
            session['loginAccount'] = True
            session['idAccount'] = account['IDACCOUNT']
            session['emailAccount'] = account['EMAIL']
            session['fullnameAccount'] = account['FULLNAME']
            if 'IMG' in account and account['IMG']: session['imgAccount'] = account['IMG']
            return redirect(url_for('home.index'))
        else:
            return render_template('login.html', error='Email hoặc mật khẩu không hợp lệ')
    return render_template('login.html')

# Route mặc đinh cho người dùng
@home_bp.route('/', methods=['POST', 'GET'])
@login_required
def index():
    get_chat_info_list = ChatInfo.get_chat_info_list(session.get('emailAccount'))
    # Khi tạo chat mới, chắc chắn chưa có tin nhắn nào từ user
    has_user_messages = False
    return render_template('index.html', get_chat_info_list=get_chat_info_list, has_user_messages=has_user_messages)

@home_bp.route('/chat/<file_token>', methods=['POST', 'GET'])
@login_required
def chat(file_token):
    get_chat_info_list = ChatInfo.get_chat_info_list(session.get('emailAccount'))
    chat_content = ChatInfo.get_chat_content(session.get('emailAccount'), file_token)

    # Kiểm tra xem có tin nhắn nào từ "user" trong chat_content không
    has_user_messages = False
    if chat_content:
        for message in chat_content:
            if message.get('sender') == 'user':
                has_user_messages = True
                break

    return render_template('index.html', get_chat_info_list=get_chat_info_list, chat_content=chat_content, file_token=file_token, has_user_messages=has_user_messages)

@home_bp.route('/messenger', methods=['POST'])
@login_required
def messenger():
    if request.method == 'POST':
        file_token = request.form.get('file_token')
        messageContent = request.form.get('messageContent')
        fileContent = request.files.get('fileContent')

        base_dir = os.path.dirname(__file__)
        listchats_dir = os.path.join(base_dir, '..', 'static', 'listchats')
        imgs_dir = os.path.join(base_dir, '..', 'static', 'imgs')
        pdfs_dir = os.path.join(base_dir, '..', 'static', 'pdfs')

        for folder in [listchats_dir, imgs_dir, pdfs_dir]:
            if not os.path.exists(folder):
                os.makedirs(folder)

        if not file_token:
            title_content = AiAgent.ask_general(f"{messageContent}. Trả về tiêu đề cho nội dung trên. Chỉ trả về tiêu đề, không trả lời gì khác, cũng không cần chào hỏi gì tôi.")
            print(title_content)
            file_token = str(uuid.uuid4())
            file_path = os.path.join(listchats_dir, f"{file_token}.json")
            data = {
                "id_email": session.get('emailAccount'),
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

            # NOTE: Giả định AiAgent.ask_general trả về một dict có key 'content' hoặc string
            bot_response = AiAgent.ask_general(f"{save_path if fileContent else '' + messageContent}")
            bot_message_content = bot_response['content'] if isinstance(bot_response, dict) and 'content' in bot_response else bot_response

            messages_to_add.append({
                "sender": "bot",
                "message": bot_message_content,
                "type": "text",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })

        if messages_to_add:
            data['chat'].extend(messages_to_add)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        return redirect(url_for('home.chat', file_token=file_token))

    return jsonify({"status": "error", "message": "Invalid request"}), 400

# ROUTE MỚI ĐỂ LẤY GỢI Ý CHAT
@home_bp.route('/get_chat_suggestions', methods=['GET'])
@login_required
def get_chat_suggestions_route():
    # Lấy 5 gợi ý phổ biến từ các file chat JSON
    suggestions = ChatSuggestions.get_popular_suggestions(num_suggestions=5)
    return jsonify(suggestions)

# Route để tải xuống đoạn chat
@home_bp.route('/download_chat/<file_token>', methods=['GET'])
@login_required
def download_chat(file_token):
    chat_file_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'listchats', f"{file_token}.json")

    if not os.path.exists(chat_file_path):
        return "File chat không tồn tại.", 404

    # Lấy định dạng mong muốn từ query parameter
    output_format = request.args.get('format', 'txt').lower() # Mặc định là txt

    try:
        with open(chat_file_path, 'r', encoding='utf-8') as f:
            chat_data = json.load(f)

        chat_content = chat_data.get('chat', [])
        title = chat_data.get('title', 'Cuộc trò chuyện')

        if output_format == 'json':
            # Trả về file JSON gốc
            return send_file(chat_file_path, as_attachment=True, download_name=f"{title.replace(' ', '_')}_{file_token}.json", mimetype='application/json')
        elif output_format == 'txt':
            # Tạo nội dung TXT
            txt_content = f"Tiêu đề: {title}\n"
            txt_content += f"ID cuộc trò chuyện: {file_token}\n"
            txt_content += f"Thời gian tạo: {chat_data.get('timestamp', 'Không rõ')}\n\n"
            txt_content += "--- Nội dung cuộc trò chuyện ---\n\n"

            for message in chat_content:
                sender = message.get('sender', 'Unknown')
                msg = message.get('message', '')
                msg_type = message.get('type', 'text')
                timestamp = message.get('timestamp', '')

                # Định dạng timestamp cho dễ đọc
                try:
                    dt_object = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    formatted_timestamp = dt_object.strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    formatted_timestamp = timestamp # Giữ nguyên nếu không parse được

                if msg_type == 'text':
                    txt_content += f"[{formatted_timestamp}] {sender.upper()}: {msg}\n"
                elif msg_type == 'image':
                    txt_content += f"[{formatted_timestamp}] {sender.upper()}: [Đã gửi ảnh: {msg}]\n"
                elif msg_type == 'file':
                    txt_content += f"[{formatted_timestamp}] {sender.upper()}: [Đã gửi file: {msg}]\n"
                # Thêm xử lý cho các loại tin nhắn khác nếu có
            
            # Lưu nội dung TXT vào một file tạm thời
            temp_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'temp')
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            temp_txt_file_path = os.path.join(temp_dir, f"chat_{file_token}.txt")

            with open(temp_txt_file_path, 'w', encoding='utf-8') as f:
                f.write(txt_content)

            return send_file(temp_txt_file_path, as_attachment=True, download_name=f"{title.replace(' ', '_')}_{file_token}.txt", mimetype='text/plain')
        else:
            return "Định dạng không hợp lệ. Chỉ hỗ trợ 'txt' hoặc 'json'.", 400

    except Exception as e:
        print(f"Error downloading chat: {e}")
        return "Có lỗi xảy ra khi tải xuống chat.", 500

# Route check-log
@home_bp.route('/check-log')
@login_required
def check_log():
    get_chat_info_list = ChatInfo.get_chat_info_list(session.get('emailAccount'))
    return render_template('jpt_payment_transaction.html', get_chat_info_list=get_chat_info_list, has_user_messages=False)

# Route role_manager
@home_bp.route('/role_manager')
@login_required
def role_manager():
    get_chat_info_list = ChatInfo.get_chat_info_list(session.get('emailAccount'))
    all_users = Auth.get_all_users()
    current_user = Auth.find_user_by_email(session.get('emailAccount'))
    is_admin = 'admin' in current_user.get('roles', [])
    return render_template('role_manager.html', get_chat_info_list=get_chat_info_list, all_users=all_users, is_admin=is_admin, has_user_messages=False)

# Route xử lý thêm người dùng mới
@home_bp.route('/add-user', methods=['POST'])
@login_required
def add_user():
    data = request.get_json()
    fullname = data.get('fullname')
    email = data.get('email')
    password = data.get('password')

    if not fullname or not email or not password:
        return jsonify({"error": "Vui lòng nhập đầy đủ Họ và tên, Email và Mật khẩu."}), 400

    id_account = str(uuid.uuid4())

    success, message = Auth.add_new_user(id_account, fullname, email, password)

    if success:
        return jsonify({"message": message})
    else:
        return jsonify({"error": message}), 400

# Route xử lý cập nhật vai trò
@home_bp.route('/update-role', methods=['POST'])
@login_required
def update_role():
    data = request.get_json()
    email = data.get('email')
    role = data.get('role')
    checked = data.get('checked')

    if Auth.update_user_role(email, role, checked):
        return jsonify({"message": "Cập nhật vai trò thành công!"})
    return jsonify({"error": "Không thể cập nhật vai trò."}), 400

# Route xử lý tạm dừng/kích hoạt người dùng
@home_bp.route('/toggle-user', methods=['POST'])
@login_required
def toggle_user():
    data = request.get_json()
    email = data.get('email')
    if Auth.toggle_user_status(email):
        return jsonify({"message": "Cập nhật trạng thái người dùng thành công!"})
    return jsonify({"error": "Không thể cập nhật trạng thái người dùng."}), 400

# Route xử lý xóa người dùng
@home_bp.route('/delete-user', methods=['POST'])
@login_required
def delete_user_route():
    data = request.get_json()
    email = data.get('email')
    if Auth.delete_user(email):
        return jsonify({"message": "Xóa người dùng thành công!"})
    return jsonify({"error": "Không thể xóa người dùng."}), 400

# Route setting
@home_bp.route('/setting')
@login_required
def setting():
    requestJsonDataSheet =ChatInfo.requestJsonDataSheet()
    requestJsonBankref  = ChatInfo.requestJsonBankref()
    get_chat_info_list = ChatInfo.get_chat_info_list(session.get('emailAccount'))
    return render_template('setting.html', get_chat_info_list=get_chat_info_list, requestJsonDataSheet=requestJsonDataSheet, has_user_messages=False)

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
    session.clear()
    return redirect(url_for('home.login'))
