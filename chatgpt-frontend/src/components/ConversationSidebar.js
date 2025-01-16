import React from 'react';
import '../assets/ConversationSidebar.css';

const ConversationSidebar = ({ conversations, onSelectConversation }) => {
  return (
    <div className="sidebar">
      <h3>Conversations</h3>
      <ul>
        {conversations.length > 0 ? (
          conversations.map((conversation) => (
            <li
              key={conversation.id}
              className="sidebar-item"
              onClick={() => onSelectConversation(conversation.id)}
            >
              {`Conversation ${conversations.indexOf(conversation) + 1}`}
            </li>
          ))
        ) : (
          <li>No conversations yet</li>
        )}
      </ul>
    </div>
  );
};

export default ConversationSidebar;
