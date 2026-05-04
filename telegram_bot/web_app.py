# web_app.py

import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    UserMixin,
    current_user,
)
from bot.handlers.admin import get_user_id_by_order_id
from bot.utils.admin_functions import (
    DATABASE,
    extract_link_from_html,
    extract_title_from_html,
    get_admin_closed_tasks,
    get_admin_open_tasks,
    get_all_users,
    get_closed_order_tasks,
    get_open_order_tasks,
    get_order_by_id,
    update_order_status,
    get_all_feedbacks,
    get_order_subscribers,
    get_order_tasks,
    update_property_status,
    get_order_properties,
    add_order_event,
    delete_order_event,
    get_individual_services,
    get_task_by_id,
    get_individual_service_by_id,
    update_order_payment_status,
    get_all_orders,
    get_user_by_id,
    update_order_task_status,
    send_message_to_user,
    get_order_events,
    credit_bonus,
    delete_bonus,
    get_user_bonuses,
    get_user_profile,       
    update_user_profile,
    translate_status,
    search_users,
    search_orders,
    get_users,
    get_order_status_counts,
    get_current_order_status_counts,
    get_previous_order_status_counts
)
import logging
from bot.handlers.language import get_message
from config import ADMIN_PASSWORD, ADMIN_USERNAME, BOT_TOKEN, CSRF_SECRET, SECRET_KEY
from bot.utils.notificate import send_notification
from flask_wtf import CSRFProtect 

from datetime import datetime
import pytz
from html import escape

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['BOT_TOKEN'] = BOT_TOKEN
app.config['TELEGRAM_BOT_TOKEN'] = os.getenv('BOT_TOKEN')

# Инициализация CSRFProtect
csrf = CSRFProtect(app)

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin):
    def __init__(self, id, language='ru'):
        self.id = id
        self.name = f"Admin {id}"
        self.language = language  # Добавлен атрибут language с значением по умолчанию 'ru'

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Admin credentials
ADMIN_CREDENTIALS = {
    ADMIN_USERNAME: ADMIN_PASSWORD
}

@app.route('/admin/tasks')
@login_required
def view_admin_tasks():
    status = request.args.get('status', 'open')  # 'open' или 'closed'
    try:
        with sqlite3.connect('bot.db') as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            if status == 'open':
                c.execute("SELECT * FROM tasks WHERE status = 'task_status_in_progress'")
            elif status == 'closed':
                c.execute("SELECT * FROM tasks WHERE status = 'task_status_completed'")
            else:
                c.execute("SELECT * FROM tasks")
            tasks = [dict(row) for row in c.fetchall()]
        return render_template('admin_tasks.html', tasks=tasks, status=status)
    except Exception as e:
        logger.error(f"Ошибка при загрузке задач администраторов: {e}", exc_info=True)
        flash('Произошла ошибка при загрузке задач администраторов.', 'danger')
        return redirect(url_for('dashboard'))

@app.route('/property_requests')
@login_required
def view_property_requests():
    status = request.args.get('status', 'open')  # 'open' или 'closed'
    try:
        with sqlite3.connect('bot.db') as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            if status == 'open':
                c.execute("SELECT * FROM order_items WHERE status IN ('property_status_waiting_agent', 'property_status_going')")
            elif status == 'closed':
                c.execute("SELECT * FROM order_items WHERE status IN ('property_status_booked', 'property_status_cancelled', 'property_status_viewed', 'property_status_ready')")
            else:
                c.execute("SELECT * FROM order_items")
            property_requests = [dict(row) for row in c.fetchall()]
        return render_template('property_requests.html', property_requests=property_requests, status=status)
    except Exception as e:
        logger.error(f"Ошибка при загрузке запросов на недвижимость: {e}", exc_info=True)
        flash('Произошла ошибка при загрузке запросов на недвижимость.', 'danger')
        return redirect(url_for('dashboard'))

# Маршрут для добавления новой задачи администратору
@app.route('/add_admin_task', methods=['GET', 'POST'])
@login_required
def add_admin_task():
    try:
        if request.method == 'POST':
            description = request.form.get('description').strip()
            status = request.form.get('status')
            order_id = request.form.get('order_id')
            
            # Валидация данных
            if not description:
                flash('Описание задачи обязательно.', 'warning')
                return redirect(url_for('add_admin_task'))
            
            if status not in ['Не выполнено', 'Выполняется', 'Выполнено']:
                flash('Некорректный статус задачи.', 'warning')
                return redirect(url_for('add_admin_task'))
            
            # Преобразование статуса в формат базы данных
            status_map = {
                'Не выполнено': 'TaskStatusNotCompleted',
                'Выполняется': 'TaskStatusInProgress',
                'Выполнено': 'TaskStatusCompleted'
            }
            db_status = status_map.get(status, 'TaskStatusNotCompleted')
            
            # Проверка наличия order_id в таблице orders, если он указан
            if order_id:
                with sqlite3.connect('bot.db') as conn_check:
                    c_check = conn_check.cursor()
                    c_check.execute("SELECT order_id FROM orders WHERE order_id = ?", (order_id,))
                    order = c_check.fetchone()
                    if not order:
                        flash('Указанный Order ID не существует.', 'warning')
                        return redirect(url_for('add_admin_task'))
            
            with sqlite3.connect('bot.db') as conn:
                c = conn.cursor()
                c.execute("""
                    INSERT INTO tasks (description, status, order_id)
                    VALUES (?, ?, ?)
                """, (description, db_status, order_id if order_id else None))
                conn.commit()
            
            flash('Задача успешно добавлена.', 'success')
            return redirect(url_for('admin_tasks'))
        
        # GET запрос: отображение формы добавления задачи
        with sqlite3.connect('bot.db') as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT order_id FROM orders")
            orders = [row['order_id'] for row in c.fetchall()]
        
        return render_template('add_admin_task.html', orders=orders)
    except Exception as e:
        logger.error(f"Ошибка при добавлении задачи администратору: {e}")
        flash('Произошла ошибка при добавлении задачи.', 'danger')
        return redirect(url_for('admin_tasks'))

# Маршрут для обновления статуса задачи
@app.route('/update_admin_task/<int:task_id>', methods=['POST'])
@login_required
def update_admin_task(task_id):
    try:
        new_status = request.form.get('status')
        if new_status not in ['Не выполнено', 'Выполняется', 'Выполнено']:
            flash('Некорректный статус задачи.', 'warning')
            return redirect(url_for('admin_tasks'))
        
        status_map = {
            'Не выполнено': 'TaskStatusNotCompleted',
            'Выполняется': 'TaskStatusInProgress',
            'Выполнено': 'TaskStatusCompleted'
        }
        db_status = status_map.get(new_status, 'TaskStatusNotCompleted')
        
        closed_at = None
        if db_status == 'TaskStatusCompleted':
            closed_at = datetime.now()
        
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            if closed_at:
                c.execute("""
                    UPDATE tasks
                    SET status = ?, closed_at = ?
                    WHERE task_id = ?
                """, (db_status, closed_at, task_id))
            else:
                c.execute("""
                    UPDATE tasks
                    SET status = ?, closed_at = NULL
                    WHERE task_id = ?
                """, (db_status, task_id))
            conn.commit()
        
        flash('Статус задачи успешно обновлён.', 'success')
        return redirect(url_for('admin_tasks'))
    except Exception as e:
        logger.error(f"Ошибка при обновлении задачи администратору: {e}")
        flash('Произошла ошибка при обновлении задачи.', 'danger')
        return redirect(url_for('admin_tasks'))

# Маршрут для удаления задачи
@app.route('/delete_admin_task/<int:task_id>', methods=['POST'])
@login_required
def delete_admin_task(task_id):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("DELETE FROM tasks WHERE task_id = ?", (task_id,))
            conn.commit()
        
        flash('Задача успешно удалена.', 'success')
        return redirect(url_for('admin_tasks'))
    except Exception as e:
        logger.error(f"Ошибка при удалении задачи администратору: {e}")
        flash('Произошла ошибка при удалении задачи.', 'danger')
        return redirect(url_for('admin_tasks'))

# Mapping display texts to keys
ORDER_STATUS_MAP = {
    "Принято": "order_status_accepted",
    "Выполняется": "order_status_in_progress",
    "Ожидание оплаты": "order_status_waiting_payment",
    "Выполнено": "order_status_completed",
    "Ожидание": "order_status_pending",
    "Отменен": "order_status_cancelled",
    "Возврат": "order_status_returned"
}

## Константы для пагинации
OPEN_TASKS_PER_PAGE = 10
CLOSED_TASKS_PER_PAGE = 10
OPEN_ADMIN_TASKS_PER_PAGE = 10
CLOSED_ADMIN_TASKS_PER_PAGE = 10
OPEN_PROPERTY_REQUESTS_PER_PAGE = 10
CLOSED_PROPERTY_REQUESTS_PER_PAGE = 10
CLIENTS_PER_PAGE = 10
ORDERS_PER_PAGE = 10

# Определение статусов как констант
TASK_STATUS_NOT_COMPLETED = 'task_status_not_completed'
TASK_STATUS_IN_PROGRESS = 'task_status_in_progress'
TASK_STATUS_COMPLETED = 'task_status_completed'

ORDER_STATUS_COMPLETED = 'order_status_completed'
ORDER_STATUS_CANCELLED = 'order_status_cancelled'
ORDER_STATUS_RETURNED = 'order_status_returned'




