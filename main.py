from flask import Flask
from routes.user.user_route import user
from routes.admin.admin_route import admin

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key' 


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s: %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Register Routes
app.register_blueprint(user)
app.register_blueprint(admin)


if __name__ == '__main__':
    app.run(debug=True)