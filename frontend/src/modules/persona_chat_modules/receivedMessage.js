import { useEffect, useRef, useState } from 'react';

import './receivedMessage.css';

function ReceivedMessage({text, onTypingComplete}) {
  const [visibleText, setVisibleText] = useState("");
  const completedRef = useRef(false);
  const timeoutRef = useRef(null);

  useEffect(() => {
    const fullText = text || "";
    let index = 0;
    completedRef.current = false;
    setVisibleText("");

    function markComplete() {
      if (completedRef.current) return;
      completedRef.current = true;
      onTypingComplete?.();
    }

    function nextDelay(character) {
      if (character === " ") return 8 + Math.random() * 16;
      if (/[,.]/.test(character)) return 42 + Math.random() * 70;
      if (/[!?;]/.test(character)) return 75 + Math.random() * 95;
      return 12 + Math.random() * 28;
    }

    function typeNextCharacter() {
      if (index >= fullText.length) {
        markComplete();
        return;
      }

      const character = fullText[index];
      index += 1;
      setVisibleText(fullText.slice(0, index));
      timeoutRef.current = window.setTimeout(
        typeNextCharacter,
        nextDelay(character)
      );
    }

    if (!fullText) {
      markComplete();
    } else {
      timeoutRef.current = window.setTimeout(typeNextCharacter, 70 + Math.random() * 110);
    }

    return () => {
      window.clearTimeout(timeoutRef.current);
    };
  }, [text, onTypingComplete]);

  return (
    <div className="ReceivedMessage">
        <div>
          <p className="unbounded-weight300">
            {visibleText}
            {visibleText.length < (text || "").length && (
              <span className="received-message-cursor" aria-hidden="true"></span>
            )}
          </p>
          <div id="received-message-bubbletick"></div>
        </div>
    </div>
  );
};

export default ReceivedMessage;
