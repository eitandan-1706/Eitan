import asyncio
import uuid
import os
from datetime import datetime
from pathlib import Path
from typing import AsyncGenerator, Optional
from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.database import get_db, Song, SessionLocal
from backend import drive
from backend.services.youtube import search_youtube, download_audio
from backend.config import settings

router = APIRouter(prefix="/download", tags=["download"])
_jobs: dict[str, dict] = {}
_job_queues: dict[str, asyncio.Queue] = {}


class BatchRequest(BaseModel):
    song_ids: Optional[list[int]] = None
    titles: Optional[list[str]] = None
    auto_mode: bool = True
    all_missing: bool = False


class SearchRequest(BaseModel):
    title: str
    artist: str
    limit: int = 3


@router.post("/search")
async def search_yt(req: SearchRequest):
    return {"results": await search_youtube(req.title, req.artist, req.limit)}


@router.post("/batch")
async def start_batch(req: BatchRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    job_id = str(uuid.uuid4())[:8]
    songs_to_process: list[dict] = []
    if req.all_missing:
        rows = db.query(Song).filter(Song.mp3_drive_id.is_(None)).all()
        songs_to_process = [{"id": s.id, "title": s.title, "artist": s.artist} for s in rows]
    elif req.song_ids:
        for sid in req.song_ids:
            s = db.get(Song, sid)
            if s:
                songs_to_process.append({"id": s.id, "title": s.title, "artist": s.artist})
    elif req.titles:
        for entry in req.titles:
            parts = entry.split(" - ", 1)
            title = parts[0].strip()
            artist = parts[1].strip() if len(parts) > 1 else ""
            found = db.query(Song).filter(Song.title == title).first()
            songs_to_process.append({"id": found.id if found else None, "title": found.title if found else title, "artist": found.artist if found else artist})
    _jobs[job_id] = {"status": "running", "total": len(songs_to_process), "done": 0, "results": []}
    q: asyncio.Queue = asyncio.Queue()
    _job_queues[job_id] = q
    background_tasks.add_task(_run_batch, job_id, songs_to_process, req.auto_mode, q)
    return {"job_id": job_id, "total": len(songs_to_process)}


@router.get("/status/{job_id}")
async def stream_status(job_id: str):
    if job_id not in _jobs:
        from fastapi import HTTPException
        raise HTTPException(404, "Job not found")
    async def event_gen() -> AsyncGenerator[str, None]:
        q = _job_queues.get(job_id)
        if not q:
            return
        while True:
            try:
                msg = await asyncio.wait_for(q.get(), timeout=60)
                yield f"data: {msg}\n\n"
                if _jobs[job_id]["done"] >= _jobs[job_id]["total"] and _jobs[job_id]["total"] > 0:
                    break
            except asyncio.TimeoutError:
                yield 'data: {"type":"ping"}\n\n'
    return StreamingResponse(event_gen(), media_type="text/event-stream")


@router.get("/job/{job_id}")
def get_job(job_id: str):
    if job_id not in _jobs:
        from fastapi import HTTPException
        raise HTTPException(404, "Job not found")
    return _jobs[job_id]


async def _run_batch(job_id: str, songs: list[dict], auto_mode: bool, q: asyncio.Queue):
    import json
    sem = asyncio.Semaphore(settings.download_concurrency)

    async def process_one(song: dict):
        title, artist, db_id = song["title"], song.get("artist", ""), song.get("id")

        async def emit(event: str, **kwargs):
            await q.put(json.dumps({"song": title, "artist": artist, "event": event, **kwargs}))

        loop = asyncio.get_event_loop()

        async with sem:
            await emit("searching_drive")
            existing = await loop.run_in_executor(None, drive.search_drive_for_mp3, title, artist)
            if existing:
                await emit("found_on_drive", drive_id=existing["id"], filename=existing["name"])
                if db_id:
                    _update_db(db_id, mp3_drive_id=existing["id"], mp3_filename=existing["name"])
                _jobs[job_id]["done"] += 1
                _jobs[job_id]["results"].append({"title": title, "status": "found_on_drive"})
                return
            await emit("searching_youtube")
            try:
                results = await search_youtube(title, artist, limit=1)
                if not results:
                    await emit("error", reason="No YouTube results found")
                    _jobs[job_id]["done"] += 1
                    _jobs[job_id]["results"].append({"title": title, "status": "error", "reason": "no_results"})
                    return
                yt = results[0]
                await emit("youtube_match", yt_title=yt["title"], url=yt["url"])
                await emit("downloading")
                Path(settings.temp_dir).mkdir(parents=True, exist_ok=True)
                safe = "".join(c for c in f"{title} - {artist}" if c.isalnum() or c in " -_")
                local_file = await download_audio(yt["url"], str(Path(settings.temp_dir) / f"{safe}.mp3"))
                if not local_file.endswith(".mp3"):
                    from backend.services.converter import convert_to_mp3
                    await emit("converting")
                    local_file = await convert_to_mp3(local_file, local_file.rsplit(".", 1)[0] + ".mp3")
                await emit("uploading")
                mp3_folder = await loop.run_in_executor(None, drive.get_or_create_mp3_folder)
                result = await loop.run_in_executor(None, drive.upload_mp3, local_file, Path(local_file).name, mp3_folder)
                os.remove(local_file)
                if db_id:
                    _update_db(db_id, mp3_drive_id=result["id"], mp3_filename=result["name"], youtube_url=yt["url"])
                await emit("done", drive_id=result["id"], filename=result["name"])
                _jobs[job_id]["done"] += 1
                _jobs[job_id]["results"].append({"title": title, "status": "downloaded"})
            except Exception as e:
                await emit("error", reason=str(e))
                _jobs[job_id]["done"] += 1
                _jobs[job_id]["results"].append({"title": title, "status": "error", "reason": str(e)})

    await asyncio.gather(*[process_one(s) for s in songs])
    _jobs[job_id]["status"] = "complete"


def _update_db(song_id: int, **kwargs):
    db = SessionLocal()
    try:
        song = db.get(Song, song_id)
        if song:
            for k, v in kwargs.items():
                setattr(song, k, v)
            song.date_downloaded = datetime.utcnow().isoformat()
            db.commit()
    finally:
        db.close()
