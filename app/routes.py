# app/routes.py
from flask import request, jsonify
from app.models import Client, User
from app import db, bcrypt, mongo
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from . import main
import requests
import os
from datetime import datetime


@main.route('/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify({'healthcheck': 'OK'}), 200

@main.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()

    if 'username' not in data or 'email' not in data or 'password' not in data or 'client_names' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    username = data['username']
    email = data['email']
    password = data['password']
    client_names = data['client_names']

    # Check if the username or email already exists
    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return jsonify({'error': 'Username or email already exists'}), 409

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    new_user = User(username=username, email=email, password=hashed_password)
    
    # Create a new client
    for c_name in client_names:
        # Check if the client already exists
        existing_client = Client.query.filter_by(client_name=c_name).first()

        if not existing_client:
            new_client = Client(client_name=c_name)
            new_user.clients.append(new_client)
        else:
            new_user.clients.append(existing_client)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

@main.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    username = data['username']
    password = data['password']

    user = User.query.filter_by(username=username).first()

    if user and bcrypt.check_password_hash(user.password, password):
        # Create an access token with user_id as identity
        access_token = create_access_token(identity=user.user_id)
        return jsonify({'message': 'Login successful', 'access_token': access_token})
    else:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    
@main.route('/start-chat', methods=['POST'])
@jwt_required()  # Requires a valid access token
def chatbot():
    data = request.get_json()

    if 'question' not in data or 'client_name' not in data:
        return jsonify({'error': 'Missing required fields'}), 400

    CHATGPT_KEY = os.environ.get('CHATGPT_KEY')
    question = data['question']
    client_name = data['client_name']

    openai_payload = {
        'model': 'gpt-3.5-turbo',
        'messages': [{"role": "user", "content": question}]
    }
    OPENAPI_BOT_URL = os.environ.get('OPENAPI_BOT_URL')
    # Make a request to OpenAI API
    response = requests.post(
        OPENAPI_BOT_URL,
        json=openai_payload,
        headers={
            'Authorization': f'Bearer {CHATGPT_KEY}',
            'Content-Type': 'application/json'
        }
    )

    if response.status_code == 200:
        assistant_response = response.json()['choices'][0]['message']['content']

        # Store conversation in MongoDB
        current_user_id = get_jwt_identity()
        new_message = {"question": question, "answer": assistant_response}

        # Check if the collection exists, create it if not
        if client_name not in mongo.db.list_collection_names():
            mongo.db.create_collection(client_name)
            # Check if the client already exists
            existing_client = Client.query.filter_by(client_name=client_name).first()

            if not existing_client:
                new_client = Client(client_name=client_name)
                db.session.add(new_client)
                db.session.commit()
                
        
        # Check if a conversation already exists for the user
        existing_conversation = mongo.db[client_name].find_one({"user_id": current_user_id})

        if existing_conversation:
            if 'messages' not in existing_conversation or not isinstance(existing_conversation['messages'], list):
                existing_conversation['messages'] = []
            
            existing_conversation['messages'].append(new_message)
            existing_conversation['timestamp'] = datetime.utcnow()

            # Update the existing conversation in the MongoDB collection
            mongo.db[client_name].update_one({"user_id": current_user_id}, {"$set": existing_conversation})
        else:
            # Create a new conversation if one doesn't exist
            new_conversation = {
                "user_id": current_user_id,
                "messages": [new_message],
                "timestamp": datetime.utcnow()
            }

            # Insert the new conversation into the MongoDB collection
            mongo.db[client_name].insert_one(new_conversation)

        # Return the assistant's response in the API response
        return jsonify({'assistant_response': assistant_response}), 200
    else:
        return jsonify({'error': 'Failed to get OpenAI completion'}), 500

    
