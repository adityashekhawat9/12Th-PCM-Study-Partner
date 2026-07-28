import { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Bot } from 'lucide-react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSend = async (text) => {
    if (!text.trim()) return;

    const userMessage = { role: "user", content: text };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Send the entire message history to the backend
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [...messages, userMessage]
        })
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      setMessages(prev => [...prev, { role: "assistant", content: data.answer }]);
    } catch (error) {
      console.error('Error fetching chat:', error);
      setMessages(prev => [...prev, { 
        role: "assistant", 
        content: "Oops! My circuits got a little tangled. Please try asking again!" 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const suggestions = [
    "What is Coulomb's Law?",
    "Explain Coordination Compounds",
    "What is an indefinite integral?"
  ];

  return (
    <div className="app-container">
      <div className="glass-panel chat-window">
        
        {/* Header */}
        <div className="chat-header">
          <div className="avatar">
            <Bot size={30} color="white" />
          </div>
          <div className="header-text">
            <h1>AI Tutor</h1>
            <p>Your friendly NCERT study buddy!</p>
          </div>
        </div>

        {/* Chat History */}
        <div className="chat-history">
          {messages.length === 0 ? (
            <div className="suggestions">
              {suggestions.map((s, i) => (
                <div key={i} className="suggestion-chip" onClick={() => handleSend(s)}>
                  {s}
                </div>
              ))}
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div key={idx} className={`message-wrapper ${msg.role === 'user' ? 'user' : 'ai'}`}>
                <div className="message-bubble">
                  {msg.role === 'assistant' ? (
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  ) : (
                    msg.content
                  )}
                </div>
              </div>
            ))
          )}

          {isLoading && (
            <div className="typing-indicator">
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
              <div className="typing-dot"></div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="chat-input-area">
          <input 
            type="text" 
            placeholder="Ask a question about Physics, Chemistry, or Math..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSend(input);
            }}
            disabled={isLoading}
          />
          <button 
            className="send-button"
            onClick={() => handleSend(input)}
            disabled={!input.trim() || isLoading}
          >
            <Send size={20} />
          </button>
        </div>

      </div>
    </div>
  );
}

export default App;
