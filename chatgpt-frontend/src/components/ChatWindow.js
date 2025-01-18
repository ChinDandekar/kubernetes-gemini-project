import React from 'react';
import '../assets/ChatWindow.css';
import 'highlight.js/styles/github.css'; // Or any other theme

const ChatWindow = ({ messages, loading }) => {
  return (
    <div className="chat-window">
      {messages.map((msg, index) => (
        <div key={index} className={`message ${msg.sender}`}>
          <p dangerouslySetInnerHTML={{ __html:msg.text_as_html}}/>
        </div>
      ))}
      {loading && <div className="loading">AI is typing...</div>}
    </div>
  );
};

export default ChatWindow;
