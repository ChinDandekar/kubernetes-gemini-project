import React from 'react';
import '../assets/ChatWindow.css';

const ChatWindow = ({ messages, loading }) => {
  return (
    <div className="chat-window">
      {messages.map((msg, index) => (
        <div key={index} className={`message ${msg.sender}`}>
          <p>{msg.text}</p>
        </div>
      ))}
      {loading && <div className="loading">AI is typing...</div>}
    </div>
  );
};

export default ChatWindow;
