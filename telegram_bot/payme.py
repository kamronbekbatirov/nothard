from flask import Flask, request, jsonify
import time
import logging
import requests
import sqlite3

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Подключение к базе данных SQLite
conn = sqlite3.connect('bot.db', check_same_thread=False)
conn.row_factory = sqlite3.Row  # Позволяет обращаться к полям по имени
cursor = conn.cursor()

# Функции для работы с базой данных

def get_order_by_id(order_id):
    cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    return cursor.fetchone()

def get_transaction_by_id(transaction_id):
    cursor.execute("SELECT * FROM transactions WHERE transaction_id = ?", (transaction_id,))
    return cursor.fetchone()

def create_new_transaction(transaction_id, order_id, amount, create_time, state):
    cursor.execute("""
        INSERT INTO transactions (transaction_id, order_id, amount, create_time, state)
        VALUES (?, ?, ?, ?, ?)
    """, (transaction_id, order_id, amount, create_time, state))
    conn.commit()
    # Возвращаем созданную транзакцию в виде словаря
    return {
        'transaction_id': transaction_id,
        'order_id': order_id,
        'amount': amount,
        'create_time': create_time,
        'state': state,
        'perform_time': None  # Пока perform_time не установлен
    }

def update_transaction(transaction_id, state, perform_time):
    cursor.execute("""
        UPDATE transactions
        SET state = ?, perform_time = ?
        WHERE transaction_id = ?
    """, (state, perform_time, transaction_id))
    conn.commit()

def update_order_status(order_id, status, paid):
    cursor.execute("""
        UPDATE orders
        SET status = ?, paid = ?
        WHERE order_id = ?
    """, (status, paid, order_id))
    conn.commit()

def get_user_id_by_order_id(order_id):
    order = get_order_by_id(order_id)
    if order:
        return order['user_id']
    return None

def get_user_language(user_id):
    # Реализуйте функцию получения языка пользователя из вашей базы данных или логики
    return 'ru'

def get_message(language, key, **kwargs):
    messages = {
        'ru': {
            'payment_successful': "Оплата заказа #{order_id} успешно завершена.",
            'payment_error': "Ошибка при обработке оплаты заказа #{order_id}.",
            'order_not_found': "Заказ не найден.",
            'incorrect_amount': "Неверная сумма.",
            'unable_to_perform': "Невозможно выполнить операцию.",
            'transaction_not_found': "Транзакция не найдена."
        },
        # Добавьте другие языки при необходимости
    }
    message = messages.get(language, {}).get(key, '')
    return message.format(**kwargs)

def send_telegram_message(chat_id, text):
    bot_token = 'YOUR_TELEGRAM_BOT_TOKEN'  # Замените на ваш токен бота
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text
    }
    response = requests.post(url, data=payload)
    return response.json()

# Обработчик уведомлений от PayMe
@app.route('/', methods=['POST'], strict_slashes=False)
def payme_handler():
    data = request.get_json()
    logging.info(f"Received data: {data}")
    method = data.get('method')

    if method == 'CheckPerformTransaction':
        return check_perform_transaction(data)
    elif method == 'CreateTransaction':
        return create_transaction(data)
    elif method == 'PerformTransaction':
        return perform_transaction(data)
    elif method == 'CheckTransaction':
        return check_transaction(data)
    else:
        return jsonify({
            "error": {
                "code": -32601,
                "message": {
                    "ru": "Метод не найден",
                    "en": "Method not found"
                }
            }
        })

def check_perform_transaction(data):
    params = data.get('params', {})
    amount = params.get('amount')  # Сумма в тийинах
    account = params.get('account', {})
    order_id = account.get('order_id')

    # Проверяем, существует ли заказ с таким order_id и корректна ли сумма
    order = get_order_by_id(order_id)
    if not order:
        # Возвращаем ошибку, если заказ не найден
        return jsonify({
            "error": {
                "code": -31050,
                "message": {
                    "ru": "Заказ не найден",
                    "en": "Order not found"
                },
                "data": "order_id"
            }
        })
    # Преобразуем сумму из базы данных в тийины для сравнения
    order_amount_in_tiyins = int(float(order['amount']) * 100)
    if amount != order_amount_in_tiyins:
        # Возвращаем ошибку, если сумма не совпадает
        return jsonify({
            "error": {
                "code": -31001,
                "message": {
                    "ru": "Неверная сумма",
                    "en": "Incorrect amount"
                },
                "data": "amount"
            }
        })

    # Возвращаем allow: true, если все проверки пройдены
    return jsonify({
        "result": {
            "allow": True
        }
    })

