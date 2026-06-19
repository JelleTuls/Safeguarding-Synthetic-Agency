// Persona chat popup.
//
// Manages the conversation transcript, streams backend responses, and sends the
// selected pipeline mode so each chat can run as guardrailed or lightweight.

import { useState, useEffect, useRef } from "react";

import './personaChat.css';
import closeCross from '../../assets/images/closeCross.png'
import sendArrow from '../../assets/images/sendArrow.png'

import { LiveLogPanel } from "../../features/logs";
import ReceivedMessage from "./receivedMessage";
import UserMessage from "./userMessage";
import AwaitingMessage from "./awaitingMessage";

function PersonaChat({
  personaProfile,
  personaDetails,
  personaCountry,
  pipelineMode,
  showChat,
  logPanelOpen = false,
  onToggleLogPanel,
}) {

  // below code is for sending and retrieving messages

  const [error, setError] = useState(null);
  const [waitingForResponse, setWaitingForResponse] = useState(false);
  const waitingForResponseRef = useRef(false);
  const chatSessionId = useRef(
    `chat-${Date.now()}-${Math.random().toString(36).slice(2)}`
  );

  const { index, ...personaWithoutIndex } = personaDetails;
  const baselineStylometry = {
    register: "everyday",
    sentence_style: "mixed",
    vocabulary_level: "moderate",
    abstraction_level: "mixed",
    hedging_style: "medium",
    confidence_style: "balanced",
    warmth_style: "warm",
    reasoning_style: "blended",
    explanation_style: "balanced",
    profile_summary: "Starting from a neutral everyday profile until the cached or live stylometric profile is available.",
  };
  const stylometricProfile = {
    ...baselineStylometry,
    ...(personaProfile?.stylometric_profile || {}),
  };
  function formatLabel(value) {
    if (value === null || value === undefined || value === "") return "Unknown";
    return String(value).replaceAll("_", " ");
  }

  function isMeaningfulMetadata(key, value) {
    if (value === null || value === undefined || value === "") return false;
    if (key === "index") return false;
    const normalizedValue = String(value).trim();
    if (/^GM\d+$/i.test(normalizedValue)) return false;
    if (/^\d+$/.test(normalizedValue)) return false;
    return true;
  }

  function cleanBiographyText(text) {
    if (!text) return "";
    return text
      .split("\n")
      .map(line => line.replace(/^\s*(part\s*[12]|neutral biography|political biography)\s*:\s*/i, ""))
      .filter(line => !/^\s*(part\s*[12]|part one|part two|neutral biography|political biography)\s*:?\s*$/i.test(line))
      .join("\n")
      .trim();
  }

  const styleFields = [
    ["Register", stylometricProfile.register],
    ["Sentence style", stylometricProfile.sentence_style],
    ["Vocabulary", stylometricProfile.vocabulary_level],
    ["Abstraction", stylometricProfile.abstraction_level],
    ["Hedging", stylometricProfile.hedging_style],
    ["Confidence", stylometricProfile.confidence_style],
    ["Warmth", stylometricProfile.warmth_style],
    ["Reasoning", stylometricProfile.reasoning_style],
    ["Explanation", stylometricProfile.explanation_style],
  ];

  function buildChatHistory(messageList) {
    return messageList
      .filter((message) => message.type === "user" || message.type === "persona")
      .map((message) => ({
        role: message.type === "user" ? "user" : "assistant",
        content: message.text,
      }));
  }

  // function to post message and receive message from backend
  async function sendAndReceiveMessage(persona, country, message, chatHistory) {
    const wait = (durationMs) => new Promise(resolve => setTimeout(resolve, durationMs));
    const removeAwaitingBubble = () => {
      setMessages(prev => prev.filter(message => message.id !== 'awaitingTemporary'));
    };
    const showStatusBubble = (text) => {
      setMessages(prev => {
        const withoutAwaiting = prev.filter(message => message.id !== 'awaitingTemporary');
        return [...withoutAwaiting, {id: 'awaitingTemporary', type: 'awaiting', text}];
      });
    };
    const attachAnalysisToLatestMessage = (messageType, analysis) => {
      if (!analysis) return;
      setMessages(prev => {
        const updated = [...prev];
        for (let index = updated.length - 1; index >= 0; index -= 1) {
          if (updated[index].type === messageType) {
            updated[index] = { ...updated[index], analysis };
            break;
          }
        }
        return updated;
      });
    };
    const addPersonaBubble = async (text, analysis = null) => {
      const nextId = numMessages.current;
      numMessages.current += 1;
      let resolveTypingComplete;
      const typingComplete = new Promise(resolve => {
        resolveTypingComplete = resolve;
      });
      const fallbackTimeout = window.setTimeout(resolveTypingComplete, 8000);
      setMessages(prev => {
        const withoutAwaiting = prev.filter(message => message.id !== 'awaitingTemporary');
        return [
          ...withoutAwaiting,
          {
            id: nextId,
            type: "persona",
            text,
            analysis,
            onTypingComplete: () => {
              window.clearTimeout(fallbackTimeout);
              resolveTypingComplete();
            }
          }
        ];
      });
      await typingComplete;
    };
    const appendToLastPersonaBubble = (text, analysis = null) => {
      setMessages(prev => {
        const withoutAwaiting = prev.filter(message => message.id !== 'awaitingTemporary');
        const updated = [...withoutAwaiting];
        const last = updated[updated.length - 1];
        if (!last || last.type !== "persona") {
          const nextId = numMessages.current;
          numMessages.current += 1;
          return [...updated, {id: nextId, type: "persona", text, analysis}];
        }
        updated[updated.length - 1] = {
          ...last,
          text: (last.text || "") + text,
          analysis: analysis || last.analysis,
        };
        return updated;
      });
    };

    try {
      const response = await fetch(`${process.env.REACT_APP_API_URL}/api/chat/chat_message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: message,
          persona_details: persona,
          persona_country: country,
          chat_history: chatHistory,
          client_session_id: chatSessionId.current,
          pipeline_mode: pipelineMode,
        })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      let currentEvent = "message"
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const blocks = buffer.split("\n\n");
        buffer = blocks.pop() || "";

        for (const block of blocks) {
          const lines = block.split("\n");

          for (const line of lines) {
            if (line.startsWith("event: ")) {
              currentEvent = line.slice(7).trim();
            } else if (line.startsWith("data: ")) {
              const payload = line.slice(6);
              if (payload === "[DONE]") break;


              const parsed = JSON.parse(payload);
              const { text } = parsed;

              if (currentEvent === "error") {
                setError(text);
                removeAwaitingBubble();
                await addPersonaBubble(text);
              } else if (currentEvent === "status") {
                showStatusBubble(text);
                await wait(parsed.duration_ms || 900);
              } else if (currentEvent === "agent_state") {
                // The left profile panel intentionally stays on baseline stylometry.
              } else if (currentEvent === "user_message_analysis") {
                attachAnalysisToLatestMessage("user", parsed.analysis);
              } else if (currentEvent === "message_part") {
                await addPersonaBubble(text, parsed.analysis);
              } else {
                appendToLastPersonaBubble(text, parsed.analysis);
              }

            currentEvent = "message";
            }
          }
        }
      }

      setError(null);
    } catch (err) {
      setError(err.message);
      setMessages(prev => prev.filter(message => message.id !== 'awaitingTemporary'));
    } finally {
      waitingForResponseRef.current = false;
      setWaitingForResponse(false);
    }
  };

  function sendMessage(message){
    if (waitingForResponseRef.current) return;
    waitingForResponseRef.current = true;
    const chatHistory = buildChatHistory(messages);
    setWaitingForResponse(true);
    addMessage("user", message);
    addMessage("awaiting")
    sendAndReceiveMessage(personaDetails, personaCountry, message, chatHistory)
  }


  // below code is for managing and inserting messages in chat

  const [messages, setMessages] = useState([]);
  const numMessages = useRef(0);

  const messageTypes = {
    "user": UserMessage,
    "persona": ReceivedMessage,
    "awaiting": AwaitingMessage
  }

  function addMessage(messageType, text=null){

    if(messageType === "awaiting"){
      setMessages(prev => [...prev, {id: 'awaitingTemporary', type: messageType, text: text}])
      return
    }

    setMessages(prev => [...prev, {id: numMessages.current, type: messageType, text: text}])
    numMessages.current += 1;
  }

  // below code is for handling sent messages

  const [inputValue, setInputValue] = useState("");

  function handleSubmit() {
    if (!inputValue.trim()) return; // ignores empty messages
    if (waitingForResponse || waitingForResponseRef.current) return;

    sendMessage(inputValue);

    setInputValue("");
  }

  const chatBottomRef = useRef(null);

  useEffect(() => {
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, []);

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="PersonaChat">
      <div className={`PersonaChatStage ${logPanelOpen ? 'isLogOpen' : ''}`}>
        <div id="chat-bubble">
            <aside id="persona-profile-card">
                <div id="profile-card-header">
                  <p id="chat-with-text" className="unbounded-weight300">SSA PROFILE</p>
                  <div id="persona-name" className="unbounded-weight400">
                      Agent {index + 1}
                  </div>
                </div>

                <div id="persona-chat-attributes">
                    {Object.entries(personaWithoutIndex).filter(([key, value]) => isMeaningfulMetadata(key, value)).map(([key, value]) => (
                        <p key={key} className="persona-chat-attributes-single unbounded-weight300">#{formatLabel(value)}</p>
                    ))}
                </div>

                <section className="profile-section">
                  <h3 className="unbounded-weight400">Profile Generated</h3>
                  <p className="profile-biography unbounded-weight300">{cleanBiographyText(personaProfile?.biography)}</p>
                </section>

                <section className="profile-section">
                  <h3 className="unbounded-weight400">Stylometric State</h3>
                  <p className="profile-summary unbounded-weight300">
                    {stylometricProfile.profile_summary}
                  </p>
                  <div className="style-pill-grid">
                    {styleFields.map(([label, value]) => (
                      <div className="style-pill" key={label}>
                        <span>{label}</span>
                        <strong>{formatLabel(value)}</strong>
                      </div>
                    ))}
                  </div>
                </section>
            </aside>

            <section id="persona-chat-panel">
              <div id="persona-chat-panel-header">
                <div className={`chat-pipeline-badge ${pipelineMode === 'lightweight' ? 'is-lightweight' : ''}`}>
                  {pipelineMode === 'lightweight' ? 'Unrestricted' : 'Guardrailed'}
                </div>
                <div id="chat-close" onClick={() => showChat(false)}>
                  <img id="chat-close-cross" src={closeCross} alt="Close chat"></img>
                </div>
              </div>

              <div id="persona-chat-history">
                {messages.map((message) => {
                  const Component = messageTypes[message.type];
                  return (
                    <Component
                      key={message.id}
                      text={message.text}
                      analysis={message.analysis}
                      onTypingComplete={message.onTypingComplete}
                    />
                  );
                })}
                <div ref={chatBottomRef} />
              </div>

              {error && <p className="persona-chat-error unbounded-weight300">{error}</p>}

              <div id="persona-chat-input">
                  <input
                    className="unbounded-weight300"
                    type="text"
                    alt="Input for persona chat interface"
                    placeholder="Message this agent..."
                    value={inputValue}
                    onChange={(e) => setInputValue(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter") handleSubmit();
                    }}
                  ></input>
                  <div><img onClick={handleSubmit} src={sendArrow} alt="Arrow to send text"></img></div>
              </div>
            </section>

        </div>
        <LiveLogPanel
          isOpen={logPanelOpen}
          onToggle={onToggleLogPanel}
        />
      </div>
    </div>
  );
};

export default PersonaChat;
