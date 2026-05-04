import secrets
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import bcrypt
import os
import time
import uuid
from threading import Lock
from dotenv import load_dotenv

load_dotenv('/var/www/nothard/telegram_bot/.env')

import logging

logging.basicConfig(level=logging.DEBUG)  # Установите уровень DEBUG для отладки
logger = logging.getLogger(__name__)

import redis

# Инициализация Redis-клиента
redis_host = os.getenv('REDIS_HOST', 'localhost')
redis_port = int(os.getenv('REDIS_PORT', 6379))
redis_password = os.getenv('REDIS_PASSWORD', '')

r = redis.StrictRedis(
    host=redis_host,
    port=redis_port,
    password=redis_password,
    decode_responses=True
)

# Загрузка переменных окружения из .env
load_dotenv()

app = Flask(__name__)

# Настройка CORS для разрешения запросов только с вашего домена
CORS(app, resources={r"/*": {"origins": "https://nothard.uz"}})

DB_PATH = '/var/www/nothard/telegram_bot/bot.db'
BOT_TOKEN = os.getenv('BOT_TOKEN')  # Получение токена из переменной окружения
BOT_USERNAME = os.getenv('BOT_USERNAME')  # Получение username бота
API_URL = os.getenv('API_URL')  # Например, "https://nothard.uz/api"

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не установлен в переменных окружения")
if not BOT_USERNAME:
    raise ValueError("BOT_USERNAME не установлен в переменных окружения")
if not API_URL:
    raise ValueError("API_URL не установлен в переменных окружения")

# Для хранения токенов авторизации
auth_tokens = {}
auth_tokens_lock = Lock()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_next_website_id():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT MAX(website_id) as max_id FROM users")
    result = cursor.fetchone()
    conn.close()
    return result['max_id'] + 1 if result['max_id'] is not None else 1

# In app.py

