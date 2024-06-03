"""Global configs and constants"""

import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()
# PostgresSQL config
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_HOST = os.getenv("POSTGRESQL_HOST", "localhost")


def get_database_url(test=False, sqlite=False):
    """Return database url"""
    if sqlite:
        return "sqlite://db.sqlite3"
    server = DB_HOST if not test else os.getenv("POSTGRESQL_HOST_TEST", "localhost")
    db = os.getenv("POSTGRESQL_DATABASE", "app") if not test else "db_test"
    user = (
        os.getenv("POSTGRESQL_USER", "root")
        if not test
        else os.getenv("POSTGRESQL_USER_TEST", "root")
    )
    password = (
        os.getenv("POSTGRESQL_PASSWORD", "")
        if not test
        else os.getenv("POSTGRESQL_PASSWORD_TEST", "")
    )
    port = os.getenv("POSTGRESQL_PORT", "5432")
    return f"postgres://{user}:{password}@{server}:{port}/{db}"


TORTOISE_ORM_TEST = {
    "connections": {"default": "sqlite://db_test.sqlite3"},
    "apps": {
        "models": {
            "models": [
                "aerich.models",
                "src.clinic_office.models",
                "src.auth.models",
                "src.scheduler.models",
                "src.billing.models",
            ],
            "default_connection": "default",
        },
    },
}

DEBUG = os.getenv("DEBUG")

# Logging config.

FORMAT = (
    "[%(asctime)s][%(levelname)s] %(name)s "
    "%(filename)s:%(funcName)s:%(lineno)d | %(message)s"
)
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
date_str = datetime.now().strftime("%Y-%m-%d")
LOG_FILENAME = f"{BASE_DIR}/logs/{date_str}.log"

DEFAULT_DATE_FORMAT = "%d/%m/%Y"
DEFAULT_DATE_TIME_FORMAT = "%d/%m/%Y %H:%M:%S"


ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1",
    "http://localhost",
    "https://localhost:3000",
    "https://127.0.0.1",
    "https://localhost",
]

INVERTEXTO_TOKEN = os.getenv("INVERTEXTO_TOKEN")
CORE_API_URL = os.getenv("CORE_API_URL")
CORE_KEY = os.getenv("CORE_KEY")
