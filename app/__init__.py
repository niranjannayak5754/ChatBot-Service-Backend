# app/__init__.py
from flask import Blueprint, Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_pymongo import PyMongo  # Import PyMongo for MongoDB integration
from app.config import Config
from flask_jwt_extended import JWTManager

jwt = JWTManager()
db = SQLAlchemy()
bcrypt = Bcrypt()
mongo = PyMongo()  # Initialize PyMongo for MongoDB

main = Blueprint('main', __name__)

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    bcrypt.init_app(app)
    mongo.init_app(app)  # Initialize PyMongo with your Flask app
    jwt.init_app(app)  # Assuming 'app' is your Flask application
    
    from app.routes import main
    app.register_blueprint(main)
    
    # Check if tables exist, and create them if not
    with app.app_context():
        from sqlalchemy import inspect

        inspector = inspect(db.engine)
        if not inspector.has_table('user') or not inspector.has_table('client'):
            db.create_all()

    return app
