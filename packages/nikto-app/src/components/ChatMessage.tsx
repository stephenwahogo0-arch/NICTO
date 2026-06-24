import React from "react";
import ReactMarkdown from "react-markdown";
import "./ChatMessage.css";

interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: number;
}

interface Props {
  message: Message;
}

function ChatMessage({ message }: Props) {
  const time = new Date(message.timestamp).toLocaleTimeString();
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  return (
    <div className={`message ${message.role}`}>
      <div className="msg-avatar">
        {isUser ? "U" : isSystem ? "S" : "N"}
      </div>
      <div className="msg-body">
        <div className="msg-header">
          <span className="msg-role">
            {isUser ? "You" : isSystem ? "System" : "NICTO"}
          </span>
          <span className="msg-time">{time}</span>
        </div>
        <div className="msg-content">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

export default ChatMessage;
