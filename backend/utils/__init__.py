import os
from pathlib import Path


def get_group_chat_id() -> int:
    return int(os.getenv("TELEGRAM_CHAT_ID", -1))


def get_root_directory() -> Path:
    return Path(__file__).parent.parent


def get_file_path(filename: str) -> str:
    return f"{get_root_directory()}/{filename}"
