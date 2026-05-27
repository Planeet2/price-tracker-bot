import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    db_name: str = os.getenv("DB_NAME", "dns_monitor")
    db_user: str = os.getenv("DB_USER", "postgres")
    db_password: str = os.getenv("DB_PASSWORD", "")
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: str = os.getenv("DB_PORT", "5432")
    bot_token: str = os.getenv("BOT_TOKEN", "")
    my_chat_id: str = os.getenv("MY_CHAT_ID", "")
    check_interval_seconds: int = int(os.getenv("CHECK_INTERVAL_SECONDS", "3600"))
    headless: bool = os.getenv("HEADLESS", "true").lower() == "true"


settings = Settings()
