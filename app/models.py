from app import db
from datetime import datetime

user_client_association = db.Table('user_client_association',
    db.Column('user_id', db.Integer, db.ForeignKey('user.user_id')),
    db.Column('client_id', db.Integer, db.ForeignKey('client.client_id')),
    db.UniqueConstraint('user_id', 'client_id', name='unique_user_client')
)

class User(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    clients = db.relationship('Client', secondary=user_client_association, backref='users', lazy=True)

    def add_client(self, client):
        if client not in self.clients:
            self.clients.append(client)
            db.session.commit()

class Client(db.Model):
    __tablename__ = 'client'
    client_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    client_name = db.Column(db.String(255), nullable=False)
    