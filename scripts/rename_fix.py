"""One-time fix: rename the incorrectly renamed file back to its original name."""
import sys
sys.path.insert(0, ".")
from backend.drive import get_service

svc = get_service()

# Find the wrongly renamed file
results = svc.files().list(
    q="name = 'אהבה - אביב גפן.mp3' and trashed = false",
    fields="files(id, name, parents)"
).execute().get("files", [])

if not results:
    print("File 'אהבה - אביב גפן.mp3' not found on Drive.")
    sys.exit(1)

file = results[0]
print(f"Found: {file['name']} (id={file['id']})")

# Rename back to original
svc.files().update(
    fileId=file["id"],
    body={"name": "דוד אהרון - אהבה ראשונה.mp3"}
).execute()

print("Renamed back to: דוד אהרון - אהבה ראשונה.mp3")
