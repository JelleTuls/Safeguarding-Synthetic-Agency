import { useEffect, useRef, useState } from 'react';

import './awaitingMessage.css';

const TYPING_PHRASES = [
  "Thinking how to respond",
  "Trying to find the right words",
  "Checking what fits this profile",
  "Remembering some recent context",
  "Correcting my own grammar",
  "Keeping the answer in bounds",
  "Making the next part sound natural",
  "Pausing before I send this",
];

const MIN_PHRASE_DURATION_MS = 800;
const MAX_PHRASE_DURATION_MS = 1600;

function randomDuration() {
  const spread = MAX_PHRASE_DURATION_MS - MIN_PHRASE_DURATION_MS;
  return MIN_PHRASE_DURATION_MS + Math.round(Math.random() * spread);
}

function randomPhrase(previousPhrase) {
  const options = TYPING_PHRASES.filter(phrase => phrase !== previousPhrase);
  return options[Math.floor(Math.random() * options.length)] || TYPING_PHRASES[0];
}

function AwaitingMessage({text}) {
  const [statusText, setStatusText] = useState(text || randomPhrase());
  const statusRef = useRef(statusText);

  useEffect(() => {
    statusRef.current = text || randomPhrase(statusRef.current);
    setStatusText(statusRef.current);

    let timeoutId;
    let mounted = true;

    function scheduleNextPhrase() {
      timeoutId = window.setTimeout(() => {
        if (!mounted) return;
        const nextPhrase = randomPhrase(statusRef.current);
        statusRef.current = nextPhrase;
        setStatusText(nextPhrase);
        scheduleNextPhrase();
      }, randomDuration());
    }

    scheduleNextPhrase();

    return () => {
      mounted = false;
      window.clearTimeout(timeoutId);
    };
  }, [text]);

  return (
    <div className="AwaitingMessage">
        <div className="unbounded-weight300">
          <span className="awaiting-status-text">{statusText}</span>
          <span className="awaiting-dots" aria-hidden="true">
            <span>.</span>
            <span>.</span>
            <span>.</span>
          </span>
          <div id="awaiting-message-bubbletick"></div>
        </div>
    </div>
  );
};

export default AwaitingMessage;
