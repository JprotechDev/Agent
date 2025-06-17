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
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.detach(), encoding='utf-8')

    if request.method == 'POST':
        # Lấy dữ liệu từ request
        file_token = request.form.get('file_token')
        messageContent = request.form.get('messageContent')
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

        # Nếu chưa có file_token, tạo mới và tạo file JSON
        if not file_token:
            try:
                ai_title = AiAgent.ask_general(f"{messageContent}. Trả về tiêu đề cho nội dung trên. Chỉ trả về tiêu đề.")
                title_result = ai_title.get("content", "Cuộc trò chuyện mới")
            except Exception as e:
                print(f"Lỗi khi gọi AI để lấy tiêu đề: {e}")
                title_result = "Cuộc trò chuyện mới"

            file_token = str(uuid.uuid4())
            file_path = os.path.join(listchats_dir, f"{file_token}.json")
            data = {
                "id_email": session.get('emailAccount'),
                "title": title_result,
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
            else:
                return jsonify({"status": "error", "message": "File token không tồn tại."}), 400

        # Xử lý message mới
        messages_to_add = []

        save_path = ""
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

        # Message text từ người dùng
        if messageContent:
            messages_to_add.append({
                "sender": "user",
                "message": messageContent,
                "type": "text",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })

            try:
                full_message = f"{save_path if fileContent else ''} {messageContent}"
                ai_response = AiAgent.ask_general(full_message)
                ai_reply = ai_response.get("content", "Xin lỗi, tôi chưa có phản hồi.")
            except Exception as e:
                print(f"Lỗi AI trả lời: {e}")
                ai_reply = "Xin lỗi, đã xảy ra lỗi khi xử lý phản hồi."

            messages_to_add.append({
                "sender": "bot",
                "message": ai_reply,
                "type": "text",
                "timestamp": datetime.utcnow().isoformat() + "Z"
            })

        # Lưu lại JSON nếu có message
        if messages_to_add:
            data['chat'].extend(messages_to_add)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

        return redirect(url_for('home.chat', file_token=file_token))

    return jsonify({"status": "error", "message": "Invalid request"}), 400

# Route check-log
# @home_bp.route('/check-log', methods=['POST'])
@home_bp.route('/check-log')
@login_required
def check_log():
    get_chat_info_list = ChatInfo.get_chat_info_list(session.get('emailAccount'))
    return render_template('jpt_payment_transaction.html', get_chat_info_list=get_chat_info_list)

@home_bp.route('/role_manager')
@login_required
def role_manager():
    get_chat_info_list = ChatInfo.get_chat_info_list(session.get('emailAccount'))
    return render_template('role_manager.html', get_chat_info_list=get_chat_info_list)

# Cập nhật quyền người dùng (thêm hoặc xóa quyền)
@home_bp.route('/update-role', methods=['POST'])
@login_required
def update_role():
    data = request.get_json()
    email = data.get('email')
    role = data.get('role')

    if not email or not role:
        return jsonify({'error': 'Thiếu thông tin email hoặc quyền'}), 400

    try:
        ChatInfo.toggle_user_role(email, role)  # Toggle logic: thêm hoặc xóa quyền
        return jsonify({'message': f'Đã cập nhật quyền "{role}" cho {email}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Xóa người dùng
@home_bp.route('/delete-user', methods=['POST'])
@login_required
def delete_user():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'error': 'Thiếu email người dùng'}), 400

    try:
        ChatInfo.delete_user(email)
        return jsonify({'message': f'Đã xóa tài khoản {email}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Tạm dừng hoặc kích hoạt người dùng
@home_bp.route('/toggle-user', methods=['POST'])
@login_required
def toggle_user():
    data = request.get_json()
    email = data.get('email')

    if not email:
        return jsonify({'error': 'Thiếu email người dùng'}), 400

    try:
        new_status = ChatInfo.toggle_user_status(email)
        return jsonify({'message': f'Tài khoản {email} hiện tại đang ở trạng thái: {"Hoạt động" if new_status else "Tạm dừng"}'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route role_manager
@home_bp.route('/setting')
@login_required
def setting():
    
    #Lấy token từ json
    requestJsonDataSheet =ChatInfo.requestJsonDataSheet() 
    #lấy dữ liệu từ json bankref
    requestJsonBankref  = ChatInfo.requestJsonBankref()
    get_chat_info_list = ChatInfo.get_chat_info_list(session.get('emailAccount'))
    return render_template('setting.html', get_chat_info_list=get_chat_info_list,requestJsonDataSheet=requestJsonDataSheet,  requestJsonBankref=requestJsonBankref)

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

