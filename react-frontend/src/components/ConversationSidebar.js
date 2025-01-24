import React, { useState } from "react"
import "../assets/ConversationSidebar.css"
import { ChevronLeft, ChevronRight } from "lucide-react"

const ConversationSidebar = ({ conversations, onSelectConversation, onNewConversation, currentConversationId, onCollapse }) => {
  const [isCollapsed, setIsCollapsed] = useState(false)

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed)
    onCollapse()
  }

  return (
    <div className={`sidebar ${isCollapsed ? "collapsed" : ""}`}>
      <button onClick={toggleSidebar} className="collapse-btn">
        {isCollapsed ? <ChevronRight size={24} /> : <ChevronLeft size={24} />}
      </button>
      {!isCollapsed && (
        <>
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
                  className={`sidebar-item ${conversation.id === currentConversationId ? "active" : ""}`}
                  onClick={() => onSelectConversation(conversation.id)}
                >
                  {`Conversation ${conversations.indexOf(conversation) + 1}`}
                </p>
              ))
            ) : (
              <p>No conversations yet</p>
            )}
          </ul>
        </>
      )}
    </div>
  )
}

export default ConversationSidebar

