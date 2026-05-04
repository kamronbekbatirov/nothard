# Real Estate Bot

This is a Telegram bot for assisting students and people in finding accommodation in London.

## Features

- User registration
- Property search
- Profile management
- Admin panel for managing users and requests
- Package management for purchasing service packages
- Feedback collection

## Setup

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install the dependencies:

pip install -r requirements.txt

4. Initialize the database:

python -c "from bot.utils.database import init_db; init_db()"

5. Set your bot token in `config.py`.
6. Run the bot:

python main.py


## Usage

Start the bot and follow the instructions to register and use the services.