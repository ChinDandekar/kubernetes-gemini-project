import React, { useState, useCallback, useMemo, useEffect } from 'react';
import './App.css';
import ChatWindow from './components/ChatWindow';
import InputForm from './components/InputForm';
import ConversationSidebar from './components/ConversationSidebar';
import TokenProgressBar from './components/TokenProgressBar';
import axios from 'axios';
import { MathJaxContext } from "better-react-mathjax";

function App() {
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [models, setModels] = useState(
    {
      "google":
      {
        "gemini-1.5-flash": 
        {
            "rpd": 1500,
            "context_window": 500000
        }
      }
    }
  )
  const [currentModel, setCurrentModel] = useState(
          {
            "make": "google", 
            "model": "gemini-1.5-flash", 
            "rpd": 1500,
            "context_window": 500000,
            "description": "General purpose fast Google model"
          }
    )
  const [tokensUsed, setTokensUsed] = useState(0);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  
  const setInitialModel = (data) => {
    console.log("data:")
    console.log(data)
    const firstProvider = Object.keys(data)[0]; //Gets "google"
    const firstModel = Object.keys(data[firstProvider])[0]; //Gets "gemini-1.5-flash"
    const modelData = data[firstProvider][firstModel];

    setCurrentModel({
      make: firstProvider,
      model: firstModel,
      rpd: modelData.rpd,
      context_window: modelData.context_window,
      description: modelData.description,
    });
  };


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
        const transformedConversations = Object.entries(data[0]).map(([id, conversationData]) => {
          return {
            id: Number(id),
            messages: conversationData.messages,
            tokensUsed: conversationData.tokens_used
          };
        });
        setConversations(transformedConversations); // Directly sets the data if it's a single chat object. If it's an array of chat objects, use a mapping function to process the array appropriately.

        if (transformedConversations.length === 0) {
          // Create a new conversation
          console.log("creating a new conversation")
          const newConversation = {
            id: Date.now(),
            messages: [],
            tokensUsed: 0
          };
          setConversations(prevConversations => [...prevConversations, newConversation]);
          setCurrentConversationId(newConversation.id);
        }
        else {
          setCurrentConversationId(transformedConversations[0].id);
          setTokensUsed(transformedConversations[0].tokensUsed)
        }



      } catch (error) {
        console.error('Error fetching chats:', error);
        // Handle error appropriately, e.g., display an error message to the user.
      }

      
    };

    fetchChats();
  }, [BACKEND_URL]); // Empty dependency array ensures this runs only once on mount

  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await fetch(BACKEND_URL + '/get_all_models');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setModels(data); // Directly sets the data if it's a single chat object. If it's an array of chat objects, use a mapping function to process the array appropriately.
        console.log("models:")
        console.log(data)
        // Fetch context window size

        setInitialModel(data)
        
      } catch (error) {
        console.error('Error fetching models:', error);
        // Handle error appropriately, e.g., display an error message to the user.
      }
    };

    fetchModels();
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
            ? { ...conv, messages: [...conv.messages, aiMessage], tokensUsed: response.data.tokens_used }
            : conv
        )
      );

    setTokensUsed(response.data.tokens_used)
    console.log(response.data.tokens_used)
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
  }, [currentConversationId, BACKEND_URL]);

  const handleSelectConversation = useCallback((conversationId) => {
    setCurrentConversationId(conversationId);
    const selectedConversation = conversations.find((conv) => conv.id === conversationId)
    setTokensUsed(selectedConversation ? selectedConversation.tokensUsed : 0)
  }, [conversations]);

  const handleNewConversation = useCallback(() => {
    const newConversation = {
      id: Date.now(),
      messages: [],
      tokensUsed: 0
    };
    setConversations(prevConversations => [...prevConversations, newConversation]);
    setCurrentConversationId(newConversation.id);
    setTokensUsed(0)
  }, []);

  const config = {
    loader: { load: ["input/asciimath", "output/chtml", "ui/menu"] },
    asciimath: {
      delimiters: [["$", "$"], ["\\(", "\\)"]]
    }
  };

  return (
    <MathJaxContext config={config}>
      <div className="App">
      <div className={`layout`}>
          <ConversationSidebar
            conversations={conversations}
            onSelectConversation={handleSelectConversation}
            onNewConversation={handleNewConversation}
            currentConversationId={currentConversationId}
            onCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
          />
          <div className={`chat-container ${isSidebarCollapsed ? "collapsed": ""}`}>
            <h1>ChinGemini</h1>
            <ChatWindow messages={getCurrentConversation()?.messages || []} loading={loading} />
            <TokenProgressBar tokensUsed={tokensUsed} contextWindow={currentModel.context_window} />
            <InputForm onSendMessage={handleSendMessage} />
          </div>
        </div>
      </div>
    </MathJaxContext>
  );
}

export default App;

