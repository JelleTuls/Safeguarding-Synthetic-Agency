import { createPortal } from 'react-dom';
import { useEffect, useRef, useState } from 'react';

import './messageAnalysis.css';

function formatValue(value) {
  if (value === null || value === undefined || value === "") return "n/a";
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "object") return JSON.stringify(value);
  return String(value).replaceAll("_", " ");
}

function MessageAnalysis({ analysis, align = "left" }) {
  const triggerRef = useRef(null);
  const closeTimerRef = useRef(null);
  const [isOpen, setIsOpen] = useState(false);
  const [popoverStyle, setPopoverStyle] = useState(null);

  useEffect(() => {
    return () => {
      window.clearTimeout(closeTimerRef.current);
    };
  }, []);

  useEffect(() => {
    if (!isOpen || !triggerRef.current) return;

    function positionPopover() {
      const rect = triggerRef.current.getBoundingClientRect();
      const width = Math.min(330, Math.max(286, window.innerWidth - 24));
      const maxHeight = Math.min(360, window.innerHeight - 24);
      const preferredLeft = align === "right" ? rect.right - width : rect.left;
      const left = Math.min(
        Math.max(12, preferredLeft),
        Math.max(12, window.innerWidth - width - 12)
      );
      const belowTop = rect.bottom + 8;
      const aboveTop = rect.top - maxHeight - 8;
      const top = belowTop + maxHeight <= window.innerHeight - 12
        ? belowTop
        : Math.max(12, aboveTop);

      setPopoverStyle({
        left: `${left}px`,
        top: `${top}px`,
        width: `${width}px`,
        maxHeight: `${maxHeight}px`,
      });
    }

    positionPopover();
    window.addEventListener("resize", positionPopover);
    window.addEventListener("scroll", positionPopover, true);

    return () => {
      window.removeEventListener("resize", positionPopover);
      window.removeEventListener("scroll", positionPopover, true);
    };
  }, [align, isOpen]);

  if (!analysis?.sections?.length) return null;

  function openPopover() {
    window.clearTimeout(closeTimerRef.current);
    setIsOpen(true);
  }

  function scheduleClose() {
    window.clearTimeout(closeTimerRef.current);
    closeTimerRef.current = window.setTimeout(() => setIsOpen(false), 120);
  }

  const popover = isOpen && popoverStyle
    ? createPortal(
        <div
          className="message-analysis-popover"
          role="tooltip"
          style={popoverStyle}
          onMouseEnter={openPopover}
          onMouseLeave={scheduleClose}
        >
          <h4 className="unbounded-weight400">{analysis.title || "Message Analysis"}</h4>
          {analysis.sections.map((section, sectionIndex) => (
            <section key={`${section.title}-${sectionIndex}`}>
              <h5 className="unbounded-weight400">{section.title}</h5>
              <div className="message-analysis-grid">
                {(section.rows || []).map(([label, value], rowIndex) => (
                  <div className="message-analysis-row" key={`${label}-${rowIndex}`}>
                    <span>{label}</span>
                    <strong>{formatValue(value)}</strong>
                  </div>
                ))}
              </div>
            </section>
          ))}
        </div>,
        document.body
      )
    : null;

  return (
    <div
      className={`MessageAnalysis MessageAnalysis--${align}`}
      onMouseEnter={openPopover}
      onMouseLeave={scheduleClose}
      onFocus={openPopover}
      onBlur={scheduleClose}
    >
      <button
        ref={triggerRef}
        className="message-analysis-trigger unbounded-weight400"
        aria-label="Show message analysis"
        type="button"
      >
        i
      </button>
      {popover}
    </div>
  );
}

export default MessageAnalysis;
