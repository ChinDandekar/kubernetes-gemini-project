import { useEffect, useRef } from "react";
import React from 'react';
import '../assets/ChatWindow.css';
import 'highlight.js/styles/github.css'; // Or any other theme

const ChatWindow = ({ messages, loading }) => {
  const chatWindowRef = useRef(null);

  useEffect(() => {
    // Scroll to the bottom whenever messages change
    if (chatWindowRef.current) {
      chatWindowRef.current.scrollTop = chatWindowRef.current.scrollHeight;
    }
  }, [messages]);

  return (
    <div ref={chatWindowRef} className="chat-window">
      {messages.filter((msg) => msg.length > 0).map((msg, index) => (
        <div key={index} className={`message ${msg.sender}`}>
          <p dangerouslySetInnerHTML={{ __html: msg.text_as_html }} />
        </div>
      ))}
      {loading && <div className="loading">AI is typing...</div>}
    </div>
  );
};

export default ChatWindow;