def create_transaction(data):
    params = data.get('params', {})
    transaction_id = params.get('id')
    time_created = params.get('time')
    amount = params.get('amount')
    account = params.get('account', {})
    order_id = account.get('order_id')

    # Проверяем, существует ли транзакция с таким ID
    existing_transaction = get_transaction_by_id(transaction_id)
    if existing_transaction:
        # Если транзакция уже существует, возвращаем ее данные
        return jsonify({
            "result": {
                "create_time": existing_transaction['create_time'],
                "transaction": existing_transaction['transaction_id'],
                "state": existing_transaction['state']
            }
        })

    # Проверяем заказ
    order = get_order_by_id(order_id)
    if not order:
        # Возвращаем ошибку, если заказ не найден
        return jsonify({
            "error": {
                "code": -31050,
                "message": {
                    "ru": "Заказ не найден",
                    "en": "Order not found"
                },
                "data": "order_id"
            }
        })

    # Преобразуем сумму из базы данных в тийины для сравнения
    order_amount_in_tiyins = int(float(order['amount']) * 100)
    if amount != order_amount_in_tiyins:
        # Возвращаем ошибку, если сумма не совпадает
        return jsonify({
            "error": {
                "code": -31001,
                "message": {
                    "ru": "Неверная сумма",
                    "en": "Incorrect amount"
                },
                "data": "amount"
            }
        })

    # Создаем транзакцию
    transaction = create_new_transaction(
        transaction_id=transaction_id,
        order_id=order_id,
        amount=amount,
        create_time=time_created,
        state=1  # Состояние транзакции: 1 - создана
    )

    # Возвращаем данные транзакции
    return jsonify({
        "result": {
            "create_time": transaction['create_time'],
            "transaction": transaction['transaction_id'],
            "state": transaction['state']
        }
    })

def perform_transaction(data):
    params = data.get('params', {})
    transaction_id = params.get('id')

    # Получаем транзакцию из базы данных
    transaction = get_transaction_by_id(transaction_id)
    if not transaction:
        # Возвращаем ошибку, если транзакция не найдена
        return jsonify({
            "error": {
                "code": -31003,
                "message": {
                    "ru": "Транзакция не найдена",
                    "en": "Transaction not found"
                }
            }
        })

    if transaction['state'] == 2:
        # Если транзакция уже выполнена, возвращаем ее данные
        return jsonify({
            "result": {
                "transaction": transaction['transaction_id'],
                "perform_time": transaction['perform_time'],
                "state": transaction['state']
            }
        })

    if transaction['state'] != 1:
        # Если транзакция в неверном состоянии, возвращаем ошибку
        return jsonify({
            "error": {
                "code": -31008,
                "message": {
                    "ru": "Невозможно выполнить операцию",
                    "en": "Unable to perform operation"
                }
            }
        })

    # Обновляем транзакцию
    perform_time = int(time.time() * 1000)
    update_transaction(
        transaction_id=transaction_id,
        state=2,  # Состояние транзакции: 2 - выполнена
        perform_time=perform_time
    )

    # Обновляем статус заказа на "Оплачено"
    update_order_status(transaction['order_id'], "Оплачено", paid=1)

    # Уведомляем пользователя через Telegram
    user_id = get_user_id_by_order_id(transaction['order_id'])
    if user_id:
        language = get_user_language(user_id)
        success_message = get_message(language, 'payment_successful', order_id=transaction['order_id'])
        send_telegram_message(user_id, success_message)

    # Возвращаем данные транзакции
    return jsonify({
        "result": {
            "transaction": transaction['transaction_id'],
            "perform_time": perform_time,
            "state": 2
        }
    })

def check_transaction(data):
    params = data.get('params', {})
    transaction_id = params.get('id')

    # Получаем транзакцию из базы данных
    transaction = get_transaction_by_id(transaction_id)
    if not transaction:
        # Возвращаем ошибку, если транзакция не найдена
        return jsonify({
            "error": {
                "code": -31003,
                "message": {
                    "ru": "Транзакция не найдена",
                    "en": "Transaction not found"
                }
            }
        })

    # Формируем ответ с информацией о транзакции
    return jsonify({
        "result": {
            "create_time": transaction['create_time'],
            "perform_time": transaction['perform_time'] or 0,
            "cancel_time": 0,  # Если транзакция не отменена
            "transaction": transaction['transaction_id'],
            "state": transaction['state'],
            "reason": None  # Если транзакция не отменена
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)