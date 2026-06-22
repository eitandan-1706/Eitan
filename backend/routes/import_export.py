import csv
import io
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.database import get_db, Song

router = APIRouter(prefix="/import", tags=["import"])


@router.post("/csv")
async def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    reader = csv.DictReader(io.StringIO((await file.read()).decode("utf-8-sig")))
    added = skipped = 0
    for row in reader:
        title = (row.get("title") or "").strip()
        artist = (row.get("artist") or "").strip()
        if not title or not artist:
            skipped += 1
            continue
        if db.query(Song).filter(Song.title == title, Song.artist == artist).first():
            skipped += 1
            continue
        db.add(Song(
            title=title, artist=artist,
            original_key=(row.get("original_key") or "").strip() or None,
            source_page=int(row["source_page"]) if row.get("source_page", "").strip().isdigit() else None,
            image_filename=(row.get("image_filename") or "").strip() or None,
            date_added=datetime.utcnow().isoformat(), language="he",
        ))
        added += 1
    db.commit()
    return {"added": added, "skipped": skipped}


@router.get("/export")
def export_csv(db: Session = Depends(get_db)):
    buf = io.StringIO()
    fields = ["id", "title", "artist", "original_key", "source_page", "image_filename",
              "mp3_filename", "youtube_url", "has_mp3", "has_chords", "language"]
    writer = csv.DictWriter(buf, fieldnames=fields)
    writer.writeheader()
    for s in db.query(Song).order_by(Song.title).all():
        writer.writerow({
            "id": s.id, "title": s.title, "artist": s.artist,
            "original_key": s.original_key or "", "source_page": s.source_page or "",
            "image_filename": s.image_filename or "", "mp3_filename": s.mp3_filename or "",
            "youtube_url": s.youtube_url or "",
            "has_mp3": "yes" if s.mp3_drive_id else "no",
            "has_chords": "yes" if s.image_drive_id else "no",
            "language": s.language or "he",
        })
    buf.seek(0)
    return StreamingResponse(
        io.BytesIO(buf.getvalue().encode()), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=songs_export.csv"},
    )