# Предполагается, что функции ниже определены либо в этом файле, либо импортированы из adminfunctions.py
def add_admin_task(description, status, order_id):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO tasks (description, status, order_id)
                VALUES (?, ?, ?)
            """, (description, status, order_id))
            conn.commit()
        return True
    except Exception as e:
        logger.error(f"Ошибка при добавлении задачи администратора: {e}", exc_info=True)
        return False

def get_admin_open_tasks(filters):
    try:
        with sqlite3.connect('bot.db') as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            query = "SELECT task_id, order_id, description, status FROM tasks WHERE status != 'task_status_completed'"
            params = []
            if 'task_id' in filters:
                query += " AND task_id = ?"
                params.append(filters['task_id'])
            if 'order_id' in filters:
                query += " AND order_id = ?"
                params.append(filters['order_id'])
            if 'description' in filters:
                query += " AND description LIKE ?"
                params.append(f"%{filters['description']}%")
            query += " ORDER BY task_id DESC LIMIT ? OFFSET ?"
            params.extend([filters['limit'], filters['offset']])
            c.execute(query, params)
            return [dict(row) for row in c.fetchall()]
    except Exception as e:
        logger.error(f"Ошибка при получении открытых задач администраторов: {e}", exc_info=True)
        return []

def get_admin_closed_tasks_count(filters):
    try:
        with sqlite3.connect('bot.db') as conn:
            conn.row_factory = sqlite3.Row  # Enable dictionary-like access
            c = conn.cursor()
            query = "SELECT COUNT(*) as count FROM tasks WHERE status = 'task_status_completed'"
            params = []
            if 'task_id' in filters:
                query += " AND task_id = ?"
                params.append(filters['task_id'])
            if 'order_id' in filters:
                query += " AND order_id = ?"
                params.append(filters['order_id'])
            if 'description' in filters:
                query += " AND description LIKE ?"
                params.append(f"%{filters['description']}%")
            c.execute(query, params)
            row = c.fetchone()
            return row['count'] if row else 0
    except Exception as e:
        logger.error(f"Ошибка при подсчёте закрытых задач администраторов: {e}", exc_info=True)
        return 0

def get_order_status_counts():
    try:
        with sqlite3.connect('bot.db') as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("""
                SELECT status, COUNT(*) as count
                FROM orders
                GROUP BY status
            """)
            return {row['status']: row['count'] for row in c.fetchall()}
    except Exception as e:
        logger.error(f"Ошибка при получении счетчиков статусов заказов: {e}", exc_info=True)
        return {}

def get_open_property_requests(conn, filters):
    try:
        c = conn.cursor()
        # Используем русские строки статусов
        query = """
            SELECT order_item_id, order_id, item, status, cloud_link
            FROM order_items
            WHERE item_type = 'property' AND status IN ('Ожидание ответа агента', 'Иду смотреть')
        """
        params = []
        if 'property_request_id' in filters:
            query += " AND order_item_id = ?"
            params.append(filters['property_request_id'])
        if 'order_id' in filters:
            query += " AND order_id = ?"
            params.append(filters['order_id'])
        if 'description' in filters:
            query += " AND item LIKE ?"
            params.append(f"%{filters['description']}%")
        query += " ORDER BY order_item_id DESC LIMIT ? OFFSET ?"
        params.extend([filters['limit'], filters['offset']])
        c.execute(query, params)
        return [dict(row) for row in c.fetchall()]
    except Exception as e:
        logger.error(f"Ошибка при получении открытых запросов на недвижимость: {e}", exc_info=True)
        return []

def get_closed_property_requests(conn, filters):
    try:
        c = conn.cursor()
        # Используем русские строки статусов
        query = """
            SELECT order_item_id, order_id, item, status, cloud_link
            FROM order_items
            WHERE item_type = 'property' AND status IN ('Бронь забронирована', 'Просмотр отменен', 'Объект просмотрен', 'Результат готов')
        """
        params = []
        if 'property_request_id' in filters:
            query += " AND order_item_id = ?"
            params.append(filters['property_request_id'])
        if 'order_id' in filters:
            query += " AND order_id = ?"
            params.append(filters['order_id'])
        if 'description' in filters:
            query += " AND item LIKE ?"
            params.append(f"%{filters['description']}%")
        query += " ORDER BY order_item_id DESC LIMIT ? OFFSET ?"
        params.extend([filters['limit'], filters['offset']])
        c.execute(query, params)
        return [dict(row) for row in c.fetchall()]
    except Exception as e:
        logger.error(f"Ошибка при получении закрытых запросов на недвижимость: {e}", exc_info=True)
        return []

def get_open_property_requests_count(conn, filters):
    try:
        c = conn.cursor()
        query = """
            SELECT COUNT(*) FROM order_items
            WHERE item_type = 'property' AND status IN ('Ожидание ответа агента', 'Иду смотреть')
        """
        params = []
        if 'property_request_id' in filters:
            query += " AND order_item_id = ?"
            params.append(filters['property_request_id'])
        if 'order_id' in filters:
            query += " AND order_id = ?"
            params.append(filters['order_id'])
        if 'description' in filters:
            query += " AND item LIKE ?"
            params.append(f"%{filters['description']}%")
        c.execute(query, params)
        row = c.fetchone()
        return row[0] if row else 0
    except Exception as e:
        logger.error(f"Ошибка при подсчёте открытых запросов на недвижимость: {e}", exc_info=True)
        return 0
    

def get_closed_property_requests_count(conn, filters):
    try:
        c = conn.cursor()
        query = """
            SELECT COUNT(*) FROM order_items
            WHERE item_type = 'property' AND status IN ('Бронь забронирована', 'Просмотр отменен', 'Объект просмотрен', 'Результат готов')
        """
        params = []
        if 'property_request_id' in filters:
            query += " AND order_item_id = ?"
            params.append(filters['property_request_id'])
        if 'order_id' in filters:
            query += " AND order_id = ?"
            params.append(filters['order_id'])
        if 'description' in filters:
            query += " AND item LIKE ?"
            params.append(f"%{filters['description']}%")
        c.execute(query, params)
        row = c.fetchone()
        return row[0] if row else 0
    except Exception as e:
        logger.error(f"Ошибка при подсчёте закрытых запросов на недвижимость: {e}", exc_info=True)
        return 0

def get_clients(conn, client_type, search_field, search_term, page, per_page):
    try:
        offset = (page - 1) * per_page
        if client_type == 'current':
            status_filter = "o.status NOT IN ('order_status_completed', 'order_status_cancelled', 'order_status_returned')"
        elif client_type == 'previous':
            status_filter = "o.status IN ('order_status_completed', 'order_status_cancelled', 'order_status_returned')"
        else:
            status_filter = "1"  # Всегда истина

        allowed_fields = ['user_id', 'name', 'phone', 'email']
        if search_field not in allowed_fields:
            search_field = 'name'  # Значение по умолчанию

        query = f"""
            SELECT u.user_id, u.name, u.phone, u.email, u.language, COUNT(o.order_id) as order_count
            FROM users u
            JOIN orders o ON u.user_id = o.user_id
            WHERE {status_filter}
        """
        params = []

        if search_term:
            query += f" AND u.{search_field} LIKE ?"
            params.append(f"%{search_term}%")

        query += """
            GROUP BY u.user_id, u.name, u.phone, u.email, u.language
            ORDER BY u.name ASC
            LIMIT ? OFFSET ?
        """
        params.extend([per_page, offset])

        logger.debug("Executing Clients Query: %s", query)
        logger.debug("With Parameters: %s", params)

        c = conn.cursor()
        c.execute(query, params)
        clients = [dict(row) for row in c.fetchall()]

        # Подсчёт общего количества для пагинации
        count_query = f"""
            SELECT COUNT(DISTINCT u.user_id)
            FROM users u
            JOIN orders o ON u.user_id = o.user_id
            WHERE {status_filter}
        """
        count_params = []
        if search_term:
            count_query += f" AND u.{search_field} LIKE ?"
            count_params.append(f"%{search_term}%")

        logger.debug("Executing Clients Count Query: %s", count_query)
        logger.debug("With Parameters: %s", count_params)

        c.execute(count_query, count_params)
        total = c.fetchone()[0]
        total_pages = (total + per_page - 1) // per_page

        return {
            "clients": clients,
            "pagination": {
                "page": page,
                "pages": total_pages
            }
        }
    except Exception as e:
        logger.error(f"Ошибка при получении клиентов: {e}", exc_info=True)
        return {
            "clients": [],
            "pagination": {
                "page": page,
                "pages": 1
            }
        }
    
def get_admin_open_tasks_count(filters):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            query = "SELECT COUNT(*) as count FROM tasks WHERE status != 'task_status_completed'"
            params = []
            if 'task_id' in filters:
                query += " AND task_id = ?"
                params.append(filters['task_id'])
            if 'order_id' in filters:
                query += " AND order_id = ?"
                params.append(filters['order_id'])
            if 'description' in filters:
                query += " AND description LIKE ?"
                params.append(f"%{filters['description']}%")
            c.execute(query, params)
            row = c.fetchone()
            return row['count'] if row else 0
    except Exception as e:
        logger.error(f"Ошибка при подсчёте открытых задач администраторов: {e}", exc_info=True)
        return 0

def get_admin_closed_tasks_count(filters):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            query = "SELECT COUNT(*) as count FROM tasks WHERE status = 'task_status_completed'"
            params = []
            if 'task_id' in filters:
                query += " AND task_id = ?"
                params.append(filters['task_id'])
            if 'order_id' in filters:
                query += " AND order_id = ?"
                params.append(filters['order_id'])
            if 'description' in filters:
                query += " AND description LIKE ?"
                params.append(f"%{filters['description']}%")
            c.execute(query, params)
            row = c.fetchone()
            return row['count'] if row else 0
    except Exception as e:
        logger.error(f"Ошибка при подсчёте закрытых задач администраторов: {e}", exc_info=True)
        return 0

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    try:
        with sqlite3.connect('bot.db') as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # -------------------------------
            # 1. Обработка добавления новой задачи администратора
            # -------------------------------
            if request.method == 'POST':
                description = request.form.get('description', '').strip()
                status = request.form.get('status', '').strip()
                order_id = request.form.get('order_id', '').strip()

                # Валидация данных
                if not description:
                    flash('Описание задачи обязательно.', 'warning')
                    return redirect(url_for('dashboard'))
                if status not in ['task_status_not_completed', 'task_status_in_progress', 'task_status_completed']:
                    flash('Некорректный статус задачи.', 'warning')
                    return redirect(url_for('dashboard'))

                order_id = int(order_id) if order_id.isdigit() else None

                success = add_admin_task(description=description, status=status, order_id=order_id, cloud_link=None)  # cloud_link=None, т.к. его нет
                if success:
                    flash('Задача успешно добавлена.', 'success')
                else:
                    flash('Ошибка при добавлении задачи.', 'danger')
                return redirect(url_for('dashboard'))

            # -------------------------------
            # 2. Получение параметров фильтрации и пагинации для задач администраторов
            # -------------------------------
            # Открытые задачи администраторов
            admin_open_task_id = request.args.get('admin_open_task_id', '').strip()
            admin_open_order_id = request.args.get('admin_open_order_id', '').strip()
            admin_open_description = request.args.get('admin_open_description', '').strip()
            admin_open_page = request.args.get('admin_open_page', 1, type=int)

            # Закрытые задачи администраторов
            admin_closed_task_id = request.args.get('admin_closed_task_id', '').strip()
            admin_closed_order_id = request.args.get('admin_closed_order_id', '').strip()
            admin_closed_description = request.args.get('admin_closed_description', '').strip()
            admin_closed_page = request.args.get('admin_closed_page', 1, type=int)

            # Подготовка фильтров для открытых задач администраторов
            admin_open_filters = {}
            if admin_open_task_id:
                admin_open_filters['task_id'] = admin_open_task_id
            if admin_open_order_id:
                admin_open_filters['order_id'] = admin_open_order_id
            if admin_open_description:
                admin_open_filters['description'] = admin_open_description

            admin_open_filters['limit'] = OPEN_ADMIN_TASKS_PER_PAGE
            admin_open_filters['offset'] = (admin_open_page - 1) * OPEN_ADMIN_TASKS_PER_PAGE

            # Получение открытых задач администраторов
            admin_open_tasks = get_admin_open_tasks(filters=admin_open_filters)

            # Подсчёт общего количества открытых задач для пагинации
            admin_open_count_filters = admin_open_filters.copy()
            admin_open_count_filters.pop('limit', None)
            admin_open_count_filters.pop('offset', None)
            admin_open_total_tasks = get_admin_open_tasks_count(filters=admin_open_count_filters)
            admin_open_total_pages = (admin_open_total_tasks + OPEN_ADMIN_TASKS_PER_PAGE - 1) // OPEN_ADMIN_TASKS_PER_PAGE

            # Подготовка фильтров для закрытых задач администраторов
            admin_closed_filters = {}
            if admin_closed_task_id:
                admin_closed_filters['task_id'] = admin_closed_task_id
            if admin_closed_order_id:
                admin_closed_filters['order_id'] = admin_closed_order_id
            if admin_closed_description:
                admin_closed_filters['description'] = admin_closed_description

            admin_closed_filters['limit'] = CLOSED_ADMIN_TASKS_PER_PAGE
            admin_closed_filters['offset'] = (admin_closed_page - 1) * CLOSED_ADMIN_TASKS_PER_PAGE

            # Получение закрытых задач администраторов
            admin_closed_tasks = get_admin_closed_tasks(filters=admin_closed_filters)

            # Подсчёт общего количества закрытых задач для пагинации
            admin_closed_count_filters = admin_closed_filters.copy()
            admin_closed_count_filters.pop('limit', None)
            admin_closed_count_filters.pop('offset', None)
            admin_closed_total_tasks = get_admin_closed_tasks_count(filters=admin_closed_count_filters)
            admin_closed_total_pages = (admin_closed_total_tasks + CLOSED_ADMIN_TASKS_PER_PAGE - 1) // CLOSED_ADMIN_TASKS_PER_PAGE

            # -------------------------------
            # 3. Получение параметров фильтрации и пагинации для запросов на недвижимость
            # -------------------------------
            # Открытые запросы на недвижимость
            open_property_request_id = request.args.get('open_property_request_id', '').strip()
            open_property_order_id = request.args.get('open_property_order_id', '').strip()
            open_property_description = request.args.get('open_property_description', '').strip()
            open_property_page = request.args.get('open_property_page', 1, type=int)

            # Закрытые запросы на недвижимость
            closed_property_request_id = request.args.get('closed_property_request_id', '').strip()
            closed_property_order_id = request.args.get('closed_property_order_id', '').strip()
            closed_property_description = request.args.get('closed_property_description', '').strip()
            closed_property_page = request.args.get('closed_property_page', 1, type=int)

            # Подготовка фильтров для открытых запросов на недвижимость
            open_property_filters = {}
            if open_property_request_id:
                open_property_filters['property_request_id'] = open_property_request_id
            if open_property_order_id:
                open_property_filters['order_id'] = open_property_order_id
            if open_property_description:
                open_property_filters['description'] = open_property_description
            open_property_filters['limit'] = OPEN_PROPERTY_REQUESTS_PER_PAGE
            open_property_filters['offset'] = (open_property_page - 1) * OPEN_PROPERTY_REQUESTS_PER_PAGE

            # Получение открытых запросов на недвижимость
            open_property_requests = get_open_property_requests(conn, open_property_filters)

            # Подсчёт общего количества открытых запросов на недвижимость для пагинации
            open_property_count_filters = open_property_filters.copy()
            open_property_count_filters.pop('limit', None)
            open_property_count_filters.pop('offset', None)
            total_open_property_requests = get_open_property_requests_count(conn, open_property_count_filters)
            total_open_property_pages = (total_open_property_requests + OPEN_PROPERTY_REQUESTS_PER_PAGE - 1) // OPEN_PROPERTY_REQUESTS_PER_PAGE

            # Подготовка фильтров для закрытых запросов на недвижимость
            closed_property_filters = {}
            if closed_property_request_id:
                closed_property_filters['property_request_id'] = closed_property_request_id
            if closed_property_order_id:
                closed_property_filters['order_id'] = closed_property_order_id
            if closed_property_description:
                closed_property_filters['description'] = closed_property_description
            closed_property_filters['limit'] = CLOSED_PROPERTY_REQUESTS_PER_PAGE
            closed_property_filters['offset'] = (closed_property_page - 1) * CLOSED_PROPERTY_REQUESTS_PER_PAGE

            # Получение закрытых запросов на недвижимость
            closed_property_requests = get_closed_property_requests(conn, closed_property_filters)

            # Подсчёт общего количества закрытых запросов на недвижимость для пагинации
            closed_property_count_filters = closed_property_filters.copy()
            closed_property_count_filters.pop('limit', None)
            closed_property_count_filters.pop('offset', None)
            total_closed_property_requests = get_closed_property_requests_count(conn, closed_property_count_filters)
            total_closed_property_pages = (total_closed_property_requests + CLOSED_PROPERTY_REQUESTS_PER_PAGE - 1) // CLOSED_PROPERTY_REQUESTS_PER_PAGE

            # -------------------------------
            # 4. Получение параметров фильтрации и пагинации для клиентов и заказов
            # -------------------------------
            # Текущие клиенты
            current_search_field = request.args.get('current_search_field', 'name').strip()
            current_search_term = request.args.get('current_search_term', '').strip()
            current_page = request.args.get('current_page', 1, type=int)
            current_per_page = 10

            # Предыдущие клиенты
            previous_search_field = request.args.get('previous_search_field', 'name').strip()
            previous_search_term = request.args.get('previous_search_term', '').strip()
            previous_page = request.args.get('previous_page', 1, type=int)
            previous_per_page = 10

            # Текущие заказы
            current_orders_search_field = request.args.get('current_orders_search_field', 'order_id').strip()
            current_orders_search_term = request.args.get('current_orders_search_term', '').strip()
            current_orders_page = request.args.get('current_orders_page', 1, type=int)
            current_orders_per_page = 10

            # Завершённые заказы
            finished_orders_search_field = request.args.get('finished_orders_search_field', 'order_id').strip()
            finished_orders_search_term = request.args.get('finished_orders_search_term', '').strip()
            finished_orders_page = request.args.get('finished_orders_page', 1, type=int)
            finished_orders_per_page = 10

            # Получение данных о статусах заказов
            status_counts = get_order_status_counts()

            # Получение клиентов с пагинацией и фильтрацией
            current_clients_data = get_clients(
                conn=conn,
                client_type='current',
                search_field=current_search_field,
                search_term=current_search_term,
                page=current_page,
                per_page=current_per_page
            )
            current_clients = current_clients_data['clients']
            current_pagination = current_clients_data['pagination']

            previous_clients_data = get_clients(
                conn=conn,
                client_type='previous',
                search_field=previous_search_field,
                search_term=previous_search_term,
                page=previous_page,
                per_page=previous_per_page
            )
            previous_clients = previous_clients_data['clients']
            previous_pagination = previous_clients_data['pagination']

            # Получение текущих заказов с пагинацией и фильтрацией
            current_orders_search_field = current_orders_search_field if current_orders_search_field in ['order_id', 'user_id'] else 'order_id'
            current_orders_search_term = current_orders_search_term.strip()

            current_orders_query = """
                SELECT order_id, user_id, order_date, status, paid
                FROM orders
                WHERE status NOT IN ('order_status_completed', 'order_status_cancelled', 'order_status_returned')
            """
            current_orders_params = []

            if current_orders_search_term:
                current_orders_query += f" AND {current_orders_search_field} LIKE ?"
                current_orders_params.append(f"%{current_orders_search_term}%")

            current_orders_query += " ORDER BY order_date DESC LIMIT ? OFFSET ?"
            current_orders_params.extend([current_orders_per_page, (current_orders_page - 1) * current_orders_per_page])

            logger.debug("Executing Current Orders Query: %s", current_orders_query)
            logger.debug("With Parameters: %s", current_orders_params)

            c.execute(current_orders_query, current_orders_params)
            current_orders = [dict(row) for row in c.fetchall()]

            # Подсчёт общего количества текущих заказов для пагинации
            current_orders_count_query = """
                SELECT COUNT(*)
                FROM orders
                WHERE status NOT IN ('order_status_completed', 'order_status_cancelled', 'order_status_returned')
            """
            current_orders_count_params = []
            if current_orders_search_term:
                current_orders_count_query += f" AND {current_orders_search_field} LIKE ?"
                current_orders_count_params.append(f"%{current_orders_search_term}%")
            logger.debug("Executing Current Orders Count Query: %s", current_orders_count_query)
            logger.debug("With Parameters: %s", current_orders_count_params)
            c.execute(current_orders_count_query, current_orders_count_params)
            total_current_orders = c.fetchone()[0]
            total_current_orders_pages = (total_current_orders + current_orders_per_page - 1) // current_orders_per_page

            current_orders_pagination = {
                "page": current_orders_page,
                "pages": total_current_orders_pages
            }

            # Получение завершённых заказов с пагинацией и фильтрацией
            finished_orders_search_field = finished_orders_search_field if finished_orders_search_field in ['order_id', 'user_id'] else 'order_id'
            finished_orders_search_term = finished_orders_search_term.strip()

            finished_orders_query = """
                SELECT order_id, user_id, order_date, status, paid
                FROM orders
                WHERE status IN ('order_status_completed', 'order_status_cancelled', 'order_status_returned')
            """
            finished_orders_params = []
            if finished_orders_search_term:
                finished_orders_query += f" AND {finished_orders_search_field} LIKE ?"
                finished_orders_params.append(f"%{finished_orders_search_term}%")

            finished_orders_query += " ORDER BY order_date DESC LIMIT ? OFFSET ?"
            finished_orders_params.extend([finished_orders_per_page, (finished_orders_page - 1) * finished_orders_per_page])

            logger.debug("Executing Finished Orders Query: %s", finished_orders_query)
            logger.debug("With Parameters: %s", finished_orders_params)

            c.execute(finished_orders_query, finished_orders_params)
            finished_orders = [dict(row) for row in c.fetchall()]

            # Подсчёт общего количества завершённых заказов для пагинации
            finished_orders_count_query = """
                SELECT COUNT(*)
                FROM orders
                WHERE status IN ('order_status_completed', 'order_status_cancelled', 'order_status_returned')
            """
            finished_orders_count_params = []
            if finished_orders_search_term:
                finished_orders_count_query += f" AND {finished_orders_search_field} LIKE ?"
                finished_orders_count_params.append(f"%{finished_orders_search_term}%")
            logger.debug("Executing Finished Orders Count Query: %s", finished_orders_count_query)
            logger.debug("With Parameters: %s", finished_orders_count_params)
            c.execute(finished_orders_count_query, finished_orders_count_params)
            total_finished_orders = c.fetchone()[0]
            total_finished_orders_pages = (total_finished_orders + finished_orders_per_page - 1) // finished_orders_per_page

            finished_orders_pagination = {
                "page": finished_orders_page,
                "pages": total_finished_orders_pages
            }

            # -------------------------------
            # 5. Получение задач из таблицы order_tasks с фильтрацией и пагинацией
            # -------------------------------
            # Открытые задачи заказов
            open_task_id = request.args.get('open_task_id', '').strip()
            open_order_id = request.args.get('open_order_id', '').strip()
            open_task_status = request.args.get('open_task_status', '').strip()
            open_page = request.args.get('open_page', 1, type=int)

            # Закрытые задачи заказов
            closed_task_id = request.args.get('closed_task_id', '').strip()
            closed_order_id = request.args.get('closed_order_id', '').strip()
            closed_page = request.args.get('closed_page', 1, type=int)

            # Открытые задачи заказов
            open_filters = []
            open_params = []

            if open_task_status:
                open_filters.append("status = ?")
                open_params.append(open_task_status)
            else:
                # Если статус не указан, показываем задачи со статусами 'task_status_not_completed' и 'task_status_in_progress'
                open_filters.append("status IN (?, ?)")
                open_params.extend(['task_status_not_completed', 'task_status_in_progress'])  # Замените на актуальные статусы

            if open_task_id:
                open_filters.append("task_id = ?")
                open_params.append(open_task_id)

            if open_order_id:
                open_filters.append("order_id = ?")
                open_params.append(open_order_id)

            # Формируем WHERE клаузулу корректно
            if open_filters:
                open_filter_query = " WHERE " + " AND ".join(open_filters)
            else:
                open_filter_query = ""

            # Подсчёт общего количества открытых задач для пагинации
            query_count_open = f"""
                SELECT COUNT(*) FROM order_tasks
                {open_filter_query}
            """
            logger.debug("Executing Open Tasks Count Query: %s", query_count_open)
            logger.debug("With Parameters: %s", open_params)
            c.execute(query_count_open, open_params)
            total_open_tasks = c.fetchone()[0]
            total_open_pages = (total_open_tasks + OPEN_TASKS_PER_PAGE - 1) // OPEN_TASKS_PER_PAGE

            # Получение открытых задач заказов
            query_open_tasks = f"""
                SELECT task_id, order_id, task_description AS description, status
                FROM order_tasks
                {open_filter_query}
                ORDER BY task_id DESC
                LIMIT ? OFFSET ?
            """
            params_open_tasks = open_params + [OPEN_TASKS_PER_PAGE, (open_page - 1) * OPEN_TASKS_PER_PAGE]

            logger.debug("Executing Open Tasks Query: %s", query_open_tasks)
            logger.debug("With Parameters: %s", params_open_tasks)

            c.execute(query_open_tasks, params_open_tasks)
            open_order_tasks = [dict(row) for row in c.fetchall()]

            # Закрытые задачи заказов
            closed_filters = []
            closed_params = []

            # Закрытые задачи имеют статус 'task_status_completed'
            closed_filters.append("status = ?")
            closed_params.append('task_status_completed')  # Замените на актуальный статус закрытых задач

            if closed_task_id:
                closed_filters.append("task_id = ?")
                closed_params.append(closed_task_id)

            if closed_order_id:
                closed_filters.append("order_id = ?")
                closed_params.append(closed_order_id)

            # Формируем WHERE клаузулу корректно
            if closed_filters:
                closed_filter_query = " WHERE " + " AND ".join(closed_filters)
            else:
                closed_filter_query = ""

            # Подсчёт общего количества закрытых задач для пагинации
            query_count_closed = f"""
                SELECT COUNT(*) FROM order_tasks
                {closed_filter_query}
            """
            logger.debug("Executing Closed Tasks Count Query: %s", query_count_closed)
            logger.debug("With Parameters: %s", closed_params)
            c.execute(query_count_closed, closed_params)
            total_closed_tasks = c.fetchone()[0]
            total_closed_pages = (total_closed_tasks + CLOSED_TASKS_PER_PAGE - 1) // CLOSED_TASKS_PER_PAGE

            # Получение закрытых задач заказов
            query_closed_tasks = f"""
                SELECT task_id, order_id, task_description AS description, status
                FROM order_tasks
                {closed_filter_query}
                ORDER BY task_id DESC
                LIMIT ? OFFSET ?
            """
            params_closed_tasks = closed_params + [CLOSED_TASKS_PER_PAGE, (closed_page - 1) * CLOSED_TASKS_PER_PAGE]

            logger.debug("Executing Closed Tasks Query: %s", query_closed_tasks)
            logger.debug("With Parameters: %s", params_closed_tasks)

            c.execute(query_closed_tasks, params_closed_tasks)
            closed_order_tasks = [dict(row) for row in c.fetchall()]

            # -------------------------------
            # 6. Получение финансовых данных
            # -------------------------------
            # Доходы
            c.execute("SELECT SUM(amount) as total_income FROM income")
            row = c.fetchone()
            total_income = row['total_income'] if row else 0

            # Расходы
            c.execute("SELECT SUM(amount) as total_expenses FROM expenses")
            row = c.fetchone()
            total_expenses = row['total_expenses'] if row else 0

            # Подготовка данных для графиков (за последние 12 месяцев)
            # Доходы
            c.execute("""
                SELECT strftime('%m-%Y', order_date) as month, SUM(o.amount) as total
                FROM orders o
                WHERE o.order_date >= date('now', '-12 months')
                GROUP BY month
                ORDER BY month
            """)
            income_records = c.fetchall()
            income_labels = [row['month'] for row in income_records]
            income_data = [row['total'] for row in income_records]

            # Расходы
            c.execute("""
                SELECT strftime('%m-%Y', expense_date) as month, SUM(amount) as total
                FROM expenses
                WHERE expense_date >= date('now', '-12 months')
                GROUP BY month
                ORDER BY month
            """)
            expenses_records = c.fetchall()
            expenses_labels = [row['month'] for row in expenses_records]
            expenses_data = [row['total'] for row in expenses_records]

            # -------------------------------
            # 7. Подготовка статистики
            # -------------------------------
            stats = {
                'current_clients_count': len(current_clients),
                'previous_clients_count': len(previous_clients),
                'open_tasks': total_open_tasks,
                'closed_tasks': total_closed_tasks,
                'open_admin_tasks_count': admin_open_total_tasks,
                'closed_admin_tasks_count': admin_closed_total_tasks,
                'open_property_requests_count': total_open_property_requests,
                'closed_property_requests_count': total_closed_property_requests,
                'income_labels': income_labels,
                'income_data': income_data,
                'expenses_labels': expenses_labels,
                'expenses_data': expenses_data,
                'order_status_counts': status_counts,
                'total_income': total_income,
                'total_expenses': total_expenses
            }

            # -------------------------------
            # 8. Логирование полученных данных
            # -------------------------------
            logger.debug(f"Open Admin Tasks Retrieved: {admin_open_tasks}")
            logger.debug(f"Closed Admin Tasks Retrieved: {admin_closed_tasks}")
            logger.debug(f"Open Property Requests Retrieved: {open_property_requests}")
            logger.debug(f"Closed Property Requests Retrieved: {closed_property_requests}")
            logger.debug(f"Open Order Tasks Retrieved: {open_order_tasks}")
            logger.debug(f"Closed Order Tasks Retrieved: {closed_order_tasks}")

            # -------------------------------
            # 9. Передача данных в шаблон
            # -------------------------------
            return render_template('dashboard.html',
                                   stats=stats,
                                   current_clients=current_clients,
                                   current_pagination=current_pagination,
                                   previous_clients=previous_clients,
                                   previous_pagination=previous_pagination,
                                   current_orders=current_orders,
                                   current_orders_pagination=current_orders_pagination,
                                   finished_orders=finished_orders,
                                   finished_orders_pagination=finished_orders_pagination,
                                   admin_open_tasks=admin_open_tasks,
                                   admin_closed_tasks=admin_closed_tasks,
                                   admin_open_page=admin_open_page,
                                   admin_open_total_pages=admin_open_total_pages,
                                   admin_closed_page=admin_closed_page,
                                   admin_closed_total_pages=admin_closed_total_pages,
                                   # Запросы на недвижимость
                                   open_property_requests=open_property_requests,
                                   total_open_property_pages=total_open_property_pages,
                                   open_property_page=open_property_page,
                                   closed_property_requests=closed_property_requests,
                                   total_closed_property_pages=total_closed_property_pages,
                                   closed_property_page=closed_property_page,
                                   # Фильтры для запросов на недвижимость
                                   open_property_request_id=open_property_request_id,
                                   open_property_order_id=open_property_order_id,
                                   open_property_description=open_property_description,
                                   closed_property_request_id=closed_property_request_id,
                                   closed_property_order_id=closed_property_order_id,
                                   closed_property_description=closed_property_description,
                                   # Фильтры и пагинация для задач заказов
                                   open_order_tasks=open_order_tasks,
                                   closed_order_tasks=closed_order_tasks,
                                   open_page=open_page,
                                   total_open_pages=total_open_pages,
                                   closed_page=closed_page,
                                   total_closed_pages=total_closed_pages,
                                   # Фильтры для задач заказов
                                   open_task_id=open_task_id,
                                   open_order_id=open_order_id,
                                   open_task_status=open_task_status,
                                   closed_task_id=closed_task_id,
                                   closed_order_id=closed_order_id)
    except Exception as e:
        logger.error(f"Ошибка при загрузке дэшборда: {e}", exc_info=True)
        flash('Произошла ошибка при загрузке дэшборда.', 'danger')
        return redirect(url_for('users'))


@app.template_filter('get_order_status_display')
def get_order_status_display_filter(status, language):
    return get_order_status_display(status, language)

def get_order_status_display(status, language):
    # Функция для отображения статуса заказа на нужном языке
    status_dict = {
        'ru': {
            'order_status_accepted': 'Принято',
            'order_status_in_progress': 'Выполняется',
            'order_status_waiting_payment': 'Ожидание оплаты',
            'order_status_completed': 'Выполнено',
            'order_status_pending': 'Ожидание',
            'order_status_cancelled': 'Отменен',
            'order_status_returned': 'Возврат'
        },
        'en': {
            'order_status_accepted': 'Accepted',
            'order_status_in_progress': 'In Progress',
            'order_status_waiting_payment': 'Waiting for Payment',
            'order_status_completed': 'Completed',
            'order_status_pending': 'Pending',
            'order_status_cancelled': 'Cancelled',
            'order_status_returned': 'Returned'
        },
        'uz': {
            'order_status_accepted': 'Qabul qilindi',
            'order_status_in_progress': 'Bajarilmoqda',
            'order_status_waiting_payment': 'To\'lovni kutmoqda',
            'order_status_completed': 'Bajarildi',
            'order_status_pending': 'Kutmoqda',
            'order_status_cancelled': 'Bekor qilindi',
            'order_status_returned': 'Qaytarildi'
        }
    }
    return status_dict.get(language, status_dict['ru']).get(status, status)

@app.route('/client/<int:user_id>/orders', methods=['GET'])
@login_required
def client_orders(user_id):
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Получение информации о пользователе
        c.execute("""
            SELECT user_id, name, phone, email, bonuses, language
            FROM users
            WHERE user_id = ?
        """, (user_id,))
        user = c.fetchone()
        if not user:
            flash(f"Пользователь с ID {user_id} не найден.", 'warning')
            logger.warning(f"User with ID {user_id} not found.")
            return redirect(url_for('users'))

        # Получение всех заказов пользователя без фильтрации
        c.execute("""
            SELECT order_id, status, order_date, payment_method, paid
            FROM orders
            WHERE user_id = ?
            ORDER BY order_date DESC
        """, (user_id,))
        orders = c.fetchall()

        # Добавление доходов и расходов к каждому заказу
        orders_with_financials = []
        for order in orders:
            order_dict = dict(order)
            
            # Получение доходов для заказа
            c.execute("""
                SELECT income_id, amount, description, income_date
                FROM income
                WHERE order_id = ?
            """, (order['order_id'],))
            income = c.fetchall()
            order_dict['incomes'] = income

            # Получение расходов для заказа
            c.execute("""
                SELECT expense_id, amount, description, expense_date
                FROM expenses
                WHERE order_id = ?
            """, (order['order_id'],))
            expenses = c.fetchall()
            order_dict['expenses'] = expenses

            orders_with_financials.append(order_dict)

        conn.close()

        if not orders:
            flash('У этого клиента нет заказов.', 'info')

        return render_template('client_orders.html', user=user, orders=orders_with_financials)
    except Exception as e:
        flash('Произошла ошибка при загрузке заказов клиента.', 'danger')
        logger.error(f"Error loading client orders for user {user_id}: {e}")
        return redirect(url_for('users'))


PAYMENT_METHOD_MAP = {
    "💵 Наличные": "cash",
    "💳 PayMe": "PayMe"
}

TASK_STATUS_MAP = {
    "Выполнено": "task_status_completed",
    "Не выполнено": "task_status_not_completed",
    "Выполняется": "task_status_in_progress"
}

PROPERTY_STATUS_LIST = [
    "Ожидание ответа агента",
    "Бронь забронирована",
    "Иду смотреть",
    "Идет просмотр объекта",
    "Объект просмотрен",
    "Результат готов",
    "Просмотр отменен"
]


PROPERTY_STATUS_MAP = {
    "Ожидание ответа агента": 'property_status_waiting_agent',
    "Бронь забронирована": 'property_status_booked',
    "Иду смотреть": 'property_status_going',
    "Идет просмотр объекта": 'property_status_in_progress',
    "Объект просмотрен": 'property_status_viewed',
    "Результат готов": 'property_status_ready',
    "Просмотр отменен": 'property_status_cancelled',
}


def notify_users_and_subscribers(order_id, message_key, **kwargs):
    """
    Отправляет уведомления пользователю и подписчикам по ключу сообщения.

    Args:
        order_id (int): ID заказа.
        message_key (str): Ключ сообщения для перевода.
        **kwargs: Дополнительные аргументы для форматирования сообщения.
    """
    order = get_order_by_id(order_id)
    if not order:
        logger.error(f"Order {order_id} not found for notifications.")
        return

    user_id = order['user_id']
    language = get_user_language(user_id)
    message_to_user = get_message(language, message_key, **kwargs)

    # Отправляем уведомление пользователю
    send_notification(
        chat_id=user_id,
        message=message_to_user,
        bot_token=app.config['TELEGRAM_BOT_TOKEN'],
        parse_mode="HTML"
    )

    # Отправляем уведомления подписчикам
    subscribers = get_order_subscribers(order_id)
    for subscriber_id in subscribers:
        subscriber_language = get_user_language(subscriber_id)
        # Предполагается, что ключ для подписчиков имеет суффикс '_subscriber'
        subscriber_message_key = f"{message_key}_subscriber"
        message_to_subscriber = get_message(subscriber_language, subscriber_message_key, **kwargs)
        send_notification(
            chat_id=subscriber_id,
            message=message_to_subscriber,
            bot_token=app.config['TELEGRAM_BOT_TOKEN'],
            parse_mode="HTML"
        )


def get_order_subscribers(order_id: int) -> list:
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("SELECT user_id FROM order_subscribers WHERE order_id = ?", (order_id,))
        return [row[0] for row in c.fetchall()]

def get_user_language(user_id):
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        c.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if row and row[0]:
            return row[0]
        return 'ru'  # По умолчанию русский

# Helper functions for options
def get_order_status_options(selected_status):
    options = ""
    for display, key in ORDER_STATUS_MAP.items():
        selected = "selected" if key == selected_status else ""
        options += f'<option value="{key}" {selected}>{display}</option>'
    return options

@app.context_processor
def utility_processor():
    def get_order_status_display(status_code, language='ru'):
        # Используем вашу функцию GetMessage для получения перевода
        return get_message(language, status_code)
    return dict(get_order_status_display=get_order_status_display)

def get_payment_method_options(selected_method):
    options = ""
    for display, key in PAYMENT_METHOD_MAP.items():
        selected = "selected" if key == selected_method else ""
        options += f'<option value="{key}" {selected}>{display}</option>'
    return options

def get_task_status_options(selected_status):
    options = ""
    for display, key in TASK_STATUS_MAP.items():
        selected = "selected" if key == selected_status else ""
        options += f'<option value="{key}" {selected}>{display}</option>'
    return options

def get_property_status_options(selected_status):
    options = ""
    for status in PROPERTY_STATUS_LIST:
        selected = "selected" if status == selected_status else ""
        options += f'<option value="{status}" {selected}>{status}</option>'
    return options

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password:
            user = User(username)
            login_user(user)
            logger.info(f"Admin {username} logged in.")
            return redirect(url_for('dashboard'))
        else:
            flash('Неверный логин или пароль.')
            logger.warning(f"Failed login attempt for username: {username}")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы.')
    logger.info(f"Admin {current_user.id} logged out.")
    return redirect(url_for('login'))

@app.route('/')
@login_required
def home():
    return redirect(url_for('dashboard'))


@app.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Инициализация фильтров
        if request.method == 'POST':
            search_field = request.form.get('search_field', '')
            search_term = request.form.get('search_term', '')
            language_filter = request.form.get('language_filter', '')
            payment_method_filter = request.form.get('payment_method_filter', '')
            paid_filter = request.form.get('paid_filter', '')
            client_type = request.form.get('client_type', 'all')
            start_date = request.form.get('start_date', '')
            end_date = request.form.get('end_date', '')
            page = 1  # При POST запросе всегда начинаем с первой страницы
        else:
            search_field = request.args.get('search_field', '')
            search_term = request.args.get('search_term', '')
            language_filter = request.args.get('language_filter', '')
            payment_method_filter = request.args.get('payment_method_filter', '')
            paid_filter = request.args.get('paid_filter', '')
            client_type = request.args.get('client_type', 'all')
            start_date = request.args.get('start_date', '')
            end_date = request.args.get('end_date', '')
            page = request.args.get('page', 1, type=int)

        per_page = 20
        offset = (page - 1) * per_page

        # Базовый запрос с объединением таблиц users и orders
        base_query = """
            SELECT u.user_id, u.name, u.phone, u.email, COUNT(o.order_id) as order_count
            FROM users u
            LEFT JOIN orders o ON u.user_id = o.user_id
        """

        # Применение фильтрации по типу клиента
        if client_type == 'current':
            base_query += " WHERE o.status NOT IN ('order_status_completed', 'order_status_cancelled', 'order_status_returned')"
        elif client_type == 'previous':
            base_query += " WHERE o.status IN ('order_status_completed', 'order_status_cancelled', 'order_status_returned')"
        elif client_type == 'no_orders':
            base_query += " WHERE o.order_id IS NULL"

        # Применение дополнительных фильтров
        filters = []
        params = []

        if search_field and search_term:
            if search_field in ['user_id', 'name', 'phone', 'email']:
                filters.append(f"u.{search_field} LIKE ?")
                params.append(f"%{search_term}%")

        if language_filter:
            filters.append("u.language = ?")
            params.append(language_filter)

        if payment_method_filter:
            filters.append("o.payment_method = ?")
            params.append(payment_method_filter)

        if paid_filter:
            filters.append("o.paid = ?")
            params.append(paid_filter)

        if start_date:
            filters.append("DATE(o.order_date) >= DATE(?)")
            params.append(start_date)

        if end_date:
            filters.append("DATE(o.order_date) <= DATE(?)")
            params.append(end_date)

        if filters:
            if client_type in ['current', 'previous', 'no_orders']:
                base_query += " AND " + " AND ".join(filters)
            else:
                base_query += " WHERE " + " AND ".join(filters)

        base_query += " GROUP BY u.user_id"

        # Добавление сортировки и пагинации
        base_query += " ORDER BY u.user_id DESC LIMIT ? OFFSET ?"
        params.extend([per_page, offset])

        # Выполнение запроса
        c.execute(base_query, params)
        clients = c.fetchall()

        # Получение общего количества записей для пагинации
        count_query = "SELECT COUNT(DISTINCT u.user_id) as total FROM users u LEFT JOIN orders o ON u.user_id = o.user_id"

        if client_type == 'current':
            count_query += " WHERE o.status NOT IN ('order_status_completed', 'order_status_cancelled', 'order_status_returned')"
        elif client_type == 'previous':
            count_query += " WHERE o.status IN ('order_status_completed', 'order_status_cancelled', 'order_status_returned')"
        elif client_type == 'no_orders':
            count_query += " WHERE o.order_id IS NULL"

        if filters:
            if client_type in ['current', 'previous', 'no_orders']:
                count_query += " AND " + " AND ".join(filters)
            else:
                count_query += " WHERE " + " AND ".join(filters)

        c.execute(count_query, params[:-2])  # Исключаем LIMIT и OFFSET
        total = c.fetchone()['total']
        total_pages = (total + per_page - 1) // per_page

        # Подготовка данных для шаблона
        pagination = {
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': total_pages
        }

        # Закрытие соединения с базой данных
        conn.close()

        return render_template('users.html',
                               clients=clients,
                               pagination=pagination,
                               client_type=client_type,
                               search_field=search_field,
                               search_term=search_term,
                               language_filter=language_filter,
                               payment_method_filter=payment_method_filter,
                               paid_filter=paid_filter,
                               start_date=start_date,
                               end_date=end_date)
    except Exception as e:
        flash('Произошла ошибка при загрузке пользователей.', 'danger')
        logger.error(f"Error loading users: {e}")
        return redirect(url_for('dashboard'))

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Для доступа к колонкам по имени
    return conn



@app.route('/orders', methods=['GET', 'POST'])
@login_required
def orders():
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Получение данных для фильтрации
        search_field = request.form.get('search_field', '')
        search_term = request.form.get('search_term', '')
        start_date = request.form.get('start_date', '')
        end_date = request.form.get('end_date', '')
        status = request.form.get('status', '')
        payment_method = request.form.get('payment_method', '')
        paid = request.form.get('paid', '')

        # Построение базового запроса с объединением таблиц orders и users
        query = """
            SELECT o.order_id, o.user_id, u.name as user_name, o.order_date, o.status, o.payment_method, o.paid
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            WHERE 1=1
        """
        params = []

        # Применение фильтров
        if search_field and search_term:
            if search_field in ['order_id', 'user_id']:
                query += f" AND o.{search_field} LIKE ?"
                params.append(f"%{search_term}%")
        if start_date:
            query += " AND DATE(o.order_date) >= DATE(?)"
            params.append(start_date)
        if end_date:
            query += " AND DATE(o.order_date) <= DATE(?)"
            params.append(end_date)
        if status:
            query += " AND o.status = ?"
            params.append(status)
        if payment_method:
            query += " AND o.payment_method = ?"
            params.append(payment_method)
        if paid:
            query += " AND o.paid = ?"
            params.append(paid)

        query += " ORDER BY o.order_id DESC"

        # Выполнение запроса
        c.execute(query, params)
        orders = c.fetchall()
        conn.close()

        return render_template('orders.html', orders=orders)
    except Exception as e:
        flash('Произошла ошибка при загрузке заказов.', 'danger')
        app.logger.error(f"Error loading orders: {e}")
        return redirect(url_for('dashboard'))

from datetime import datetime

@app.template_filter('format_datetime')
def format_datetime(value, format='%d-%m-%Y %H:%M'):
    london_tz = pytz.timezone('Europe/London')  # Часовой пояс Лондона

    if isinstance(value, str):
        try:
            # Преобразование строки в объект datetime
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
            # Локализуем время как UTC
            value = pytz.utc.localize(value)
        except ValueError:
            try:
                # Если формат отличается, например, содержит 'T'
                value = datetime.strptime(value, '%Y-%m-%dT%H:%M')
                value = pytz.utc.localize(value)
            except ValueError:
                return value  # Возврат оригинального значения, если формат не соответствует

    if isinstance(value, datetime):
        # Конвертация времени в Лондонское время
        value = value.astimezone(london_tz)
        return value.strftime(format)

    return value

@app.route('/update_user_info/<int:order_id>/<int:user_id>', methods=['POST'])
@login_required
def update_user_info(order_id, user_id):
    form = UpdateUserInfoForm()
    if form.validate_on_submit():
        name = form.name.data
        phone = form.phone.data
        email = form.email.data
        language = form.language.data

        # Обновление информации о пользователе
        try:
            success = True
            success &= update_user_profile(user_id, 'name', name)
            success &= update_user_profile(user_id, 'phone', phone)
            success &= update_user_profile(user_id, 'email', email)
            success &= update_user_profile(user_id, 'language', language)
            
            if success:
                flash("Информация о пользователе успешно обновлена.", 'success')
            else:
                flash("Произошла ошибка при обновлении информации о пользователе.", 'danger')
        except Exception as e:
            flash("Произошла ошибка при обновлении информации о пользователе.", 'danger')
            logger.error(f"Ошибка при обновлении информации о пользователе {user_id}: {e}")

    else:
        # Если форма не прошла валидацию, можно отобразить ошибки
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"Ошибка в поле '{getattr(form, field).label.text}': {error}", 'danger')

    return redirect(url_for('order_detail', order_id=order_id))

from forms import (
    AddTaskForm,
    AddPropertyForm,
    UpdateUserInfoForm,
)



def get_order_incomes(order_id):
    conn = get_db_connection()
    incomes = conn.execute("""
        SELECT income_id, order_id, amount, description, income_date
        FROM income
        WHERE order_id = ?
        ORDER BY income_date DESC
    """, (order_id,)).fetchall()
    conn.close()
    return incomes

def get_order_expenses(order_id):
    conn = get_db_connection()
    expenses = conn.execute("""
        SELECT expense_id, order_id, amount, description, expense_date
        FROM expenses
        WHERE order_id = ?
        ORDER BY expense_date DESC
    """, (order_id,)).fetchall()
    conn.close()
    return expenses

@app.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = get_order_by_id(order_id)
    if not order:
        flash(f"Заказ с ID {order_id} не найден.", 'warning')
        logger.warning(f"Order with ID {order_id} not found.")
        return redirect(url_for('orders'))
    
    # Получение информации о пользователе
    user = get_user_profile(order['user_id'])
    if not user:
        flash("Информация о пользователе не найдена.", 'warning')
        # Создаём пустой профиль или перенаправляем
        user = {
            'user_id': order['user_id'],
            'name': 'Неизвестно',
            'phone': 'Неизвестно',
            'email': 'Неизвестно',
            'language': 'ru'
        }

    # Получение текущего баланса бонусов пользователя
    user_id = order['user_id']
    bonuses = get_user_bonuses(user_id)
    order['bonuses'] = bonuses
    
    properties = get_order_properties(order_id)
    tasks = get_order_tasks(order_id)
    events = get_order_events(order_id)
    incomes = get_order_incomes(order_id)
    expenses = get_order_expenses(order_id)
    
    # Подготовка отображаемого метода оплаты
    payment_method_display = next((k for k, v in PAYMENT_METHOD_MAP.items() if v == order['payment_method']), order['payment_method'])
    order['payment_method_display'] = payment_method_display
    
    # Получение сообщений для заказа
    try:
        with get_db_connection() as conn:
            messages = conn.execute("""
                SELECT sender_type, sender_id, message_text, timestamp
                FROM messages
                WHERE order_id = ?
                ORDER BY timestamp ASC
            """, (order_id,)).fetchall()
            messages = [dict(message) for message in messages]
    except Exception as e:
        flash("Произошла ошибка при загрузке сообщений.", 'danger')
        logger.error(f"Error loading messages for order {order_id}: {e}")
        messages = []
    
    return render_template(
        'order_detail.html',
        order=order,
        user=user,
        properties=properties,
        tasks=tasks,
        events=events,
        incomes=incomes,
        expenses=expenses,
        messages=messages
    )

@app.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            # Удаляем пользователя из таблицы users
            c.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            conn.commit()
            if c.rowcount > 0:
                flash(f"Пользователь {user_id} успешно удален.")
                logger.info(f"User {user_id} deleted by admin.")
            else:
                flash(f"Пользователь {user_id} не найден.")
                logger.warning(f"User {user_id} not found for deletion.")
    except sqlite3.Error as e:
        flash("Произошла ошибка при удалении пользователя.")
        logger.error(f"Error deleting user {user_id}: {e}")
    return redirect(url_for('users'))

@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if request.method == 'POST':
        # Получаем данные из формы
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        bonuses = request.form.get('bonuses')
        language = request.form.get('language')
        
        # Валидация данных при необходимости
        
        try:
            with sqlite3.connect('bot.db') as conn:
                c = conn.cursor()
                c.execute("""
                    UPDATE users SET name = ?, phone = ?, email = ?, bonuses = ?, language = ?
                    WHERE user_id = ?
                """, (name, phone, email, bonuses, language, user_id))
                conn.commit()
                flash("Профиль пользователя успешно обновлен.")
                logger.info(f"User {user_id} profile updated by admin.")
            return redirect(url_for('users'))
        except sqlite3.Error as e:
            flash("Произошла ошибка при обновлении профиля пользователя.")
            logger.error(f"Error updating user {user_id}: {e}")
            return redirect(url_for('users'))
    else:
        # Получаем данные пользователя для отображения в форме
        user = get_user_by_id(user_id)
        if not user:
            flash("Пользователь не найден.")
            return redirect(url_for('users'))
        return render_template('edit_user.html', user=user)

from datetime import datetime

@app.route('/order/<int:order_id>/income/add', methods=['POST'])
@login_required
def add_income(order_id):
    amount = request.form.get('amount')
    description = request.form.get('description')
    income_date = request.form.get('income_date')

    # Валидация данных
    if not amount or not income_date:
        flash('Сумма и дата дохода обязательны.', 'danger')
        return redirect(url_for('order_detail', order_id=order_id))

    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            # Вставка нового дохода
            c.execute("""
                INSERT INTO income (order_id, amount, description, income_date)
                VALUES (?, ?, ?, ?)
            """, (order_id, amount, description, income_date))
            conn.commit()
        flash('Доход успешно добавлен.', 'success')
    except Exception as e:
        flash('Произошла ошибка при добавлении дохода.', 'danger')
        logger.error(f"Error adding income for order {order_id}: {e}")
        return redirect(url_for('order_detail', order_id=order_id))

    return redirect(url_for('order_detail', order_id=order_id))


@app.route('/order/<int:order_id>/expense/add', methods=['POST'])
@login_required
def add_expense(order_id):
    amount = request.form.get('amount')
    description = request.form.get('description')
    expense_date_str = request.form.get('expense_date')  # Получаем строку даты из формы

    # Валидация данных
    if not amount or not expense_date_str:
        flash('Сумма и дата расхода обязательны.', 'danger')
        return redirect(url_for('order_detail', order_id=order_id))

    try:
        # Парсим дату и время, полученные из формы
        expense_datetime = datetime.strptime(expense_date_str, '%Y-%m-%dT%H:%M')
        # Применяем часовой пояс Лондона, если необходимо
        london_tz = pytz.timezone('Europe/London')
        expense_datetime = london_tz.localize(expense_datetime)
        # Форматируем дату для сохранения в базе данных
        expense_timestamp = expense_datetime.strftime('%Y-%m-%d %H:%M:%S')

        with get_db_connection() as conn:
            c = conn.cursor()
            # Вставка нового расхода
            c.execute("""
                INSERT INTO expenses (order_id, amount, description, expense_date)
                VALUES (?, ?, ?, ?)
            """, (order_id, amount, description, expense_timestamp))
            conn.commit()
        flash('Расход успешно добавлен.', 'success')
    except ValueError as ve:
        flash("Неверный формат даты расхода.", 'danger')
        logger.error(f"ValueError when parsing expense_date for order {order_id}: {ve}")
        return redirect(url_for('order_detail', order_id=order_id))
    except Exception as e:
        flash('Произошла ошибка при добавлении расхода.', 'danger')
        logger.error(f"Error adding expense for order {order_id}: {e}")
        return redirect(url_for('order_detail', order_id=order_id))

    return redirect(url_for('order_detail', order_id=order_id))

@app.route('/order/<int:order_id>/income/<int:income_id>/delete', methods=['POST'])
@login_required
def delete_income(order_id, income_id):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                DELETE FROM income
                WHERE income_id = ? AND order_id = ?
            """, (income_id, order_id))
            conn.commit()
        flash('Доход успешно удалён.', 'success')
    except Exception as e:
        flash('Произошла ошибка при удалении дохода.', 'danger')
        logger.error(f"Error deleting income {income_id} for order {order_id}: {e}")

    return redirect(url_for('order_detail', order_id=order_id))


