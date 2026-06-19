// Collapsible in-app log console for backend narrative traces.
//
// The panel polls the backend only while open and renders redacted Python log
// output in a compact terminal-like view for live thesis demos and debugging.

import { useEffect, useMemo, useRef, useState } from 'react';

import { backendApiUrl } from '../../config/api';
import './liveLogPanel.css';

function formatLogEntry(entry) {
  const source = entry.source || 'backend';
  const level = entry.level || 'INFO';
  const message = entry.message || '';
  const stamp = entry.timestamp ? new Date(entry.timestamp) : null;
  const time = stamp && !Number.isNaN(stamp.getTime())
    ? stamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })
    : '';
  return `${time ? `${time} ` : ''}${level} ${source} :: ${message}`;
}

function LiveLogPanel({ isOpen, onToggle }) {
  const [entries, setEntries] = useState([]);
  const [status, setStatus] = useState('idle');
  const [error, setError] = useState('');
  const logBodyRef = useRef(null);

  const renderedLines = useMemo(() => entries.map(formatLogEntry), [entries]);

  useEffect(() => {
    if (!isOpen) return undefined;

    let cancelled = false;

    async function fetchLogs() {
      try {
        setStatus((current) => (current === 'ready' ? current : 'loading'));
        const response = await fetch(`${backendApiUrl}/api/logs/recent?limit=900`);
        if (!response.ok) {
          throw new Error(`Log request failed with ${response.status}`);
        }
        const payload = await response.json();
        if (!cancelled) {
          setEntries(Array.isArray(payload.entries) ? payload.entries : []);
          setStatus('ready');
          setError('');
        }
      } catch (fetchError) {
        if (!cancelled) {
          setStatus('error');
          setError(fetchError.message || 'Could not load logs.');
        }
      }
    }

    fetchLogs();
    const intervalId = window.setInterval(fetchLogs, 1500);
    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen || !logBodyRef.current) return;
    logBodyRef.current.scrollTop = logBodyRef.current.scrollHeight;
  }, [isOpen, renderedLines.length]);

  return (
    <aside className={`liveLogPanel ${isOpen ? 'isOpen' : 'isClosed'}`} aria-label="Python log panel">
      <button
        aria-expanded={isOpen}
        aria-label={isOpen ? 'Hide Python logs' : 'Show Python logs'}
        className="liveLogToggle"
        title={isOpen ? 'Hide Python logs' : 'Show Python logs'}
        type="button"
        onClick={onToggle}
      >
        <span aria-hidden="true">{isOpen ? '-' : '+'}</span>
      </button>

      {isOpen && (
        <div className="liveLogWindow">
          <div className="liveLogHeader">
            <strong>Python log</strong>
            <small>{status === 'ready' ? `${entries.length} lines` : status}</small>
          </div>
          <pre ref={logBodyRef} className="liveLogBody">
            {error || (renderedLines.length ? renderedLines.join('\n') : 'Waiting for backend log output...')}
          </pre>
        </div>
      )}
    </aside>
  );
}

export default LiveLogPanel;
