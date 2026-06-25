import React, { useState, useRef, useEffect, useCallback } from "react";
import ChatMessage from "./components/ChatMessage";
import StatusPanel from "./components/StatusPanel";
import BrainMonitor from "./components/BrainMonitor";
import "./App.css";

type View = "chat" | "brain" | "status";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: number;
}

const WELCOME: Message = {
  id: "0",
  role: "system",
  content:
    "NICTO v7.0.0 — 7-Brain MoE+MLA Architecture\n"
    + "19 specialized heads, 70 subnetworks, 1.33B total parameters.\n"
    + "Ready for creative cognition.",
  timestamp: Date.now(),
};

function App() {
  const [view, setView] = useState<View>("chat");
  const [messages, setMessages] = useState<Message[]>([WELCOME]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSend = async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: text,
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8765/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, history: messages.slice(-10) }),
      });
      const data = await response.json();
      const assistantMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: data.response || "No response from NICTO core.",
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      const fallback: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content:
          "_NICTO core offline. Running local fallback._\n\n"
          + "The full 7-brain MoE+MLA engine requires the Python backend "
          + "(run `python packages/nikto-app/server.py`).\n\n"
          + "In standalone mode, I can still help with creative concepts, "
          + "cinematography knowledge, and visual design ideas.",
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, fallback]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: "clear",
        role: "system",
        content: "NICTO v7.0.0 — Terminal cleared. Ready for new creative session.",
        timestamp: Date.now(),
      },
    ]);
  };

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="logo">
          <div className="logo-icon">N</div>
          <div className="logo-text">
            <span className="logo-title">NICTO</span>
            <span className="logo-sub">v7.0.0</span>
          </div>
        </div>
        <nav className="nav">
          <button
            className={`nav-btn ${view === "chat" ? "active" : ""}`}
            onClick={() => setView("chat")}
          >
            <span className="nav-icon">&#9998;</span>
            Chat
          </button>
          <button
            className={`nav-btn ${view === "brain" ? "active" : ""}`}
            onClick={() => setView("brain")}
          >
            <span className="nav-icon">&#9733;</span>
            Brain
          </button>
          <button
            className={`nav-btn ${view === "status" ? "active" : ""}`}
            onClick={() => setView("status")}
          >
            <span className="nav-icon">&#9881;</span>
            Status
          </button>
        </nav>
        <div className="sidebar-footer">
          <div className="brain-indicator">
            <div className="status-dot" />
            <span className="status-text">7-Brain MoE+MLA</span>
          </div>
          <div className="head-count">19H &middot; 70S</div>
        </div>
      </aside>

      <main className="main">
        {view === "chat" && (
          <div className="chat-view">
            <div className="chat-header">
              <h2>Creative Terminal</h2>
              <button className="clear-btn" onClick={clearChat}>
                Clear
              </button>
            </div>
            <div className="chat-messages">
              {messages.map((msg) => (
                <ChatMessage key={msg.id} message={msg} />
              ))}
              {loading && (
                <div className="loading-indicator">
                  <span className="loading-dot" />
                  <span className="loading-dot" />
                  <span className="loading-dot" />
                </div>
              )}
              <div ref={chatEndRef} />
            </div>
            <div className="chat-input-area">
              <textarea
                className="chat-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Enter a creative prompt..."
                rows={2}
              />
              <button
                className="send-btn"
                onClick={handleSend}
                disabled={loading || !input.trim()}
              >
                Send
              </button>
            </div>
          </div>
        )}

        {view === "brain" && <BrainMonitor />}
        {view === "status" && <StatusPanel />}
      </main>
    </div>
  );
}

export default App;