@app.route('/order/<int:order_id>/expense/<int:expense_id>/delete', methods=['POST'])
@login_required
def delete_expense(order_id, expense_id):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                DELETE FROM expenses
                WHERE expense_id = ? AND order_id = ?
            """, (expense_id, order_id))
            conn.commit()
        flash('Расход успешно удалён.', 'success')
    except Exception as e:
        flash('Произошла ошибка при удалении расхода.', 'danger')
        logger.error(f"Error deleting expense {expense_id} for order {order_id}: {e}")

    return redirect(url_for('order_detail', order_id=order_id))


@app.route('/order/<int:order_id>/income/<int:income_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_income(order_id, income_id):
    try:
        conn = get_db_connection()
        income = conn.execute("""
            SELECT income_id, order_id, amount, description, income_date
            FROM income
            WHERE income_id = ? AND order_id = ?
        """, (income_id, order_id)).fetchone()
        
        if not income:
            flash('Доход не найден.', 'warning')
            return redirect(url_for('order_detail', order_id=order_id))
        
        if request.method == 'POST':
            amount = request.form.get('amount')
            description = request.form.get('description')
            income_date = request.form.get('income_date')
            
            # Валидация данных
            if not amount or not income_date:
                flash('Сумма и дата дохода обязательны.', 'danger')
                return redirect(url_for('edit_income', order_id=order_id, income_id=income_id))
            
            try:
                conn.execute("""
                    UPDATE income
                    SET amount = ?, description = ?, income_date = ?
                    WHERE income_id = ? AND order_id = ?
                """, (amount, description, income_date, income_id, order_id))
                conn.commit()
                flash('Доход успешно обновлён.', 'success')
                return redirect(url_for('order_detail', order_id=order_id))
            except Exception as e:
                flash('Произошла ошибка при обновлении дохода.', 'danger')
                logger.error(f"Error updating income {income_id} for order {order_id}: {e}")
                return redirect(url_for('edit_income', order_id=order_id, income_id=income_id))
        
        return render_template('edit_income.html', income=income, order_id=order_id)
    
    except Exception as e:
        flash('Произошла ошибка.', 'danger')
        logger.error(f"Error editing income {income_id} for order {order_id}: {e}")
        return redirect(url_for('order_detail', order_id=order_id))
    
    finally:
        conn.close()


@app.route('/order/<int:order_id>/expense/<int:expense_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_expense(order_id, expense_id):
    try:
        conn = get_db_connection()
        expense = conn.execute("""
            SELECT expense_id, order_id, amount, description, expense_date
            FROM expenses
            WHERE expense_id = ? AND order_id = ?
        """, (expense_id, order_id)).fetchone()
        
        if not expense:
            flash('Расход не найден.', 'warning')
            return redirect(url_for('order_detail', order_id=order_id))
        
        if request.method == 'POST':
            amount = request.form.get('amount')
            description = request.form.get('description')
            expense_date = request.form.get('expense_date')
            
            # Валидация данных
            if not amount or not expense_date:
                flash('Сумма и дата расхода обязательны.', 'danger')
                return redirect(url_for('edit_expense', order_id=order_id, expense_id=expense_id))
            
            try:
                conn.execute("""
                    UPDATE expenses
                    SET amount = ?, description = ?, expense_date = ?
                    WHERE expense_id = ? AND order_id = ?
                """, (amount, description, expense_date, expense_id, order_id))
                conn.commit()
                flash('Расход успешно обновлён.', 'success')
                return redirect(url_for('order_detail', order_id=order_id))
            except Exception as e:
                flash('Произошла ошибка при обновлении расхода.', 'danger')
                logger.error(f"Error updating expense {expense_id} for order {order_id}: {e}")
                return redirect(url_for('edit_expense', order_id=order_id, expense_id=expense_id))
        
        return render_template('edit_expense.html', expense=expense, order_id=order_id)
    
    except Exception as e:
        flash('Произошла ошибка.', 'danger')
        logger.error(f"Error editing expense {expense_id} for order {order_id}: {e}")
        return redirect(url_for('order_detail', order_id=order_id))
    
    finally:
        conn.close()

@app.route('/users/<int:user_id>/add_order', methods=['GET', 'POST'])
@login_required
def add_order(user_id):
    if request.method == 'POST':
        status = request.form.get('status')
        payment_method = request.form.get('payment_method')
        paid = request.form.get('paid')  # Значение будет 'on' или отсутствовать

        # Преобразование значения paid в 1 или 0
        paid = 1 if paid == 'on' else 0

        # Валидация данных
        valid_statuses = ['order_status_accepted', 'order_status_in_progress', 'order_status_waiting_payment',
                          'order_status_completed', 'order_status_pending', 'order_status_cancelled',
                          'order_status_returned']
        valid_payment_methods = ['cash', 'PayMe']

        if status not in valid_statuses:
            flash('Неверный статус заказа.', 'danger')
            return redirect(url_for('add_order', user_id=user_id))

        if payment_method not in valid_payment_methods:
            flash('Неверный метод оплаты.', 'danger')
            return redirect(url_for('add_order', user_id=user_id))

        try:
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("""
                INSERT INTO orders (user_id, status, payment_method, paid, order_date)
                VALUES (?, ?, ?, ?, DATETIME('now'))
            """, (user_id, status, payment_method, paid))
            conn.commit()
            conn.close()
            flash('Заказ успешно добавлен.', 'success')
            return redirect(url_for('users'))
        except Exception as e:
            flash('Произошла ошибка при добавлении заказа.', 'danger')
            app.logger.error(f"Error adding order for user {user_id}: {e}")
            return redirect(url_for('add_order', user_id=user_id))
    else:
        return render_template('add_order.html', user_id=user_id)
    
@app.route('/orders/<int:order_id>/delete', methods=['POST'])
@login_required
def delete_order(order_id):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            # Удаляем заказ из таблицы orders
            c.execute("DELETE FROM orders WHERE order_id = ?", (order_id,))
            conn.commit()
            if c.rowcount > 0:
                flash(f"Заказ {order_id} успешно удален.")
                logger.info(f"Order {order_id} deleted by admin.")
            else:
                flash(f"Заказ {order_id} не найден.")
                logger.warning(f"Order {order_id} not found for deletion.")
    except sqlite3.Error as e:
        flash("Произошла ошибка при удалении заказа.")
        logger.error(f"Error deleting order {order_id}: {e}")
    return redirect(url_for('orders'))

@app.route('/orders/<int:order_id>/update_status', methods=['POST'])
@login_required
def update_order_status_route(order_id):
    new_status_key = request.form.get('status')  # Предполагается, что форма передает ключ статуса
    if not new_status_key:
        flash("Статус не может быть пустым.")
        logger.warning(f"Empty status received for order {order_id}.")
        return redirect(url_for('order_detail', order_id=order_id))
    
    # Соответствие между текстом и ключом статуса (дублирование для консистентности)
    status_map = {
        "Принят": 'order_status_accepted',
        "Возврат": 'order_status_returned',
        "Отменен": 'order_status_cancelled',
        "Ожидание": 'order_status_pending',
        "Ожидание оплаты": 'order_status_waiting_payment',
        "Выполняется": 'order_status_in_progress',
        "Выполнен": 'order_status_completed'
    }
    
    # Проверка наличия статуса
    if new_status_key not in status_map.values():
        flash("Неверный статус. Попробуйте снова.")
        logger.warning(f"Invalid status key '{new_status_key}' received for order {order_id}.")
        return redirect(url_for('order_detail', order_id=order_id))
    
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            # Обновляем статус заказа в базе данных
            c.execute("UPDATE orders SET status = ? WHERE order_id = ?", (new_status_key, order_id))
            conn.commit()
            if c.rowcount > 0:
                flash(f"Статус заказа {order_id} обновлен.")
                logger.info(f"Order {order_id} status updated to '{new_status_key}'.")
                
                # Получаем информацию о заказе для отправки уведомлений
                order = get_order_by_id(order_id)
                if order:
                    user_id = order['user_id']
                    language = get_user_language(user_id)
                    
                    # Получаем перевод статуса на языке пользователя
                    translated_status = get_message(language, new_status_key)
                    
                    # Формирование сообщения для пользователя
                    additional_message = get_message(language, f"{new_status_key}_message")
                    status_message = (
                        f"{get_message(language, 'dear_client')}, "
                        f"{get_message(language, 'order_status_order_status_update')} #{order_id} "
                        f"{get_message(language, 'order_status_status_updated_to')} '{translated_status}'.\n\n"
                        f"{additional_message}\n\n{get_message(language, 'order_status_view_orders_info')}"
                    )
                    
                    # Отправка уведомления пользователю
                    send_notification(
                        chat_id=user_id,
                        message=status_message,
                        bot_token=app.config['TELEGRAM_BOT_TOKEN'],
                        parse_mode="HTML"
                    )
                    
                    # Получаем список подписчиков заказа
                    subscribers = get_order_subscribers(order_id)
                    
                    # Отправляем уведомление всем подписчикам с учётом их языка
                    for subscriber_id in subscribers:
                        subscriber_language = get_user_language(subscriber_id)
                        
                        # Получаем перевод статуса на языке подписчика
                        translated_status_subscriber = get_message(subscriber_language, new_status_key)
                        additional_message_subscriber = get_message(subscriber_language, f"{new_status_key}_message")
                        status_message_subscriber = (
                            f"{get_message(subscriber_language, 'dear_client')}, "
                            f"{get_message(subscriber_language, 'order_status_order_status_update_subscriber')} #{order_id} "
                            f"{get_message(subscriber_language, 'order_status_status_updated_to')} '{translated_status_subscriber}'.\n\n"
                            f"{additional_message_subscriber}\n\n{get_message(subscriber_language, 'order_subscribe_status_view_orders_info')}"
                        )
                        
                        # Отправляем уведомление подписчику
                        send_notification(
                            chat_id=subscriber_id,
                            message=status_message_subscriber,
                            bot_token=app.config['TELEGRAM_BOT_TOKEN'],
                            parse_mode="HTML"
                        )
            else:
                flash(f"Не удалось обновить статус заказа {order_id}.")
                logger.error(f"Failed to update status for order {order_id}.")
    except sqlite3.Error as e:
        flash("Произошла ошибка при обновлении статуса заказа.")
        logger.error(f"Database error when updating status for order {order_id}: {e}")
    
    return redirect(url_for('order_detail', order_id=order_id))



@app.route('/view_orders_by_status/<string:client_type>/<string:status>', methods=['GET'])
@login_required
def view_orders_by_status(client_type, status):
    try:
        with sqlite3.connect('bot.db') as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()

            # Определение фильтрации на основе типа клиента
            if client_type == 'current':
                # Текущие клиенты: заказы не завершены, не отменены и не возвращены
                status_filter = "o.status NOT IN ('order_status_completed', 'order_status_cancelled', 'order_status_returned')"
            elif client_type == 'previous':
                # Предыдущие клиенты: заказы завершены, отменены или возвращены
                status_filter = "o.status IN ('order_status_completed', 'order_status_cancelled', 'order_status_returned')"
            else:
                flash('Неверный тип клиента.', 'warning')
                return redirect(url_for('dashboard'))

            # Получение параметров фильтрации из запроса
            order_id = request.args.get('order_id', '').strip()
            user_id = request.args.get('user_id', '').strip()
            order_date = request.args.get('order_date', '').strip()

            # Построение дополнительного фильтрации
            additional_filters = []
            params = []

            if status != 'All':
                additional_filters.append("o.status = ?")
                params.append(status)

            if order_id:
                additional_filters.append("o.order_id = ?")
                params.append(order_id)

            if user_id:
                additional_filters.append("o.user_id = ?")
                params.append(user_id)

            if order_date:
                additional_filters.append("DATE(o.order_date) = DATE(?)")
                params.append(order_date)

            # Объединение фильтров
            if additional_filters:
                additional_filter = " AND " + " AND ".join(additional_filters)
            else:
                additional_filter = ""

            query = f"""
                SELECT o.order_id, o.user_id, o.order_date, o.status, o.paid
                FROM orders o
                JOIN users u ON o.user_id = u.user_id
                WHERE {status_filter} {additional_filter}
                ORDER BY o.order_date DESC
            """
            c.execute(query, params)
            orders = [dict(row) for row in c.fetchall()]

            # Подготовка фильтров для формы
            filters = {
                'order_id': order_id,
                'user_id': user_id,
                'order_date': order_date,
                'status': status
            }

            return render_template('orders_by_status.html',
                                   orders=orders,
                                   status=status,
                                   client_type=client_type.capitalize(),
                                   filters=filters)
    except Exception as e:
        logger.error(f"Ошибка при просмотре заказов по статусу: {e}")
        flash('Произошла ошибка при просмотре заказов.', 'danger')
        return redirect(url_for('dashboard'))
    
    

@app.route('/orders/<int:order_id>/update_payment_method', methods=['POST'])
@login_required
def update_payment_method_route(order_id):
    payment_method_key = request.form.get('payment_method')
    payment_link = request.form.get('payment_link')  # Не используется в текущей реализации

    if payment_method_key not in PAYMENT_METHOD_MAP.values():
        flash("Неверный метод оплаты.")
        logger.warning(f"Invalid payment method key '{payment_method_key}' for order {order_id}.")
        return redirect(url_for('order_detail', order_id=order_id))
    
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("UPDATE orders SET payment_method = ? WHERE order_id = ?", (payment_method_key, order_id))
            conn.commit()
            if c.rowcount > 0:
                display_method = next(k for k, v in PAYMENT_METHOD_MAP.items() if v == payment_method_key)
                flash(f"Метод оплаты заказа {order_id} обновлен на '{display_method}'.")
                logger.info(f"Order {order_id} payment method updated to '{payment_method_key}'.")
                # Здесь можно добавить логику уведомления пользователя о смене метода оплаты
            else:
                flash(f"Не удалось обновить метод оплаты заказа {order_id}.")
                logger.error(f"Failed to update payment method for order {order_id}.")
    except sqlite3.Error as e:
        flash("Произошла ошибка при обновлении метода оплаты.")
        logger.error(f"Error updating payment method for order_id {order_id}: {e}")
    
    return redirect(url_for('order_detail', order_id=order_id))

@app.route('/orders/<int:order_id>/update_payment_status', methods=['POST'])
@login_required
def update_payment_status_route(order_id):
    new_paid_status = request.form.get('paid')  # Предполагается, что форма передает '1' или '0'
    if new_paid_status not in ['0', '1']:
        flash("Неверный статус оплаты.")
        logger.warning(f"Invalid payment status '{new_paid_status}' for order {order_id}.")
        return redirect(url_for('order_detail', order_id=order_id))
    
    paid = int(new_paid_status)
    
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            # Обновляем статус оплаты в базе данных
            c.execute("UPDATE orders SET paid = ? WHERE order_id = ?", (paid, order_id))
            conn.commit()
            if c.rowcount > 0:
                flash(f"Статус оплаты заказа {order_id} обновлен.")
                logger.info(f"Order {order_id} payment status updated to {'Оплачено' if paid else 'Не оплачено'}.")
                
                # Получаем информацию о заказе для отправки уведомлений
                order = get_order_by_id(order_id)
                if order:
                    user_id = order['user_id']
                    language = get_user_language(user_id)
                    
                    # Определяем ключ статуса оплаты
                    status_key = 'payment_paid' if paid else 'payment_not_paid'
                    translated_status = get_message(language, status_key)
                    
                    # Формирование сообщения для пользователя
                    message_to_user = get_message(language, 'payment_status_updated', order_id=order_id, status=translated_status)
                    
                    # Отправка уведомления пользователю
                    send_notification(
                        chat_id=user_id,
                        message=message_to_user,
                        bot_token=app.config['TELEGRAM_BOT_TOKEN'],
                        parse_mode="HTML"
                    )
                    
                    # Получаем подписчиков и отправляем им уведомления
                    subscribers = get_order_subscribers(order_id)
                    for subscriber_id in subscribers:
                        subscriber_language = get_user_language(subscriber_id)
                        translated_status_subscriber = get_message(subscriber_language, status_key)
                        message_to_subscriber = get_message(subscriber_language, 'payment_status_updated_subscriber', order_id=order_id, status=translated_status_subscriber)
                        send_notification(
                            chat_id=subscriber_id,
                            message=message_to_subscriber,
                            bot_token=app.config['TELEGRAM_BOT_TOKEN'],
                            parse_mode="HTML"
                        )
            else:
                flash(f"Не удалось обновить статус оплаты заказа {order_id}.")
                logger.error(f"Failed to update payment status for order {order_id}.")
    except sqlite3.Error as e:
        flash("Произошла ошибка при обновлении статуса оплаты.")
        logger.error(f"Database error when updating payment status for order {order_id}: {e}")
    
    return redirect(url_for('order_detail', order_id=order_id))

@app.route('/orders/<int:order_id>/tasks')
@login_required
def manage_tasks(order_id):
    tasks = get_order_tasks(order_id)
    individual_services = get_individual_services(order_id)
    return render_template(
        'tasks.html',
        order_id=order_id,
        tasks=tasks,
        individual_services=individual_services,
        TASK_STATUS_MAP=TASK_STATUS_MAP
    )



@app.route('/orders/<int:order_id>/tasks/<int:task_id>/update', methods=['POST'])
@login_required
def update_task_status_web(order_id, task_id):
    new_status_key = request.form.get('status')  # Предполагается, что форма передаёт ключ статуса
    cloud_link = request.form.get('link')  # Если требуется для статуса "Выполнено"

    # Список допустимых ключей статусов задач
    valid_status_keys = {
        "task_status_completed",
        "task_status_not_completed",
        "task_status_in_progress"
    }

    if new_status_key not in valid_status_keys:
        flash("Неверный статус задачи.")
        logger.warning(f"Invalid task status key '{new_status_key}' for task {task_id} in order {order_id}.")
        return redirect(url_for('order_detail', order_id=order_id))

    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            if cloud_link:
                # Обновляем статус и сохраняем ссылку на облако
                c.execute("UPDATE order_tasks SET status = ?, cloud_link = ? WHERE task_id = ?", 
                          (new_status_key, cloud_link, task_id))
            else:
                # Обновляем только статус
                c.execute("UPDATE order_tasks SET status = ? WHERE task_id = ?", 
                          (new_status_key, task_id))
            conn.commit()

            if c.rowcount > 0:
                flash(f"Статус задачи {task_id} обновлен.")
                logger.info(f"Task {task_id} status updated to '{new_status_key}' for order {order_id}.")

                # Получаем информацию о задаче для уведомлений
                task = get_task_by_id(task_id) or get_individual_service_by_id(task_id)
                if task:
                    user_id = get_user_id_by_order_id(order_id)
                    language = get_user_language(user_id)

                    # Переводим описание задачи
                    translated_task_description = get_message(language, task['task_description'])

                    # Получаем перевод статуса на языке пользователя
                    translated_status = get_message(language, new_status_key)

                    # Формирование сообщения для пользователя
                    additional_message = get_message(language, f"{new_status_key}_message")
                    status_message = (
                        f"{get_message(language, 'dear_client')},\n\n"
                        f"{get_message(language, 'task_status_status')} '{translated_task_description}' "
                        f"{get_message(language, 'from_order')} #{order_id} "
                        f"{get_message(language, 'status_updated_to')} '{translated_status}'.\n\n"
                        f"{additional_message}\n\n"
                    )

                    # Если статус "Выполнено" и есть ссылка на облако, добавляем её в сообщение
                    if new_status_key == 'task_status_completed' and cloud_link:
                        status_message += (
                            f"{get_message(language, 'cloud_link_message')}: <a href='{cloud_link}'>{cloud_link}</a>\n\n"
                        )

                    # Добавляем инструкцию для просмотра статусов задач
                    status_message += get_message(language, 'view_tasks_info_message')

                    # Отправка уведомления пользователю
                    send_notification(
                        chat_id=user_id,
                        message=status_message,
                        bot_token=app.config['TELEGRAM_BOT_TOKEN'],
                        parse_mode="HTML"
                    )

                    # Получаем список подписчиков заказа
                    subscribers = get_order_subscribers(order_id)

                    # Отправляем уведомление всем подписчикам с учётом их языка
                    for subscriber_id in subscribers:
                        subscriber_language = get_user_language(subscriber_id)

                        # Переводим описание задачи на языке подписчика
                        translated_task_description_subscriber = get_message(subscriber_language, task['task_description'])

                        # Получаем перевод статуса на языке подписчика
                        translated_status_subscriber = get_message(subscriber_language, new_status_key)

                        # Формирование сообщения для подписчика
                        status_message_subscriber = (
                            f"{get_message(subscriber_language, 'dear_client')},\n\n"
                            f"{get_message(subscriber_language, 'task_status_status')} '{translated_task_description_subscriber}' "
                            f"{get_message(subscriber_language, 'from_order_subscriber')} #{order_id} "
                            f"{get_message(subscriber_language, 'status_updated_to')} '{translated_status_subscriber}'.\n\n"
                            f"{get_message(subscriber_language, f'{new_status_key}_message')}\n\n"
                        )

                        # Если статус "Выполнено" и есть ссылка на облако, добавляем её в сообщение подписчика
                        if new_status_key == 'task_status_completed' and cloud_link:
                            status_message_subscriber += (
                                f"{get_message(subscriber_language, 'cloud_link_message')}: <a href='{cloud_link}'>{cloud_link}</a>\n\n"
                            )

                        # Добавляем инструкцию для просмотра статусов задач подписчиком
                        status_message_subscriber += get_message(subscriber_language, 'view_subscribe_tasks_info_message')

                        # Отправляем уведомление подписчику
                        send_notification(
                            chat_id=subscriber_id,
                            message=status_message_subscriber,
                            bot_token=app.config['TELEGRAM_BOT_TOKEN'],
                            parse_mode="HTML"
                        )
                else:
                    flash("Не удалось получить информацию о задаче для отправки уведомлений.")
                    logger.error(f"Task {task_id} not found for order {order_id} when sending notifications.")
            else:
                flash(f"Не удалось обновить статус задачи {task_id}.")
                logger.error(f"Failed to update status for task {task_id} in order {order_id}.")
    except sqlite3.Error as e:
        flash("Произошла ошибка при обновлении статуса задачи.")
        logger.error(f"Database error when updating task status for task {task_id} in order {order_id}: {e}")

    return redirect(url_for('order_detail', order_id=order_id))



@app.route('/orders/<int:order_id>/properties')
@login_required
def manage_properties(order_id):
    properties = get_order_properties(order_id)
    return render_template(
        'properties.html',
        order_id=order_id,
        properties=properties,
        PROPERTY_STATUS_LIST=PROPERTY_STATUS_LIST
    )



from html import escape

@app.route('/orders/<int:order_id>/properties/<int:property_id>/update', methods=['POST'])
@login_required
def update_property_status_web(order_id, property_id):
    new_status_text = request.form.get('status')
    link_or_reason = request.form.get('link_or_reason')  # Используется для ссылки, причины или даты брони

    # Список допустимых статусов недвижимости
    PROPERTY_STATUS_LIST = [
        "Ожидание ответа агента",
        "Бронь забронирована",
        "Иду смотреть",
        "Идет просмотр объекта",
        "Объект просмотрен",
        "Результат готов",
        "Просмотр отменен"
    ]

    # Карта соответствий статусов
    PROPERTY_STATUS_MAP = {
        "Ожидание ответа агента": 'property_status_waiting_agent',
        "Бронь забронирована": 'property_status_booked',
        "Иду смотреть": 'property_status_going',
        "Идет просмотр объекта": 'property_status_in_progress',
        "Объект просмотрен": 'property_status_viewed',
        "Результат готов": 'property_status_ready',
        "Просмотр отменен": 'property_status_cancelled',
    }

    if new_status_text not in PROPERTY_STATUS_LIST:
        flash("Неверный статус недвижимости.")
        logger.warning(f"Invalid property status '{new_status_text}' for property {property_id} in order {order_id}.")
        return redirect(url_for('order_detail', order_id=order_id))

    # Валидация: если статус требует ввода ссылки, причины или даты брони, убедимся, что поле заполнено
    if new_status_text in ['Результат готов', 'Просмотр отменен', 'Бронь забронирована'] and not link_or_reason:
        flash("Пожалуйста, введите ссылку на результат, причину отмены или дату брони.")
        logger.warning(f"Missing link, reason или дата брони для property {property_id} in order {order_id}.")
        return redirect(url_for('order_detail', order_id=order_id))

    # Получаем ключ статуса из PROPERTY_STATUS_MAP
    status_key = PROPERTY_STATUS_MAP.get(new_status_text)
    if not status_key:
        flash("Неизвестный статус недвижимости.")
        logger.error(f"Status key for '{new_status_text}' not found in PROPERTY_STATUS_MAP.")
        return redirect(url_for('order_detail', order_id=order_id))

    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            # Обновляем статус недвижимости и сохраняем ссылку, причину или дату брони в cloud_link
            if new_status_text in ['Результат готов', 'Просмотр отменен', 'Бронь забронирована']:
                c.execute("UPDATE order_items SET status = ?, cloud_link = ? WHERE order_item_id = ?", 
                          (new_status_text, link_or_reason, property_id))
            else:
                c.execute("UPDATE order_items SET status = ? WHERE order_item_id = ?", 
                          (new_status_text, property_id))
            conn.commit()

            if c.rowcount > 0:
                flash(f"Статус недвижимости {property_id} обновлен на '{new_status_text}'.")
                logger.info(f"Property {property_id} status updated to '{new_status_text}' in order {order_id}.")

                # Получаем информацию о недвижимости для уведомлений
                property_info = get_property_by_id(property_id)
                if not property_info:
                    flash("Недвижимость не найдена.")
                    logger.error(f"Property with ID {property_id} not found in order {order_id}.")
                    return redirect(url_for('order_detail', order_id=order_id))

                user_id = get_user_id_by_order_id(order_id)
                language = get_user_language(user_id)

                # Используем title и link из property_info
                property_title = property_info.get('title') or get_message(language, 'property_added_by_user')
                property_link = property_info.get('link', '')

                # Экранируем заголовок и ссылку
                property_title_escaped = escape(property_title)
                property_link_escaped = escape(property_link)

                # Формируем кликабельное название недвижимости
                if property_link:
                    property_title_formatted = f"<a href='{property_link_escaped}'>{property_title_escaped}</a>"
                else:
                    property_title_formatted = property_title_escaped

                # Получаем перевод статуса
                translated_status = translate_status(new_status_text, language)

                # Получаем дополнительное сообщение
                additional_message = get_message(language, status_key)

                # Формируем основное сообщение для пользователя
                status_message = (
                    f"{get_message(language, 'dear_client')},\n\n"
                    f"{get_message(language, 'save_property_status_update_prefix')} '{property_title_formatted}' "
                    f"{get_message(language, 'save_property_in_order')} #{order_id} "
                    f"{get_message(language, 'save_property_has_been_updated_to')} '{translated_status}'.\n\n"
                    f"{additional_message}\n\n"
                )

                # Добавляем ссылку, причину отмены или дату брони
                if new_status_text == 'Результат готов' and link_or_reason:
                    status_message += (
                        f"{get_message(language, 'cloud_link_message')}: <a href='{escape(link_or_reason)}'>{escape(link_or_reason)}</a>\n\n"
                    )
                elif new_status_text == 'Просмотр отменен' and link_or_reason:
                    status_message += (
                        f"{get_message(language, 'save_property_cancellation_reason')}: {escape(link_or_reason)}\n\n"
                    )
                elif new_status_text == 'Бронь забронирована' and link_or_reason:
                    try:
                        # Преобразуем строку даты и времени в объект datetime
                        booking_datetime = datetime.strptime(link_or_reason, '%Y-%m-%dT%H:%M')
                        # Форматируем дату и время
                        booking_formatted = booking_datetime.strftime('%d-%m-%Y %H:%M')
                    except ValueError:
                        # Если формат некорректен, используем оригинальное значение
                        booking_formatted = escape(link_or_reason)
                        logger.error(f"Invalid datetime format for booking: {link_or_reason}")

                    status_message += (
                        f"{get_message(language, 'reservation_date_message')}: {booking_formatted}\n\n"
                    )

                # Добавляем инструкцию для просмотра статусов
                status_message += get_message(language, 'view_properties_info')

                # Отправляем уведомление пользователю
                send_notification(
                    chat_id=user_id,
                    message=status_message,
                    bot_token=app.config['TELEGRAM_BOT_TOKEN'],
                    parse_mode="HTML"
                )

                # Получаем список подписчиков заказа
                subscribers = get_order_subscribers(order_id)

                # Отправляем уведомление всем подписчикам с учётом их языка
                for subscriber_id in subscribers:
                    subscriber_language = get_user_language(subscriber_id)

                    # Переводим статус на язык подписчика
                    translated_status_subscriber = translate_status(new_status_text, subscriber_language)

                    # Получаем название и ссылку на недвижимость
                    property_title_subscriber = property_info.get('title') or get_message(subscriber_language, 'property_added_by_user')
                    property_link_subscriber = property_info.get('link', '')

                    # Экранируем заголовок и ссылку
                    property_title_escaped_subscriber = escape(property_title_subscriber)
                    property_link_escaped_subscriber = escape(property_link_subscriber)

                    # Формируем кликабельное название недвижимости
                    if property_link_subscriber:
                        property_title_formatted_subscriber = f"<a href='{property_link_escaped_subscriber}'>{property_title_escaped_subscriber}</a>"
                    else:
                        property_title_formatted_subscriber = property_title_escaped_subscriber

                    # Получаем дополнительное сообщение для подписчика
                    additional_message_subscriber = get_message(subscriber_language, status_key)

                    # Формируем основное сообщение для подписчика
                    status_message_subscriber = (
                        f"{get_message(subscriber_language, 'dear_client')},\n\n"
                        f"{get_message(subscriber_language, 'save_property_status_update_prefix')} '{property_title_formatted_subscriber}' "
                        f"{get_message(subscriber_language, 'save_property_in_order')} #{order_id} "
                        f"{get_message(subscriber_language, 'save_property_has_been_updated_to')} '{translated_status_subscriber}'.\n\n"
                        f"{additional_message_subscriber}\n\n"
                    )

                    # Добавляем ссылку, причину отмены или дату брони
                    if new_status_text == 'Результат готов' and link_or_reason:
                        status_message_subscriber += (
                            f"{get_message(subscriber_language, 'cloud_link_message')}: <a href='{escape(link_or_reason)}'>{escape(link_or_reason)}</a>\n\n"
                        )
                    elif new_status_text == 'Просмотр отменен' and link_or_reason:
                        status_message_subscriber += (
                            f"{get_message(subscriber_language, 'save_property_cancellation_reason')}: {escape(link_or_reason)}\n\n"
                        )
                    elif new_status_text == 'Бронь забронирована' and link_or_reason:
                        try:
                            # Преобразуем строку даты и времени в объект datetime
                            booking_datetime_subscriber = datetime.strptime(link_or_reason, '%Y-%m-%dT%H:%M')
                            # Форматируем дату и время
                            booking_formatted_subscriber = booking_datetime_subscriber.strftime('%d-%m-%Y %H:%M')
                        except ValueError:
                            # Если формат некорректен, используем оригинальное значение
                            booking_formatted_subscriber = escape(link_or_reason)
                            logger.error(f"Invalid datetime format for booking: {link_or_reason}")

                        status_message_subscriber += (
                            f"{get_message(subscriber_language, 'reservation_date_message')}: {booking_formatted_subscriber}\n\n"
                        )

                    # Добавляем инструкцию для подписчиков
                    status_message_subscriber += get_message(subscriber_language, 'view_subscribe_properties_info')

                    # Отправляем уведомление подписчику
                    send_notification(
                        chat_id=subscriber_id,
                        message=status_message_subscriber,
                        bot_token=app.config['TELEGRAM_BOT_TOKEN'],
                        parse_mode="HTML"
                    )

                return redirect(url_for('order_detail', order_id=order_id))
            else:
                flash(f"Не удалось обновить статус недвижимости {property_id}.")
                logger.error(f"Failed to update status for property {property_id} in order {order_id}.")
    except sqlite3.Error as e:
        flash("Произошла ошибка при обновлении статуса недвижимости.")
        logger.error(f"Database error when updating property status for property {property_id} in order {order_id}: {e}")

    return redirect(url_for('order_detail', order_id=order_id))


def get_property_by_id(property_id):
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT order_item_id, order_id, item_type, item, status, cloud_link
                FROM order_items
                WHERE order_item_id = ?
            """, (property_id,))
            row = c.fetchone()
            if row:
                order_item_id, order_id, item_type, item_content, status_text, cloud_link = row

                # Инициализация переменных
                link = ''
                title = ''

                if item_content.startswith('<div class='):
                    # Парсим HTML-код, чтобы извлечь название и ссылку
                    title = extract_title_from_html(item_content)
                    link = extract_link_from_html(item_content)
                elif item_content.startswith('http'):
                    # Если item является ссылкой, добавленной пользователем
                    title = 'Недвижимость, добавленная пользователем'
                    link = item_content
                else:
                    # Если формат item неизвестен
                    title = 'Неизвестная недвижимость'
                    link = ''

                return {
                    'order_item_id': order_item_id,
                    'order_id': order_id,
                    'item_type': item_type,
                    'item': item_content,
                    'status': status_text,
                    'cloud_link': cloud_link,
                    'link': link,
                    'title': title
                }
            else:
                return None
    except sqlite3.Error as e:
        logger.error(f"Error retrieving property by ID {property_id}: {e}")
        return None

