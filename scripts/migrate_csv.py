"""
One-time migration: import songs_all.csv into SQLite and optionally
link existing Drive PNG/MP3 files by scanning the Drive folders.

Usage:
  python -m scripts.migrate_csv --csv data/songs_all.csv
  python -m scripts.migrate_csv --csv data/songs_all.csv --link-drive
"""
import sys
import csv
import argparse
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import init_db, SessionLocal, Song
from backend.config import settings


def import_csv(csv_path: str):
    init_db()
    db = SessionLocal()
    added = skipped = 0
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
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
    db.close()
    print(f"Import complete: {added} added, {skipped} skipped")
    return added


def link_drive_images():
    from backend.drive import get_service
    db = SessionLocal()
    print("Searching Drive for song_*.png chord sheets...")
    svc = get_service()
    png_map = {}
    page_token = None
    while True:
        resp = svc.files().list(
            q="name contains 'song_' and mimeType = 'image/png' and trashed = false",
            fields="nextPageToken, files(id, name)",
            pageSize=1000,
            pageToken=page_token,
        ).execute()
        for f in resp.get("files", []):
            png_map[f["name"]] = f["id"]
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    print(f"Found {len(png_map)} PNG files on Drive")
    updated = 0
    for song in db.query(Song).filter(Song.image_filename.isnot(None), Song.image_drive_id.is_(None)).all():
        if song.image_filename in png_map:
            song.image_drive_id = png_map[song.image_filename]
            updated += 1
    db.commit()
    db.close()
    print(f"Linked {updated} chord sheet PNGs")


def link_drive_mp3s():
    from backend import drive as drv
    from thefuzz import process as fuzz_process
    db = SessionLocal()
    print("Scanning Drive 'MP3 files' folder for existing MP3s...")
    folder_id = drv.get_or_create_mp3_folder()
    mp3_files = [f for f in drv.list_files_in_folder(folder_id) if "audio" in f.get("mimeType", "") or f["name"].endswith(".mp3")]
    songs = db.query(Song).filter(Song.mp3_drive_id.is_(None)).all()
    song_titles = {s.id: f"{s.title} {s.artist}" for s in songs}
    updated = 0
    for mp3 in mp3_files:
        match, score = fuzz_process.extractOne(Path(mp3["name"]).stem, list(song_titles.values()))
        if score >= 75:
            song_id = next(k for k, v in song_titles.items() if v == match)
            song = db.get(Song, song_id)
            if song and not song.mp3_drive_id:
                song.mp3_drive_id = mp3["id"]
                song.mp3_filename = mp3["name"]
                updated += 1
    db.commit()
    db.close()
    print(f"Linked {updated} existing MP3 files from Drive")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default=None)
    parser.add_argument("--link-drive", action="store_true")
    args = parser.parse_args()
    if args.csv:
        import_csv(args.csv)
    if args.link_drive:
        link_drive_images()
        link_drive_mp3s()
