import io
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from backend.config import settings

_service = None


def get_service():
    global _service
    if _service:
        return _service
    creds = None
    if Path(settings.token_file).exists():
        creds = Credentials.from_authorized_user_file(settings.token_file, settings.drive_scopes)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not Path(settings.credentials_file).exists():
                raise FileNotFoundError(
                    f"credentials.json not found at {settings.credentials_file}. "
                    "Copy it from your Botty for WhatsApp project."
                )
            flow = InstalledAppFlow.from_client_secrets_file(settings.credentials_file, settings.drive_scopes)
            creds = flow.run_local_server(port=8765, open_browser=True, timeout_seconds=120)
        with open(settings.token_file, "w") as f:
            f.write(creds.to_json())
    _service = build("drive", "v3", credentials=creds)
    return _service


def get_or_create_mp3_folder() -> str:
    svc = get_service()
    results = svc.files().list(
        q=f"name = '{settings.drive_mp3_folder_name}' and '{settings.drive_root_folder_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
        fields="files(id, name)"
    ).execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]
    folder = svc.files().create(
        body={"name": settings.drive_mp3_folder_name, "mimeType": "application/vnd.google-apps.folder", "parents": [settings.drive_root_folder_id]},
        fields="id"
    ).execute()
    return folder["id"]


def search_drive_for_mp3(title: str, artist: str) -> dict | None:
    svc = get_service()
    safe_title = title.replace("'", "\\'")
    for q in [
        f"fullText contains '{safe_title}' and (mimeType = 'audio/mpeg' or mimeType = 'audio/mp3') and trashed = false",
        f"name contains '{safe_title}' and trashed = false and (mimeType = 'audio/mpeg' or mimeType = 'audio/mp3' or mimeType = 'audio/x-m4a' or mimeType = 'audio/wav')",
    ]:
        try:
            files = svc.files().list(q=q, fields="files(id, name, mimeType, size)", pageSize=5).execute().get("files", [])
            if files:
                return files[0]
        except Exception:
            continue
    return None


def move_and_rename_mp3(file_id: str, title: str, artist: str, folder_id: str) -> dict:
    svc = get_service()
    new_name = f"{title} - {artist}.mp3" if artist else f"{title}.mp3"
    new_name = "".join(c for c in new_name if c not in r'\/:*?"<>|')
    file_meta = svc.files().get(fileId=file_id, fields="parents").execute()
    old_parents = ",".join(file_meta.get("parents", []))
    return svc.files().update(
        fileId=file_id,
        addParents=folder_id,
        removeParents=old_parents,
        body={"name": new_name},
        fields="id, name"
    ).execute()


def upload_mp3(local_path: str, filename: str, folder_id: str) -> dict:
    svc = get_service()
    return svc.files().create(
        body={"name": filename, "parents": [folder_id]},
        media_body=MediaFileUpload(local_path, mimetype="audio/mpeg", resumable=True),
        fields="id, name, size"
    ).execute()


def upload_image(local_path: str, filename: str, folder_id: str) -> dict:
    svc = get_service()
    return svc.files().create(
        body={"name": filename, "parents": [folder_id]},
        media_body=MediaFileUpload(local_path, mimetype="image/png", resumable=False),
        fields="id, name"
    ).execute()


def download_file(file_id: str) -> bytes:
    svc = get_service()
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, svc.files().get_media(fileId=file_id))
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buf.getvalue()


def list_files_in_folder(folder_id: str) -> list[dict]:
    svc = get_service()
    results, page_token = [], None
    while True:
        params = dict(q=f"'{folder_id}' in parents and trashed = false", fields="nextPageToken, files(id, name, mimeType)", pageSize=1000)
        if page_token:
            params["pageToken"] = page_token
        resp = svc.files().list(**params).execute()
        results.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return results
