import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.database import get_db, Song
from backend import drive
from backend.config import settings
from backend.services.chord_importer import pdf_to_pngs, screenshot_url

router = APIRouter(prefix="/chords", tags=["chords"])


@router.post("/upload/{song_id}")
async def upload_chord_sheet(song_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(404, "Song not found")
    tmp_dir = Path(settings.temp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    tmp_path = str(tmp_dir / file.filename)
    with open(tmp_path, "wb") as f:
        f.write(await file.read())
    if file.filename.lower().endswith(".pdf"):
        png_paths = await pdf_to_pngs(tmp_path, str(tmp_dir))
        os.remove(tmp_path)
    else:
        png_paths = [tmp_path]
    result = drive.upload_image(png_paths[0], f"chord_{song_id}_{Path(png_paths[0]).name}", settings.drive_root_folder_id)
    for p in png_paths:
        if Path(p).exists():
            os.remove(p)
    song.image_drive_id = result["id"]
    song.image_filename = result["name"]
    db.commit()
    return {"drive_id": result["id"], "filename": result["name"]}


@router.post("/scrape/{song_id}")
async def scrape_chord_sheet(song_id: int, url: str = Form(...), db: Session = Depends(get_db)):
    song = db.get(Song, song_id)
    if not song:
        raise HTTPException(404, "Song not found")
    tmp_dir = Path(settings.temp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    out_path = str(tmp_dir / f"scrape_{song_id}.png")
    await screenshot_url(url, out_path)
    result = drive.upload_image(out_path, f"chord_scraped_{song_id}.png", settings.drive_root_folder_id)
    os.remove(out_path)
    song.image_drive_id = result["id"]
    song.image_filename = result["name"]
    db.commit()
    return {"drive_id": result["id"], "filename": result["name"]}
