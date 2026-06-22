import React, { useState } from 'react';
import api from '../api';

export default function Import() {
  const [csvFile, setCsvFile] = useState(null);
  const [csvResult, setCsvResult] = useState(null);
  const [csvLoading, setCsvLoading] = useState(false);
  const [chordSongId, setChordSongId] = useState('');
  const [chordFile, setChordFile] = useState(null);
  const [chordResult, setChordResult] = useState(null);
  const [scrapeUrl, setScrapeUrl] = useState('');
  const [scrapeResult, setScrapeResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const importCsv = async () => {
    if (!csvFile) return;
    setCsvLoading(true);
    const fd = new FormData();
    fd.append('file', csvFile);
    setCsvResult((await api.post('/import/csv', fd)).data);
    setCsvLoading(false);
  };

  const uploadChord = async () => {
    if (!chordSongId || !chordFile) return;
    setLoading(true);
    const fd = new FormData();
    fd.append('file', chordFile);
    setChordResult((await api.post(`/chords/upload/${chordSongId}`, fd)).data);
    setLoading(false);
  };

  const scrapeChord = async () => {
    if (!chordSongId || !scrapeUrl) return;
    setLoading(true);
    const fd = new FormData();
    fd.append('url', scrapeUrl);
    setScrapeResult((await api.post(`/chords/scrape/${chordSongId}`, fd)).data);
    setLoading(false);
  };

  return (
    <div>
      <h1>Import</h1>
      <div className="card">
        <h2>Import Songs from CSV</h2>
        <p className="info-text">Columns: title, artist, original_key, source_page, image_filename</p>
        <div className="gap-row" style={{ marginBottom: '0.75rem' }}>
          <input type="file" accept=".csv,.xlsx" style={{ width: 'auto' }} onChange={e => setCsvFile(e.target.files[0])} />
          <button className="btn-primary" onClick={importCsv} disabled={csvLoading || !csvFile}>
            {csvLoading ? 'Importing…' : 'Import'}
          </button>
        </div>
        {csvResult && <p style={{ color: '#6ee7b7' }}>✓ Added {csvResult.added}, skipped {csvResult.skipped}</p>}
        <hr style={{ borderColor: '#2d3148', margin: '1rem 0' }} />
        <a href="http://localhost:8000/import/export" download>
          <button className="btn-secondary">⬇ Export library as CSV</button>
        </a>
      </div>
      <div className="card">
        <h2>Add Chord Sheet</h2>
        <p className="info-text">Attach a PNG, JPG, or PDF to a song by its DB ID.</p>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <input type="number" placeholder="Song ID" value={chordSongId} onChange={e => setChordSongId(e.target.value)} style={{ maxWidth: 200 }} />
          <div>
            <p style={{ marginBottom: '0.4rem', color: '#94a3b8', fontSize: '0.85rem' }}>Option 1 — Upload file (PNG / JPG / PDF):</p>
            <div className="gap-row">
              <input type="file" accept=".png,.jpg,.jpeg,.pdf" style={{ width: 'auto' }} onChange={e => setChordFile(e.target.files[0])} />
              <button className="btn-primary" onClick={uploadChord} disabled={loading || !chordSongId || !chordFile}>
                {loading ? 'Uploading…' : 'Upload'}
              </button>
            </div>
            {chordResult && <p style={{ color: '#6ee7b7', marginTop: '0.4rem' }}>✓ {chordResult.filename}</p>}
          </div>
          <div>
            <p style={{ marginBottom: '0.4rem', color: '#94a3b8', fontSize: '0.85rem' }}>Option 2 — Screenshot from URL:</p>
            <div className="gap-row">
              <input placeholder="https://example.com/chords/song" value={scrapeUrl} onChange={e => setScrapeUrl(e.target.value)} />
              <button className="btn-primary" onClick={scrapeChord} disabled={loading || !chordSongId || !scrapeUrl}>
                {loading ? 'Capturing…' : 'Capture'}
              </button>
            </div>
            {scrapeResult && <p style={{ color: '#6ee7b7', marginTop: '0.4rem' }}>✓ {scrapeResult.filename}</p>}
          </div>
        </div>
      </div>
    </div>
  );
}
