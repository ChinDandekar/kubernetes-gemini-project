import React from 'react';
import '../assets/ConversationSidebar.css';

const ConversationSidebar = ({ conversations, onSelectConversation, onNewConversation, currentConversationId }) => {
  return (
    <div className="sidebar">
      {conversations.length > 0 && (
        <button onClick={onNewConversation} className="new-conversation-btn">
          New Conversation
        </button>
      )}
      <ul>
        {conversations.length > 0 ? (
          conversations.map((conversation) => (
            <p
              key={conversation.id}
              className={`sidebar-item ${conversation.id === currentConversationId ? 'active' : ''}`}
              onClick={() => onSelectConversation(conversation.id)}
            >
              {`Conversation ${conversations.indexOf(conversation) + 1}`}
            </p>
          ))
        ) : (
          <p>No conversations yet</p>
        )}
      </ul>
    </div>
  );
};

export default ConversationSidebar;

