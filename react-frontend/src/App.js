import React, { useState, useCallback, useMemo } from 'react';
import './App.css';
import ChatWindow from './components/ChatWindow';
import InputForm from './components/InputForm';
import ConversationSidebar from './components/ConversationSidebar';
import { Remarkable } from 'remarkable';
import hljs from 'highlight.js';
import axios from 'axios';

function App() {
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [loading, setLoading] = useState(false);

  const BACKEND_URL = useMemo(() => {
    return process.env.REACT_APP_BACKEND_URL
  }, []);
  

  if (conversations.length === 0 || currentConversationId === null) {
    // Create a new conversation
    const newConversation = {
      id: Date.now(),
      messages: [],
    };
    setConversations(prevConversations => [...prevConversations, newConversation]);
    setCurrentConversationId(newConversation.id);
  }

  const md = useMemo(() => {
    return new Remarkable({
      highlight: function (str, lang) {
        if (lang && hljs.getLanguage(lang)) {
          try {
            return hljs.highlight(str, { language: lang }).value;
          } catch (__) {}
        }
        return ''; // Use external default escaping
      },
    });
  }, []); // No dependencies, so it will only be created once

  const getCurrentConversation = useCallback(() => {
    return conversations.find(conv => conv.id === currentConversationId) || null;
  }, [conversations, currentConversationId]);

  const handleSendMessage = useCallback(async (userMessage) => {
    setLoading(true);

    const newMessage = { length: userMessage.length, text_as_html: md.render(userMessage), sender: 'user' };

    // Add message to current conversation
    setConversations(prevConversations => 
      prevConversations.map(conv => 
        conv.id === currentConversationId 
          ? { ...conv, messages: [...conv.messages, newMessage] }
          : conv
      )
    );

    try {
      const response = await axios.post(
        BACKEND_URL + `/answer_query/`,
        { 
          chatid: currentConversationId,
          query: userMessage 
        },
        {
            headers: {
              'Content-Type': 'application/json',
            },
        }
      );
      
      const aiMessage = { length: response.data.reply.length, text_as_html: md.render(response.data.reply), sender: 'ai' };
      
      setConversations(prevConversations => 
        prevConversations.map(conv => 
          conv.id === currentConversationId 
            ? { ...conv, messages: [...conv.messages, aiMessage] }
            : conv
        )
      );
    } catch (error) {
      console.error("Error fetching AI response", error);
      const errorMessage = { length: 0, text_as_html: "Sorry, there was an error.", sender: 'ai' };
      setConversations(prevConversations => 
        prevConversations.map(conv => 
          conv.id === currentConversationId 
            ? { ...conv, messages: [...conv.messages, errorMessage] }
            : conv
        )
      );
    }

    setLoading(false);
  }, [currentConversationId, md, BACKEND_URL  ]);

  const handleSelectConversation = useCallback((conversationId) => {
    setCurrentConversationId(conversationId);
  }, []);

  const handleNewConversation = useCallback(() => {
    const newConversation = {
      id: Date.now(),
      messages: [],
    };
    setConversations(prevConversations => [...prevConversations, newConversation]);
    setCurrentConversationId(newConversation.id);
  }, []);

  return (
    <div className="App">
      <div className="layout">
        <ConversationSidebar
          conversations={conversations}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
          currentConversationId={currentConversationId}
        />
        <div className="chat-container">
          <h1>ChinGemini</h1>
          <ChatWindow messages={getCurrentConversation()?.messages || []} loading={loading} />
          <InputForm onSendMessage={handleSendMessage} />
        </div>
      </div>
    </div>
  );
}

export default App;

