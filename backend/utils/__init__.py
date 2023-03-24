import os
from pathlib import Path


def get_group_chat_id() -> int:
    return int(os.getenv("TELEGRAM_CHAT_ID", -1))


def get_root_directory() -> Path:
    return Path(__file__).parent.parent


def get_file_path(filename: str) -> str:
    return f"{get_root_directory()}/{filename}"


def get_is_dev_env() -> bool:
    return bool(os.getenv("IS_DEV", False))


def get_is_mock_location() -> bool:
    return bool(os.getenv("MOCK_LOCATION", False))
