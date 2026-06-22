import io
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from pydantic import BaseModel
from backend.database import get_db, Song
from backend import drive

router = APIRouter(prefix="/songs", tags=["songs"])


class SongUpdate(BaseModel):
    title: Optional[str] = None
    artist: Optional[str] = None
    original_key: Optional[str] = None
    language: Optional[str] = None
    youtube_url: Optional[str] = None


def song_to_dict(s: Song) -> dict:
    return {
        "id": s.id, "title": s.title, "artist": s.artist,
        "original_key": s.original_key, "source_page": s.source_page,
        "image_filename": s.image_filename, "image_drive_id": s.image_drive_id,
        "mp3_drive_id": s.mp3_drive_id, "mp3_filename": s.mp3_filename,
        "youtube_url": s.youtube_url, "duration_sec": s.duration_sec,
        "language": s.language, "date_added": s.date_added,
        "date_downloaded": s.date_downloaded,
        "has_mp3": bool(s.mp3_drive_id), "has_chords": bool(s.image_drive_id),
    }


@router.get("")
def list_songs(
    q: str = Query(None), artist: str = Query(None), key: str = Query(None),
    has_mp3: Optional[bool] = Query(None), has_chords: Optional[bool] = Query(None),
    language: str = Query(None), skip: int = 0, limit: int = 100,
    db: Session = Depends(get_db),
):
    query = db.query(Song)
    if q:
        query = query.filter(or_(Song.title.contains(q), Song.artist.contains(q)))
    if artist:
        query = query.filter(Song.artist.contains(artist))
    if key:
        query = query.filter(Song.original_key == key)
    if language:
        query = query.filter(Song.language == language)
    if has_mp3 is True:
        query = query.filter(Song.mp3_drive_id.isnot(None))
    elif has_mp3 is False:
        query = query.filter(Song.mp3_drive_id.is_(None))
    if has_chords is True:
        query = query.filter(Song.image_drive_id.isnot(None))
    elif has_chords is False:
        query = query.filter(Song.image_drive_id.is_(None))
    total = query.count()
    songs = query.order_by(Song.title).offset(skip).limit(limit).all()
    return {"total": total, "items": [song_to_dict(s) for s in songs]}


@router.get("/{song_id}")
def get_song(song_id: int, db: Session = Depends(get_db)):
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(404, "Song not found")
    return song_to_dict(song)


@router.put("/{song_id}")
def update_song(song_id: int, data: SongUpdate, db: Session = Depends(get_db)):
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(404, "Song not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(song, field, value)
    db.commit()
    return song_to_dict(song)


@router.get("/{song_id}/chords")
def get_chords(song_id: int, db: Session = Depends(get_db)):
    song = db.get(Song, song_id)
    if not song or not song.image_drive_id:
        raise HTTPException(404, "Chord sheet not found")
    return StreamingResponse(io.BytesIO(drive.download_file(song.image_drive_id)), media_type="image/png")


@router.get("/{song_id}/mp3")
def get_mp3(song_id: int, db: Session = Depends(get_db)):
    song = db.get(Song, song_id)
    if not song or not song.mp3_drive_id:
        raise HTTPException(404, "MP3 not found")
    filename = song.mp3_filename or f"{song.title}.mp3"
    return StreamingResponse(
        io.BytesIO(drive.download_file(song.mp3_drive_id)), media_type="audio/mpeg",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
