from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.database import init_db
from backend.routes import songs, downloader, import_export, chords

app = FastAPI(title="Song Manager", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()


app.include_router(songs.router)
app.include_router(downloader.router)
app.include_router(import_export.router)
app.include_router(chords.router)


@app.get("/health")
def health():
    return {"status": "ok"}