def get_services(language='ru'):
    services = [
        # Индивидуальные услуги
        {
            "title_key": 'public_transport_service',
            "price": "£99 ($130)"
        },
        {
            "title_key": 'private_transfer_service',
            "price": "£300 ($381)"
        },
        {
            "title_key": 'sim_card_assistance_service',
            "price": "£23 ($30)"
        },
        {
            "title_key": 'oyster_card_assistance_service',
            "price": "£23 ($30)"
        },
        {
            "title_key": 'regular_reports_service',
            "price": "£38 ($50)"
        },
        {
            "title_key": 'housing_search_service',
            "price": "£45 ($60)"
        },
        {
            "title_key": 'area_consultation_service',
            "price": "£23 ($30)"
        },
        {
            "title_key": 'temporary_housing_assistance_service',
            "price": "£38 ($50)"
        },
        {
            "title_key": 'moving_assistance_service',
            "price": "£76 ($100)"
        },
        {
            "title_key": 'local_registration_service',
            "price": "£76 ($100)"
        },
        {
            "title_key": 'support_24_7_service',
            "price": "£76 ($100)"
        },
        {
            "title_key": 'neighbourhood_review_service',
            "price": "£38 ($50)"
        },
        {
            "title_key": 'utility_connection_service',
            "price": "£76 ($100)"
        },
        {
            "title_key": 'bank_account_assistance_service',
            "price": "£38 ($50)"
        },
        {
            "title_key": 'lease_agreement_assistance_service',
            "price": "£38 ($50)"
        },
        {
            "title_key": 'document_translation',
            "price": "£20 ($26)"
        },
        # Пакеты услуг
        {
            "title_key": 'package_meet_me',
            "price": "£114 ($150)",
            "details": [
                'airport_pickup',
                'transport_to_residence',
                'sim_card_assistance',
                'oyster_card_assistance',
                'regular_reports_to_parents'
            ]
        },
        {
            "title_key": 'package_housing',
            "price": "£342 ($450)",
            "details": [
                'airport_pickup',
                'transport_to_residence',
                'sim_card_assistance',
                'oyster_card_assistance',
                'regular_reports_to_parents',
                'housing_search',
                'area_consultation',
                'apartment_viewing',
                'temporary_housing_assistance',
                'moving_assistance'
            ]
        },
        {
            "title_key": 'premium_package',
            "price": "£647 ($850)",
            "details": [
                'airport_pickup',
                'transport_to_residence',
                'sim_card_assistance',
                'oyster_card_assistance',
                'regular_reports_to_parents',
                'housing_search',
                'area_consultation',
                'apartment_viewing',
                'temporary_housing_assistance',
                'moving_assistance',
                'local_registration_assistance',
                'support_24_7',
                'neighbourhood_review',
                'utility_connection',
                'bank_account_assistance',
                'lease_agreement_assistance',
                'gift_from_company'
            ]
        }
    ]

    # Переводим названия услуг
    for service in services:
        service['title'] = get_message(language, service['title_key'])
    return services

