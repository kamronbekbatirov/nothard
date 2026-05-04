# bot/utils/admin_functions.py

import sqlite3
from typing import List, Dict, Optional
import logging
from bs4 import BeautifulSoup
from datetime import datetime
import pytz

# Импортируем get_message из language.py
from bot.utils.admin_language import get_message

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Установите уровень логирования по необходимости

# Настройка обработчика логов (например, консольный)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

DATABASE = 'bot.db'  # Путь к вашей базе данных

# adminfunctions.py или webapp.py

def get_current_clients_count(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE client_type = 'current'")
    return c.fetchone()[0]

def get_previous_clients_count(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users WHERE client_type = 'previous'")
    return c.fetchone()[0]

def get_open_tasks_count(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tasks WHERE status != 'task_status_completed'")
    return c.fetchone()[0]

def get_closed_tasks_count(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tasks WHERE status = 'task_status_completed'")
    return c.fetchone()[0]

def get_open_admin_tasks_count(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tasks WHERE status = 'task_status_in_progress'")
    return c.fetchone()[0]

def get_closed_admin_tasks_count(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM tasks WHERE status = 'task_status_completed'")
    return c.fetchone()[0]

def get_open_property_requests_count(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM order_items WHERE status IN ('property_status_waiting_agent', 'property_status_going')")
    return c.fetchone()[0]

def get_closed_property_requests_count(conn):
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM order_items WHERE status IN ('property_status_booked', 'property_status_cancelled', 'property_status_viewed', 'property_status_ready')")
    return c.fetchone()[0]

def get_income_data(conn):
    # Пример функции для получения доходов за последние 12 месяцев
    c = conn.cursor()
    c.execute("""
        SELECT strftime('%m-%Y', order_date) as month, SUM(amount) as total
        FROM orders
        WHERE status = 'order_status_completed'
        GROUP BY month
        ORDER BY month
        LIMIT 12
    """)
    rows = c.fetchall()
    labels = [row['month'] for row in rows]
    data = [row['total'] for row in rows]
    return labels, data

def get_expenses_data(conn):
    # Пример функции для получения расходов за последние 12 месяцев
    c = conn.cursor()
    c.execute("""
        SELECT strftime('%m-%Y', expense_date) as month, SUM(amount) as total
        FROM expenses
        GROUP BY month
        ORDER BY month
        LIMIT 12
    """)
    rows = c.fetchall()
    labels = [row['month'] for row in rows]
    data = [row['total'] for row in rows]
    return labels, data


def get_admin_open_tasks(filters: Dict = None) -> List[Dict]:
    """
    Получает все текущие задачи администраторов из таблицы Tasks.
    Текущими считаются задачи со статусами 'task_status_not_completed' и 'task_status_in_progress'.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            base_query = """
                SELECT task_id, order_id, description, status, created_at, closed_at
                FROM Tasks
                WHERE status IN ('task_status_not_completed', 'task_status_in_progress')
            """
            params = []
            
            # Применение фильтров, если они заданы
            if filters:
                if 'task_id' in filters and filters['task_id']:
                    base_query += " AND task_id = ?"
                    params.append(filters['task_id'])
                if 'order_id' in filters and filters['order_id']:
                    base_query += " AND order_id = ?"
                    params.append(filters['order_id'])
                if 'description' in filters and filters['description']:
                    base_query += " AND description LIKE ?"
                    params.append(f"%{filters['description']}%")
            
            base_query += " ORDER BY task_id DESC LIMIT ? OFFSET ?"
            params.extend([filters.get('limit', 10), filters.get('offset', 0)])
            
            logger.debug(f"Executing Admin Open Tasks Query: {base_query}")
            logger.debug(f"With Parameters: {params}")
            c.execute(base_query, params)
            tasks = [dict(row) for row in c.fetchall()]
            logger.info(f"Retrieved {len(tasks)} open admin tasks.")
            return tasks
    except sqlite3.Error as e:
        logger.error(f"Error retrieving admin open tasks: {e}")
        return []

def get_admin_closed_tasks(filters: Dict = None) -> List[Dict]:
    """
    Получает все завершённые задачи администраторов из таблицы Tasks.
    Завершёнными считаются задачи со статусом 'task_status_completed'.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            base_query = """
                SELECT task_id, order_id, description, status, created_at, closed_at
                FROM Tasks
                WHERE status = 'task_status_completed'
            """
            params = []
            
            # Применение фильтров, если они заданы
            if filters:
                if 'task_id' in filters and filters['task_id']:
                    base_query += " AND task_id = ?"
                    params.append(filters['task_id'])
                if 'order_id' in filters and filters['order_id']:
                    base_query += " AND order_id = ?"
                    params.append(filters['order_id'])
                if 'description' in filters and filters['description']:
                    base_query += " AND description LIKE ?"
                    params.append(f"%{filters['description']}%")
            
            base_query += " ORDER BY task_id DESC LIMIT ? OFFSET ?"
            params.extend([filters.get('limit', 10), filters.get('offset', 0)])
            
            logger.debug(f"Executing Admin Closed Tasks Query: {base_query}")
            logger.debug(f"With Parameters: {params}")
            c.execute(base_query, params)
            tasks = [dict(row) for row in c.fetchall()]
            logger.info(f"Retrieved {len(tasks)} closed admin tasks.")
            return tasks
    except sqlite3.Error as e:
        logger.error(f"Error retrieving admin closed tasks: {e}")
        return []

def add_admin_task(description: str, status: str, order_id: int = None) -> bool:
    """
    Добавляет новую задачу администратора в таблицу Tasks.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            query = """
                INSERT INTO Tasks (description, status, created_at, order_id)
                VALUES (?, ?, datetime('now'), ?, ?)
            """
            c.execute(query, (description, status, order_id))
            conn.commit()
            logger.info(f"Added new admin task with ID: {c.lastrowid}")
            return True
    except sqlite3.Error as e:
        logger.error(f"Error adding admin task: {e}")
        return False

def update_admin_task_status(task_id: int, new_status: str) -> bool:
    """
    Обновляет статус задачи администратора. Если статус изменён на 'task_status_completed',
    устанавливает поле closed_at.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            if new_status == 'task_status_completed':
                query = """
                    UPDATE Tasks
                    SET status = ?, closed_at = datetime('now')
                    WHERE task_id = ?
                """
                c.execute(query, (new_status, task_id))
            else:
                query = """
                    UPDATE Tasks
                    SET status = ?
                    WHERE task_id = ?
                """
                c.execute(query, (new_status, task_id))
            conn.commit()
            logger.info(f"Updated status of admin task ID {task_id} to {new_status}.")
            return True
    except sqlite3.Error as e:
        logger.error(f"Error updating admin task status: {e}")
        return False
    


def get_all_users():
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        c.execute("SELECT user_id, name, phone, email, bonuses, language FROM users")
        return [{
            "user_id": row[0],
            "name": row[1],
            "phone": row[2],
            "email": row[3],
            "bonuses": row[4],
            "language": row[5]
        } for row in c.fetchall()]


def search_users(field, term):
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        allowed_fields = ['user_id', 'name', 'phone', 'email']  # Добавьте все разрешенные поля
        if field not in allowed_fields:
            field = 'name'  # Значение по умолчанию
        query = f"SELECT user_id, name, phone, email, bonuses, language FROM users WHERE {field} LIKE ?"
        c.execute(query, (f"%{term}%",))
        return [{
            "user_id": row[0],
            "name": row[1],
            "phone": row[2],
            "email": row[3],
            "bonuses": row[4],
            "language": row[5]
        } for row in c.fetchall()]


def search_orders(field, term, start_date, end_date, status, paid):
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()

        # Базовый запрос
        query = """
            SELECT o.order_id, o.user_id, o.order_date, o.status, o.paid, u.language
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            WHERE 1=1
        """
        params = []

        # Фильтрация по полю поиска (order_id или user_id)
        allowed_fields = ['order_id', 'user_id']
        if field in allowed_fields and term:
            query += f" AND o.{field} LIKE ?"
            params.append(f"%{term}%")

        # Фильтрация по диапазону дат
        if start_date:
            query += " AND DATE(o.order_date) >= DATE(?)"
            params.append(start_date)
        if end_date:
            query += " AND DATE(o.order_date) <= DATE(?)"
            params.append(end_date)

        # Фильтрация по статусу заказа
        if status:
            query += " AND o.status = ?"
            params.append(status)

        # Фильтрация по оплате
        if paid in ('0', '1'):
            query += " AND o.paid = ?"
            params.append(int(paid))

        query += " ORDER BY o.order_date DESC"  # Сортировка по дате заказа

        c.execute(query, params)
        orders = [{
            'order_id': row[0],
            'user_id': row[1],
            'order_date': row[2],
            'status': row[3],
            'paid': row[4],
            'language': row[5]
        } for row in c.fetchall()]
    return orders
    


def get_open_order_tasks() -> List[Dict]:
    """
    Получает все открытые задачи из таблицы order_tasks.
    Открытыми считаются задачи со статусами 'Выполняется' и 'Не выполнено'.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            open_statuses = ('Выполняется', 'Не выполнено')  # Измените в соответствии с вашими статусами
            query = """
                SELECT task_id, order_id, description, status, cloud_link
                FROM order_tasks 
                WHERE status IN (?, ?)
                ORDER BY task_id ASC
            """
            c.execute(query, open_statuses)
            tasks = [{
                "task_id": row[0],
                "order_id": row[1],
                "description": row[2],
                "status": row[3],
                "cloud_link": row[4]
            } for row in c.fetchall()]
            logger.info(f"Retrieved open tasks: {tasks}")
            return tasks
    except sqlite3.Error as e:
        logger.error(f"Error retrieving open tasks: {e}")
        return []

def get_closed_order_tasks() -> List[Dict]:
    """
    Получает все закрытые задачи из таблицы order_tasks.
    Закрытыми считаются задачи со статусами, отличными от 'Выполняется' и 'Не выполнено'.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            # Предполагаем, что закрытыми считаются все статусы, кроме открытых
            open_statuses = ('Выполняется', 'Не выполнено')  # Те же статусы, что и для открытых задач
            query = """
                SELECT task_id, order_id, description, status, cloud_link
                FROM order_tasks 
                WHERE status NOT IN (?, ?)
                ORDER BY task_id ASC
            """
            c.execute(query, open_statuses)
            tasks = [{
                "task_id": row[0],
                "order_id": row[1],
                "description": row[2],
                "status": row[3],
                "cloud_link": row[4]
            } for row in c.fetchall()]
            logger.info(f"Retrieved closed tasks: {tasks}")
            return tasks
    except sqlite3.Error as e:
        logger.error(f"Error retrieving closed tasks: {e}")
        return []
# bot/utils/admin_functions.py

def get_users(client_type: str, search_field: Optional[str] = None, search_term: Optional[str] = None, page: int = 1, per_page: int = 20) -> Dict:
    """
    Получает список пользователей (current, previous, no_orders, or all) с учетом поиска и пагинации.
    
    Args:
        client_type (str): 'current', 'previous', 'no_orders' или 'all'.
        search_field (Optional[str]): Поле для поиска ('user_id', 'name', 'phone', 'email').
        search_term (Optional[str]): Термин поиска.
        page (int): Номер страницы.
        per_page (int): Количество записей на странице.
    
    Returns:
        Dict: Словарь с пользователями и информацией о пагинации.
    """
    offset = (page - 1) * per_page
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            
            # Определяем условие для типа клиентов
            if client_type == 'current':
                status_condition = "o.status NOT IN ('order_status_completed', 'order_status_cancelled', 'order_status_returned')"
            elif client_type == 'previous':
                status_condition = "o.status IN ('order_status_completed', 'order_status_cancelled', 'order_status_returned')"
            elif client_type == 'no_orders':
                # Пользователи без заказов
                status_condition = "o.order_id IS NULL"
            elif client_type == 'all':
                status_condition = "1=1"  # Нет дополнительных условий
            else:
                raise ValueError("Invalid client_type. Must be 'current', 'previous', 'no_orders', or 'all'.")
    
            # Базовый запрос с LEFT JOIN для учета пользователей без заказов
            query = f"""
                SELECT u.user_id, u.name, u.phone, u.email, u.language, COUNT(o.order_id) as order_count
                FROM users u
                LEFT JOIN orders o ON u.user_id = o.user_id
                WHERE {status_condition}
            """
            params = []
    
            # Добавление условий поиска
            allowed_fields = ['user_id', 'name', 'phone', 'email']
            if search_field in allowed_fields and search_term:
                query += f" AND u.{search_field} LIKE ?"
                params.append(f"%{search_term}%")
    
            query += " GROUP BY u.user_id, u.name, u.phone, u.email, u.language"
    
            # Получение общего количества записей для пагинации
            if client_type == 'all':
                count_query = "SELECT COUNT(DISTINCT u.user_id) FROM users u LEFT JOIN orders o ON u.user_id = o.user_id WHERE 1=1"
                if search_field in allowed_fields and search_term:
                    count_query += f" AND u.{search_field} LIKE ?"
            elif client_type == 'no_orders':
                count_query = "SELECT COUNT(DISTINCT u.user_id) FROM users u LEFT JOIN orders o ON u.user_id = o.user_id WHERE o.order_id IS NULL"
                if search_field in allowed_fields and search_term:
                    count_query += f" AND u.{search_field} LIKE ?"
            else:
                count_query = f"SELECT COUNT(DISTINCT u.user_id) FROM users u JOIN orders o ON u.user_id = o.user_id WHERE {status_condition}"
                if search_field in allowed_fields and search_term:
                    count_query += f" AND u.{search_field} LIKE ?"
    
            c.execute(count_query, params if client_type != 'all' else params)
            total = c.fetchone()[0]
    
            # Добавление лимита и оффсета для пагинации
            query += " ORDER BY u.name ASC LIMIT ? OFFSET ?"
            params.extend([per_page, offset])
    
            c.execute(query, params)
            users = [{
                "user_id": row[0],
                "name": row[1],
                "phone": row[2],
                "email": row[3],
                "language": row[4],
                "order_count": row[5]
            } for row in c.fetchall()]
    
        return {
            "users": users,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page  # Округление вверх
        }
    except sqlite3.Error as e:
        logger.error(f"Database error when retrieving users: {e}")
        return {
            "users": [],
            "total": 0,
            "page": page,
            "per_page": per_page,
            "pages": 0
        }



def get_user_profile(user_id: int) -> Optional[Dict]:
    """
    Получает профиль пользователя по его ID.

    Args:
        user_id (int): ID пользователя.

    Returns:
        Optional[Dict]: Словарь с данными пользователя или None, если пользователь не найден.
    """
    query = "SELECT user_id, name, phone, email, bonuses, language FROM users WHERE user_id = ?"
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute(query, (user_id,))
            row = c.fetchone()
            if row:
                user = {
                    'user_id': row[0],
                    'name': row[1],
                    'phone': row[2],
                    'email': row[3],
                    'bonuses': row[4],
                    'language': row[5] if row[5] else 'ru'  # По умолчанию русский
                }
                logger.info(f"Retrieved profile for user_id {user_id}.")
                return user
            else:
                logger.warning(f"User with ID {user_id} not found.")
                return None
    except sqlite3.Error as e:
        logger.error(f"Database error when retrieving profile for user_id {user_id}: {e}")
        return None

def update_user_profile(user_id: int, field: str, new_value: str) -> bool:
    """
    Обновляет определенное поле профиля пользователя.

    Args:
        user_id (int): ID пользователя.
        field (str): Поле для обновления ('name', 'phone', 'email', 'language').
        new_value (str): Новое значение для поля.

    Returns:
        bool: True, если обновление прошло успешно, иначе False.
    """
    allowed_fields = ['name', 'phone', 'email', 'language']
    if field not in allowed_fields:
        logger.error(f"Недопустимое поле для обновления: {field}")
        return False

    query = f"UPDATE users SET {field} = ? WHERE user_id = ?"

    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute(query, (new_value, user_id))
            conn.commit()
            if c.rowcount > 0:
                logger.info(f"User {user_id} updated field '{field}' to '{new_value}'.")
                return True
            else:
                logger.warning(f"No user found with ID {user_id} to update field '{field}'.")
                return False
    except sqlite3.Error as e:
        logger.error(f"Database error when updating profile for user_id {user_id}: {e}")
        return False
    
def extract_title_from_html(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        # Ищем элемент h2 с классом 'propertyCard-title', как в вашей функции show_property
        title_element = soup.find("h2", class_="propertyCard-title")
        if title_element:
            title = title_element.get_text(strip=True)
            return title
        else:
            # Если не нашли, пытаемся найти h2 без класса
            title_element = soup.find("h2")
            if title_element:
                title = title_element.get_text(strip=True)
                return title
            else:
                # Если не нашли, возвращаем значение по умолчанию
                return 'Unknown Property'
    except Exception as e:
        logger.error(f"Error extracting title from HTML: {e}")
        return 'Unknown Property'
    
def translate_status(status, language):
    status_translations = {
    'Ожидание ответа агента': {
        'ru': 'Ожидание ответа агента',
        'en': 'Waiting for agent response',
        'uz': 'Agentdan javob kutilyapti'
    },
    'Бронь забронирована': {
        'ru': 'Бронь забронирована',
        'en': 'Viewing booked',
        'uz': 'Koʻrish uchun joy band qilindi'
    },
    'Иду смотреть': {
        'ru': 'Иду смотреть',
        'en': 'Going to view',
        'uz': 'Koʻrishga ketyapman'
    },
    'Идет просмотр объекта': {
        'ru': 'Идет просмотр объекта',
        'en': 'Viewing in progress',
        'uz': 'Koʻrish jarayonida'
    },
    'Объект просмотрен': {
        'ru': 'Объект просмотрен',
        'en': 'Property viewed',
        'uz': 'Koʻrilgan'
    },
    'Результат готов': {
        'ru': 'Результат готов',
        'en': 'Result ready',
        'uz': 'Natija tayyor'
    },
    'Просмотр отменен': {
        'ru': 'Просмотр отменен',
        'en': 'Viewing cancelled',
        'uz': 'Koʻrish bekor qilindi'
    }
}
        # Проверяем, есть ли перевод для данного статуса
    if status in status_translations:
        return status_translations[status].get(language, status)
    return status  # Если нет перевода, возвращаем исходный статус



def get_order_by_id(order_id: int) -> Optional[Dict]:
    """
    Получает информацию о заказе по его ID.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("SELECT order_id, user_id, order_date, status, paid, payment_method FROM orders WHERE order_id = ?", (order_id,))
            row = c.fetchone()
            if row:
                order = {
                    "order_id": row[0],
                    "user_id": row[1],
                    "order_date": row[2],
                    "status": row[3],
                    "paid": row[4],
                    "payment_method": row[5]
                }
                logger.info(f"Retrieved order {order_id} successfully.")
                return order
            logger.warning(f"Order with ID {order_id} not found.")
            return None
    except sqlite3.Error as e:
        logger.error(f"Error retrieving order by ID {order_id}: {e}")
        return None

def update_order_status(order_id: int, status: str) -> bool:
    """
    Обновляет статус заказа по его ID.
    Возвращает True, если обновление прошло успешно, иначе False.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("UPDATE orders SET status = ? WHERE order_id = ?", (status, order_id))
            conn.commit()
            if c.rowcount > 0:
                logger.info(f"Order {order_id} status updated to {status}.")
                return True
            else:
                logger.warning(f"No order found with ID {order_id} to update status.")
                return False
    except sqlite3.Error as e:
        logger.error(f"Error updating order status for order_id {order_id}: {e}")
        return False
    
def credit_bonus(user_id: int, amount: float) -> bool:
    """
    Зачисляет бонус пользователю.
    
    Args:
        user_id (int): ID пользователя.
        amount (float): Сумма бонуса для зачисления.
        
    Returns:
        bool: True, если бонус успешно зачислен, иначе False.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            
            # Проверяем, существует ли пользователь
            c.execute("SELECT bonuses FROM users WHERE user_id = ?", (user_id,))
            row = c.fetchone()
            if row is None:
                logger.warning(f"Пользователь с ID {user_id} не найден.")
                return False
            
            current_bonuses = row[0] if row[0] is not None else 0
            new_bonuses = current_bonuses + amount
            
            # Обновляем поле бонусов
            c.execute(
                "UPDATE users SET bonuses = ? WHERE user_id = ?",
                (new_bonuses, user_id)
            )
            conn.commit()
            
            if c.rowcount > 0:
                logger.info(f"Бонус в размере {amount} зачислен пользователю {user_id}. Текущий баланс бонусов: {new_bonuses}.")
                return True
            else:
                logger.error(f"Не удалось зачислить бонус пользователю {user_id}.")
                return False
    except sqlite3.Error as e:
        logger.error(f"Ошибка при зачислении бонуса пользователю {user_id}: {e}")
        return False

def delete_bonus(user_id: int, amount: float) -> bool:
    """
    Удаляет бонусы у пользователя.
    
    Args:
        user_id (int): ID пользователя.
        amount (float): Сумма бонуса для удаления.
        
    Returns:
        bool: True, если бонус успешно удалён, иначе False.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            
            # Проверяем, существует ли пользователь и достаточно ли у него бонусов
            c.execute("SELECT bonuses FROM users WHERE user_id = ?", (user_id,))
            row = c.fetchone()
            if row is None:
                logger.warning(f"Пользователь с ID {user_id} не найден.")
                return False
            
            current_bonuses = row[0] if row[0] is not None else 0
            if current_bonuses < amount:
                logger.warning(f"Недостаточно бонусов у пользователя {user_id}. Текущий баланс: {current_bonuses}, требуемая сумма: {amount}.")
                return False
            
            new_bonuses = current_bonuses - amount
            
            # Обновляем поле бонусов
            c.execute(
                "UPDATE users SET bonuses = ? WHERE user_id = ?",
                (new_bonuses, user_id)
            )
            conn.commit()
            
            if c.rowcount > 0:
                logger.info(f"Бонус в размере {amount} удалён у пользователя {user_id}. Текущий баланс бонусов: {new_bonuses}.")
                return True
            else:
                logger.error(f"Не удалось удалить бонус у пользователя {user_id}.")
                return False
    except sqlite3.Error as e:
        logger.error(f"Ошибка при удалении бонуса у пользователя {user_id}: {e}")
        return False
    



def get_all_feedbacks() -> List[Dict]:
    """
    Получает все отзывы из базы данных.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("SELECT user_id, feedback FROM feedbacks")
            feedbacks = [{"user_id": row[0], "feedback": row[1]} for row in c.fetchall()]
            logger.info("Retrieved all feedbacks successfully.")
            return feedbacks
    except sqlite3.Error as e:
        logger.error(f"Error retrieving all feedbacks: {e}")
        return []
    

def get_order_status_counts():
    """
    Возвращает словарь с подсчётом заказов по статусам.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT status, COUNT(*) as count
                FROM orders
                GROUP BY status
            """)
            results = c.fetchall()
            status_counts = {row[0]: row[1] for row in results}
        return status_counts
    except sqlite3.Error as e:
        logging.error(f"Ошибка при получении подсчёта статусов заказов: {e}")
        return {}

def get_order_subscribers(order_id: int) -> List[int]:
    """
    Получает список ID пользователей, подписанных на заказ.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("SELECT user_id FROM order_subscribers WHERE order_id = ?", (order_id,))
            subscribers = [row[0] for row in c.fetchall()]
            logger.info(f"Retrieved subscribers for order {order_id}: {subscribers}")
            return subscribers
    except sqlite3.Error as e:
        logger.error(f"Error retrieving subscribers for order_id {order_id}: {e}")
        return []

def get_all_orders():
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        c.execute("""
            SELECT o.order_id, o.user_id, o.order_date, o.status, o.paid, o.payment_method
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            ORDER BY o.order_date DESC
        """)
        orders = [{
            'order_id': row[0],
            'user_id': row[1],
            'order_date': row[2],
            'status': row[3],
            'paid': row[4],
            'payment_method': row[5]
        } for row in c.fetchall()]
    return orders

def add_order_event(order_id: int, event_description: str, event_link: Optional[str] = None) -> bool:
    """
    Добавляет событие к заказу.
    """
    try:
        # Получаем текущую дату и время в часовом поясе Лондона
        london_tz = pytz.timezone('Europe/London')
        event_timestamp = datetime.now(london_tz).strftime('%Y-%m-%d %H:%M:%S')

        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO order_events (order_id, event_description, event_link, event_timestamp) 
                VALUES (?, ?, ?, ?)""", 
                (order_id, event_description, event_link, event_timestamp)
            )
            conn.commit()
            logger.info(f"Added event to order {order_id}: {event_description}, Link: {event_link}")
            return True
    except sqlite3.Error as e:
        logger.error(f"Error adding event to order_id {order_id}: {e}")
        return False

def delete_order_event(event_id: int) -> bool:
    """
    Удаляет событие по его ID.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("DELETE FROM order_events WHERE event_id = ?", (event_id,))
            conn.commit()
            if c.rowcount > 0:
                logger.info(f"Deleted event with ID {event_id}.")
                return True
            else:
                logger.warning(f"No event found with ID {event_id} to delete.")
                return False
    except sqlite3.Error as e:
        logger.error(f"Error deleting event_id {event_id}: {e}")
        return False

def get_order_events(order_id: int) -> List[Dict]:
    """
    Получает события для конкретного заказа.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT event_id, event_description, event_link, event_timestamp 
                FROM order_events 
                WHERE order_id = ?
                ORDER BY event_timestamp DESC
                """, (order_id,))
            events = [{
                "event_id": row[0],
                "event_description": row[1],
                "event_link": row[2],
                "event_timestamp": row[3]
            } for row in c.fetchall()]
            logger.info(f"Retrieved events for order {order_id}: {events}")
            return events
    except sqlite3.Error as e:
        logger.error(f"Error retrieving events for order_id {order_id}: {e}")
        return []



def get_current_order_status_counts() -> Dict[str, int]:
    """
    Получает количество текущих заказов по каждому статусу.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT status, COUNT(*) 
                FROM orders 
                WHERE status IN ('OrderStatusAccepted', 'OrderStatusInProgress', 'OrderStatusWaitingPayment', 'OrderStatusWaiting')
                GROUP BY status
            """)
            rows = c.fetchall()
            status_counts = {row[0]: row[1] for row in rows}
            logger.info(f"Retrieved current order status counts: {status_counts}")
            return status_counts
    except sqlite3.Error as e:
        logger.error(f"Error retrieving current order status counts: {e}")
        return {}

def get_previous_order_status_counts() -> Dict[str, int]:
    """
    Получает количество предыдущих заказов по каждому статусу.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT status, COUNT(*) 
                FROM orders 
                WHERE status IN ('OrderStatusCompleted', 'OrderStatusCancelled', 'OrderStatusReturned')
                GROUP BY status
            """)
            rows = c.fetchall()
            status_counts = {row[0]: row[1] for row in rows}
            logger.info(f"Retrieved previous order status counts: {status_counts}")
            return status_counts
    except sqlite3.Error as e:
        logger.error(f"Error retrieving previous order status counts: {e}")
        return {}
    

def get_order_tasks(order_id: int) -> List[Dict]:
    """
    Получает список задач для заказа и добавляет переведённые описания и статусы.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT task_id, task_description, status, COALESCE(cloud_link, '') 
                FROM order_tasks 
                WHERE order_id = ?
                """, (order_id,))
            tasks = []
            for row in c.fetchall():
                task_id, task_description_key, status_key, cloud_link = row
                translated_description = get_message(task_description_key)
                status_display = get_message(status_key)
                tasks.append({
                    "task_id": task_id,
                    "translated_description": translated_description,
                    "status_key": status_key,            # Добавлено
                    "status_display": status_display,
                    "cloud_link": cloud_link
                })
            logger.info(f"Retrieved tasks for order {order_id}: {tasks}")
            return tasks
    except sqlite3.Error as e:
        logger.error(f"Error retrieving tasks for order_id {order_id}: {e}")
        return []

def get_individual_services(order_id: int) -> List[Dict]:
    """
    Получает индивидуальные услуги для заказа.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT order_item_id, item, status
                FROM order_items
                WHERE order_id = ? AND item_type = 'individual_service'
                """, (order_id,))
            services = [{
                "order_item_id": row[0],
                "item": row[1],
                "status": row[2]
            } for row in c.fetchall()]
            logger.info(f"Retrieved individual services for order {order_id}: {services}")
            return services
    except sqlite3.Error as e:
        logger.error(f"Error retrieving individual services for order_id {order_id}: {e}")
        return []

def get_task_by_id(task_id: int) -> Optional[Dict]:
    """
    Получает задачу по ее ID.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT task_id, order_id, task_description, status, cloud_link 
                FROM order_tasks 
                WHERE task_id = ?
                """, (task_id,))
            row = c.fetchone()
            if row:
                task = {
                    "task_id": row[0],
                    "order_id": row[1],
                    "task_description": row[2],
                    "status": row[3],
                    "cloud_link": row[4]
                }
                logger.info(f"Retrieved task {task_id}: {task}")
                return task
            logger.warning(f"Task with ID {task_id} not found.")
            return None
    except sqlite3.Error as e:
        logger.error(f"Error retrieving task by ID {task_id}: {e}")
        return None

def get_individual_service_by_id(order_item_id: int) -> Optional[Dict]:
    """
    Получает индивидуальную услугу по ее ID.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT order_item_id, order_id, item, status 
                FROM order_items 
                WHERE order_item_id = ? AND item_type = 'individual_service'
                """, (order_item_id,))
            row = c.fetchone()
            if row:
                service = {
                    "order_item_id": row[0],
                    "order_id": row[1],
                    "item": row[2],
                    "status": row[3]
                }
                logger.info(f"Retrieved individual service {order_item_id}: {service}")
                return service
            logger.warning(f"Individual service with ID {order_item_id} not found.")
            return None
    except sqlite3.Error as e:
        logger.error(f"Error retrieving individual service by ID {order_item_id}: {e}")
        return None

def update_order_payment_status(order_id: int, paid: int) -> bool:
    """
    Обновляет статус оплаты заказа.
    paid: 1 - Оплачено, 0 - Не оплачено
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("UPDATE orders SET paid = ? WHERE order_id = ?", (paid, order_id))
            conn.commit()
            if c.rowcount > 0:
                logger.info(f"Order {order_id} payment status updated to {'Оплачено' if paid else 'Не оплачено'}.")
                return True
            else:
                logger.warning(f"No order found with ID {order_id} to update payment status.")
                return False
    except sqlite3.Error as e:
        logger.error(f"Error updating payment status for order_id {order_id}: {e}")
        return False


def get_order_properties(order_id: int) -> List[Dict]:
    """
    Получает свойства (недвижимость) для заказа и добавляет переведённые заголовки и статусы.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("""
                SELECT order_item_id, item, status, cloud_link
                FROM order_items 
                WHERE order_id = ? AND item_type = 'property'
                """, (order_id,))
            properties = []
            for row in c.fetchall():
                order_item_id, item_content, status_text, cloud_link = row

                # Инициализация переменных
                translated_title = ''
                link = ''
                result_link = None
                cancel_reason = None

                if item_content.startswith('<div class='):
                    # Парсим HTML-код, чтобы извлечь название
                    translated_title = extract_title_from_html(item_content)
                    # Извлекаем ссылку из HTML, если необходимо
                    link = extract_link_from_html(item_content)
                elif item_content.startswith('http'):
                    # Если item является ссылкой, добавленной пользователем
                    translated_title = 'Недвижимость, добавленная пользователем'
                    link = item_content
                else:
                    # Если формат item неизвестен
                    translated_title = 'Неизвестная недвижимость'
                    link = ''

                # Обработка статусов
                status_display = status_text

                if status_text == 'Результат готов':
                    result_link = cloud_link
                elif status_text == 'Просмотр отменен':
                    cancel_reason = cloud_link

                properties.append({
                    "order_item_id": order_item_id,
                    "translated_title": translated_title,
                    "link": link,
                    "status_display": status_display,
                    "status_text": status_text,
                    "result_link": result_link,
                    "cancel_reason": cancel_reason,
                    "cloud_link": cloud_link
                })
            logger.info(f"Retrieved properties for order {order_id}: {properties}")
            return properties
    except sqlite3.Error as e:
        logger.error(f"Error retrieving properties for order_id {order_id}: {e}")
        return []
    
def extract_title_from_html(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        title_element = soup.find("h2", class_="propertyCard-title")
        if title_element:
            title = title_element.get_text(strip=True)
            return title
        else:
            return 'Неизвестная недвижимость'
    except Exception as e:
        logger.error(f"Error extracting title from HTML: {e}")
        return 'Неизвестная недвижимость'

def extract_link_from_html(html_content):
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        link_element = soup.find("a", class_="propertyCard-link")
        if link_element and link_element.get('href'):
            link = 'https://www.rightmove.co.uk' + link_element['href']
            return link
        else:
            return ''
    except Exception as e:
        logger.error(f"Error extracting link from HTML: {e}")
        return ''

def get_property_cloud_link(order_item_id: int) -> Optional[str]:
    """
    Получает cloud_link для конкретного свойства.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("SELECT cloud_link FROM order_items WHERE order_item_id = ?", (order_item_id,))
            row = c.fetchone()
            if row and row[0]:
                return row[0]
            return None
    except sqlite3.Error as e:
        logger.error(f"Error retrieving cloud_link for property {order_item_id}: {e}")
        return None
    


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

                if item_content.startswith('http'):
                    # Если item является ссылкой, добавленной пользователем
                    title = 'Недвижимость, добавленная пользователем'
                    link = item_content
                else:
                    # Парсим HTML-код, чтобы извлечь название и ссылку
                    property_soup = BeautifulSoup(item_content, "html.parser")
                    title_element = property_soup.find("h2", class_="propertyCard-title")
                    link_element = property_soup.find("a", class_="propertyCard-link")

                    title = title_element.get_text(strip=True) if title_element else 'Неизвестная недвижимость'
                    link = "https://www.rightmove.co.uk" + link_element["href"] if link_element else ''

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

def update_property_status(order_item_id: int, status_key: str, cloud_link: Optional[str] = None) -> bool:
    """
    Обновляет статус свойства (недвижимости) по его ID.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            if cloud_link:
                c.execute("""
                    UPDATE order_items 
                    SET status = ?, cloud_link = ? 
                    WHERE order_item_id = ?
                    """, (status_key, cloud_link, order_item_id))
            else:
                c.execute("""
                    UPDATE order_items 
                    SET status = ? 
                    WHERE order_item_id = ?
                    """, (status_key, order_item_id))
            conn.commit()
            if c.rowcount > 0:
                logger.info(f"Property {order_item_id} status updated to {status_key} with cloud_link={cloud_link}.")
                return True
            else:
                logger.warning(f"No property found with ID {order_item_id} to update status.")
                return False
    except sqlite3.Error as e:
        logger.error(f"Error updating property status for order_item_id {order_item_id}: {e}")
        return False
    

def send_message_to_user(user_id: int, message: str, bot_token: str) -> bool:
    """
    Отправляет сообщение пользователю через Telegram-бота.
    """
    import requests

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": user_id,
            "text": message,
            "parse_mode": "HTML"  # Или "Markdown" в зависимости от ваших потребностей
        }
        response = requests.post(url, data=payload)
        if response.status_code == 200:
            logger.info(f"Notification sent to user {user_id}.")
            return True
        else:
            logger.error(f"Failed to send notification to user {user_id}. Status Code: {response.status_code}, Response: {response.text}")
            return False
    except Exception as e:
        logger.error(f"Exception occurred while sending notification to user {user_id}: {e}")
        return False
    

def get_user_language(user_id):
    """
    Получает язык пользователя по его ID из базы данных.
    
    :param user_id: ID пользователя
    :return: Код языка (например, 'ru', 'uz') или 'ru' по умолчанию
    """
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
            row = c.fetchone()
            if row and row[0]:
                language = row[0]
                logger.info(f"Retrieved language for user_id={user_id}: {language}")
                return language
            else:
                logger.info(f"No language set for user_id={user_id}. Defaulting to 'ru'.")
                return 'ru'  # Возвращаем 'ru' по умолчанию, если язык не задан
    except sqlite3.Error as e:
        logger.error(f"Error retrieving language for user_id={user_id}: {e}")
        return 'ru'  # Возвращаем 'ru' по умолчанию в случае ошибки
    

def get_user_bonuses(user_id: int) -> float:
    """
    Извлекает текущий баланс бонусов пользователя.
    
    Args:
        user_id (int): ID пользователя.
        
    Returns:
        float: Текущий баланс бонусов или 0.0, если пользователь не найден.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            c.execute("SELECT bonuses FROM users WHERE user_id = ?", (user_id,))
            row = c.fetchone()
            if row and row[0] is not None:
                return row[0]
            else:
                return 0.0
    except sqlite3.Error as e:
        logger.error(f"Ошибка при получении бонусов пользователя {user_id}: {e}")
        return 0.0

def get_user_by_id(user_id):
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        c.execute("SELECT user_id, name, phone, email, bonuses, language FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if row:
            return {
                "user_id": row[0],
                "name": row[1],
                "phone": row[2],
                "email": row[3],
                "bonuses": row[4],
                "language": row[5]
            }
        else:
            return None

def update_order_task_status(task_id: int, status_key: str, cloud_link: Optional[str] = None) -> bool:
    """
    Обновляет статус задачи по ее ID. При необходимости добавляет ссылку на облако.
    """
    try:
        with sqlite3.connect(DATABASE) as conn:
            c = conn.cursor()
            if cloud_link:
                c.execute("""
                    UPDATE order_tasks 
                    SET status = ?, cloud_link = ? 
                    WHERE task_id = ?
                    """, (status_key, cloud_link, task_id))
            else:
                c.execute("""
                    UPDATE order_tasks 
                    SET status = ? 
                    WHERE task_id = ?
                    """, (status_key, task_id))
            conn.commit()
            if c.rowcount > 0:
                logger.info(f"Task {task_id} status updated to {status_key} with cloud_link={cloud_link}.")
                return True
            else:
                logger.warning(f"No task found with ID {task_id} to update status.")
                return False
    except sqlite3.Error as e:
        logger.error(f"Error updating task status for task_id {task_id}: {e}")
        return False