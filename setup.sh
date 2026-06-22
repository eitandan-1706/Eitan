#!/usr/bin/env bash
# One-time setup script for Song Manager
set -e

echo "=== Song Manager Setup ==="

pip install -r requirements.txt

cd frontend && npm install && cd ..

mkdir -p data/tmp

echo ""
echo "NEXT STEPS:"
echo "1. Copy your Google credentials.json to backend/credentials.json"
echo "   (from your Botty for WhatsApp project)"
echo ""
echo "2. Import the CSV into the database:"
echo "   python -m scripts.migrate_csv --csv data/songs_all.csv"
echo ""
echo "3. (Optional) Link existing Drive files:"
echo "   python -m scripts.migrate_csv --csv data/songs_all.csv --link-drive"
echo ""
echo "4. Start the app:"
echo "   ./start.sh"
