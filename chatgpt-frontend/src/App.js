import React, { useState } from 'react';
import './App.css'; // Updated with sidebar and other styles
import ChatWindow from './components/ChatWindow';
import InputForm from './components/InputForm';
import ConversationSidebar from './components/ConversationSidebar';
import { Remarkable } from 'remarkable';
import hljs from 'highlight.js';
import axios from 'axios';

function App() {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [conversations, setConversations] = useState([]); // Holds the history of conversations

  const md = new Remarkable({
    highlight: function (str, lang) {
      if (lang && hljs.getLanguage(lang)) {
        try {
          return hljs.highlight(str, { language: lang }).value;
        } catch (__) {}
      }
      return ''; // Use external default escaping
    },
  });

  // Function to handle the message submission
  const handleSendMessage = async (userMessage) => {
    const newMessages = [...messages, { length: userMessage.length, text_as_html: md.render(userMessage), sender: 'user' }];
    setMessages(newMessages);
    
    setLoading(true);

    try {
      const response = await axios.post(
        `http://127.0.0.1:8000/answer_query/`, // Replace chatId with the actual chat ID
        { 
          chatid: 1,
          query: userMessage 
        }, // The body of the POST request
        {
          headers: {
            'Content-Type': 'application/json', // Ensure the content type is JSON
          },
        }
      );
      const aiMessage = md.render(response.data.reply);
      newMessages.push({ length: aiMessage.length, text_as_html: aiMessage, sender: 'ai' });
      setMessages(newMessages);

      // Save the conversation to history
      setConversations([...conversations, { id: Date.now(), messages: newMessages }]);
    } catch (error) {
      console.error("Error fetching AI response", error);
      setMessages([
        ...newMessages,
        { text: "Sorry, there was an error.", sender: 'ai' },
      ]);
    }

    setLoading(false);
  };

  // Function to handle conversation selection from the sidebar
  const handleSelectConversation = (conversationId) => {
    const selectedConversation = conversations.find(
      (conv) => conv.id === conversationId
    );
    setMessages(selectedConversation.messages);
  };

  return (
    <div className="App">
      <div className="layout">
        {/* Sidebar */}
        <ConversationSidebar
          conversations={conversations}
          onSelectConversation={handleSelectConversation}
        />
        
        {/* Chat Window */}
        <div className="chat-container">
          <h1>ChinGemini</h1>
          <ChatWindow messages={messages} loading={loading} />
          <InputForm onSendMessage={handleSendMessage} />
        </div>
      </div>
    </div>
  );
}

export default App;
