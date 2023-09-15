from flask import Flask
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

#DUMMY LIST
users = []

app = Flask(__name__)

app.config['SECRET_KEY'] = 'b89f2cd1ff1b9950937c5a0453348f91'

bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

from app import routes