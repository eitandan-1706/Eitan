from sqlalchemy import create_engine, Column, Integer, Text, String
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from pathlib import Path
from backend.config import settings

Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(f"sqlite:///{settings.db_path}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


class Song(Base):
    __tablename__ = "songs"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(Text, nullable=False)
    artist = Column(Text, nullable=False)
    original_key = Column(String(10))
    source_page = Column(Integer)
    image_filename = Column(Text)
    image_drive_id = Column(Text)
    mp3_drive_id = Column(Text)
    mp3_filename = Column(Text)
    youtube_url = Column(Text)
    duration_sec = Column(Integer)
    language = Column(String(10), default="he")
    date_added = Column(Text)
    date_downloaded = Column(Text)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
