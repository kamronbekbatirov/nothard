# config.py

from dotenv import load_dotenv
import os
import binascii


# Load environment variables from .env file
load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
BOT_PAYME = os.getenv('BOT_PAYME')
PROVIDER_TOKEN = os.getenv('PROVIDER_TOKEN')  # Добавляем получение PROVIDER_TOKEN
CSRF_SECRET = os.getenv('CSRF_SECRET')
PAYME_MERCHANT_ID = os.getenv('PAYME_MERCHANT_ID')
PAYME_KEY = os.getenv('PAYME_KEY')

import logging

logging.basicConfig(level=logging.DEBUG)

SECRET_KEY = os.getenv('SECRET_KEY', 'uksrf67345-0hdf56hk47fhio3449sas')
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

# Debugging: Print the raw SECRET_KEY
print(f"Raw SECRET_KEY: {SECRET_KEY!r}")

# Ensure SECRET_KEY is present
if not SECRET_KEY:
    raise ValueError("No SECRET_KEY found in environment variables")

# Remove surrounding quotes if present
SECRET_KEY = SECRET_KEY.strip('"').strip("'")
print(f"Stripped SECRET_KEY: {SECRET_KEY!r}")

# Convert SECRET_KEY to bytes if necessary
# If your application requires SECRET_KEY as bytes, encode it
# Otherwise, you can use it as a string directly

# Example: If bytes are needed
SECRET_KEY = SECRET_KEY.encode('utf-8')  # Convert string to bytes
print(f"SECRET_KEY (bytes): {SECRET_KEY}")

# Validate other required environment variables
if BOT_TOKEN is None:
    raise ValueError("No BOT_TOKEN found in environment variables")

if BOT_PAYME is None:
    raise ValueError("No BOT_PAYME found in environment variables")

if PROVIDER_TOKEN is None:
    raise ValueError("No PROVIDER_TOKEN found in environment variables")