@app.route('/orders/<int:order_id>/tasks/add', methods=['GET', 'POST'])
@login_required
def add_task(order_id):
    form = AddTaskForm()
    services = get_services(current_user.language)  # Получаем услуги и пакеты с переводами
    form.service.choices = [(service['title_key'], service['title']) for service in services]
    
    if form.validate_on_submit():
        selected_service_key = form.service.data
        selected_service = next((s for s in services if s['title_key'] == selected_service_key), None)
        
        if not selected_service:
            flash('Выбранная услуга недействительна.', 'danger')
            logger.warning(f"Selected service key '{selected_service_key}' not found.")
            return redirect(url_for('add_task', order_id=order_id))
        
        try:
            with sqlite3.connect(DATABASE) as conn:
                c = conn.cursor()
                if 'details' in selected_service:
                    # Это пакет, добавляем каждую услугу из пакета как отдельную задачу
                    for detail_key in selected_service['details']:
                        # Получаем перевод названия детальной услуги
                        detail_title = get_message(current_user.language, detail_key)
                        c.execute("""
                            INSERT INTO order_tasks (order_id, task_description, status, cloud_link)
                            VALUES (?, ?, ?, ?)
                        """, (order_id, detail_key, 'task_status_in_progress', None))
                        logger.info(f"Added task '{detail_key}' from package '{selected_service_key}' to order {order_id}.")
                else:
                    # Это индивидуальная услуга, добавляем одну задачу
                    c.execute("""
                        INSERT INTO order_tasks (order_id, task_description, status, cloud_link)
                        VALUES (?, ?, ?, ?)
                    """, (order_id, selected_service_key, 'task_status_in_progress', None))
                    logger.info(f"Added task '{selected_service_key}' to order {order_id}.")
                conn.commit()
            flash('Задача(и) успешно добавлены.', 'success')
            return redirect(url_for('order_detail', order_id=order_id))
        except sqlite3.Error as e:
            flash('Произошла ошибка при добавлении задачи(ий).', 'danger')
            logger.error(f"Database error when adding task to order {order_id}: {e}")
            return redirect(url_for('order_detail', order_id=order_id))
    
    return render_template('add_task.html', order_id=order_id, form=form)

