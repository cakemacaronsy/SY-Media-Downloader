import React, { useState, useEffect, useRef } from 'react';
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
  const [job, setJob] = useState(null);
  const alive = useRef(true);

  // Re-arm on mount: StrictMode mounts, unmounts and remounts in development
  useEffect(() => {
    alive.current = true;
    return () => { alive.current = false; };
  }, []);

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

  const sleep = ms => new Promise(r => setTimeout(r, ms));

  const errorMessage = (err) => {
    if (err.response) {
      const { error, detail } = err.response.data || {};
      // FastAPI validation errors put a list of objects in `detail`
      return error || (typeof detail === 'string' ? detail : null) || 'Server error';
    }
    if (err.request) return 'No response from server. Is the backend running?';
    return err.message || 'Unknown error';
  };

  // Start a background job, then poll it until it finishes
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (busy) return;
    setBusy(true);
    setStatus('Starting...');
    setDownloadLink(null);
    setVideoTitle('');
    setShowPreview(false);
    setJob(null);
    try {
      const { data: created } = await axios.post(`${API_URL}/api/jobs`, { url, format, resolution });
      let failures = 0;
      while (alive.current) {
        await sleep(1000);
        let current;
        try {
          ({ data: current } = await axios.get(`${API_URL}/api/jobs/${created.id}`));
          failures = 0;
        } catch (pollErr) {
          // ride out brief network blips, but give up if the job is gone
          if (pollErr.response?.status === 404 || ++failures >= 5) throw pollErr;
          continue;
        }
        if (!alive.current) return;
        setJob(current);
        if (current.status === 'done') {
          const result = current.result;
          setDownloadLink(`${API_URL}${result.file}`);
          // The server may fall back to another container, so trust its answer
          setFileFormat(result.format || format);
          setVideoTitle(result.title || '');
          setStatus(result.title ? `Ready: "${result.title}"` : 'Ready!');
          break;
        }
        if (current.status === 'error') {
          setStatus(`Error: ${current.error || 'Download failed'}`);
          break;
        }
        setStatus(current.status === 'processing'
          ? 'Processing (merging / converting)...'
          : current.status === 'queued' ? 'Fetching video info...' : 'Downloading...');
      }
    } catch (err) {
      setStatus(`Error: ${errorMessage(err)}`);
    } finally {
      if (alive.current) {
        setBusy(false);
        setJob(null);
      }
    }
  };

  const formatBytes = (n) => {
    if (!n) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB'];
    const i = Math.min(Math.floor(Math.log(n) / Math.log(1024)), units.length - 1);
    return `${(n / 1024 ** i).toFixed(i ? 1 : 0)} ${units[i]}`;
  };

  const formatEta = (s) => (s == null ? '' : s >= 60 ? `${Math.floor(s / 60)}m ${s % 60}s left` : `${s}s left`);

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
      {busy && job && (
        <div className="progress" role="progressbar" aria-valuemin={0} aria-valuemax={100}
             aria-valuenow={Math.round(job.progress || 0)}>
          <div className="progress-track">
            <div
              className={`progress-fill${job.status === 'processing' ? ' pulsing' : ''}`}
              style={{ width: `${job.progress || 0}%` }}
            />
          </div>
          <div className="progress-meta">
            <span>{Math.round(job.progress || 0)}%</span>
            {job.status === 'downloading' && (
              <span>
                {job.parts > 1 && `${job.part === 1 ? 'Video' : 'Audio'} · `}
                {formatBytes(job.downloaded_bytes)}
                {job.total_bytes ? ` / ${formatBytes(job.total_bytes)}` : ''}
                {job.speed ? ` · ${formatBytes(job.speed)}/s` : ''}
                {job.eta != null ? ` · ${formatEta(job.eta)}` : ''}
              </span>
            )}
          </div>
        </div>
      )}
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
