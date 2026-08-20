import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, BatteryCharging, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import EVRouteMap from './components/EVRouteMap';
import './index.css';

// Random session ID so each tab refresh gets a new memory context in backend
const SESSION_ID = Math.random().toString(36).substring(7);

function App() {
  const [messages, setMessages] = useState([
    {
      role: 'ai',
      content: 'Merhaba! Ben **EV Asistanı**. Elektrikli araçların batarya/menzil/şarj özellikleri ve Türkiye genelindeki şarj istasyonları hakkında sana yardımcı olabilirim. Ne öğrenmek istersin?'
    }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      // Backend'e POST isteği atıyoruz
      const response = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: userMessage,
          session_id: SESSION_ID 
        }),
      });

      if (!response.ok) {
        throw new Error('API Hatası');
      }

      const data = await response.json();
      
      setMessages((prev) => [...prev, { role: 'ai', content: data.response }]);
    } catch (error) {
      console.error(error);
      setMessages((prev) => [
        ...prev, 
        { role: 'ai', content: 'Üzgünüm, sunucuya bağlanırken bir hata oluştu. Lütfen backendin çalıştığından emin ol.' }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <div className="logo-container">
          <BatteryCharging color="#10b981" size={24} strokeWidth={2.5} />
        </div>
        <div>
          <h1>EV Intelligence</h1>
          <p>Yapay Zeka Destekli Şarj ve Araç Rehberi</p>
        </div>
      </header>

      {/* Chat Area */}
      <div className="chat-container">
        {messages.map((msg, idx) => (
          <div key={idx} className={`message-wrapper ${msg.role}`}>
            {msg.role === 'ai' ? (
              <div className="ai-avatar-container">
                <div className="avatar" style={{ background: 'rgba(59, 130, 246, 0.2)' }}>
                  <Bot size={16} />
                </div>
                <span>EV Asistanı</span>
              </div>
            ) : (
              <div className="user-avatar-container">
                <span style={{ color: 'rgba(255, 255, 255, 0.7)', fontSize: '0.85rem' }}>Sen</span>
                <div className="avatar" style={{ background: 'rgba(255, 255, 255, 0.2)' }}>
                  <User size={16} />
                </div>
              </div>
            )}
            
            <div className={`message ${msg.role}`}>
              {msg.role === 'ai' ? (
                <ReactMarkdown
                  components={{
                    code({ node, inline, className, children, ...props }) {
                      const match = /language-(\w+)/.exec(className || '');
                      const lang = match ? match[1] : '';
                      
                      if (!inline && lang === 'json') {
                        try {
                          const data = JSON.parse(String(children).replace(/\n$/, ''));
                          if (data.type === 'ev_route_map') {
                            return <EVRouteMap data={data} />;
                          }
                        } catch (e) {
                          console.error("Failed to parse map json", e);
                        }
                      }
                      
                      return (
                        <code className={className} {...props}>
                          {children}
                        </code>
                      );
                    }
                  }}
                >
                  {msg.content}
                </ReactMarkdown>
              ) : (
                msg.content
              )}
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="message-wrapper ai">
            <div className="ai-avatar-container">
              <div className="avatar" style={{ background: 'rgba(59, 130, 246, 0.2)' }}>
                <Bot size={16} />
              </div>
              <span>EV Asistanı Düşünüyor...</span>
            </div>
            <div className="message ai typing-indicator">
              <div className="dot"></div>
              <div className="dot"></div>
              <div className="dot"></div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form className="input-area" onSubmit={handleSubmit}>
        <div className="input-wrapper">
          <input
            type="text"
            className="chat-input"
            placeholder="Bir araç adı veya şehir yazın..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={isLoading}
          />
        </div>
        <button type="submit" className="send-btn" disabled={!input.trim() || isLoading}>
          {isLoading ? <Loader2 className="animate-spin" size={20} /> : <Send size={20} />}
        </button>
      </form>
    </div>
  );
}

export default App;
