from flask import Flask, request, jsonify
import time
import logging
import requests
from functools import wraps

# Импортируем SQLAlchemy модули
from sqlalchemy import create_engine, Column, Integer, String, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

app = Flask(__name__)

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Настройка подключения к базе данных
engine = create_engine('sqlite:////var/www/nothard.uz/payme/payme.db')
Session = sessionmaker(bind=engine)
Base = declarative_base()

# Определение моделей
class Order(Base):
    __tablename__ = 'orders'
    order_id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    amount = Column(BigInteger)
    status = Column(String)
    paid = Column(Integer)

class Transaction(Base):
    __tablename__ = 'transactions'
    transaction_id = Column(String, primary_key=True)
    order_id = Column(Integer)
    amount = Column(BigInteger)
    create_time = Column(BigInteger)
    state = Column(Integer)
    perform_time = Column(BigInteger)
    cancel_time = Column(BigInteger, nullable=True)
    reason = Column(Integer, nullable=True)

# Создаем таблицы
Base.metadata.create_all(engine)

# Создаем сессию
session = Session()

# Функции для работы с базой данных
def get_order_by_id(order_id):
    return session.query(Order).filter_by(order_id=order_id).first()

def get_transaction_by_id(transaction_id):
    return session.query(Transaction).filter_by(transaction_id=transaction_id).first()

def create_new_transaction(transaction_id, order_id, amount, create_time, state):
    transaction = Transaction(
        transaction_id=transaction_id,
        order_id=order_id,
        amount=amount,
        create_time=create_time,
        state=state
    )
    session.add(transaction)
    session.commit()
    return transaction

def update_transaction(transaction_id, state, perform_time=None, cancel_time=None, reason=None):
    transaction = get_transaction_by_id(transaction_id)
    if transaction:
        transaction.state = state
        if perform_time:
            transaction.perform_time = perform_time
        if cancel_time:
            transaction.cancel_time = cancel_time
        if reason:
            transaction.reason = reason
        session.commit()

def update_order_status(order_id, status, paid):
    order = get_order_by_id(order_id)
    if order:
        order.status = status
        order.paid = paid
        session.commit()

def get_user_id_by_order_id(order_id):
    order = get_order_by_id(order_id)
    if order:
        return order.user_id
    return None

def get_user_language(user_id):
    # Реализуйте функцию получения языка пользователя
    return 'ru'

