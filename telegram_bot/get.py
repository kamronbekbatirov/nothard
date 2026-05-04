from cryptography.fernet import Fernet

# Генерация секретного ключа
def generate_secret_key():
    key = Fernet.generate_key()
    print(f"Секретный ключ для вашего .env файла: {key.decode()}")
    return key.decode()

# Вызываем функцию для генерации ключа
secret_key = generate_secret_key()

# Выводите ключ и добавляете его в ваш .env файл вручную