PROPERTY_STATUS_DISPLAY = {
    "Ожидание ответа агента": 'Ожидание ответа агента',
    "Бронь забронирована": 'Бронь забронирована',
    "Иду смотреть": 'Иду смотреть',
    "Идет просмотр объекта": 'Идет просмотр объекта',
    "Объект просмотрен": 'Объект просмотрен',
    "Результат готов": 'Результат готов',
    "Просмотр отменен": 'Просмотр отменен',
}

@app.route('/orders/<int:order_id>/properties/add', methods=['GET', 'POST'])
@login_required
def add_property(order_id):
    form = AddPropertyForm()
    
    if form.validate_on_submit():
        status = form.status.data  # Человекочитаемый статус
        link = form.link.data  # URL объекта
        additional_info = form.additional_info.data  # Дополнительная информация
        
        # Определение, что сохранять в 'cloud_link' в зависимости от статуса
        if status == "Бронь забронирована":
            cloud_link = additional_info  # Дата брони
        elif status == "Результат готов":
            cloud_link = additional_info  # Ссылка на результат
        elif status == "Просмотр отменен":
            cloud_link = additional_info  # Причина отмены
        else:
            cloud_link = None  # Для остальных статусов
        
        try:
            with sqlite3.connect(DATABASE) as conn:
                c = conn.cursor()
                c.execute("""
                    INSERT INTO order_items (order_id, item_type, item, status, cloud_link)
                    VALUES (?, ?, ?, ?, ?)
                """, (order_id, 'property', link, status, cloud_link))
                conn.commit()
            flash('Недвижимость успешно добавлена.', 'success')
            logger.info(f"Property added to order {order_id} with status '{status}'.")
            return redirect(url_for('order_detail', order_id=order_id))
        except sqlite3.Error as e:
            flash('Произошла ошибка при добавлении недвижимости.', 'danger')
            logger.error(f"Database error when adding property to order {order_id}: {e}")
            return redirect(url_for('order_detail', order_id=order_id))
    
    return render_template('add_property.html', order_id=order_id, form=form)

    
