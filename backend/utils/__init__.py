from pathlib import Path


def get_root_directory() -> Path:
    return Path(__file__).parent.parent


def get_file_path(filename: str) -> str:
    return f"{get_root_directory()}/{filename}"
