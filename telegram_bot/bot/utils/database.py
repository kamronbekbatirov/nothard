
# bot/utils/database.py

import asyncio
import datetime
import json
import sqlite3
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



def init_db():
    conn = sqlite3.connect('bot.db')
    c = conn.cursor()
    
    # Таблица пользователей с дополнительными полями
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            website_id INTEGER UNIQUE,
            name TEXT,
            phone TEXT,
            email TEXT,
            bonuses INTEGER DEFAULT 0,
            language TEXT,
            password_hash TEXT
        )
    ''')

    # Таблица лайков бонусов
    c.execute('''CREATE TABLE IF NOT EXISTS bonus_likes (
                    user_id INTEGER,
                    order_id INTEGER,
                    property TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(user_id),
                    FOREIGN KEY(order_id) REFERENCES orders(order_id)
                )''')

    # Таблица корзины
    c.execute('''CREATE TABLE IF NOT EXISTS cart (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    item_type TEXT,
                    item TEXT,
                    status TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )''')

    # Таблица отзывов
    c.execute('''CREATE TABLE IF NOT EXISTS feedbacks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    feedback TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )''')

    # Таблица лайков
    c.execute('''CREATE TABLE IF NOT EXISTS likes (
                    user_id INTEGER,
                    property TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )''')

    # Таблица событий заказов
    c.execute('''CREATE TABLE IF NOT EXISTS order_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    event_description TEXT NOT NULL,
                    event_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    event_link TEXT,
                    FOREIGN KEY(order_id) REFERENCES orders(order_id) ON DELETE CASCADE
                )''')

    # Таблица элементов заказов
    c.execute('''CREATE TABLE IF NOT EXISTS order_items (
                    order_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER,
                    item_type TEXT,
                    item TEXT,
                    status TEXT,
                    cloud_link TEXT,
                    FOREIGN KEY(order_id) REFERENCES orders(order_id) ON DELETE CASCADE
                )''')

    # Таблица подписчиков заказов
    c.execute('''CREATE TABLE IF NOT EXISTS order_subscribers (
                    order_id INTEGER,
                    user_id INTEGER,
                    FOREIGN KEY(order_id) REFERENCES orders(order_id),
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )''')

    # Таблица заказов
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
                    order_id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    order_date TEXT,
                    status TEXT,
                    payment_method TEXT,
                    paid INTEGER,
                    amount REAL DEFAULT 0,
                    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )''')

    # Таблица задач заказа
    c.execute('''CREATE TABLE IF NOT EXISTS order_tasks (
                    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER,
                    task_description TEXT,
                    status TEXT,
                    cloud_link TEXT,
                    FOREIGN KEY(order_id) REFERENCES orders(order_id) ON DELETE CASCADE
                )''')

    # Новые таблицы

    # Таблица транзакций
    c.execute('''CREATE TABLE IF NOT EXISTS transactions (
                    transaction_id VARCHAR NOT NULL,
                    order_id INTEGER,
                    amount BIGINT,
                    create_time BIGINT,
                    state INTEGER,
                    perform_time BIGINT,
                    cancel_time BIGINT,
                    reason INTEGER,
                    PRIMARY KEY (transaction_id),
                    FOREIGN KEY(order_id) REFERENCES orders(order_id) ON DELETE CASCADE
                )''')

    # Таблица расходов
    c.execute('''CREATE TABLE IF NOT EXISTS expenses (
                    expense_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER,
                    amount REAL NOT NULL,
                    description TEXT,
                    expense_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(order_id) REFERENCES orders(order_id) ON DELETE CASCADE
                )''')

    # Таблица доходов
    c.execute('''CREATE TABLE IF NOT EXISTS income (
                    income_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER,
                    amount REAL NOT NULL,
                    description TEXT,
                    income_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(order_id) REFERENCES orders(order_id) ON DELETE CASCADE
                )''')

    # Таблица сообщений
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
                    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_id INTEGER NOT NULL,
                    sender_type TEXT CHECK(sender_type IN ('admin', 'user')) NOT NULL,
                    sender_id INTEGER NOT NULL,
                    message_text TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(order_id) REFERENCES orders(order_id) ON DELETE CASCADE
                )''')

    # Таблица задач
    c.execute('''CREATE TABLE IF NOT EXISTS tasks (
                    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    order_id INTEGER,
                    closed_at DATETIME,
                    FOREIGN KEY(order_id) REFERENCES orders(order_id) ON DELETE CASCADE
                )''')

    # Таблица запросов
    c.execute('''CREATE TABLE IF NOT EXISTS requests (
                    request_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    package_id INTEGER,
                    request TEXT,
                    status TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(user_id),
                    FOREIGN KEY(package_id) REFERENCES packages(package_id)
                )''')

    # Таблица пакетов
    c.execute('''CREATE TABLE IF NOT EXISTS packages (
                    package_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price REAL NOT NULL
                )''')

    conn.commit()
    conn.close()


def get_order_subscribers(order_id):
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        c.execute("SELECT user_id FROM order_subscribers WHERE order_id = ?", (order_id,))
        return [row[0] for row in c.fetchall()]

def add_property_to_order_db(order_id, item_type, item, status):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("INSERT INTO order_items (order_id, item_type, item, status) VALUES (?, ?, ?, ?)",
                      (order_id, item_type, item, status))
            conn.commit()
            logger.info(f"Property added to order: order_id={order_id}, item_type={item_type}, item={item}, status={status}")
    except sqlite3.Error as e:
        logger.error(f"Error adding property to order: {e}")

def add_like(user_id, property):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("INSERT INTO likes (user_id, property) VALUES (?, ?)", (user_id, property))
            conn.commit()
            logger.info(f"Like added: user_id={user_id}, property={property}")
    except sqlite3.Error as e:
        logger.error(f"Error adding like: {e}")

def get_likes(user_id):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("SELECT property FROM likes WHERE user_id = ?", (user_id,))
            likes = [row[0] for row in c.fetchall()]
            logger.info(f"Retrieved likes for user_id={user_id}")
            return likes
    except sqlite3.Error as e:
        logger.error(f"Error retrieving likes: {e}")
        return []

async def add_to_cart_db(user_id: int, item_type: str, item: str, status: str = None):
    try:
        if status is None:
            status = 'Ожидание ответа агента' if item_type == 'property' else 'Не выполнено'
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _add_to_cart_db, user_id, item_type, item, status)
        logger.info(f"Added to cart: user_id={user_id}, item_type={item_type}, item={item}, status={status}")
    except Exception as e:
        logger.error(f"Error adding to cart: {e}")

def _add_to_cart_db(user_id: int, item_type: str, item: str, status: str):
    try:
        if isinstance(item, dict):  # Если item - это словарь, преобразуем его в строку JSON
            item = json.dumps(item)
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("INSERT INTO cart (user_id, item_type, item, status) VALUES (?, ?, ?, ?)", (user_id, item_type, item, status))
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Error in _add_to_cart_db: {e}")

async def get_cart(user_id: int):
    try:
        loop = asyncio.get_event_loop()
        cart = await loop.run_in_executor(None, _get_cart, user_id)
        logger.info(f"Retrieved cart for user_id={user_id}")
        return cart
    except Exception as e:
        logger.error(f"Error getting cart: {e}")
        return []


def _get_cart(user_id: int):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("SELECT id, item_type, item FROM cart WHERE user_id = ?", (user_id,))
            items = []
            for row in c.fetchall():
                item_id, item_type, item = row
                try:
                    item = json.loads(item)  # Пробуем десериализовать строку JSON обратно в словарь
                except json.JSONDecodeError:
                    pass  # Если не удалось, значит это обычная строка
                items.append({"id": item_id, "item_type": item_type, "item": item})
            return items
    except sqlite3.Error as e:
        logger.error(f"Error in _get_cart: {e}")
        return []
    


def find_user_by_phone_or_email(value):
    try:
        with sqlite3.connect('bot.db') as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE phone = ? OR email = ?", (value, value))
            row = c.fetchone()
            if row:
                user_data = {
                    'website_id': row['website_id'],
                    'name': row['name'],
                    'phone': row['phone'],
                    'email': row['email'],
                    'bonuses': row['bonuses'],
                    'language': row['language'],
                }
                return user_data
            else:
                return None
    except sqlite3.Error as e:
        logger.error(f"Error in find_user_by_phone_or_email: {e}")
        return None

def update_user_profile_by_website_id(website_id, field, value):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute(f"UPDATE users SET {field} = ? WHERE website_id = ?", (value, website_id))
            conn.commit()
            logger.info(f"User profile updated: website_id={website_id}, field={field}, value={value}")
    except sqlite3.Error as e:
        logger.error(f"Error updating user profile by website_id: {e}")

def get_next_website_id():
    """
    Возвращает следующий доступный идентификатор website_id для нового пользователя.
    """
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("SELECT MAX(website_id) FROM users")
            max_id = c.fetchone()[0]
            if max_id is None:
                return 1
            else:
                return max_id + 1
    except sqlite3.Error as e:
        logger.error(f"Error in get_next_website_id: {e}")
        return 1  # Возвращаем 1 по умолчанию в случае ошибки

        
def clear_cart(user_id):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
            conn.commit()
            logger.info(f"Cleared cart for user_id={user_id}")
    except sqlite3.Error as e:
        logger.error(f"Error clearing cart: {e}")

async def remove_item_from_cart_db(user_id: int, item_id: int):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("DELETE FROM cart WHERE user_id = ? AND id = ?", (user_id, item_id))
            conn.commit()
            logger.info(f"Item removed from cart: user_id={user_id}, item_id={item_id}")
    except sqlite3.Error as e:
        logger.error(f"Error removing item from cart: {e}")
        raise e

def remove_item_from_cart_db(user_id: int, item_id: int):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("DELETE FROM cart WHERE user_id = ? AND id = ?", (user_id, item_id))
            conn.commit()
            logger.info(f"Item removed from cart: user_id={user_id}, item_id={item_id}")
    except sqlite3.Error as e:
        logger.error(f"Error removing item from cart: {e}")
        raise e

def remove_like_from_db(user_id, property):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("DELETE FROM likes WHERE user_id = ? AND property = ?", (user_id, property))
            conn.commit()
            logger.info(f"Removed like: user_id={user_id}, property={property}")
    except sqlite3.Error as e:
        logger.error(f"Error removing like: {e}")
        raise e
    

def update_property_status(order_item_id, status_key, cloud_link=None):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            if cloud_link:
                c.execute("UPDATE order_items SET status = ?, cloud_link = ? WHERE order_item_id = ?", (status_key, cloud_link, order_item_id))
            else:
                c.execute("UPDATE order_items SET status = ? WHERE order_item_id = ?", (status_key, order_item_id))
            conn.commit()
            logger.info(f"Updated property status: order_item_id={order_item_id}, status={status_key}, cloud_link={cloud_link}")
    except sqlite3.Error as e:
        logger.error(f"Error updating property status: {e}")

def get_user_language(user_id):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
            row = c.fetchone()
            if row:
                logger.info(f"Retrieved language for user_id={user_id}: {row[0]}")
                return row[0]
            return 'ru'  # Возвращаем 'ru' по умолчанию, если язык не найден
    except sqlite3.Error as e:
        logger.error(f"Error retrieving language for user_id={user_id}: {e}")
        return 'ru'  # Возвращаем 'ru' по умолчанию в случае ошибки

def get_user_bonuses(user_id):
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        c.execute("SELECT bonuses FROM users WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        return row[0] if row else 0

def decrement_user_bonuses(user_id):
    # Уменьшение количества бонусов на 1
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        c.execute("UPDATE users SET bonuses = bonuses - 1 WHERE user_id = ? AND bonuses > 0", (user_id,))
        conn.commit()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



import sqlite3
import datetime
import json
import logging

logger = logging.getLogger(__name__)



def create_order(user_id, items, payment_method="cash", paid=False, amount=0.0):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            # Получаем текущее время в UTC
            utc_now = datetime.datetime.utcnow()
            order_date = utc_now.strftime('%Y-%m-%d %H:%M:%S')
            status = 'order_status_waiting_payment'  # Статус "Ожидание оплаты"
            paid_status = 1 if paid else 0  # Конвертация boolean в целое число

            # Вставка нового заказа с указанной суммой
            try:
                c.execute(
                    "INSERT INTO orders (user_id, order_date, status, payment_method, paid, amount) VALUES (?, ?, ?, ?, ?, ?)",
                    (user_id, order_date, status, payment_method, paid_status, amount)
                )
                order_id = c.lastrowid
                logger.info(f"Order created with ID: {order_id}")
            except sqlite3.Error as e:
                logger.error(f"Error inserting order: {e}")
                return None

            # Определение пакетов услуг
            package_services = {
                "package_meet_me": [
                    "airport_pickup",
                    "transport_to_residence",
                    "sim_card_assistance",
                    "oyster_card_assistance",
                    "regular_reports_to_parents"
                ],
                "package_housing": [
                    "airport_pickup",
                    "transport_to_residence",
                    "sim_card_assistance",
                    "oyster_card_assistance",
                    "regular_reports_to_parents",
                    "housing_search",
                    "area_consultation",
                    "apartment_viewing",
                    "temporary_housing_assistance",
                    "moving_assistance"
                ],
                "premium_package": [
                    "airport_pickup",
                    "transport_to_residence",
                    "sim_card_assistance",
                    "oyster_card_assistance",
                    "regular_reports_to_parents",
                    "housing_search",
                    "area_consultation",
                    "apartment_viewing",
                    "temporary_housing_assistance",
                    "moving_assistance",
                    "local_registration_assistance",
                    "support_24_7",
                    "neighbourhood_review",
                    "utility_connection",
                    "bank_account_assistance",
                    "lease_agreement_assistance",
                    "gift_from_company"
                ]
            }

            # Вставка элементов заказа и задач
            for item in items:
                try:
                    # Определение статуса элемента
                    item_status = 'Ожидание ответа агента' if item['item_type'] == 'property' else 'task_status_not_completed'

                    # Если элемент является "сервисом" или "индивидуальной услугой", не вставляем его в order_items
                    if item['item_type'] == 'service':
                        service_key = item['item']['key']
                        tasks = package_services.get(service_key, item['item'].get('details', []))

                        for task in tasks:
                            task_status = 'task_status_not_completed'
                            # Вставка задачи для каждого сервиса в order_tasks
                            c.execute("INSERT INTO order_tasks (order_id, task_description, status) VALUES (?, ?, ?)", 
                                      (order_id, task, task_status))
                            logger.info(f"Task added to order {order_id}: {task}")
    
                    # Обработка индивидуальных услуг как задач
                    elif item['item_type'] == 'individual_service':
                        task_description = item['item']['key']
                        # Вставка индивидуальной услуги как задачи в order_tasks
                        c.execute("INSERT INTO order_tasks (order_id, task_description, status) VALUES (?, ?, ?)", 
                                  (order_id, task_description, 'task_status_not_completed'))
                        logger.info(f"Individual service added as task to order {order_id}: {task_description}")

                    # Вставляем только объекты недвижимости в order_items
                    elif item['item_type'] == 'property':
                        # Вставка элемента недвижимости в order_items
                        item_data = item['item'] if isinstance(item['item'], str) else json.dumps(item['item'])
                        c.execute("INSERT INTO order_items (order_id, item_type, item, status) VALUES (?, ?, ?, ?)", 
                                  (order_id, item['item_type'], item_data, item_status))
                        logger.info(f"Property added to order {order_id}: {item}")

                except sqlite3.Error as e:
                    logger.error(f"Error inserting order item or task: {e}")
                    return None

            # Подтверждение транзакции
            try:
                conn.commit()
            except sqlite3.Error as e:
                logger.error(f"Failed to commit transaction: {e}")
                return None

            logger.info(f"Order created successfully with ID: {order_id}")
            return order_id

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None


def remove_duplicates_from_order_tasks(order_id):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            # Удаляем дубликаты, оставляя только одну запись с минимальным task_id
            c.execute("""
                DELETE FROM order_tasks
                WHERE task_id NOT IN (
                    SELECT MIN(task_id)
                    FROM order_tasks
                    WHERE order_id = ?
                    GROUP BY task_description
                ) AND order_id = ?
            """, (order_id, order_id))
            conn.commit()
            logger.info(f"Removed duplicates from order_tasks for order_id={order_id}")
    except sqlite3.Error as e:
        logger.error(f"Error removing duplicates from order_tasks: {e}")


def add_task_if_not_exists(order_id, task_description):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            # Проверка на существование задачи перед добавлением
            c.execute("SELECT task_id FROM order_tasks WHERE order_id = ? AND task_description = ?", (order_id, task_description))
            if c.fetchone() is None:
                c.execute("INSERT INTO order_tasks (order_id, task_description, status) VALUES (?, ?, ?)", (order_id, task_description, 'Не выполнено'))
                conn.commit()
                logger.info(f"Task added to order {order_id}: {task_description}")
            else:
                logger.info(f"Task already exists for order {order_id}: {task_description}")
    except sqlite3.Error as e:
        logger.error(f"Error adding task: {e}")


        

async def get_order_tasks(order_id: int) -> List[Dict]:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _get_order_tasks, order_id)

def _get_order_tasks(order_id: int) -> List[Dict]:
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        c.execute("SELECT task_id, task_description, status, COALESCE(cloud_link, '') FROM order_tasks WHERE order_id = ?", (order_id,))
        tasks = [{"task_id": row[0], "task_description": row[1], "status": row[2], "cloud_link": row[3]} for row in c.fetchall()]
        logger.info(f"Tasks for order {order_id}: {tasks}")
        return tasks
    
def update_task_status(task_id, status, is_service=False):
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        if is_service:
            c.execute("UPDATE order_items SET status = ? WHERE order_item_id = ? AND item_type = 'individual_service'", (status, task_id))
        else:
            c.execute("UPDATE order_tasks SET status = ? WHERE task_id = ?", (status, task_id))
        conn.commit()

def get_task(task_id):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("SELECT task_id, order_id, task_description, status FROM order_tasks WHERE task_id = ?", (task_id,))
            row = c.fetchone()
            if row:
                logger.info(f"Retrieved task: task_id={task_id}")
                return {"task_id": row[0], "order_id": row[1], "description": row[2], "status": row[3]}
            return None
    except sqlite3.Error as e:
        logger.error(f"Error retrieving task: {e}")
        return None

def get_user_orders(user_id):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            # Получаем данные о заказах
            c.execute("SELECT order_id, order_date, status, payment_method, paid FROM orders WHERE user_id = ?", (user_id,))
            orders = c.fetchall()

            order_dict = {}

            for order in orders:
                order_id = order[0]
                # Теперь также извлекаем поле cloud_link
                c.execute("SELECT item_type, item, status, cloud_link FROM order_items WHERE order_id = ?", (order_id,))
                items = c.fetchall()

                order_dict[order_id] = {
                    "date": order[1],
                    "status": order[2],
                    "payment_method": order[3],
                    "paid": bool(order[4]),
                    "items": items
                }
            logger.info(f"Retrieved orders for user_id={user_id}")
            return order_dict
    except sqlite3.Error as e:
        logger.error(f"Error retrieving user orders: {e}")
        return {}

def get_all_orders():
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            # Извлечение всех данных, включая метод оплаты и статус оплаты
            c.execute("SELECT order_id, user_id, order_date, status, payment_method, paid FROM orders")
            orders = [
                {
                    "order_id": row[0],
                    "user_id": row[1],
                    "order_date": row[2],
                    "status": row[3],
                    "payment_method": row[4],
                    "paid": row[5]
                }
                for row in c.fetchall()
            ]
            logger.info("Retrieved all orders")
            return orders
    except sqlite3.Error as e:
        logger.error(f"Error retrieving all orders: {e}")
        return []


def decrement_user_bonuses(user_id):
    with sqlite3.connect('bot.db') as conn:
        c = conn.cursor()
        c.execute("UPDATE users SET bonuses = bonuses - 1 WHERE user_id = ? AND bonuses > 0", (user_id,))
        conn.commit()


def get_all_packages():
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM packages")
            packages = [{"name": row[1], "description": row[2], "price": row[3]} for row in c.fetchall()]
            logger.info("Retrieved all packages")
            return packages
    except sqlite3.Error as e:
        logger.error(f"Error retrieving all packages: {e}")
        return []

def get_package_by_name(name):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM packages WHERE name = ?", (name,))
            row = c.fetchone()
            if row:
                logger.info(f"Retrieved package by name: {name}")
                return {"package_id": row[0], "name": row[1], "description": row[2], "price": row[3]}
            return None
    except sqlite3.Error as e:
        logger.error(f"Error retrieving package by name: {e}")
        return None

def create_request(user_id, package_id):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("INSERT INTO requests (user_id, package_id, request, status) VALUES (?, ?, ?, ?)", (user_id, package_id, 'Запрос создан', 'В процессе'))
            conn.commit()
            logger.info(f"Request created: user_id={user_id}, package_id={package_id}")
    except sqlite3.Error as e:
        logger.error(f"Error creating request: {e}")

def get_user_requests(user_id):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM requests WHERE user_id = ?", (user_id,))
            requests = [{"package_id": row[2], "request": row[3], "status": row[4]} for row in c.fetchall()]
            logger.info(f"Retrieved requests for user_id={user_id}")
            return requests
    except sqlite3.Error as e:
        logger.error(f"Error retrieving user requests: {e}")
        return []

def get_package_by_id(package_id):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM packages WHERE package_id = ?", (package_id,))
            row = c.fetchone()
            if row:
                logger.info(f"Retrieved package by ID: {package_id}")
                return {"package_id": row[0], "name": row[1], "description": row[2], "price": row[3]}
            return None
    except sqlite3.Error as e:
        logger.error(f"Error retrieving package by ID: {e}")
        return None

def save_user(user_data: dict):
    """
    Сохраняет пользователя. Если 'password_hash' присутствует, создаёт или заменяет запись.
    Если 'password_hash' отсутствует, обновляет существующую запись без изменения пароля.
    """
    if 'password_hash' in user_data and user_data['password_hash']:
        create_user(user_data)
    else:
        update_user(user_data)

DB_PATH = '/var/www/nothard.uz/telegram_bot/bot.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def create_user(user_data: dict):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                INSERT INTO users (user_id, name, phone, email, language, password_hash, website_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_data['user_id'],
                user_data['name'],
                user_data['phone'],
                user_data['email'],
                user_data['language'],
                user_data['password_hash'],
                user_data['website_id']
            ))
            conn.commit()
            logger.info(f"New user created: {user_data}")
    except sqlite3.IntegrityError as e:
        logger.error(f"IntegrityError while creating user: {e}")
    except sqlite3.Error as e:
        logger.error(f"SQLite error while creating user: {e}")

def update_user(user_data: dict):
    try:
        with get_db_connection() as conn:
            c = conn.cursor()
            # Формируем список полей для обновления
            fields = []
            values = []
            for key in ['name', 'phone', 'email', 'language', 'website_id']:
                if key in user_data:
                    fields.append(f"{key} = ?")
                    values.append(user_data[key])
            
            # Добавляем условие для WHERE
            values.append(user_data['user_id'])
            set_clause = ", ".join(fields)
            sql = f"UPDATE users SET {set_clause} WHERE user_id = ?"
            
            c.execute(sql, values)
            conn.commit()
            logger.info(f"User updated: {user_data}")
    except sqlite3.Error as e:
        logger.error(f"SQLite error while updating user: {e}")


def is_user_registered(user_id):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            is_registered = c.fetchone() is not None
            logger.info(f"Checked if user is registered: user_id={user_id}, is_registered={is_registered}")
            return is_registered
    except sqlite3.Error as e:
        logger.error(f"Error checking if user is registered: {e}")
        return False

def get_user_profile(user_id):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("SELECT user_id, name, phone, email, bonuses, language FROM users WHERE user_id = ?", (user_id,))
            row = c.fetchone()
            if row:
                logger.info(f"Retrieved user profile: user_id={user_id}")
                return {
                    "user_id": row[0],
                    "name": row[1],
                    "phone": row[2],
                    "email": row[3],
                    "bonuses": row[4],  # Добавляем обработку bonuses
                    "language": row[5]  # Корректно извлекаем language
                }
            return None
    except sqlite3.Error as e:
        logger.error(f"Error retrieving user profile: {e}")
        return None

def update_user_profile(user_id, field, value):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", (value, user_id))
            conn.commit()
            logger.info(f"User profile updated: user_id={user_id}, field={field}, value={value}")
    except sqlite3.Error as e:
        logger.error(f"Error updating user profile: {e}")

def update_order_status(order_id, status_key, paid=None):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            if paid is not None:
                c.execute("UPDATE orders SET status = ?, paid = ? WHERE order_id = ?", (status_key, paid, order_id))
            else:
                c.execute("UPDATE orders SET status = ? WHERE order_id = ?", (status_key, order_id))
            conn.commit()
            logger.info(f"Order status updated: order_id={order_id}, status={status_key}, paid={paid}")
    except sqlite3.Error as e:
        logger.error(f"Error updating order status: {e}")




def get_all_users():
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM users")
            users = [{"user_id": row[0], "name": row[1], "phone": row[2], "email": row[3]} for row in c.fetchall()]
            logger.info("Retrieved all users")
            return users
    except sqlite3.Error as e:
        logger.error(f"Error retrieving all users: {e}")
        return []

def get_all_requests():
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM requests")
            requests = [{"user_id": row[1], "package_id": row[2], "request": row[3], "status": row[4]} for row in c.fetchall()]
            logger.info("Retrieved all requests")
            return requests
    except sqlite3.Error as e:
        logger.error(f"Error retrieving all requests: {e}")
        return []
    
def get_user_id_by_order_id(order_id):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("SELECT user_id FROM orders WHERE order_id = ?", (order_id,))
            row = c.fetchone()
            if row:
                logger.info(f"Retrieved user_id by order_id: {order_id}")
                return row[0]
            return None
    except sqlite3.Error as e:
        logger.error(f"Error retrieving user_id by order_id: {e}")
        return None

def save_feedback_to_db(user_id, feedback):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("INSERT INTO feedbacks (user_id, feedback) VALUES (?, ?)", (user_id, feedback))
            conn.commit()
            logger.info(f"Feedback saved: user_id={user_id}, feedback={feedback}")
    except sqlite3.Error as e:
        logger.error(f"Error saving feedback: {e}")

def get_all_feedbacks():
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("SELECT user_id, feedback FROM feedbacks")
            feedbacks = [{"user_id": row[0], "feedback": row[1]} for row in c.fetchall()]
            logger.info("Retrieved all feedbacks")
            return feedbacks
    except sqlite3.Error as e:
        logger.error(f"Error retrieving all feedbacks: {e}")
        return []
    

def add_bonus_like(user_id, order_id, property_html):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO bonus_likes (user_id, order_id, property) VALUES (?, ?, ?)",
                (user_id, order_id, property_html)
            )
            conn.commit()
            logging.info(f"Bonus like added for user {user_id} on order {order_id}")
    except sqlite3.Error as e:
        logging.error(f"Error adding bonus like for user {user_id} on order {order_id}: {e}")

def get_bonus_likes(user_id, order_id):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("SELECT property FROM bonus_likes WHERE user_id = ? AND order_id = ?", (user_id, order_id))
            likes = [row[0] for row in c.fetchall()]
            logger.info(f"Retrieved bonus likes for user_id={user_id}, order_id={order_id}")
            return likes
    except sqlite3.Error as e:
        logger.error(f"Error retrieving bonus likes: {e}")
        return []
    

def remove_bonus_like(user_id, property):
    try:
        with sqlite3.connect('bot.db') as conn:
            c = conn.cursor()
            c.execute("DELETE FROM bonus_likes WHERE user_id = ? AND property = ?", (user_id, property))
            conn.commit()
            logger.info(f"Removed bonus like: user_id={user_id}, property={property}")
    except sqlite3.Error as e:
        logger.error(f"Error removing bonus like: {e}")