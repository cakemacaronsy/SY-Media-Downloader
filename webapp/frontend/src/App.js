import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [url, setUrl] = useState('');
  const [format, setFormat] = useState('mp4');
  const [resolution, setResolution] = useState('best');
  const [status, setStatus] = useState('');
  const [downloadLink, setDownloadLink] = useState(null);
  const [videoTitle, setVideoTitle] = useState('');
  const [platform, setPlatform] = useState('');
  const [lightMode, setLightMode] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [busy, setBusy] = useState(false);
  const [elapsed, setElapsed] = useState(0);
  const [fileFormat, setFileFormat] = useState('');

  // Get API URL from environment variable or use localhost as fallback
  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  useEffect(() => {
    if (lightMode) {
      document.body.classList.add('light');
    } else {
      document.body.classList.remove('light');
    }
  }, [lightMode]);

  // Tick a timer while a download runs so the user can see it hasn't hung
  useEffect(() => {
    if (!busy) return undefined;
    setElapsed(0);
    const id = setInterval(() => setElapsed(s => s + 1), 1000);
    return () => clearInterval(id);
  }, [busy]);

  const handleThemeToggle = () => {
    setLightMode(lm => !lm);
  };

  // Detect platform from URL
  const detectPlatform = (url) => {
    let host;
    try {
      host = new URL(url).hostname.toLowerCase();
    } catch {
      return 'Unknown';
    }
    const is = (...domains) => domains.some(d => host === d || host.endsWith('.' + d));
    if (is('youtube.com', 'youtu.be')) return 'YouTube';
    if (is('facebook.com', 'fb.watch')) return 'Facebook';
    if (is('instagram.com')) return 'Instagram';
    if (is('tiktok.com')) return 'TikTok';
    if (is('twitter.com', 'x.com')) return 'Twitter/X';
    if (is('reddit.com', 'redd.it')) return 'Reddit';
    if (is('vimeo.com')) return 'Vimeo';
    if (is('pinterest.com', 'pin.it')) return 'Pinterest';
    return 'Unknown';
  };

  // Update platform when URL changes
  useEffect(() => {
    if (url) {
      setPlatform(detectPlatform(url));
    } else {
      setPlatform('');
    }
  }, [url]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setStatus('Downloading on the server... large videos can take a few minutes.');
    setDownloadLink(null);
    setVideoTitle('');
    setShowPreview(false);
    try {
      const response = await axios.post(`${API_URL}/api/download`, {
        url,
        format,
        resolution
      });
      const data = response.data;
      if (data.file) {
        setDownloadLink(`${API_URL}${data.file}`);
        // The server may fall back to another container, so trust its answer
        setFileFormat(data.format || format);
        if (data.title) {
          setVideoTitle(data.title);
          setStatus(`Ready: "${data.title}"`);
        } else {
          setStatus('Ready!');
        }
      } else if (data.error) {
        setStatus(`Error: ${data.error}`);
      } else {
        setStatus('Failed to download.');
      }
    } catch (err) {
      if (err.response) {
        // Server responded with error
        const { error, detail } = err.response.data || {};
        // FastAPI validation errors put a list of objects in `detail`
        const msg = error || (typeof detail === 'string' ? detail : null) || 'Server error';
        setStatus(`Error: ${msg}`);
      } else if (err.request) {
        // Request made but no response
        setStatus('Error: No response from server. Is the backend running?');
      } else {
        // Something else happened
        setStatus(`Error: ${err.message || 'Unknown error'}`);
      }
    } finally {
      setBusy(false);
    }
  };

  // Browsers can't play MKV/AVI (or FLAC everywhere), so only offer preview where it works
  const PREVIEW_TYPES = {
    mp4: 'video/mp4', webm: 'video/webm',
    mp3: 'audio/mpeg', m4a: 'audio/mp4', wav: 'audio/wav',
  };
  const previewType = PREVIEW_TYPES[fileFormat];

  return (
    <div className="container">
      <button className="theme-toggle" onClick={handleThemeToggle} aria-label="Toggle dark/light mode">
        {lightMode ? '🌞' : '🌙'}
      </button>
      <h1>SY Media Downloader</h1>
      {platform && <div className="platform-indicator">Platform: {platform}</div>}
      <form onSubmit={handleSubmit}>
        <input
          type="text"
          placeholder="Enter video URL..."
          value={url}
          onChange={e => setUrl(e.target.value)}
          disabled={busy}
          required
        />
        <select value={format} onChange={e => setFormat(e.target.value)}>
          <optgroup label="Video Formats">
            <option value="mp4">MP4 (QuickTime Compatible)</option>
            <option value="webm">WEBM</option>
            <option value="mkv">MKV</option>
            <option value="avi">AVI</option>
          </optgroup>
          <optgroup label="Audio Formats">
            <option value="mp3">MP3</option>
            <option value="m4a">M4A</option>
            <option value="wav">WAV</option>
            <option value="flac">FLAC</option>
          </optgroup>
        </select>
        
        {/* Only show resolution selector for video formats */}
        {['mp4', 'webm', 'mkv', 'avi'].includes(format) && (
          <select value={resolution} onChange={e => setResolution(e.target.value)} className="resolution-select">
            <option value="best">Best Quality</option>
            <option value="2160">4K (2160p)</option>
            <option value="1440">QHD (1440p)</option>
            <option value="1080">Full HD (1080p)</option>
            <option value="720">HD (720p)</option>
            <option value="480">SD (480p)</option>
            <option value="360">Low (360p)</option>
            <option value="240">Very Low (240p)</option>
            <option value="144">Lowest (144p)</option>
          </select>
        )}
        <button type="submit" disabled={busy}>
          {busy ? `Working... ${elapsed}s` : 'Download'}
        </button>
      </form>
      <div className="status">{status}</div>
      {downloadLink && (
        <div className="download-section">
          {previewType && (
            <button
              className="preview-button"
              onClick={() => setShowPreview(!showPreview)}
            >
              {showPreview ? 'Hide Preview' : 'Preview'}
            </button>
          )}

          <a href={downloadLink} download={videoTitle || true} className="download-link">
            {videoTitle ? `Download "${videoTitle}"` : 'Download file'}
          </a>
          
          {showPreview && previewType && (
            <div className="media-preview">
              {previewType.startsWith('video') ? (
                <video controls width="100%" src={downloadLink} />
              ) : (
                <audio controls style={{ width: '100%' }} src={downloadLink} />
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
