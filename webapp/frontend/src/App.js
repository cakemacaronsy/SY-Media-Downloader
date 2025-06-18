import React, { useState, useEffect } from 'react';
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

  useEffect(() => {
    if (lightMode) {
      document.body.classList.add('light');
    } else {
      document.body.classList.remove('light');
    }
  }, [lightMode]);

  const handleThemeToggle = () => {
    setLightMode(lm => !lm);
  };

  // Detect platform from URL
  const detectPlatform = (url) => {
    if (url.includes('youtube.com') || url.includes('youtu.be')) return 'YouTube';
    if (url.includes('facebook.com') || url.includes('fb.watch')) return 'Facebook';
    if (url.includes('instagram.com')) return 'Instagram';
    if (url.includes('tiktok.com')) return 'TikTok';
    if (url.includes('twitter.com') || url.includes('x.com')) return 'Twitter/X';
    if (url.includes('reddit.com')) return 'Reddit';
    if (url.includes('vimeo.com')) return 'Vimeo';
    if (url.includes('pinterest.com')) return 'Pinterest';
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
    setStatus('Downloading...');
    setDownloadLink(null);
    setVideoTitle('');
    try {
      const res = await fetch('http://localhost:8000/api/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url, format, resolution })
      });
      const data = await res.json();
      if (data.file) {
        setDownloadLink(`http://localhost:8000${data.file}`);
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
      setStatus(`Error: ${err.message || 'Unknown error'}`);
    }
  };

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
        <button type="submit">Download</button>
      </form>
      <div className="status">{status}</div>
      {downloadLink && (
        <div className="download-section">
          <button 
            className="preview-button" 
            onClick={() => setShowPreview(!showPreview)}
          >
            {showPreview ? 'Hide Preview' : 'Preview'}
          </button>
          
          <a href={downloadLink} download={videoTitle || true} className="download-link">
            {videoTitle ? `Download "${videoTitle}"` : 'Download file'}
          </a>
          
          {showPreview && (
            <div className="media-preview">
              {['mp4', 'webm', 'mkv', 'avi'].includes(format) ? (
                <video controls width="100%">
                  <source src={downloadLink} type={`video/${format}`} />
                  Your browser does not support the video tag.
                </video>
              ) : (
                <audio controls style={{width: '100%'}}>
                  <source 
                    src={downloadLink} 
                    type={format === 'mp3' ? 'audio/mpeg' : 
                          format === 'm4a' ? 'audio/mp4' : 
                          format === 'wav' ? 'audio/wav' : 
                          'audio/flac'} 
                  />
                  Your browser does not support the audio tag.
                </audio>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
