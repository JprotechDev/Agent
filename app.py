from controllers import home_bp
from dotenv import load_dotenv
from datetime import timedelta
from flask import Flask
import base64, os
import threading

# Load biến môi trường
load_dotenv()

app = Flask(__name__)
app.secret_key = base64.b64decode(os.getenv('SECRET_KEY')).decode('utf-8')
# Thiết lập thời gian tồn tại của session
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=300)  # Session hết hạn sau 30 phút
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024 # Đặt giới hạn kích thước file upload trong Flask

# Đăng ký Blueprint
app.register_blueprint(home_bp)

if __name__ == '__main__':
    
    app.run(host='127.0.0.1', port=5000, debug=True, threaded=True)
    