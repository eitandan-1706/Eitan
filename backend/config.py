from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent


class Settings(BaseSettings):
    drive_root_folder_id: str = "109r37ssvvMBqlJYye7Ut1JZwl-EHFqsv"
    drive_mp3_folder_name: str = "MP3 files"
    credentials_file: str = str(BASE_DIR / "backend" / "credentials.json")
    token_file: str = str(BASE_DIR / "backend" / "token.json")
    drive_scopes: list[str] = ["https://www.googleapis.com/auth/drive"]
    db_path: str = str(BASE_DIR / "data" / "songs.db")
    temp_dir: str = str(BASE_DIR / "data" / "tmp")
    default_mp3_bitrate: str = "320k"
    download_concurrency: int = 3
    frontend_origin: str = "http://localhost:5173"

    class Config:
        env_file = str(BASE_DIR / ".env")


settings = Settings()
