# app/config.py
import os

class Config:
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or '123123123'
    SQLALCHEMY_DATABASE_URI = os.environ.get('MYSQL_MASTER_URI')
    MONGO_URI = os.environ.get('MONGO_DB_URI')
