import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api';

const PAGE_SIZE = 100;

export default function Library() {
  const [songs, setSongs] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [q, setQ] = useState('');
  const [artist, setArtist] = useState('');
  const [hasMp3, setHasMp3] = useState('');
  const [hasChords, setHasChords] = useState('');
  const navigate = useNavigate();

  const load = useCallback(async () => {
    const params = { skip: page * PAGE_SIZE, limit: PAGE_SIZE };
    if (q) params.q = q;
    if (artist) params.artist = artist;
    if (hasMp3 !== '') params.has_mp3 = hasMp3 === 'yes';
    if (hasChords !== '') params.has_chords = hasChords === 'yes';
    const res = await api.get('/songs', { params });
    setSongs(res.data.items);
    setTotal(res.data.total);
  }, [page, q, artist, hasMp3, hasChords]);

  useEffect(() => { load(); }, [load]);

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div>
      <h1>Song Library <span style={{ color: '#64748b', fontSize: '1rem' }}>({total} songs)</span></h1>
      <div className="card">
        <div className="filters">
          <input placeholder="Search title or artist…" value={q} onChange={e => { setQ(e.target.value); setPage(0); }} />
          <input placeholder="Filter by artist…" value={artist} onChange={e => { setArtist(e.target.value); setPage(0); }} />
          <select value={hasMp3} onChange={e => { setHasMp3(e.target.value); setPage(0); }}>
            <option value="">All (MP3)</option>
            <option value="yes">Has MP3</option>
            <option value="no">No MP3</option>
          </select>
          <select value={hasChords} onChange={e => { setHasChords(e.target.value); setPage(0); }}>
            <option value="">All (Chords)</option>
            <option value="yes">Has Chords</option>
            <option value="no">No Chords</option>
          </select>
        </div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>#</th><th>Title</th><th>Artist</th><th>Key</th><th>MP3</th><th>Chords</th></tr></thead>
            <tbody>
              {songs.map((s, i) => (
                <tr key={s.id} onClick={() => navigate(`/songs/${s.id}`)}>
                  <td style={{ color: '#64748b' }}>{page * PAGE_SIZE + i + 1}</td>
                  <td className="rtl">{s.title}</td>
                  <td className="rtl">{s.artist}</td>
                  <td><span className="tag">{s.original_key || '—'}</span></td>
                  <td>{s.has_mp3 ? <span className="badge badge-green">✓</span> : <span className="badge badge-gray">—</span>}</td>
                  <td>{s.has_chords ? <span className="badge badge-green">✓</span> : <span className="badge badge-gray">—</span>}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {totalPages > 1 && (
          <div className="pagination">
            <button className="btn-secondary" onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0}>← Prev</button>
            <span>Page {page + 1} / {totalPages}</span>
            <button className="btn-secondary" onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1}>Next →</button>
          </div>
        )}
      </div>
    </div>
  );
}
