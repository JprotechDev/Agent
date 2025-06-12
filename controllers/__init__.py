from flask import Blueprint

# Khai báo các Blueprint
home_bp = Blueprint('home', __name__, url_prefix='/')

# Import các route từ các controller
from . import homeController