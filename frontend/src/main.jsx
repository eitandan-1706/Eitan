import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import Library from './pages/Library';
import Downloader from './pages/Downloader';
import SongDetail from './pages/SongDetail';
import Import from './pages/Import';
import './app.css';

function Nav() {
  return (
    <nav className="navbar">
      <span className="nav-brand">🎵 Song Manager</span>
      <NavLink className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')} to="/">Library</NavLink>
      <NavLink className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')} to="/download">Download</NavLink>
      <NavLink className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')} to="/import">Import</NavLink>
    </nav>
  );
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <Nav />
    <main className="main-content">
      <Routes>
        <Route path="/" element={<Library />} />
        <Route path="/songs/:id" element={<SongDetail />} />
        <Route path="/download" element={<Downloader />} />
        <Route path="/import" element={<Import />} />
      </Routes>
    </main>
  </BrowserRouter>
);
