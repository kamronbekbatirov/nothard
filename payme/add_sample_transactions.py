from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import time

# Импортируйте ваши модели
from app import Order, Transaction, Base  # Убедитесь, что путь к вашим моделям верный

# Настройка подключения к базе данных
engine = create_engine('sqlite:////var/www/nothard.uz/payme/payme.db')
Session = sessionmaker(bind=engine)
session = Session()

# Функция для создания заказов, если их нет
def create_sample_orders():
    # Проверяем, существуют ли заказы с order_id 46 и 47
    order1 = session.query(Order).filter_by(order_id=46).first()
    order2 = session.query(Order).filter_by(order_id=47).first()

    if not order1:
        order1 = Order(
            order_id=46,
            user_id=12345,
            amount=12650,
            status='Новый',
            paid=0
        )
        session.add(order1)

    if not order2:
        order2 = Order(
            order_id=47,
            user_id=67890,
            amount=20000,
            status='Новый',
            paid=0
        )
        session.add(order2)

    session.commit()

# Функция для добавления транзакций
def add_sample_transactions():
    # Создаем заказы, если их нет
    create_sample_orders()

    # Проверяем, существует ли транзакция с таким transaction_id
    transaction1 = session.query(Transaction).filter_by(transaction_id='6705b18b10b1f7f17185d114').first()
    transaction2 = session.query(Transaction).filter_by(transaction_id='7706c29c20c2g8g28296e225').first()

    if not transaction1:
        transaction1 = Transaction(
            transaction_id='6705b18b10b1f7f17185d114',
            order_id=46,
            amount=12650,
            create_time=1728426379278,
            state=0,
            perform_time=None
        )
        session.add(transaction1)

    if not transaction2:
        current_time_ms = int(time.time() * 1000)
        transaction2 = Transaction(
            transaction_id='7706c29c20c2g8g28296e225',
            order_id=47,
            amount=20000,
            create_time=current_time_ms,
            state=0,
            perform_time=None
        )
        session.add(transaction2)

    session.commit()
    print("Два транзакции успешно добавлены в базу данных.")

if __name__ == '__main__':
    add_sample_transactions()