@app.route('/orders/<int:order_id>/tasks/<int:task_id>/delete', methods=['POST'])
@login_required
def delete_task(order_id, task_id):
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM order_tasks WHERE task_id = ? AND order_id = ?", (task_id, order_id))
            conn.commit()
        flash('Задача успешно удалена.')
    except sqlite3.Error as e:
        flash('Произошла ошибка при удалении задачи.')
        logger.error(f"Database error when deleting task {task_id} from order {order_id}: {e}")
    return redirect(url_for('order_detail', order_id=order_id))

@app.route('/orders/<int:order_id>/properties/<int:property_id>/delete', methods=['POST'])
@login_required
def delete_property(order_id, property_id):
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM order_items WHERE order_item_id = ? AND order_id = ?", (property_id, order_id))
            conn.commit()
        flash('Недвижимость успешно удалена.')
    except sqlite3.Error as e:
        flash('Произошла ошибка при удалении недвижимости.')
        logger.error(f"Database error when deleting property {property_id} from order {order_id}: {e}")
    return redirect(url_for('order_detail', order_id=order_id))

@app.route('/orders/<int:order_id>/events')
@login_required
def manage_events(order_id):
    events = get_order_events(order_id)
    return render_template('events.html', order_id=order_id, events=events)

@app.route('/orders/<int:order_id>/events/add', methods=['POST'])
@login_required
def add_event_route(order_id):
    description = request.form.get('description')
    link = request.form.get('link')  # Опционально
    event_date_str = request.form.get('event_date')  # Получаем строку даты из формы
    
    if not description or not event_date_str:
        flash("Описание и дата события обязательны.", 'danger')
        logger.warning(f"Empty event description or date for order {order_id}.")
        return redirect(url_for('order_detail', order_id=order_id))
    
    try:
        # Парсим дату и время, полученные из формы
        event_datetime = datetime.strptime(event_date_str, '%Y-%m-%dT%H:%M')
        # Применяем часовой пояс Лондона, если необходимо
        london_tz = pytz.timezone('Europe/London')
        event_datetime = london_tz.localize(event_datetime)
        # Форматируем дату для сохранения в базе данных
        event_timestamp = event_datetime.strftime('%Y-%m-%d %H:%M:%S')
        
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            # Сохраняем событие в базе данных
            c.execute("""
                INSERT INTO order_events (order_id, event_description, event_link, event_timestamp) 
                VALUES (?, ?, ?, ?)""", 
                (order_id, description, link, event_timestamp)
            )
            conn.commit()
            flash("Событие добавлено.", 'success')
            logger.info(f"Added event to order {order_id}: {description}, Link: {link}, Timestamp: {event_timestamp}")
        
        # Получаем информацию о заказе для отправки уведомлений
        order = get_order_by_id(order_id)
        if order:
            user_id = order['user_id']
            language = get_user_language(user_id)
            
            # Формируем сообщение для пользователя
            formatted_date = datetime.strptime(event_timestamp, '%Y-%m-%d %H:%M:%S').strftime('%d.%m.%Y %H:%M')
            
            # Используем разделенные ключи для добавления сообщения
            part1 = get_message(language, 'event_added_to_order_part1')
            part2 = get_message(language, 'event_added_to_order_part2')
            intro_message = f"{part1}{order_id} {part2}"
            
            event_description = f"📝 {get_message(language, 'event_description')}: {description}"
            event_time = f"🕒 {get_message(language, 'event_timestamp')}: {formatted_date}"
            
            if link:
                event_link = f"🔗 {get_message(language, 'event_link')}: <a href='{link}'>{link}</a>"
                message_to_user = (
                    f"{intro_message}\n\n"
                    f"{event_description}\n"
                    f"{event_time}\n"
                    f"{event_link}\n\n"
                    f"{get_message(language, 'view_user_events_info_message')}"
                )
            else:
                message_to_user = (
                    f"{intro_message}\n\n"
                    f"{event_description}\n"
                    f"{event_time}\n\n"
                    f"{get_message(language, 'view_user_events_info_message')}"
                )
            
            # Отправляем уведомление пользователю
            send_notification(
                chat_id=user_id,
                message=message_to_user,
                bot_token=app.config['TELEGRAM_BOT_TOKEN'],
                parse_mode="HTML"
            )
            
            # Отправляем уведомления подписчикам
            subscribers = get_order_subscribers(order_id)
            for subscriber_id in subscribers:
                subscriber_language = get_user_language(subscriber_id)
                
                # Используем разделенные ключи для добавления сообщения
                part1_sub = get_message(subscriber_language, 'event_added_to_order_part1_subscriber')
                part2_sub = get_message(subscriber_language, 'event_added_to_order_part2')
                intro_message_sub = f"{part1_sub}{order_id} {part2_sub}"
                
                event_description_sub = f"📝 {get_message(subscriber_language, 'event_description')}: {description}"
                event_time_sub = f"🕒 {get_message(subscriber_language, 'event_timestamp')}: {formatted_date}"
                
                if link:
                    event_link_sub = f"🔗 {get_message(subscriber_language, 'event_link')}: <a href='{link}'>{link}</a>"
                    message_to_subscriber = (
                        f"{intro_message_sub}\n\n"
                        f"{event_description_sub}\n"
                        f"{event_time_sub}\n"
                        f"{event_link_sub}\n\n"
                        f"{get_message(subscriber_language, 'view_subscribe_events_info_message')}"
                    )
                else:
                    message_to_subscriber = (
                        f"{intro_message_sub}\n\n"
                        f"{event_description_sub}\n"
                        f"{event_time_sub}\n\n"
                        f"{get_message(subscriber_language, 'view_subscribe_events_info_message')}"
                    )
                
                send_notification(
                    chat_id=subscriber_id,
                    message=message_to_subscriber,
                    bot_token=app.config['TELEGRAM_BOT_TOKEN'],
                    parse_mode="HTML"
                )
    except sqlite3.Error as e:
        flash("Произошла ошибка при добавлении события.")
        logger.error(f"Database error when adding event for order {order_id}: {e}")
    
    return redirect(url_for('order_detail', order_id=order_id))


