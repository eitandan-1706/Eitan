import React, { useState, useRef } from 'react';
import api from '../api';

const ICONS = {
  queued: '⏳', searching_drive: '🔍', found_on_drive: '✅',
  searching_youtube: '▶️', youtube_match: '🎬', downloading: '⬇️',
  converting: '🔄', uploading: '☁️', done: '✅', error: '❌',
  needs_confirmation: '❓', skipped: '⏭️',
};

export default function Downloader() {
  const [input, setInput] = useState('');
  const [autoMode, setAutoMode] = useState(true);
  const [allMissing, setAllMissing] = useState(false);
  const [queue, setQueue] = useState([]);
  const [running, setRunning] = useState(false);
  const [pendingConfirmations, setPendingConfirmations] = useState([]);
  const esRef = useRef(null);

  const startDownload = async () => {
    const lines = input.split('\n').map(l => l.trim()).filter(Boolean);
    if (!allMissing && lines.length === 0) return;
    setRunning(true); setQueue([]); setPendingConfirmations([]);
    const payload = { auto_mode: autoMode, all_missing: allMissing };
    if (!allMissing) payload.titles = lines;
    const res = await api.post('/download/batch', payload);
    const jobId = res.data.job_id;
    if (!allMissing) setQueue(lines.map(t => ({ key: t, title: t, event: 'queued', extra: '' })));
    const es = new EventSource(`http://localhost:8000/download/status/${jobId}`);
    esRef.current = es;
    es.onmessage = (e) => {
      try {
        const d = JSON.parse(e.data);
        if (d.type === 'ping') return;
        if (d.event === 'needs_confirmation') {
          setPendingConfirmations(prev => [...prev, {
            conf_key: d.conf_key,
            song: d.song,
            artist: d.artist,
            found_name: d.found_name,
          }]);
        }
        if (d.event === 'skipped') {
          setPendingConfirmations(prev => prev.filter(c => c.conf_key !== d.conf_key));
        }
        setQueue(prev => {
          const exists = prev.find(x => x.title === d.song);
          const update = { event: d.event, extra: d.yt_title || d.filename || d.found_name || d.reason || '' };
          if (exists) return prev.map(x => x.title === d.song ? { ...x, ...update } : x);
          return [...prev, { key: `${d.song}-${d.artist}`, title: d.song, artist: d.artist, ...update }];
        });
      } catch {}
    };
    es.onerror = () => { es.close(); setRunning(false); };
  };

  const respond = async (conf_key, proceed) => {
    await api.post('/download/confirm', { conf_key, proceed });
    setPendingConfirmations(prev => prev.filter(c => c.conf_key !== conf_key));
  };

  const stop = () => { esRef.current?.close(); setRunning(false); };
  const doneCount = queue.filter(q => ['done', 'found_on_drive', 'skipped'].includes(q.event)).length;
  const errCount = queue.filter(q => q.event === 'error').length;

  return (
    <div>
      <h1>YouTube → MP3 Downloader</h1>
      <div className="card">
        <h2>Input</h2>
        <p className="info-text">One song per line: "Title - Artist". Or check below to process all missing.</p>
        <div style={{ marginBottom: '0.75rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
            <input type="checkbox" style={{ width: 'auto' }} checked={allMissing} onChange={e => setAllMissing(e.target.checked)} />
            Download all songs in library that have no MP3
          </label>
        </div>
        {!allMissing && (
          <textarea rows={6} placeholder={'אהבה - אביב גפן\nBohemian Rhapsody - Queen'}
            value={input} onChange={e => setInput(e.target.value)}
            style={{ fontFamily: 'monospace', marginBottom: '0.75rem' }} />
        )}
        <div className="gap-row" style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer', whiteSpace: 'nowrap' }}>
            <input type="checkbox" style={{ width: 'auto' }} checked={autoMode} onChange={e => setAutoMode(e.target.checked)} />
            Auto mode (pick first YouTube result)
          </label>
        </div>
        <div className="gap-row">
          <button className="btn-primary" onClick={startDownload} disabled={running}>
            {running ? '⏳ Running…' : '▶ Start Download'}
          </button>
          {running && <button className="btn-danger" onClick={stop}>Stop</button>}
        </div>
      </div>

      {pendingConfirmations.length > 0 && (
        <div className="card">
          <h2>⚠️ Confirmation Required</h2>
          {pendingConfirmations.map(c => (
            <div key={c.conf_key} style={{ border: '1px solid #f59e0b', borderRadius: '8px', padding: '1rem', marginBottom: '0.75rem' }}>
              <p style={{ margin: '0 0 0.4rem' }}>
                <span style={{ color: '#94a3b8' }}>Requested:</span>{' '}
                <strong className="rtl">{c.song}{c.artist ? ` — ${c.artist}` : ''}</strong>
              </p>
              <p style={{ margin: '0 0 0.75rem' }}>
                <span style={{ color: '#94a3b8' }}>Found on Drive:</span>{' '}
                <strong className="rtl">{c.found_name}</strong>
              </p>
              <p style={{ color: '#f59e0b', margin: '0 0 0.75rem', fontSize: '0.85rem' }}>
                The filename doesn't exactly match. Use this file anyway?
              </p>
              <div className="gap-row">
                <button className="btn-primary" onClick={() => respond(c.conf_key, true)}>Use it</button>
                <button className="btn-danger" onClick={() => respond(c.conf_key, false)}>Skip → try YouTube</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {queue.length > 0 && (
        <div className="card">
          <h2>Queue {running && `— ${doneCount + errCount} / ${queue.length} done`}</h2>
          {queue.map((item, i) => (
            <div className="queue-item" key={i}>
              <span className="queue-icon">{ICONS[item.event] || '⏳'}</span>
              <span className="rtl" style={{ flex: 1 }}>{item.title}{item.artist ? ` — ${item.artist}` : ''}</span>
              <span style={{ color: '#64748b', fontSize: '0.78rem' }}>
                {item.event?.replace(/_/g, ' ')}{item.extra ? ` · ${item.extra}` : ''}
              </span>
            </div>
          ))}
          {!running && (
            <p style={{ marginTop: '0.75rem', color: '#6ee7b7' }}>
              Done: {doneCount} &nbsp;·&nbsp;
              <span style={{ color: errCount > 0 ? '#f87171' : '#64748b' }}>{errCount} errors</span>
            </p>
          )}
        </div>
      )}
    </div>
  );
}
