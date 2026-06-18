// Assistant message bubble with inline analysis popovers.
//
// Renders streamed persona responses, safely handles small markdown fragments,
// and exposes guardrail/lightweight analysis metadata through `MessageAnalysis`.

import { useEffect, useRef, useState } from 'react';

import './receivedMessage.css';
import MessageAnalysis from './messageAnalysis';

function safeLinkHref(href) {
  if (/^(https?:|mailto:)/i.test(href)) return href;
  return "#";
}

function parseInlineMarkdown(text, keyPrefix = "inline") {
  const elements = [];
  const pattern = /(\[([^\]]+)\]\(([^)\s]+)\))|(`([^`]+)`)|(\*\*([^*]+)\*\*)|(__([^_]+)__)|(~~([^~]+)~~)|(\*([^*\n]+)\*)|(_([^_\n]+)_)/g;
  let lastIndex = 0;
  let match;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      elements.push(text.slice(lastIndex, match.index));
    }

    const key = `${keyPrefix}-${match.index}`;
    if (match[1]) {
      elements.push(
        <a
          key={key}
          href={safeLinkHref(match[3])}
          target="_blank"
          rel="noreferrer"
        >
          {parseInlineMarkdown(match[2], `${key}-link`)}
        </a>
      );
    } else if (match[4]) {
      elements.push(<code key={key}>{match[5]}</code>);
    } else if (match[6]) {
      elements.push(<strong key={key}>{parseInlineMarkdown(match[7], `${key}-bold`)}</strong>);
    } else if (match[8]) {
      elements.push(<strong key={key}>{parseInlineMarkdown(match[9], `${key}-bold`)}</strong>);
    } else if (match[10]) {
      elements.push(<del key={key}>{parseInlineMarkdown(match[11], `${key}-del`)}</del>);
    } else if (match[12]) {
      elements.push(<em key={key}>{parseInlineMarkdown(match[13], `${key}-em`)}</em>);
    } else if (match[14]) {
      elements.push(<em key={key}>{parseInlineMarkdown(match[15], `${key}-em`)}</em>);
    }

    lastIndex = pattern.lastIndex;
  }

  if (lastIndex < text.length) {
    elements.push(text.slice(lastIndex));
  }

  return elements;
}

function splitMarkdownTableRow(line) {
  return line
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map(cell => cell.trim());
}

function isMarkdownTableSeparator(line) {
  return /^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?\s*$/.test(line);
}

function renderMarkdown(text) {
  const lines = (text || "").split("\n");
  const blocks = [];
  let index = 0;

  while (index < lines.length) {
    const line = lines[index];

    if (!line.trim()) {
      index += 1;
      continue;
    }

    if (
      line.includes("|") &&
      index + 1 < lines.length &&
      isMarkdownTableSeparator(lines[index + 1])
    ) {
      const blockKey = index;
      const headerCells = splitMarkdownTableRow(line);
      const rows = [];
      index += 2;
      while (index < lines.length && lines[index].includes("|") && lines[index].trim()) {
        rows.push(splitMarkdownTableRow(lines[index]));
        index += 1;
      }
      blocks.push(
        <div className="received-message-table-wrap" key={`table-${blockKey}`}>
          <table>
            <thead>
              <tr>
                {headerCells.map((cell, cellIndex) => (
                  <th key={`th-${cellIndex}`}>{parseInlineMarkdown(cell, `th-${blockKey}-${cellIndex}`)}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, rowIndex) => (
                <tr key={`tr-${rowIndex}`}>
                  {row.map((cell, cellIndex) => (
                    <td key={`td-${rowIndex}-${cellIndex}`}>
                      {parseInlineMarkdown(cell, `td-${blockKey}-${rowIndex}-${cellIndex}`)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      );
      continue;
    }

    if (/^\s*[-*+]\s+/.test(line)) {
      const blockKey = index;
      const items = [];
      while (index < lines.length && /^\s*[-*+]\s+/.test(lines[index])) {
        items.push(lines[index].replace(/^\s*[-*+]\s+/, ""));
        index += 1;
      }
      blocks.push(
        <ul key={`ul-${blockKey}`}>
          {items.map((item, itemIndex) => (
            <li key={`li-${itemIndex}`}>{parseInlineMarkdown(item, `ul-${blockKey}-${itemIndex}`)}</li>
          ))}
        </ul>
      );
      continue;
    }

    if (/^\s*\d+[.)]\s+/.test(line)) {
      const blockKey = index;
      const items = [];
      while (index < lines.length && /^\s*\d+[.)]\s+/.test(lines[index])) {
        items.push(lines[index].replace(/^\s*\d+[.)]\s+/, ""));
        index += 1;
      }
      blocks.push(
        <ol key={`ol-${blockKey}`}>
          {items.map((item, itemIndex) => (
            <li key={`oli-${itemIndex}`}>{parseInlineMarkdown(item, `ol-${blockKey}-${itemIndex}`)}</li>
          ))}
        </ol>
      );
      continue;
    }

    if (/^\s*>\s?/.test(line)) {
      const quoteLines = [];
      while (index < lines.length && /^\s*>\s?/.test(lines[index])) {
        quoteLines.push(lines[index].replace(/^\s*>\s?/, ""));
        index += 1;
      }
      blocks.push(
        <blockquote key={`quote-${index}`}>
          {parseInlineMarkdown(quoteLines.join(" "), `quote-${index}`)}
        </blockquote>
      );
      continue;
    }

    const headingMatch = /^(#{1,3})\s+(.+)$/.exec(line);
    if (headingMatch) {
      const HeadingTag = `h${headingMatch[1].length + 3}`;
      blocks.push(
        <HeadingTag key={`heading-${index}`}>
          {parseInlineMarkdown(headingMatch[2], `heading-${index}`)}
        </HeadingTag>
      );
      index += 1;
      continue;
    }

    const paragraphLines = [];
    while (
      index < lines.length &&
      lines[index].trim() &&
      !/^\s*[-*+]\s+/.test(lines[index]) &&
      !/^\s*\d+[.)]\s+/.test(lines[index]) &&
      !/^\s*>\s?/.test(lines[index]) &&
      !/^(#{1,3})\s+/.test(lines[index])
    ) {
      if (
        lines[index].includes("|") &&
        index + 1 < lines.length &&
        isMarkdownTableSeparator(lines[index + 1])
      ) {
        break;
      }
      paragraphLines.push(lines[index]);
      index += 1;
    }

    if (paragraphLines.length) {
      blocks.push(
        <p key={`p-${index}`} className="unbounded-weight300">
          {parseInlineMarkdown(paragraphLines.join("\n"), `p-${index}`)}
        </p>
      );
    }
  }

  return blocks;
}

function ReceivedMessage({text, onTypingComplete, analysis}) {
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
      if (character === " ") return 4 + Math.random() * 9;
      if (/[,.]/.test(character)) return 22 + Math.random() * 40;
      if (/[!?;]/.test(character)) return 38 + Math.random() * 55;
      return 7 + Math.random() * 17;
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
      timeoutRef.current = window.setTimeout(typeNextCharacter, 30 + Math.random() * 60);
    }

    return () => {
      window.clearTimeout(timeoutRef.current);
    };
  }, [text, onTypingComplete]);

  return (
    <div className="ReceivedMessage">
        <div>
          <MessageAnalysis analysis={analysis} align="left" />
          <div className="received-message-markdown unbounded-weight300">
            {renderMarkdown(visibleText)}
            {visibleText.length < (text || "").length && (
              <span className="received-message-cursor" aria-hidden="true"></span>
            )}
          </div>
          <div id="received-message-bubbletick"></div>
        </div>
    </div>
  );
};

export default ReceivedMessage;