@app.route('/order/<int:order_id>/event/<int:event_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event(order_id, event_id):
    try:
        conn = get_db_connection()
        event = conn.execute("""
            SELECT event_id, order_id, event_description, event_link, event_timestamp
            FROM order_events
            WHERE event_id = ? AND order_id = ?
        """, (event_id, order_id)).fetchone()
        
        if not event:
            flash('Событие не найдено.', 'warning')
            return redirect(url_for('order_detail', order_id=order_id))
        
        if request.method == 'POST':
            description = request.form.get('description')
            link = request.form.get('link')
            event_date = request.form.get('event_date')  # Предполагается, что вы добавите поле даты в форму
    
            # Валидация данных
            if not description or not event_date:
                flash('Описание и дата события обязательны.', 'danger')
                return redirect(url_for('edit_event', order_id=order_id, event_id=event_id))
            
            try:
                conn.execute("""
                    UPDATE order_events
                    SET event_description = ?, event_link = ?, event_timestamp = ?
                    WHERE event_id = ? AND order_id = ?
                """, (description, link, event_date, event_id, order_id))
                conn.commit()
                flash('Событие успешно обновлено.', 'success')
                return redirect(url_for('order_detail', order_id=order_id))
            except Exception as e:
                flash('Произошла ошибка при обновлении события.', 'danger')
                logger.error(f"Error updating event {event_id} for order {order_id}: {e}")
                return redirect(url_for('edit_event', order_id=order_id, event_id=event_id))
        
        return render_template('edit_event.html', event=event, order_id=order_id)
    
    except Exception as e:
        flash('Произошла ошибка.', 'danger')
        logger.error(f"Error editing event {event_id} for order {order_id}: {e}")
        return redirect(url_for('order_detail', order_id=order_id))
    
    finally:
        conn.close()

@app.route('/order/<int:order_id>/event/<int:event_id>/delete', methods=['POST'])
@login_required
def delete_event_route(order_id, event_id):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                DELETE FROM order_events
                WHERE event_id = ? AND order_id = ?
            """, (event_id, order_id))
            conn.commit()
        flash('Событие успешно удалено.', 'success')
    except Exception as e:
        flash('Произошла ошибка при удалении события.', 'danger')
        logger.error(f"Error deleting event {event_id} for order {order_id}: {e}")

    return redirect(url_for('order_detail', order_id=order_id))


@app.route('/orders/<int:order_id>/send_message', methods=['POST'])
@login_required
def send_message_route(order_id):
    message_text = request.form.get('message')

    if not message_text:
        flash("Сообщение не может быть пустым.", 'danger')
        return redirect(url_for('order_detail', order_id=order_id))
    
    try:
        # Получаем информацию о заказе
        order = get_order_by_id(order_id)
        if not order:
            flash(f"Заказ с ID {order_id} не найден.", 'warning')
            return redirect(url_for('dashboard'))
        
        user_id = order['user_id']
        
        # Получаем язык пользователя
        user_language = get_user_language(user_id)  # Функция уже определена
        
        # Предполагается, что у вас есть функция для получения текущего администратора
        admin_id = current_user.id  # Если у вас admin_id хранится иначе, скорректируйте эту строку
        
        # Сохранение сообщения в базе данных
        with get_db_connection() as conn:
            conn.execute("""
                INSERT INTO messages (order_id, sender_type, sender_id, message_text)
                VALUES (?, 'admin', ?, ?)
            """, (order_id, admin_id, message_text))
            conn.commit()
        
        # Формирование сообщения для отправки через Telegram на языке пользователя
        status_message = get_message(
            language=user_language,
            key='new_admin_message',
            order_id=order_id,
            message_text=escape(message_text)  # Экранирование текста сообщения
        )
        
        # Отправка уведомления пользователю через Telegram
        send_notification(
            chat_id=user_id,
            message=status_message,
            bot_token=app.config['TELEGRAM_BOT_TOKEN'],
            parse_mode="HTML"
        )
        
        flash("Сообщение успешно отправлено пользователю.", 'success')
    except Exception as e:
        flash("Произошла ошибка при отправке сообщения.", 'danger')
        logger.error(f"Error sending message for order {order_id}: {e}")
    
    return redirect(url_for('order_detail', order_id=order_id))

@app.route('/orders/<int:order_id>/credit_bonus', methods=['POST'])
@login_required
def credit_bonus_route(order_id):
    bonus_amount = request.form.get('bonus_amount')
    if not bonus_amount:
        flash("Необходимо указать сумму бонуса.")
        logger.warning(f"Bonus amount not provided for order {order_id}.")
        return redirect(url_for('order_detail', order_id=order_id))
    
    try:
        bonus_amount = float(bonus_amount)
        if bonus_amount <= 0:
            raise ValueError("Сумма бонуса должна быть положительной.")
    except ValueError as ve:
        flash(str(ve))
        logger.warning(f"Invalid bonus amount '{bonus_amount}' for order {order_id}: {ve}")
        return redirect(url_for('order_detail', order_id=order_id))
    
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("""
                UPDATE users 
                SET bonuses = bonuses + ? 
                WHERE user_id = (SELECT user_id FROM orders WHERE order_id = ?)
            """, (bonus_amount, order_id))
            conn.commit()
            if c.rowcount > 0:
                flash(f"Бонус в размере {bonus_amount} зачислен пользователю.")
                logger.info(f"Credited {bonus_amount} bonus to user for order {order_id}.")
                
                # Получаем информацию о заказе для отправки уведомлений
                order = get_order_by_id(order_id)
                if order:
                    user_id = order['user_id']
                    language = get_user_language(user_id)
                    
                    # Формируем сообщение для пользователя
                    bonus_message = (
                        get_message(language, 'bonus_received_message') + "\n\n" +
                        get_message(language, 'bonus_usage_instructions')
                    )
                    
                    # Отправляем уведомление пользователю
                    send_notification(
                        chat_id=user_id,
                        message=bonus_message,
                        bot_token=app.config['TELEGRAM_BOT_TOKEN'],
                        parse_mode="HTML"
                    )
            else:
                flash(f"Не удалось зачислить бонус пользователю для заказа {order_id}.")
                logger.error(f"Failed to credit bonus for order {order_id}.")
    except sqlite3.Error as e:
        flash("Произошла ошибка при зачислении бонуса.")
        logger.error(f"Database error when crediting bonus for order {order_id}: {e}")
    
    return redirect(url_for('order_detail', order_id=order_id))


@app.route('/orders/<int:order_id>/delete_bonus', methods=['POST'])
@login_required
def delete_bonus_route(order_id):
    delete_amount = request.form.get('delete_amount')
    if not delete_amount:
        flash("Необходимо указать сумму для удаления бонусов.")
        logger.warning(f"Delete amount not provided for order {order_id}.")
        return redirect(url_for('order_detail', order_id=order_id))
    
    try:
        delete_amount = float(delete_amount)
        if delete_amount <= 0:
            raise ValueError("Сумма для удаления должна быть положительной.")
    except ValueError as ve:
        flash(str(ve))
        logger.warning(f"Invalid delete amount '{delete_amount}' for order {order_id}: {ve}")
        return redirect(url_for('order_detail', order_id=order_id))
    
    order = get_order_by_id(order_id)
    if not order:
        flash(f"Заказ с ID {order_id} не найден.")
        logger.warning(f"Order with ID {order_id} not found when trying to delete bonus.")
        return redirect(url_for('orders'))
    
    user_id = order['user_id']
    success = delete_bonus(user_id, delete_amount)
    if success:
        flash(f"Бонус в размере {delete_amount} удалён у пользователя.")
        logger.info(f"Deleted {delete_amount} bonus from user {user_id} for order {order_id}.")
        # Здесь можно добавить логику уведомления пользователя об удалении бонуса
    else:
        flash("Не удалось удалить бонус.")
        logger.error(f"Failed to delete bonus from user {user_id} for order {order_id}.")
    return redirect(url_for('order_detail', order_id=order_id))

@app.route('/orders/<int:order_id>/messages', methods=['GET'])
@login_required
def get_messages(order_id):
    try:
        with get_db_connection() as conn:
            messages = conn.execute("""
                SELECT sender_type, sender_id, message_text, timestamp
                FROM messages
                WHERE order_id = ?
                ORDER BY timestamp ASC
            """, (order_id,)).fetchall()
            messages = [dict(message) for message in messages]
        return jsonify(messages)
    except Exception as e:
        logger.error(f"Error retrieving messages for order {order_id}: {e}")
        return jsonify({"error": "Произошла ошибка при получении сообщений."}), 500

@app.route('/feedbacks')
@login_required
def feedbacks():
    feedbacks = get_all_feedbacks()
    return render_template('feedbacks.html', feedbacks=feedbacks)

@app.route('/users/<int:user_id>')
@login_required
def user_detail(user_id):
    user = get_user_by_id(user_id)
    if not user:
        flash(f"Пользователь с ID {user_id} не найден.")
        logger.warning(f"User with ID {user_id} not found.")
        return redirect(url_for('users'))
    return render_template('user_detail.html', user=user)

# API routes (optional, for AJAX requests)
@app.route('/api/orders/<int:order_id>/tasks', methods=['GET'])
@login_required
def api_get_tasks(order_id):
    tasks = get_order_tasks(order_id)
    return jsonify(tasks)

@app.route('/api/orders/<int:order_id>/properties', methods=['GET'])
@login_required
def api_get_properties(order_id):
    properties = get_order_properties(order_id)
    return jsonify(properties)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