@app.route('/telegram_auth_request', methods=['POST'])
def telegram_auth_request():
    try:
        data = request.json
        action = data.get('action')
        website_id = data.get('website_id')  # Include website_id if needed

        if action not in ['auth', 'link']:
            return jsonify({"error": "Invalid action"}), 400

        token_prefix = 'auth_' if action == 'auth' else 'link_'
        token = token_prefix + secrets.token_urlsafe(16)

        # Prepare token data
        token_data = {
            'authenticated': 'False'
        }
        if action == 'link':
            if not website_id:
                return jsonify({"error": "website_id is required for linking"}), 400
            token_data['website_id'] = str(website_id)

        # Store the token data in Redis with an expiration
        r.hmset(token, token_data)
        r.expire(token, 300)  # Expires in 5 minutes

        return jsonify({'token': token}), 200

    except Exception as e:
        app.logger.error(f"Error in telegram_auth_request: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/check_telegram_auth', methods=['POST'])
def check_telegram_auth():
    try:
        data = request.json
        logger.debug(f"Received data for check_telegram_auth: {data}")
        login_token = data.get('login_token')

        if not login_token:
            logger.warning("Login token missing in request")
            return jsonify({"error": "Login token is required"}), 400

        login_token_key = f'login_token_{login_token}'
        token_data = r.hgetall(login_token_key)

        if not token_data:
            logger.warning(f"Login token not found or expired: {login_token}")
            return jsonify({"error": "Invalid or expired login token"}), 400

        user_id = token_data.get('user_id')
        expires_at = float(token_data.get('expires_at', 0))

        if time.time() > expires_at:
            r.delete(login_token_key)
            logger.warning(f"Login token has expired: {login_token}")
            return jsonify({"error": "Login token has expired"}), 400

        # Удаляем токен после использования
        r.delete(login_token_key)

        return jsonify({"user_id": user_id}), 200

    except Exception as e:
        logger.error(f"Error in validate_login_token: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/telegram_auth_confirm', methods=['POST'])
def telegram_auth_confirm():
    try:
        data = request.get_json()
        logger.debug(f"Received data: {data}")
        token = data.get('token')
        user_id = data.get('user_id')

        if not token or not user_id:
            logger.warning("Token and/or user_id missing in request")
            return jsonify({"error": "Token and user_id are required"}), 400

        token_data = r.hgetall(token)

        if not token_data:
            logger.warning(f"Token not found or expired: {token}")
            return jsonify({"error": "Invalid or expired token"}), 400

        authenticated = token_data.get('authenticated')
        if authenticated == 'True':
            logger.warning(f"Token already used: {token}")
            return jsonify({"error": "Token already used"}), 400

        # Обновляем данные токена
        r.hset(token, 'authenticated', 'True')
        r.hset(token, 'user_id', user_id)

        conn = get_db_connection()
        cursor = conn.cursor()

        if token.startswith('auth_'):
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user = cursor.fetchone()
            if user:
                # Преобразуем данные пользователя в словарь и исключаем password_hash
                user_profile = {
                    "user_id": user["user_id"],
                    "name": user["name"],
                    "phone": user["phone"],
                    "email": user["email"],
                    "website_id": user["website_id"],
                    "bonuses": user["bonuses"] if "bonuses" in user.keys() else 0,
                    "language": user["language"]  # Убедитесь, что поле 'language' присутствует
                }
                is_new_user = False

                # Генерируем login_token
                login_token = secrets.token_urlsafe(16)
                login_token_key = f"login_token_{login_token}"
                login_token_data = {
                    'user_id': user_id,
                    'expires_at': time.time() + 300  # Токен действует 5 минут
                }
                r.hset(login_token_key, mapping=login_token_data)
                r.expire(login_token_key, 300)

                conn.close()

                logger.debug(f"Authorization successful for user_id: {user_id}, login_token: {login_token}")

                return jsonify({
                    "message": "Authorization successful",
                    "login_token": login_token,
                    "user_profile": user_profile
                }), 200
            else:
                logger.warning(f"User not found for user_id: {user_id}")
                return jsonify({"error": "User not found"}), 404

        elif token.startswith('link_'):
            # Логика связывания
            website_id = token_data.get('website_id')
            if not website_id:
                logger.warning("Website ID not found in token data")
                return jsonify({"error": "Website ID not found in token data"}), 400

            website_id = int(website_id)
            cursor.execute("UPDATE users SET user_id = ? WHERE website_id = ?", (user_id, website_id))
            conn.commit()

            # Получаем обновленный профиль пользователя
            cursor.execute("SELECT * FROM users WHERE website_id = ?", (website_id,))
            user = cursor.fetchone()
            user_profile = {
                "user_id": user["user_id"],
                "name": user["name"],
                "phone": user["phone"],
                "email": user["email"],
                "website_id": user["website_id"],
                "bonuses": user["bonuses"] if "bonuses" in user.keys() else 0,
                "language": user["language"]
            }
            is_new_user = False

            logger.debug(f"Linking successful for user_id: {user_id}, website_id: {website_id}")

        else:
            logger.warning(f"Invalid token prefix: {token}")
            return jsonify({"error": "Invalid token prefix"}), 400

        conn.close()

        return jsonify({
            "message": "Authorization successful",
            "is_new_user": is_new_user,
            "user_profile": user_profile  # Включаем данные профиля пользователя, если необходимо
        }), 200

    except Exception as e:
        logger.error(f"Error in telegram_auth_confirm: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/test', methods=['GET'])
def test_endpoint():
    return jsonify({"message": "API is working"}), 200
    
@app.route('/validate_login_token', methods=['POST'])
def validate_login_token():
    try:
        data = request.json
        login_token = data.get('login_token')

        if not login_token:
            return jsonify({"error": "Login token is required"}), 400

        login_token_key = f'login_token_{login_token}'
        token_data = r.hgetall(login_token_key)

        if not token_data:
            return jsonify({"error": "Invalid or expired login token"}), 400

        user_id = token_data.get('user_id')
        expires_at = float(token_data.get('expires_at', 0))

        if time.time() > expires_at:
            r.delete(login_token_key)
            return jsonify({"error": "Login token has expired"}), 400

        # Удаляем токен после использования
        r.delete(login_token_key)

        return jsonify({"user_id": user_id}), 200

    except Exception as e:
        app.logger.error(f"Error in validate_login_token: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/update_profile', methods=['POST'])
def update_profile():
    try:
        data = request.json
        user_id = data.get('user_id')  # Telegram user_id
        name = data.get('name')
        phone = data.get('phone')
        email = data.get('email')

        if not user_id or not name or not phone or not email:
            return jsonify({"error": "user_id, name, phone, and email are required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"error": "User not found"}), 404

        # Update user profile
        cursor.execute("""
            UPDATE users
            SET name = ?, phone = ?, email = ?
            WHERE user_id = ?
        """, (name, phone, email, user_id))
        conn.commit()

        return jsonify({"message": "Profile updated successfully"}), 200

    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    phone = data.get('phone')
    email = data.get('email')
    password = data.get('password')

    if not all([name, phone, email, password]):
        return jsonify({"error": "All fields are required"}), 400

    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Check if user exists
        cursor.execute("SELECT * FROM users WHERE email = ? OR phone = ?", (email, phone))
        existing_user = cursor.fetchone()

        if existing_user:
            if existing_user['password_hash']:
                return jsonify({"error": "User with this email or phone already exists"}), 400
            else:
                # Update existing user with password_hash and website_id
                website_id = get_next_website_id()
                cursor.execute("""
                    UPDATE users
                    SET password_hash = ?, website_id = ?
                    WHERE user_id = ?
                """, (hashed_password, website_id, existing_user['user_id']))
                conn.commit()
                return jsonify({"message": "User registered successfully", "website_id": website_id}), 200
        else:
            # Create new user
            website_id = get_next_website_id()
            cursor.execute("""
                INSERT INTO users (name, phone, email, password_hash, website_id)
                VALUES (?, ?, ?, ?, ?)
            """, (name, phone, email, hashed_password, website_id))
            conn.commit()
            return jsonify({"message": "User registered successfully", "website_id": website_id}), 201

    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if user and user['password_hash'] and bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return jsonify({
                "message": "Login successful",
                "user_id": user['user_id'],        # Может быть NULL, если зарегистрирован только через Telegram
                "website_id": user['website_id'],
                "role": user['role'] if user['role'] else 'user',
                "name": user['name']
            }), 200
        else:
            return jsonify({"error": "Invalid email or password"}), 401
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()


@app.route('/profile/<int:user_id>', methods=['GET'])
def get_profile(user_id):
    """
    Возвращает профиль пользователя по user_id.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT user_id, name, phone, email, website_id, bonuses FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()

        if user:
            profile_data = {
                "user_id": user["user_id"],
                "name": user["name"],
                "phone": user["phone"],
                "email": user["email"],
                "website_id": user["website_id"],
                "bonuses": user["bonuses"] if "bonuses" in user.keys() else 0
            }
            return jsonify(profile_data), 200
        else:
            return jsonify({"error": "User not found"}), 404
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# CRM API Endpoints

@app.route('/api/students', methods=['GET'])
def get_students():
    """Получение списка студентов для админа или агентства"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        user_id = request.args.get('user_id')
        user_role = request.args.get('user_role', 'admin')
        agency_id = request.args.get('agency_id')
        
        if user_role == 'admin':
            # Админ видит всех неархивированных студентов
            cursor.execute('''
                SELECT s.*, a.name as agency_name 
                FROM students s 
                LEFT JOIN agencies a ON s.agency_id = a.agency_id 
                WHERE (s.archived IS NULL OR s.archived = 0)
                ORDER BY s.created_at DESC
            ''')
        elif user_role == 'agency' and agency_id:
            # Агентство видит только своих неархивированных студентов
            cursor.execute('''
                SELECT s.*, a.name as agency_name 
                FROM students s 
                LEFT JOIN agencies a ON s.agency_id = a.agency_id 
                WHERE s.agency_id = ? AND (s.archived IS NULL OR s.archived = 0)
                ORDER BY s.created_at DESC
            ''', (agency_id,))
        else:
            return jsonify({"error": "Недостаточно прав доступа"}), 403
            
        students = [dict(row) for row in cursor.fetchall()]
        return jsonify({"students": students}), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/students', methods=['POST'])
def create_student():
    """Создание нового студента"""
    data = request.json
    required_fields = ['first_name', 'last_name']
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Не все обязательные поля заполнены"}), 400
    
    # Проверяем и очищаем необязательные поля - пустые строки заменяем на None
    def clean_field(field_name):
        value = data.get(field_name)
        return value if value and value.strip() else None
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO students (first_name, last_name, date_of_birth, nationality, 
                                passport_number, email, phone, telegram_username, 
                                emergency_contact, emergency_phone, university, city, 
                                course, start_date, end_date, agency_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['first_name'], data['last_name'], clean_field('date_of_birth'),
            clean_field('nationality'), clean_field('passport_number'), clean_field('email'),
            clean_field('phone'), clean_field('telegram_username'), clean_field('emergency_contact'),
            clean_field('emergency_phone'), clean_field('university'), data.get('city', 'London'),
            clean_field('course'), clean_field('start_date'), clean_field('end_date'), 
            data.get('agency_id')
        ))
        
        student_id = cursor.lastrowid
        conn.commit()
        
        return jsonify({
            "message": "Студент успешно создан",
            "student_id": student_id
        }), 201
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/service-requests', methods=['GET'])
def get_service_requests():
    """Получение заявок на услуги"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        student_id = request.args.get('student_id')
        user_role = request.args.get('user_role', 'admin')
        user_id = request.args.get('user_id')
        agency_id = request.args.get('agency_id')
        runner_id = request.args.get('runner_id')
        
        if student_id:
            # Заявки конкретного студента
            cursor.execute('''
                SELECT sr.*, s.first_name, s.last_name, s.email as student_email,
                       st.name as service_name, st.description as service_description,
                       a.name as agency_name, u.name as runner_name
                FROM service_requests sr
                JOIN students s ON sr.student_id = s.student_id
                JOIN service_types st ON sr.service_type_id = st.service_type_id
                LEFT JOIN agencies a ON sr.agency_id = a.agency_id
                LEFT JOIN users u ON sr.runner_id = u.user_id
                WHERE sr.student_id = ?
                ORDER BY sr.created_at DESC
            ''', (student_id,))
        elif user_role == 'admin':
            # Админ видит все заявки неархивированных студентов
            cursor.execute('''
                SELECT sr.*, s.first_name, s.last_name, s.email as student_email,
                       st.name as service_name, st.description as service_description,
                       a.name as agency_name, u.name as runner_name
                FROM service_requests sr
                JOIN students s ON sr.student_id = s.student_id
                JOIN service_types st ON sr.service_type_id = st.service_type_id
                LEFT JOIN agencies a ON sr.agency_id = a.agency_id
                LEFT JOIN users u ON sr.runner_id = u.user_id
                WHERE (s.archived IS NULL OR s.archived = 0)
                ORDER BY sr.created_at DESC
            ''')
        elif user_role == 'agency' and agency_id:
            # Агентство видит заявки своих неархивированных студентов
            cursor.execute('''
                SELECT sr.*, s.first_name, s.last_name, s.email as student_email,
                       st.name as service_name, st.description as service_description,
                       a.name as agency_name, u.name as runner_name
                FROM service_requests sr
                JOIN students s ON sr.student_id = s.student_id
                JOIN service_types st ON sr.service_type_id = st.service_type_id
                LEFT JOIN agencies a ON sr.agency_id = a.agency_id
                LEFT JOIN users u ON sr.runner_id = u.user_id
                WHERE sr.agency_id = ? AND (s.archived IS NULL OR s.archived = 0)
                ORDER BY sr.created_at DESC
            ''', (agency_id,))
        elif user_role == 'runner' and runner_id:
            # Раннер видит назначенные ему заявки неархивированных студентов
            cursor.execute('''
                SELECT sr.*, s.first_name, s.last_name, s.email as student_email,
                       st.name as service_name, st.description as service_description,
                       a.name as agency_name, u.name as runner_name
                FROM service_requests sr
                JOIN students s ON sr.student_id = s.student_id
                JOIN service_types st ON sr.service_type_id = st.service_type_id
                LEFT JOIN agencies a ON sr.agency_id = a.agency_id
                LEFT JOIN users u ON sr.runner_id = u.user_id
                WHERE (sr.runner_id = ? OR sr.status = 'new') AND (s.archived IS NULL OR s.archived = 0)
                ORDER BY sr.created_at DESC
            ''', (runner_id,))
        else:
            return jsonify({"error": "Недостаточно прав доступа"}), 403
            
        requests_data = [dict(row) for row in cursor.fetchall()]
        return jsonify({"requests": requests_data}), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/service-requests', methods=['POST'])
def create_service_request():
    """Создание новой заявки на услугу"""
    data = request.json
    required_fields = ['student_id', 'service_type_id', 'title']
    
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Не все обязательные поля заполнены"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO service_requests (student_id, agency_id, service_type_id, title, 
                                        description, priority, price, scheduled_date, 
                                        location, notes, created_by, payment_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['student_id'], data.get('agency_id'), data['service_type_id'],
            data['title'], data.get('description'), data.get('priority', 'medium'),
            data.get('price', 0), data.get('scheduled_date'), data.get('location'),
            data.get('notes'), data.get('created_by'), 'unpaid'
        ))
        
        request_id = cursor.lastrowid
        
        # Получаем название выбранной услуги/пакета
        cursor.execute('SELECT name FROM service_types WHERE service_type_id = ?', (data['service_type_id'],))
        service_result = cursor.fetchone()
        
        if service_result:
            service_name = service_result['name']
            
            # Если это пакет, создаем задачи для всех услуг в пакете
            if service_name.startswith('Пакет'):
                cursor.execute('SELECT service_name FROM package_services WHERE package_name = ?', (service_name,))
                package_services = cursor.fetchall()
                
                # Создаем задачу для каждой услуги в пакете
                for service in package_services:
                    cursor.execute('''
                        INSERT INTO tasks (request_id, service_name, status, created_at, updated_at)
                        VALUES (?, ?, 'waiting', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ''', (request_id, service['service_name']))
            else:
                # Для индивидуальной услуги создаем одну задачу
                cursor.execute('''
                    INSERT INTO tasks (request_id, service_name, status, created_at, updated_at)
                    VALUES (?, ?, 'waiting', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ''', (request_id, service_name))
        
        conn.commit()
        
        return jsonify({
            "message": "Заявка успешно создана",
            "request_id": request_id
        }), 201
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/service-requests/<int:request_id>/tasks', methods=['GET'])
def get_request_tasks(request_id):
    """Получение всех задач для заявки"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT task_id, service_name, status, created_at, updated_at
            FROM tasks 
            WHERE request_id = ?
            ORDER BY task_id
        ''', (request_id,))
        
        tasks = cursor.fetchall()
        
        return jsonify({
            "tasks": [dict(task) for task in tasks]
        }), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/tasks/<int:task_id>/status', methods=['PUT'])
def update_task_status(task_id):
    """Обновление статуса задачи"""
    data = request.json
    new_status = data.get('status')
    
    if not new_status:
        return jsonify({"error": "Статус обязателен"}), 400
    
    valid_statuses = ['waiting', 'in_progress', 'completed', 'cancelled']
    if new_status not in valid_statuses:
        return jsonify({"error": f"Недопустимый статус. Доступны: {', '.join(valid_statuses)}"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Проверяем существование задачи
        cursor.execute('SELECT task_id FROM tasks WHERE task_id = ?', (task_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Задача не найдена"}), 404
        
        # Обновляем статус
        cursor.execute('''
            UPDATE tasks 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE task_id = ?
        ''', (new_status, task_id))
        
        conn.commit()
        
        return jsonify({"message": "Статус задачи обновлен"}), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/service-requests/<int:request_id>/status', methods=['PUT'])
def update_request_status(request_id):
    """Обновление статуса заявки"""
    data = request.json
    new_status = data.get('status')
    changed_by = data.get('changed_by')
    comment = data.get('comment', '')
    
    if not new_status or not changed_by:
        return jsonify({"error": "Статус и ID пользователя обязательны"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Получаем текущий статус
        cursor.execute('SELECT status FROM service_requests WHERE request_id = ?', (request_id,))
        current_request = cursor.fetchone()
        
        if not current_request:
            return jsonify({"error": "Заявка не найдена"}), 404
        
        old_status = current_request['status']
        
        # Обновляем статус
        cursor.execute('''
            UPDATE service_requests 
            SET status = ?, updated_at = CURRENT_TIMESTAMP,
                completed_at = CASE WHEN ? = 'completed' THEN CURRENT_TIMESTAMP ELSE completed_at END
            WHERE request_id = ?
        ''', (new_status, new_status, request_id))
        
        # Добавляем запись в историю
        cursor.execute('''
            INSERT INTO request_status_history (request_id, old_status, new_status, changed_by, comment)
            VALUES (?, ?, ?, ?, ?)
        ''', (request_id, old_status, new_status, changed_by, comment))
        
        conn.commit()
        
        return jsonify({"message": "Статус успешно обновлен"}), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/service-types', methods=['GET'])
def get_service_types():
    """Получение всех типов услуг с учетом индивидуальных цен агентства"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        agency_id = request.args.get('agency_id')
        
        if agency_id:
            # Получаем услуги с индивидуальными ценами для агентства
            cursor.execute('''
                SELECT st.service_type_id, st.name, st.description, st.base_price, st.price_text, st.is_active,
                       COALESCE(asp.custom_price, st.base_price) as price,
                       COALESCE(asp.price_gbp, st.price_gbp) as price_gbp,
                       COALESCE(asp.price_usd, st.price_usd) as price_usd,
                       COALESCE(asp.price_uzs, st.price_uzs) as price_uzs,
                       CASE WHEN asp.custom_price IS NOT NULL THEN 1 ELSE 0 END as has_custom_price
                FROM service_types st
                LEFT JOIN agency_service_pricing asp ON st.service_type_id = asp.service_type_id 
                    AND asp.agency_id = ? AND asp.is_active = 1
                WHERE st.is_active = 1
                ORDER BY st.name
            ''', (agency_id,))
        else:
            # Стандартный список услуг
            cursor.execute('SELECT *, base_price as price, 0 as has_custom_price FROM service_types WHERE is_active = 1 ORDER BY name')
            
        service_types = [dict(row) for row in cursor.fetchall()]
        return jsonify({"service_types": service_types}), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/agencies', methods=['GET'])
def get_agencies():
    """Получение всех агентств"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT * FROM agencies ORDER BY name')
        agencies = [dict(row) for row in cursor.fetchall()]
        return jsonify({"agencies": agencies}), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/runners', methods=['GET'])
def get_runners():
    """Получение всех раннеров"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT user_id, name, phone, email FROM users WHERE role = "runner"')
        runners = [dict(row) for row in cursor.fetchall()]
        return jsonify({"runners": runners}), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/assign-runner', methods=['POST'])
def assign_runner():
    """Назначение раннера на заявку"""
    data = request.json
    request_id = data.get('request_id')
    runner_id = data.get('runner_id')
    assigned_by = data.get('assigned_by')
    
    if not all([request_id, runner_id, assigned_by]):
        return jsonify({"error": "Все поля обязательны"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE service_requests 
            SET runner_id = ?, status = 'assigned', updated_at = CURRENT_TIMESTAMP
            WHERE request_id = ?
        ''', (runner_id, request_id))
        
        # Добавляем в историю
        cursor.execute('''
            INSERT INTO request_status_history (request_id, old_status, new_status, changed_by, comment)
            VALUES (?, 'new', 'assigned', ?, 'Назначен раннер')
        ''', (request_id, assigned_by))
        
        conn.commit()
        
        return jsonify({"message": "Раннер назначен успешно"}), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# API для админ-панели

@app.route('/api/admin/full-data', methods=['GET'])
def get_admin_full_data():
    """Получение полных данных для админ-панели"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Получаем всех пользователей с правильными ID
        cursor.execute('''
            SELECT u.id, 
                   u.user_id as telegram_id, 
                   u.name, 
                   u.phone, 
                   u.email, 
                   u.role, 
                   u.bonuses, 
                   u.language,
                   CASE 
                       WHEN u.password_hash IS NOT NULL THEN 'Сайт' 
                       WHEN u.user_id IS NOT NULL THEN 'Telegram' 
                       ELSE 'Неизвестно' 
                   END as registration_method,
                   datetime('now') as created_at
            FROM users u
            ORDER BY u.id DESC
        ''')
        users = [dict(row) for row in cursor.fetchall()]
        
        # Получаем студентов с информацией об агентстве
        cursor.execute('''
            SELECT s.*, a.name as agency_name
            FROM students s
            LEFT JOIN agencies a ON s.agency_id = a.agency_id
            ORDER BY s.created_at DESC
        ''')
        students = [dict(row) for row in cursor.fetchall()]
        
        # Получаем заявки на услуги
        cursor.execute('''
            SELECT sr.*, s.first_name, s.last_name, st.description as service_description,
                   a.name as agency_name, u.name as runner_name
            FROM service_requests sr
            LEFT JOIN students s ON sr.student_id = s.student_id
            LEFT JOIN service_types st ON sr.service_type_id = st.service_type_id
            LEFT JOIN agencies a ON sr.agency_id = a.agency_id
            LEFT JOIN users u ON sr.runner_id = u.id
            ORDER BY sr.created_at DESC
        ''')
        requests = [dict(row) for row in cursor.fetchall()]
        
        # Получаем агентства
        cursor.execute('''
            SELECT a.*, u.name as contact_user_name, u.email as contact_email, u.phone as contact_phone
            FROM agencies a
            LEFT JOIN users u ON a.user_id = u.id
            ORDER BY a.created_at DESC
        ''')
        agencies = [dict(row) for row in cursor.fetchall()]
        
        # Получаем последние заказы
        cursor.execute('''
            SELECT o.*, u.name as user_name, u.phone as user_phone
            FROM orders o
            LEFT JOIN users u ON (o.user_id = u.user_id OR o.user_id = u.id)
            ORDER BY o.order_date DESC
            LIMIT 50
        ''')
        orders = [dict(row) for row in cursor.fetchall()]
        
        # Получаем задачи
        cursor.execute('''
            SELECT t.*, sr.student_id, s.first_name, s.last_name
            FROM tasks t
            LEFT JOIN service_requests sr ON t.request_id = sr.request_id
            LEFT JOIN students s ON sr.student_id = s.student_id
            ORDER BY t.created_at DESC
            LIMIT 50
        ''')
        tasks = [dict(row) for row in cursor.fetchall()]
        
        # Получаем доходы
        cursor.execute('''
            SELECT i.*, o.user_id as order_user_id
            FROM income i
            LEFT JOIN orders o ON i.order_id = o.order_id
            ORDER BY i.income_date DESC
            LIMIT 30
        ''')
        income = [dict(row) for row in cursor.fetchall()]
        
        # Получаем расходы
        cursor.execute('''
            SELECT e.*, o.user_id as order_user_id
            FROM expenses e
            LEFT JOIN orders o ON e.order_id = o.order_id
            ORDER BY e.expense_date DESC
            LIMIT 30
        ''')
        expenses = [dict(row) for row in cursor.fetchall()]
        
        return jsonify({
            "users": users,
            "students": students,
            "requests": requests,
            "agencies": agencies,
            "orders": orders,
            "tasks": tasks,
            "income": income,
            "expenses": expenses
        }), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# API для работы с индивидуальными ценами агентств

@app.route('/api/agency-pricing', methods=['GET'])
def get_agency_pricing():
    """Получение индивидуальных цен агентства"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        agency_id = request.args.get('agency_id')
        if not agency_id:
            return jsonify({"error": "agency_id is required"}), 400
        
        cursor.execute('''
            SELECT asp.*, st.name, st.description, st.base_price,
                   st.price_gbp as base_price_gbp, st.price_usd as base_price_usd, st.price_uzs as base_price_uzs
            FROM agency_service_pricing asp
            JOIN service_types st ON asp.service_type_id = st.service_type_id
            WHERE asp.agency_id = ? AND asp.is_active = 1
            ORDER BY st.name
        ''', (agency_id,))
        
        pricing = [dict(row) for row in cursor.fetchall()]
        return jsonify({"agency_pricing": pricing}), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/agency-pricing', methods=['POST'])
def set_agency_pricing():
    """Установка индивидуальной цены агентства на услугу"""
    data = request.json
    agency_id = data.get('agency_id')
    service_type_id = data.get('service_type_id')
    custom_price = data.get('custom_price')
    
    if not all([agency_id, service_type_id, custom_price]):
        return jsonify({"error": "Все поля обязательны"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO agency_service_pricing 
            (agency_id, service_type_id, custom_price)
            VALUES (?, ?, ?)
        ''', (agency_id, service_type_id, custom_price))
        
        conn.commit()
        return jsonify({"message": "Цена успешно установлена"}), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/workflow-statuses/<int:service_type_id>', methods=['GET'])
def get_workflow_statuses(service_type_id):
    """Получение статусов workflow для конкретного типа услуги"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT * FROM service_workflow_statuses 
            WHERE service_type_id = ? AND is_active = 1
            ORDER BY order_sequence
        ''', (service_type_id,))
        
        statuses = [dict(row) for row in cursor.fetchall()]
        return jsonify({"workflow_statuses": statuses}), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/request-files', methods=['GET'])
def get_request_files():
    """Получение файлов для заявки"""
    request_id = request.args.get('request_id')
    if not request_id:
        return jsonify({"error": "request_id is required"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT rf.*, u.name as uploaded_by_name
            FROM request_files rf
            LEFT JOIN users u ON rf.uploaded_by = u.id
            WHERE rf.request_id = ?
            ORDER BY rf.uploaded_at DESC
        ''', (request_id,))
        
        files = [dict(row) for row in cursor.fetchall()]
        return jsonify({"request_files": files}), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/custom-services', methods=['GET'])
def get_custom_services():
    """Получение кастомных услуг агентства"""
    agency_id = request.args.get('agency_id')
    if not agency_id:
        return jsonify({"error": "agency_id is required"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT * FROM agency_custom_services 
            WHERE agency_id = ? AND is_active = 1
            ORDER BY service_name
        ''', (agency_id,))
        
        services = [dict(row) for row in cursor.fetchall()]
        return jsonify({"custom_services": services}), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/custom-services', methods=['POST'])
def create_custom_service():
    """Создание кастомной услуги для агентства"""
    data = request.json
    agency_id = data.get('agency_id')
    service_name = data.get('service_name')
    service_description = data.get('service_description')
    price = data.get('price')
    
    if not all([agency_id, service_name, price]):
        return jsonify({"error": "Название услуги, агентство и цена обязательны"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO agency_custom_services 
            (agency_id, service_name, service_description, price)
            VALUES (?, ?, ?, ?)
        ''', (agency_id, service_name, service_description, price))
        
        service_id = cursor.lastrowid
        conn.commit()
        
        return jsonify({
            "message": "Кастомная услуга создана",
            "service_id": service_id
        }), 201
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# API для управления пользователями

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    """Полное обновление пользователя"""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Получаем текущие данные пользователя
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        current_user = dict(cursor.fetchone() or {})
        
        if not current_user:
            return jsonify({"error": "Пользователь не найден"}), 404
        
        # Строим динамический запрос обновления
        updates = []
        params = []
        
        # Проверяем и обновляем каждое поле
        if 'role' in data:
            role = data.get('role')
            if role and role in ['student', 'agency', 'runner', 'admin']:
                updates.append('role = ?')
                params.append(role)
        
        if 'name' in data and data.get('name'):
            updates.append('name = ?')
            params.append(data.get('name'))
        
        if 'email' in data and data.get('email'):
            updates.append('email = ?')
            params.append(data.get('email'))
        
        if 'phone' in data and data.get('phone'):
            updates.append('phone = ?')
            params.append(data.get('phone'))
        
        if 'bonuses' in data:
            updates.append('bonuses = ?')
            params.append(data.get('bonuses', 0))
        
        if 'user_id' in data:  # Telegram ID
            updates.append('user_id = ?')
            params.append(data.get('user_id'))
        
        if not updates:
            return jsonify({"error": "Нет данных для обновления"}), 400
        
        # Выполняем обновление
        params.append(user_id)
        query = f'UPDATE users SET {", ".join(updates)} WHERE id = ?'
        cursor.execute(query, params)
        
        conn.commit()
        return jsonify({"message": "Пользователь обновлен"}), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# Для совместимости с существующим кодом
@app.route('/api/users/<int:user_id>/role', methods=['PUT'])
def update_user_role(user_id):
    """Обновление роли пользователя (совместимость)"""
    data = request.json
    new_role = data.get('role')
    
    if not new_role or new_role not in ['student', 'agency', 'runner', 'admin']:
        return jsonify({"error": "Неверная роль"}), 400
    
    return update_user(user_id)


# API для управления агентствами

@app.route('/api/agencies', methods=['GET', 'POST'])
def manage_agencies():
    """Получение списка агентств или создание нового"""
    if request.method == 'GET':
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT a.*, u.name as contact_user_name, u.email as contact_email
                FROM agencies a
                LEFT JOIN users u ON a.user_id = u.id
                ORDER BY a.created_at DESC
            ''')
            agencies = [dict(row) for row in cursor.fetchall()]
            return jsonify({"agencies": agencies}), 200
            
        except sqlite3.Error as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()
    
    elif request.method == 'POST':
        data = request.json
        name = data.get('name')
        description = data.get('description', '')
        user_email = data.get('user_email')
        user_password = data.get('user_password')
        user_name = data.get('user_name')
        user_phone = data.get('user_phone', '')
        
        if not all([name, user_email, user_password, user_name]):
            return jsonify({"error": "Все обязательные поля должны быть заполнены"}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Проверяем уникальность email
            cursor.execute('SELECT id FROM users WHERE email = ?', (user_email,))
            if cursor.fetchone():
                return jsonify({"error": "Пользователь с таким email уже существует"}), 400
            
            # Хешируем пароль
            hashed_password = bcrypt.hashpw(user_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            # Создаем пользователя
            cursor.execute('''
                INSERT INTO users (name, email, phone, role, password_hash, bonuses, language)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_name, user_email, user_phone, 'agency', hashed_password, 0, 'ru'))
            
            user_id = cursor.lastrowid
            
            # Создаем агентство
            cursor.execute('''
                INSERT INTO agencies (name, description, user_id, created_at)
                VALUES (?, ?, ?, datetime('now'))
            ''', (name, description, user_id))
            
            agency_id = cursor.lastrowid
            conn.commit()
            
            return jsonify({"message": "Агентство создано", "agency_id": agency_id}), 201
            
        except sqlite3.Error as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()

@app.route('/api/agencies/<int:agency_id>', methods=['PUT', 'DELETE'])
def update_delete_agency(agency_id):
    """Обновление или удаление агентства"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'PUT':
        data = request.json
        
        try:
            # Получаем текущие данные агентства
            cursor.execute('SELECT * FROM agencies WHERE agency_id = ?', (agency_id,))
            current_agency = dict(cursor.fetchone() or {})
            
            if not current_agency:
                return jsonify({"error": "Агентство не найдено"}), 404
            
            # Обновляем данные агентства
            updates = []
            params = []
            
            if 'name' in data and data.get('name'):
                updates.append('name = ?')
                params.append(data.get('name'))
            
            if 'description' in data:
                updates.append('description = ?')
                params.append(data.get('description', ''))
            
            if updates:
                params.append(agency_id)
                query = f'UPDATE agencies SET {", ".join(updates)} WHERE agency_id = ?'
                cursor.execute(query, params)
            
            # Если переданы данные пользователя, обновляем их
            user_updates = {}
            for field in ['name', 'email', 'phone']:
                if f'user_{field}' in data and data.get(f'user_{field}'):
                    user_updates[field] = data.get(f'user_{field}')
            
            if user_updates and current_agency.get('user_id'):
                user_update_parts = []
                user_params = []
                for field, value in user_updates.items():
                    user_update_parts.append(f'{field} = ?')
                    user_params.append(value)
                
                user_params.append(current_agency['user_id'])
                user_query = f'UPDATE users SET {", ".join(user_update_parts)} WHERE id = ?'
                cursor.execute(user_query, user_params)
            
            conn.commit()
            return jsonify({"message": "Агентство обновлено"}), 200
            
        except sqlite3.Error as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()
    
    elif request.method == 'DELETE':
        try:
            cursor.execute('DELETE FROM agencies WHERE agency_id = ?', (agency_id,))
            
            if cursor.rowcount == 0:
                return jsonify({"error": "Агентство не найдено"}), 404
            
            conn.commit()
            return jsonify({"message": "Агентство удалено"}), 200
            
        except sqlite3.Error as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()

# API для управления ценами агентств

@app.route('/api/agencies/<int:agency_id>/pricing', methods=['GET', 'POST', 'PUT'])
def manage_agency_pricing(agency_id):
    """Управление ценами агентства"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'GET':
        try:
            cursor.execute('''
                SELECT asp.*, st.name as service_name, st.description,
                       st.price_gbp as base_price_gbp, st.price_usd as base_price_usd, st.price_uzs as base_price_uzs
                FROM agency_service_pricing asp
                JOIN service_types st ON asp.service_type_id = st.service_type_id
                WHERE asp.agency_id = ?
            ''', (agency_id,))
            pricing = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute('''
                SELECT * FROM agency_custom_services 
                WHERE agency_id = ?
            ''', (agency_id,))
            custom_services = [dict(row) for row in cursor.fetchall()]
            
            return jsonify({
                "pricing": pricing,
                "custom_services": custom_services
            }), 200
            
        except sqlite3.Error as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()
    
    elif request.method == 'POST':
        data = request.json
        service_type_id = data.get('service_type_id')
        price_gbp = data.get('price_gbp')
        price_usd = data.get('price_usd')
        
        if not all([service_type_id, price_gbp, price_usd]):
            return jsonify({"error": "Все поля обязательны"}), 400
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO agency_service_pricing 
                (agency_id, service_type_id, price_gbp, price_usd, price_uzs, custom_price, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, datetime('now'))
            ''', (agency_id, service_type_id, price_gbp, price_usd, data.get('price_uzs'), price_gbp))
            
            conn.commit()
            return jsonify({"message": "Цена установлена"}), 201
            
        except sqlite3.Error as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()

@app.route('/api/agencies/<int:agency_id>/custom-services', methods=['POST'])
def add_agency_custom_service(agency_id):
    """Добавление кастомной услуги для агентства"""
    data = request.json
    service_name = data.get('service_name')
    description = data.get('description', '')
    price_gbp = data.get('price_gbp')
    price_usd = data.get('price_usd')
    
    if not all([service_name, price_gbp, price_usd]):
        return jsonify({"error": "Название и цены обязательны"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO agency_custom_services 
            (agency_id, service_name, description, price_gbp, price_usd, created_at)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        ''', (agency_id, service_name, description, price_gbp, price_usd))
        
        conn.commit()
        return jsonify({"message": "Кастомная услуга добавлена"}), 201
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# API для управления студентами

@app.route('/api/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    """Обновление данных студента"""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Получаем текущие данные студента
        cursor.execute('SELECT * FROM students WHERE student_id = ?', (student_id,))
        current_student = dict(cursor.fetchone() or {})
        
        if not current_student:
            return jsonify({"error": "Студент не найден"}), 404
        
        # Строим динамический запрос обновления
        updates = []
        params = []
        
        # Проверяем и обновляем каждое поле
        if 'first_name' in data and data.get('first_name'):
            updates.append('first_name = ?')
            params.append(data.get('first_name'))
        
        if 'last_name' in data:
            updates.append('last_name = ?')
            params.append(data.get('last_name') if data.get('last_name') else None)
        
        if 'email' in data:
            updates.append('email = ?')
            params.append(data.get('email') if data.get('email') else None)
        
        if 'phone' in data:
            updates.append('phone = ?')
            params.append(data.get('phone') if data.get('phone') else None)
            
        if 'date_of_birth' in data:
            updates.append('date_of_birth = ?')
            params.append(data.get('date_of_birth') if data.get('date_of_birth') else None)
            
        if 'nationality' in data:
            updates.append('nationality = ?')
            params.append(data.get('nationality') if data.get('nationality') else None)
            
        if 'university' in data:
            updates.append('university = ?')
            params.append(data.get('university') if data.get('university') else None)
            
        if 'city' in data and data.get('city'):
            updates.append('city = ?')
            params.append(data.get('city'))
            
        if 'accommodation_type' in data:
            updates.append('accommodation_type = ?')
            params.append(data.get('accommodation_type'))
            
        if 'budget_min' in data:
            updates.append('budget_min = ?')
            params.append(data.get('budget_min'))
            
        if 'budget_max' in data:
            updates.append('budget_max = ?')
            params.append(data.get('budget_max'))
        
        if not updates:
            return jsonify({"error": "Нет данных для обновления"}), 400
        
        # Выполняем обновление
        params.append(student_id)
        query = f'UPDATE students SET {", ".join(updates)} WHERE student_id = ?'
        cursor.execute(query, params)
        
        conn.commit()
        return jsonify({"message": "Данные студента обновлены"}), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    """Удаление студента"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Проверяем, есть ли активные заявки у студента
        cursor.execute('''
            SELECT title, status FROM service_requests 
            WHERE student_id = ? AND status NOT IN ('completed', 'cancelled')
        ''', (student_id,))
        
        active_requests = cursor.fetchall()
        
        if active_requests:
            request_details = []
            for req in active_requests:
                request_details.append(f'"{req[0]}" (статус: {req[1]})')
            
            return jsonify({
                "error": f"Нельзя удалить студента с активными заявками ({len(active_requests)} заявок). Активные заявки: {', '.join(request_details)}. Сначала завершите или отмените заявки."
            }), 400
        
        # Удаляем студента
        cursor.execute('DELETE FROM students WHERE student_id = ?', (student_id,))
        
        if cursor.rowcount == 0:
            return jsonify({"error": "Студент не найден"}), 404
            
        conn.commit()
        return jsonify({"message": "Студент успешно удален"}), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/service-requests/<int:request_id>', methods=['DELETE'])
def delete_service_request(request_id):
    """Удаление заявки"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Удаляем заявку
        cursor.execute('DELETE FROM service_requests WHERE request_id = ?', (request_id,))
        
        if cursor.rowcount == 0:
            return jsonify({"error": "Заявка не найдена"}), 404
            
        conn.commit()
        return jsonify({"message": "Заявка успешно удалена"}), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/service-requests/<int:request_id>', methods=['PUT'])
def update_service_request(request_id):
    """Обновление заявки"""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Получаем текущие данные заявки
        cursor.execute('SELECT * FROM service_requests WHERE request_id = ?', (request_id,))
        current_request = dict(cursor.fetchone() or {})
        
        if not current_request:
            return jsonify({"error": "Заявка не найдена"}), 404
        
        # Строим динамический запрос обновления
        updates = []
        params = []
        
        # Проверяем и обновляем каждое поле
        if 'title' in data and data.get('title'):
            updates.append('title = ?')
            params.append(data.get('title'))
        
        if 'description' in data:
            updates.append('description = ?')
            params.append(data.get('description'))
            
        if 'status' in data and data.get('status'):
            valid_statuses = ['new', 'assigned', 'in_progress', 'completed', 'cancelled']
            if data.get('status') in valid_statuses:
                updates.append('status = ?')
                params.append(data.get('status'))
        
        if 'priority' in data and data.get('priority'):
            valid_priorities = ['low', 'medium', 'high', 'urgent']
            if data.get('priority') in valid_priorities:
                updates.append('priority = ?')
                params.append(data.get('priority'))
        
        if 'price' in data:
            updates.append('price = ?')
            params.append(data.get('price'))
            
        if 'location' in data:
            updates.append('location = ?')
            params.append(data.get('location'))
            
        if 'notes' in data:
            updates.append('notes = ?')
            params.append(data.get('notes'))
            
        if 'scheduled_date' in data:
            updates.append('scheduled_date = ?')
            params.append(data.get('scheduled_date'))
            
        if 'runner_id' in data:
            updates.append('runner_id = ?')
            params.append(data.get('runner_id'))
        
        if 'payment_status' in data and data.get('payment_status'):
            valid_payment_statuses = ['paid', 'unpaid', 'partial']
            if data.get('payment_status') in valid_payment_statuses:
                updates.append('payment_status = ?')
                params.append(data.get('payment_status'))
        
        if not updates:
            return jsonify({"error": "Нет данных для обновления"}), 400
        
        # Выполняем обновление
        params.append(request_id)
        query = f'UPDATE service_requests SET {", ".join(updates)} WHERE request_id = ?'
        cursor.execute(query, params)
        
        conn.commit()
        return jsonify({"message": "Заявка обновлена"}), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/service-requests/<int:request_id>/payment-status', methods=['PUT'])
def update_payment_status(request_id):
    """Обновление статуса оплаты заявки"""
    data = request.json
    payment_status = data.get('payment_status')
    
    if not payment_status:
        return jsonify({"error": "payment_status обязательное поле"}), 400
    
    valid_statuses = ['paid', 'unpaid', 'partial']
    if payment_status not in valid_statuses:
        return jsonify({"error": f"Недопустимый статус оплаты. Разрешены: {', '.join(valid_statuses)}"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Проверяем существование заявки
        cursor.execute('SELECT request_id FROM service_requests WHERE request_id = ?', (request_id,))
        if not cursor.fetchone():
            return jsonify({"error": "Заявка не найдена"}), 404
        
        # Обновляем статус оплаты
        cursor.execute('''
            UPDATE service_requests 
            SET payment_status = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE request_id = ?
        ''', (payment_status, request_id))
        
        conn.commit()
        
        # Получаем обновленную информацию
        cursor.execute('SELECT title, payment_status FROM service_requests WHERE request_id = ?', (request_id,))
        updated_request = cursor.fetchone()
        
        return jsonify({
            "message": f"Статус оплаты обновлен на '{payment_status}'",
            "request_id": request_id,
            "title": updated_request['title'] if updated_request else None,
            "payment_status": updated_request['payment_status'] if updated_request else None
        }), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# API для управления недвижимостью

@app.route('/api/tasks/<int:task_id>/properties', methods=['GET'])
def get_task_properties(task_id):
    """Получение всех объектов недвижимости для задачи"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT property_id, property_url, property_title, property_address, 
                   property_rent, property_description, status, is_selected_for_viewing,
                   viewing_date, viewing_notes, agent_notes, created_at, updated_at
            FROM property_listings 
            WHERE task_id = ?
            ORDER BY created_at DESC
        ''', (task_id,))
        
        properties = cursor.fetchall()
        
        return jsonify({
            "properties": [dict(prop) for prop in properties]
        }), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/tasks/<int:task_id>/properties', methods=['POST'])
def add_task_property(task_id):
    """Добавление нового объекта недвижимости к задаче"""
    data = request.json
    
    required_fields = ['property_url']
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"Поле {field} обязательно"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Получаем информацию о задаче
        cursor.execute('''
            SELECT sr.request_id, sr.student_id, sr.agency_id
            FROM tasks t
            JOIN service_requests sr ON t.request_id = sr.request_id
            WHERE t.task_id = ?
        ''', (task_id,))
        
        task_info = cursor.fetchone()
        if not task_info:
            return jsonify({"error": "Задача не найдена"}), 404
        
        # Добавляем объект недвижимости
        cursor.execute('''
            INSERT INTO property_listings (
                task_id, service_request_id, student_id, agency_id,
                property_url, property_title, property_address, 
                property_rent, property_description, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending')
        ''', (
            task_id, 
            task_info['request_id'],
            task_info['student_id'], 
            task_info['agency_id'],
            data.get('property_url'),
            data.get('property_title', ''),
            data.get('property_address', ''),
            data.get('property_rent', ''),
            data.get('property_description', ''),
        ))
        
        property_id = cursor.lastrowid
        conn.commit()
        
        return jsonify({
            "message": "Объект недвижимости добавлен", 
            "property_id": property_id
        }), 201
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/properties/<int:property_id>/status', methods=['PUT'])
def update_property_status(property_id):
    """Обновление статуса объекта недвижимости"""
    data = request.json
    new_status = data.get('status')
    
    if not new_status:
        return jsonify({"error": "Статус обязателен"}), 400
    
    valid_statuses = ['pending', 'contacted', 'available', 'unavailable', 
                     'viewing_scheduled', 'viewing_completed', 'selected', 'rejected']
    if new_status not in valid_statuses:
        return jsonify({"error": f"Недопустимый статус. Доступны: {', '.join(valid_statuses)}"}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Обновляем статус
        cursor.execute('''
            UPDATE property_listings 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE property_id = ?
        ''', (new_status, property_id))
        
        if cursor.rowcount == 0:
            return jsonify({"error": "Объект недвижимости не найден"}), 404
        
        conn.commit()
        return jsonify({"message": "Статус объекта недвижимости обновлен"}), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/properties/<int:property_id>', methods=['PUT'])
def update_property(property_id):
    """Обновление информации об объекте недвижимости"""
    data = request.json
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Проверяем существование объекта недвижимости
        cursor.execute('SELECT * FROM property_listings WHERE property_id = ?', (property_id,))
        current_property = cursor.fetchone()
        
        if not current_property:
            return jsonify({"error": "Объект недвижимости не найден"}), 404
        
        # Строим динамический запрос обновления
        updates = []
        params = []
        
        # Проверяем и обновляем каждое поле
        if 'property_url' in data:
            if not data.get('property_url').strip():
                return jsonify({"error": "URL недвижимости обязателен"}), 400
            updates.append('property_url = ?')
            params.append(data.get('property_url').strip())
        
        if 'property_title' in data:
            updates.append('property_title = ?')
            params.append(data.get('property_title', ''))
        
        if 'property_address' in data:
            updates.append('property_address = ?')
            params.append(data.get('property_address', ''))
        
        if 'property_rent' in data:
            updates.append('property_rent = ?')
            params.append(data.get('property_rent', ''))
        
        if 'property_description' in data:
            updates.append('property_description = ?')
            params.append(data.get('property_description', ''))
        
        if 'agent_notes' in data:
            updates.append('agent_notes = ?')
            params.append(data.get('agent_notes', ''))
        
        if not updates:
            return jsonify({"error": "Нет данных для обновления"}), 400
        
        # Добавляем updated_at
        updates.append('updated_at = CURRENT_TIMESTAMP')
        
        # Выполняем обновление
        params.append(property_id)
        query = f'UPDATE property_listings SET {", ".join(updates)} WHERE property_id = ?'
        cursor.execute(query, params)
        
        conn.commit()
        return jsonify({"message": "Информация о недвижимости обновлена"}), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/properties/<int:property_id>/select-viewing', methods=['PUT'])
def select_property_for_viewing(property_id):
    """Выбор объекта недвижимости для просмотра"""
    data = request.json
    is_selected = data.get('is_selected', False)
    viewing_date = data.get('viewing_date')
    viewing_notes = data.get('viewing_notes', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Получаем информацию об объекте и лимитах
        cursor.execute('''
            SELECT pl.task_id, t.service_name, sr.service_type_id
            FROM property_listings pl
            JOIN tasks t ON pl.task_id = t.task_id
            JOIN service_requests sr ON t.request_id = sr.request_id
            WHERE pl.property_id = ?
        ''', (property_id,))
        
        prop_info = cursor.fetchone()
        if not prop_info:
            return jsonify({"error": "Объект недвижимости не найден"}), 404
        
        if is_selected:
            # Проверяем лимиты просмотров
            cursor.execute('''
                SELECT COUNT(*) as selected_count
                FROM property_listings 
                WHERE task_id = ? AND is_selected_for_viewing = 1
            ''', (prop_info['task_id'],))
            
            selected_count = cursor.fetchone()['selected_count']
            
            # Определяем лимит по типу услуги
            is_package_housing = 'Пакет "Жилье"' in prop_info['service_name']
            max_viewings = 3 if is_package_housing else 1
            
            if selected_count >= max_viewings:
                return jsonify({
                    "error": f"Достигнут лимит просмотров ({max_viewings})"
                }), 400
        
        # Обновляем выбор для просмотра
        cursor.execute('''
            UPDATE property_listings 
            SET is_selected_for_viewing = ?, 
                viewing_date = ?,
                viewing_notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE property_id = ?
        ''', (is_selected, viewing_date, viewing_notes, property_id))
        
        conn.commit()
        return jsonify({"message": "Выбор для просмотра обновлен"}), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# API для архивации студентов

@app.route('/api/students/<int:student_id>/archive', methods=['PUT'])
def archive_student(student_id):
    """Архивация студента"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Проверяем существование студента
        cursor.execute('SELECT * FROM students WHERE student_id = ?', (student_id,))
        student = cursor.fetchone()
        
        if not student:
            return jsonify({"error": "Студент не найден"}), 404
        
        # Архивируем студента
        cursor.execute('''
            UPDATE students 
            SET archived = 1, archived_at = CURRENT_TIMESTAMP 
            WHERE student_id = ?
        ''', (student_id,))
        
        conn.commit()
        return jsonify({"message": "Студент успешно архивирован"}), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/students/<int:student_id>/unarchive', methods=['PUT'])
def unarchive_student(student_id):
    """Разархивация студента"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Проверяем существование студента
        cursor.execute('SELECT * FROM students WHERE student_id = ?', (student_id,))
        student = cursor.fetchone()
        
        if not student:
            return jsonify({"error": "Студент не найден"}), 404
        
        # Разархивируем студента
        cursor.execute('''
            UPDATE students 
            SET archived = 0, archived_at = NULL 
            WHERE student_id = ?
        ''', (student_id,))
        
        conn.commit()
        return jsonify({"message": "Студент успешно восстановлен из архива"}), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/students/archived', methods=['GET'])
def get_archived_students():
    """Получение всех архивированных студентов агентства"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        agency_id = request.args.get('agency_id')
        if not agency_id:
            return jsonify({"error": "agency_id is required"}), 400
        
        cursor.execute('''
            SELECT * FROM students 
            WHERE agency_id = ? AND archived = 1
            ORDER BY archived_at DESC
        ''', (agency_id,))
        
        students = [dict(row) for row in cursor.fetchall()]
        return jsonify({"students": students}), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/students/<int:student_id>/requests/archived', methods=['GET'])
def get_archived_student_requests(student_id):
    """Получение всех заявок архивированного студента"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Проверяем, что студент действительно архивирован
        cursor.execute('SELECT archived FROM students WHERE student_id = ?', (student_id,))
        student_result = cursor.fetchone()
        
        if not student_result or not student_result['archived']:
            return jsonify({"error": "Студент не найден или не архивирован"}), 404
        
        # Получаем все заявки студента (включая завершенные/отмененные)
        cursor.execute('''
            SELECT sr.*, s.first_name, s.last_name, s.email as student_email,
                   st.name as service_name, st.description as service_description,
                   a.name as agency_name, u.name as runner_name
            FROM service_requests sr
            JOIN students s ON sr.student_id = s.student_id
            JOIN service_types st ON sr.service_type_id = st.service_type_id
            LEFT JOIN agencies a ON sr.agency_id = a.agency_id
            LEFT JOIN users u ON sr.runner_id = u.user_id
            WHERE sr.student_id = ?
            ORDER BY sr.created_at DESC
        ''', (student_id,))
        
        requests_data = [dict(row) for row in cursor.fetchall()]
        return jsonify({"requests": requests_data}), 200
        
    except sqlite3.Error as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

# Дополнительные эндпоинты (например, для обновления профиля) можно добавить здесь

if __name__ == '__main__':
    app.run(debug=True)