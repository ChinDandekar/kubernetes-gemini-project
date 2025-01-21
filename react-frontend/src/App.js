import React, { useState, useCallback, useMemo, useEffect } from 'react';
import './App.css';
import ChatWindow from './components/ChatWindow';
import InputForm from './components/InputForm';
import ConversationSidebar from './components/ConversationSidebar';
import axios from 'axios';

function App() {
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [loading, setLoading] = useState(false);

  const BACKEND_URL = useMemo(() => {
    return process.env.REACT_APP_BACKEND_URL
  }, []);
  
  useEffect(() => {
    const fetchChats = async () => {
      try {
        const response = await fetch(BACKEND_URL + '/load_all_chats');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log("response:")
        console.log(data)
        const transformedConversations = Object.entries(data[0]).map(([id, messages]) => {
          return {
            id: Number(id),
            messages: messages
          };
        });
        setConversations(transformedConversations); // Directly sets the data if it's a single chat object. If it's an array of chat objects, use a mapping function to process the array appropriately.

        if (transformedConversations.length === 0) {
          // Create a new conversation
          console.log("creating a new conversation")
          const newConversation = {
            id: Date.now(),
            messages: [],
          };
          setConversations(prevConversations => [...prevConversations, newConversation]);
          setCurrentConversationId(newConversation.id);
        }
        else {
          setCurrentConversationId(transformedConversations[0].id);
        }
      } catch (error) {
        console.error('Error fetching chats:', error);
        // Handle error appropriately, e.g., display an error message to the user.
      }
    };

    fetchChats();
  }, [BACKEND_URL]); // Empty dependency array ensures this runs only once on mount



  const getCurrentConversation = useCallback(() => {
    return conversations.find(conv => conv.id === currentConversationId) || null;
  }, [conversations, currentConversationId]);

  const handleSendMessage = useCallback(async (userMessage) => {
    setLoading(true);

    const newMessage = { length: userMessage.length, text: userMessage, sender: 'user' };

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
        BACKEND_URL + `/answer_query`,
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
      
      const aiMessage = { length: response.data.reply.length, text: response.data.reply, sender: 'ai' };
      
      setConversations(prevConversations => 
        prevConversations.map(conv => 
          conv.id === currentConversationId 
            ? { ...conv, messages: [...conv.messages, aiMessage] }
            : conv
        )
      );
    } catch (error) {
      console.error("Error fetching AI response", error);
      const errorMessage = { length: 0, text: "Sorry, there was an error.", sender: 'ai' };
      setConversations(prevConversations => 
        prevConversations.map(conv => 
          conv.id === currentConversationId 
            ? { ...conv, messages: [...conv.messages, errorMessage] }
            : conv
        )
      );
    }

    setLoading(false);
  }, [currentConversationId, BACKEND_URL  ]);

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