def get_message(language, key, **kwargs):
    messages = {
        'ru': {
            'payment_successful': "Оплата заказа #{order_id} успешно завершена.",
            'payment_error': "Ошибка при обработке оплаты заказа #{order_id}.",
            'order_not_found': "Заказ не найден.",
            'incorrect_amount': "Неверная сумма.",
            'unable_to_perform': "Невозможно выполнить операцию.",
            'transaction_not_found': "Транзакция не найдена.",
            'account_already_processing': "Счет уже обрабатывается другой транзакцией.",
            'transaction_canceled': "Транзакция отменена.",
            'invalid_reason': "Неверная причина отмены.",
            'authorization_failed': "Неверный логин или пароль."  # Обновлено
        },
        'en': {
            'payment_successful': "Payment for order #{order_id} was successful.",
            'payment_error': "Error processing payment for order #{order_id}.",
            'order_not_found': "Order not found.",
            'incorrect_amount': "Incorrect amount.",
            'unable_to_perform': "Unable to perform operation.",
            'transaction_not_found': "Transaction not found.",
            'account_already_processing': "Account is already being processed by another transaction.",
            'transaction_canceled': "Transaction has been canceled.",
            'invalid_reason': "Invalid cancellation reason.",
            'authorization_failed': "Invalid login or password."  # Обновлено
        },
        'uz': {
            'payment_successful': "Buyurtma #{order_id} uchun to'lov muvaffaqiyatli amalga oshirildi.",
            'payment_error': "Buyurtma #{order_id} uchun to'lovni qayta ishlashda xato yuz berdi.",
            'order_not_found': "Buyurtma topilmadi.",
            'incorrect_amount': "Noto'g'ri summa.",
            'unable_to_perform': "Operatsiyani bajarish mumkin emas.",
            'transaction_not_found': "Tranzaksiya topilmadi.",
            'account_already_processing': "Hisob boshqa tranzaksiya tomonidan qayta ishlanmoqda.",
            'transaction_canceled': "Tranzaksiya bekor qilindi.",
            'invalid_reason': "Bekor qilish sababi noto'g'ri.",
            'authorization_failed': "Noto'g'ri login yoki parol."  # Обновлено
        }
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

# Допустимые Base64 закодированные строки (без "Basic ")
ALLOWED_AUTH_HEADERS = {
    "UGF5Y29tOnlGcVdPNiV3bSZCb0J1ZloxRkEyZ3cybmNaQVh6MUpiV3dGWg==",  # Sandbox: "Paycom:yFWO6wm&BoBuzZFA2gw2ncZAHz1JbWwFZ"
    "UGF5Y29tOkhpRlc0WVh1TlRGZDNacVo0OGtuellTSVA4WVN1UyN5akJkUw=="   # Production: "Paycom:HiFW4YXuNTFd3ZqZ48knzYSIP8YSuS#yjBdS"
}

def authorize(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '').strip()
        logging.info(f"Received Authorization header: '{auth_header}'")

        # Проверяем, начинается ли заголовок с "Basic " (без учета регистра)
        if not auth_header.lower().startswith('basic '):
            logging.warning("Authorization header does not start with 'Basic '")
            return jsonify({
                "error": {
                    "code": -32504,
                    "message": {
                        "ru": "Неверный логин или пароль.",
                        "en": "Invalid login or password.",
                        "uz": "Noto'g'ri login yoki parol."
                    }
                }
            })

        # Извлекаем Base64 часть заголовка
        encoded_credentials = auth_header[6:].strip()  # Удаляем 'Basic ' (6 символов) и пробелы

        logging.info(f"Extracted Base64 credentials: '{encoded_credentials}'")

        if encoded_credentials not in ALLOWED_AUTH_HEADERS:
            logging.warning("Base64 credentials do not match any allowed credentials")
            return jsonify({
                "error": {
                    "code": -32504,
                    "message": {
                        "ru": "Неверный логин или пароль.",
                        "en": "Invalid login or password.",
                        "uz": "Noto'g'ri login yoki parol."
                    }
                }
            })

        return f(*args, **kwargs)
    return decorated_function

@app.route('/', methods=['POST'], strict_slashes=False)
@authorize
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
    elif method == 'CancelTransaction':
        return cancel_transaction(data)
    elif method == 'GetStatement':
        return get_statement(data)
    elif method == 'ChangePassword':
        return change_password(data)
    else:
        # Возвращаем ошибку, если метод не найден
        return jsonify({
            "error": {
                "code": -32601,
                "message": {
                    "ru": "Метод не найден",
                    "en": "Method not found",
                    "uz": "Metod topilmadi"
                }
            }
        })  # Убираем ', 404'

# Реализация методов

def check_perform_transaction(data):
    try:
        logging.info("Starting check_perform_transaction")
        params = data.get('params', {})
        amount = int(params.get('amount'))
        account = params.get('account', {})
        order_id = int(account.get('order_id')) if account.get('order_id') else None

        logging.info(f"CheckPerformTransaction - Order ID: {order_id}, Amount: {amount}")

        if not order_id:
            logging.warning("order_id is missing in account")
            return jsonify({
                "error": {
                    "code": -31050,
                    "message": {
                        "ru": "Заказ не найден.",
                        "en": "Order not found.",
                        "uz": "Buyurtma topilmadi."
                    },
                    "data": "order_id"
                }
            })

        # Проверяем, существует ли заказ с таким order_id и корректна ли сумма
        order = get_order_by_id(order_id)
        if not order:
            logging.warning("Order not found")
            # Возвращаем ошибку, если заказ не найден
            return jsonify({
                "error": {
                    "code": -31050,
                    "message": {
                        "ru": "Заказ не найден.",
                        "en": "Order not found.",
                        "uz": "Buyurtma topilmadi."
                    },
                    "data": "order_id"
                }
            })

        if amount != order.amount:
            logging.warning(f"Incorrect amount: {amount} != {order.amount}")
            # Возвращаем ошибку, если сумма не совпадает
            return jsonify({
                "error": {
                    "code": -31001,
                    "message": {
                        "ru": "Неверная сумма.",
                        "en": "Incorrect amount.",
                        "uz": "Noto'g'ri summa."
                    },
                    "data": "amount"
                }
            })

        # Возвращаем allow: true, если все проверки пройдены
        logging.info("CheckPerformTransaction successful")
        return jsonify({
            "result": {
                "allow": True
            }
        })
    except Exception as e:
        logging.exception("Error in check_perform_transaction:")
        # Откатываем сессию в случае ошибки
        session.rollback()
        # Возвращаем ошибку согласно спецификации JSON-RPC
        return jsonify({
            "error": {
                "code": -32400,
                "message": {
                    "ru": "Внутренняя ошибка сервера.",
                    "en": "Internal server error.",
                    "uz": "Ichki server xatosi."
                }
            }
        })

def create_transaction(data):
    try:
        logging.info("Starting create_transaction")
        params = data.get('params', {})
        transaction_id = params.get('id')
        time_created = params.get('time')
        amount = int(params.get('amount'))
        account = params.get('account', {})
        order_id = int(account.get('order_id')) if account.get('order_id') else None

        logging.info(f"Transaction ID: {transaction_id}, Order ID: {order_id}, Amount: {amount}")

        if not order_id:
            logging.warning("order_id is missing in account")
            return jsonify({
                "error": {
                    "code": -31050,
                    "message": {
                        "ru": "Заказ не найден.",
                        "en": "Order not found.",
                        "uz": "Buyurtma topilmadi."
                    },
                    "data": "order_id"
                }
            })

        # Проверяем, существует ли транзакция с таким ID
        existing_transaction = get_transaction_by_id(transaction_id)
        if existing_transaction:
            logging.info("Transaction already exists")
            # Если транзакция уже существует, возвращаем её данные
            return jsonify({
                "result": {
                    "create_time": int(existing_transaction.create_time),
                    "transaction": str(existing_transaction.transaction_id),
                    "state": int(existing_transaction.state)
                }
            })

        # Проверяем заказ
        order = get_order_by_id(order_id)
        if not order:
            logging.warning("Order not found")
            # Возвращаем ошибку, если заказ не найден
            return jsonify({
                "error": {
                    "code": -31050,
                    "message": {
                        "ru": "Заказ не найден.",
                        "en": "Order not found.",
                        "uz": "Buyurtma topilmadi."
                    },
                    "data": "order_id"
                }
            })

        # Проверяем соответствие суммы
        order_amount = int(order.amount)
        if amount != order_amount:
            logging.warning(f"Incorrect amount: {amount} != {order_amount}")
            # Возвращаем ошибку, если сумма не совпадает
            return jsonify({
                "error": {
                    "code": -31001,
                    "message": {
                        "ru": "Неверная сумма.",
                        "en": "Incorrect amount.",
                        "uz": "Noto'g'ri summa."
                    },
                    "data": "amount"
                }
            })

        # Проверяем, есть ли уже активная транзакция для этого заказа
        active_transaction = session.query(Transaction).filter_by(order_id=order_id, state=1).first()
        if active_transaction:
            logging.warning("Another transaction is already processing for this order")
            # Возвращаем ошибку, если уже существует активная транзакция
            return jsonify({
                "error": {
                    "code": -31050,
                    "message": {
                        "ru": "Счет уже обрабатывается другой транзакцией.",
                        "en": "Account is already being processed by another transaction.",
                        "uz": "Hisob boshqa tranzaksiya tomonidan qayta ishlanmoqda."
                    },
                    "data": "account"
                }
            })

        # Создаём транзакцию
        transaction = create_new_transaction(
            transaction_id=transaction_id,
            order_id=order_id,
            amount=amount,
            create_time=time_created,
            state=1  # Состояние транзакции: 1 - создана
        )

        # Обновляем статус заказа на "ожидание оплаты"
        update_order_status(order_id, "ожидание оплаты", paid=0)

        logging.info("Transaction created successfully")

        # Возвращаем данные транзакции
        return jsonify({
            "result": {
                "create_time": int(transaction.create_time),
                "transaction": str(transaction.transaction_id),
                "state": int(transaction.state)
            }
        })
    except Exception as e:
        logging.exception("Error in create_transaction:")
        # Откатываем сессию в случае ошибки
        session.rollback()
        # Возвращаем ошибку согласно спецификации JSON-RPC
        return jsonify({
            "error": {
                "code": -32400,
                "message": {
                    "ru": "Внутренняя ошибка сервера.",
                    "en": "Internal server error.",
                    "uz": "Ichki server xatosi."
                }
            }
        })

def perform_transaction(data):
    try:
        logging.info("Starting perform_transaction")
        params = data.get('params', {})
        transaction_id = params.get('id')

        # Получаем транзакцию из базы данных
        transaction = get_transaction_by_id(transaction_id)
        if not transaction:
            logging.warning("Transaction not found")
            # Возвращаем ошибку, если транзакция не найдена
            return jsonify({
                "error": {
                    "code": -31003,
                    "message": {
                        "ru": "Транзакция не найдена.",
                        "en": "Transaction not found.",
                        "uz": "Tranzaksiya topilmadi."
                    }
                }
            })

        if transaction.state == 2:
            logging.info("Transaction already performed")
            # Если транзакция уже выполнена, возвращаем её данные
            return jsonify({
                "result": {
                    "transaction": str(transaction.transaction_id),
                    "perform_time": int(transaction.perform_time),
                    "state": int(transaction.state)
                }
            })

        if transaction.state != 1:
            logging.warning("Unable to perform operation due to invalid state")
            # Возвращаем ошибку, если транзакция в неверном состоянии
            return jsonify({
                "error": {
                    "code": -31008,
                    "message": {
                        "ru": "Невозможно выполнить операцию.",
                        "en": "Unable to perform operation.",
                        "uz": "Operatsiyani bajarish mumkin emas."
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
        update_order_status(transaction.order_id, "Оплачено", paid=1)

        logging.info("Transaction performed successfully")

        # Возвращаем данные транзакции
        return jsonify({
            "result": {
                "transaction": str(transaction.transaction_id),
                "perform_time": perform_time,
                "state": 2
            }
        })
    except Exception as e:
        logging.exception("Error in perform_transaction:")
        # Откатываем сессию в случае ошибки
        session.rollback()
        # Возвращаем ошибку согласно спецификации JSON-RPC
        return jsonify({
            "error": {
                "code": -32400,
                "message": {
                    "ru": "Внутренняя ошибка сервера.",
                    "en": "Internal server error.",
                    "uz": "Ichki server xatosi."
                }
            }
        })

def check_transaction(data):
    try:
        logging.info("Starting check_transaction")
        params = data.get('params', {})
        transaction_id = params.get('id')

        # Получаем транзакцию из базы данных
        transaction = get_transaction_by_id(transaction_id)
        if not transaction:
            logging.warning("Transaction not found")
            # Возвращаем ошибку, если транзакция не найдена
            return jsonify({
                "error": {
                    "code": -31003,
                    "message": {
                        "ru": "Транзакция не найдена.",
                        "en": "Transaction not found.",
                        "uz": "Tranzaksiya topilmadi."
                    }
                }
            })

        # Формируем ответ с информацией о транзакции
        return jsonify({
            "result": {
                "create_time": transaction.create_time,
                "perform_time": int(transaction.perform_time) if transaction.perform_time else 0,
                "cancel_time": int(transaction.cancel_time) if transaction.cancel_time else 0,
                "transaction": str(transaction.transaction_id),
                "state": int(transaction.state),
                "reason": transaction.reason if transaction.reason else None
            }
        })
    except Exception as e:
        logging.exception("Error in check_transaction:")
        # Откатываем сессию в случае ошибки
        session.rollback()
        # Возвращаем ошибку согласно спецификации JSON-RPC
        return jsonify({
            "error": {
                "code": -32400,
                "message": {
                    "ru": "Внутренняя ошибка сервера.",
                    "en": "Internal server error.",
                    "uz": "Ichki server xatosi."
                }
            }
        })

def cancel_transaction(data):
    try:
        logging.info("Starting cancel_transaction")
        params = data.get('params', {})
        transaction_id = params.get('id')
        reason = params.get('reason')

        logging.info(f"CancelTransaction - Transaction ID: {transaction_id}, Reason: {reason}")

        # Проверка наличия причины отмены
        if reason is None:
            logging.warning("Invalid cancellation reason")
            return jsonify({
                "error": {
                    "code": -31007,
                    "message": {
                        "ru": "Неверная причина отмены.",
                        "en": "Invalid cancellation reason.",
                        "uz": "Bekor qilish sababi noto'g'ri."
                    }
                }
            })

        # Получаем транзакцию из базы данных
        transaction = get_transaction_by_id(transaction_id)
        if not transaction:
            logging.warning("Transaction not found")
            # Возвращаем ошибку, если транзакция не найдена
            return jsonify({
                "error": {
                    "code": -31003,
                    "message": {
                        "ru": "Транзакция не найдена.",
                        "en": "Transaction not found.",
                        "uz": "Tranzaksiya topilmadi."
                    }
                }
            })

        # Проверяем текущее состояние транзакции
        if transaction.state in [-1, -2]:
            logging.info("Transaction is already canceled or in error state. Returning existing data.")
            return jsonify({
                "result": {
                    "transaction": str(transaction.transaction_id),
                    "cancel_time": int(transaction.cancel_time) if transaction.cancel_time else 0,
                    "state": transaction.state
                }
            })

        # Определяем новый статус на основе текущего состояния
        if transaction.state == 1:
            new_state = -1  # Отменена
        elif transaction.state == 2:
            new_state = -2  # В ошибочном состоянии
        else:
            logging.warning("Invalid transaction state for cancellation")
            return jsonify({
                "error": {
                    "code": -31008,
                    "message": {
                        "ru": "Невозможно выполнить операцию.",
                        "en": "Unable to perform operation.",
                        "uz": "Operatsiyani bajarish mumkin emas."
                    }
                }
            })

        # Обновляем транзакцию
        cancel_time = int(time.time() * 1000)
        
        # Если новая state -2, устанавливаем perform_time в 0
        perform_time = 0 if new_state == -2 else transaction.perform_time

        update_transaction(
            transaction_id=transaction_id,
            state=new_state,
            cancel_time=cancel_time,
            perform_time=perform_time,  # Устанавливаем 0 при state=-2
            reason=reason
        )

        # Обновляем статус заказа на "Отменено"
        update_order_status(transaction.order_id, "Отменено", paid=0)

        logging.info(f"Transaction canceled successfully with new state: {new_state}")

        # Возвращаем данные транзакции
        return jsonify({
            "result": {
                "transaction": str(transaction.transaction_id),
                "cancel_time": cancel_time,
                "state": new_state
            }
        })
    except Exception as e:
        logging.exception("Error in cancel_transaction:")
        # Откатываем сессию в случае ошибки
        session.rollback()
        # Возвращаем ошибку согласно спецификации JSON-RPC
        return jsonify({
            "error": {
                "code": -32400,
                "message": {
                    "ru": "Внутренняя ошибка сервера.",
                    "en": "Internal server error.",
                    "uz": "Ichki server xatosi."
                }
            }
        })

def get_statement(data):
    try:
        logging.info("Starting get_statement")
        params = data.get('params', {})
        from_time = params.get('from')
        to_time = params.get('to')

        # Реализуйте логику получения отчёта
        # Пример:
        transactions = session.query(Transaction).filter(
            Transaction.create_time >= from_time,
            Transaction.create_time <= to_time
        ).all()

        # Формируем ответ
        return jsonify({
            "result": {
                "transactions": [
                    {
                        "transaction": t.transaction_id,
                        "create_time": t.create_time,
                        "perform_time": int(t.perform_time) if t.perform_time else 0,
                        "cancel_time": int(t.cancel_time) if t.cancel_time else 0,
                        "state": t.state,
                        "reason": t.reason
                    } for t in transactions
                ]
            }
        })
    except Exception as e:
        logging.exception("Error in get_statement:")
        session.rollback()
        return jsonify({
            "error": {
                "code": -32400,
                "message": {
                    "ru": "Внутренняя ошибка сервера.",
                    "en": "Internal server error.",
                    "uz": "Ichki server xatosi."
                }
            }
        })

def change_password(data):
    try:
        logging.info("Starting change_password")
        params = data.get('params', {})
        new_password = params.get('password')

        if not new_password:
            logging.warning("Password parameter is missing")
            return jsonify({
                "error": {
                    "code": -31007,
                    "message": {
                        "ru": "Неверная причина отмены.",
                        "en": "Invalid cancellation reason.",
                        "uz": "Bekor qilish sababi noto'g'ri."
                    }
                }
            })

        # Реализуйте логику смены пароля
        # Например, обновите запись пользователя в базе данных

        # Пример ответа
        return jsonify({
            "result": {
                "message": {
                    "ru": "Пароль успешно изменен.",
                    "en": "Password successfully changed.",
                    "uz": "Parol muvaffaqiyatli o'zgartirildi."
                }
            }
        })
    except Exception as e:
        logging.exception("Error in change_password:")
        session.rollback()
        return jsonify({
            "error": {
                "code": -32400,
                "message": {
                    "ru": "Внутренняя ошибка сервера.",
                    "en": "Internal server error.",
                    "uz": "Ichki server xatosi."
                }
            }
        })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)