import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api';

export default function SongDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [song, setSong] = useState(null);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({});
  const [downloading, setDownloading] = useState(false);
  const [dlStatus, setDlStatus] = useState('');
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!downloading) { setElapsed(0); return; }
    const t = setInterval(() => setElapsed(s => s + 1), 1000);
    return () => clearInterval(t);
  }, [downloading]);

  useEffect(() => {
    api.get(`/songs/${id}`).then(r => { setSong(r.data); setForm(r.data); });
  }, [id]);

  const save = async () => {
    const res = await api.put(`/songs/${id}`, {
      title: form.title, artist: form.artist,
      original_key: form.original_key, language: form.language,
      youtube_url: form.youtube_url,
    });
    setSong(res.data);
    setEditing(false);
  };

  const downloadSingle = async () => {
    setDownloading(true);
    setDlStatus('Starting…');
    const res = await api.post('/download/batch', { song_ids: [parseInt(id)], auto_mode: true });
    const src = new EventSource(`http://localhost:8000/download/status/${res.data.job_id}`);
    src.onmessage = e => {
      try {
        const d = JSON.parse(e.data);
        if (d.event === 'needs_confirmation') {
          api.post('/download/confirm', { conf_key: d.conf_key, proceed: false });
        }
        if (d.event) setDlStatus(d.event.replace(/_/g, ' '));
        if (d.event === 'done' || d.event === 'found_on_drive') {
          src.close(); setDownloading(false);
          api.get(`/songs/${id}`).then(r => setSong(r.data));
        }
        if (d.event === 'error') { setDlStatus('Error: ' + d.reason); src.close(); setDownloading(false); }
      } catch {}
    };
  };

  if (!song) return <p style={{ color: '#64748b' }}>Loading…</p>;

  return (
    <div>
      <button className="btn-secondary" style={{ marginBottom: '1rem' }} onClick={() => navigate(-1)}>← Back</button>
      <div className="grid2">
        <div className="card">
          <h1 className="rtl">{song.title}</h1>
          <p className="rtl" style={{ color: '#94a3b8', marginBottom: '1rem' }}>{song.artist}</p>
          {!editing ? (
            <>
              <p><strong>Key:</strong> {song.original_key || '—'}</p>
              <p><strong>Language:</strong> {song.language || 'he'}</p>
              {song.youtube_url && <p><strong>YouTube:</strong> <a href={song.youtube_url} target="_blank" rel="noreferrer" style={{ color: '#a78bfa' }}>Link</a></p>}
              <br />
              <button className="btn-secondary" onClick={() => setEditing(true)}>Edit</button>
            </>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              <input value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} placeholder="Title" />
              <input value={form.artist} onChange={e => setForm(f => ({ ...f, artist: e.target.value }))} placeholder="Artist" />
              <input value={form.original_key || ''} onChange={e => setForm(f => ({ ...f, original_key: e.target.value }))} placeholder="Key" />
              <input value={form.youtube_url || ''} onChange={e => setForm(f => ({ ...f, youtube_url: e.target.value }))} placeholder="YouTube URL (optional)" />
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button className="btn-primary" onClick={save}>Save</button>
                <button className="btn-secondary" onClick={() => setEditing(false)}>Cancel</button>
              </div>
            </div>
          )}
          <hr style={{ borderColor: '#2d3148', margin: '1rem 0' }} />
          {song.has_mp3 ? (
            <>
              <p style={{ color: '#6ee7b7', marginBottom: '0.5rem' }}>✓ MP3 available</p>
              <audio controls src={`http://localhost:8000/songs/${id}/mp3`} />
              <br /><br />
              <a href={`http://localhost:8000/songs/${id}/mp3`} download>
                <button className="btn-success">⬇ Download MP3</button>
              </a>
            </>
          ) : (
            <>
              <p style={{ color: '#64748b', marginBottom: '0.5rem' }}>No MP3 yet</p>
              <button className="btn-primary" onClick={downloadSingle} disabled={downloading}>
                {downloading ? `⏳ ${dlStatus}` : '⬇ Find & Download MP3'}
              </button>
              {downloading && (
                <div style={{ marginTop: '0.5rem' }}>
                  <div style={{ height: '4px', background: '#2d3148', borderRadius: '2px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: '40%', background: '#a78bfa', borderRadius: '2px', animation: 'slide 1.4s ease-in-out infinite' }} />
                  </div>
                  <p style={{ color: '#64748b', fontSize: '0.75rem', marginTop: '0.25rem' }}>{elapsed}s elapsed</p>
                </div>
              )}
            </>
          )}
        </div>
        <div className="card">
          <h2>Chord Sheet</h2>
          {song.has_chords
            ? <img className="chord-img" src={`http://localhost:8000/songs/${id}/chords`} alt="Chord sheet" />
            : <p style={{ color: '#64748b' }}>No chord sheet attached.</p>}
        </div>
      </div>
    </div>
  );
}
