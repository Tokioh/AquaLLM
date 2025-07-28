import { useState, useEffect, useRef } from 'react';
import MessageBox from './MessageBox';
import './ChatWindow.css';

const ChatWindow = () => {
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState('');
  const [identifier, setIdentifier] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [processingStatus, setProcessingStatus] = useState('');
  const [conversationHistory, setConversationHistory] = useState([]);

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages]);

  const handleSendMessage = async () => {
    if (!userInput.trim() || !identifier.trim()) {
        alert("Por favor, introduce un identificador y una pregunta.");
        return;
    }

    const newUserMessage = { text: userInput, sender: 'user' };
    setMessages(prevMessages => [...prevMessages, newUserMessage]);
    const currentQuestion = userInput;
    setUserInput('');
    setIsLoading(true);
    setProcessingStatus('Iniciando...');

    try {
      // Usar el nuevo endpoint de streaming
      const response = await fetch('http://localhost:8000/api/chat-stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: currentQuestion,
          identifier: identifier,
          history: conversationHistory,
        }),
      });

      if (!response.ok) {
        throw new Error(`Error del servidor: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.status) {
                setProcessingStatus(`${data.status} (${data.step}/${data.total})`);
              }
              
              if (data.done && data.response) {
                // Respuesta final recibida
                const botResponse = { text: data.response, sender: 'bot' };
                setMessages(prevMessages => [...prevMessages, botResponse]);
                
                // Actualizar el historial de conversación
                const newHistoryItem = {
                  pregunta: currentQuestion,
                  respuesta: data.response
                };
                setConversationHistory(prev => [...prev, newHistoryItem]);
                
                setProcessingStatus('');
                setIsLoading(false);
                return;
              }
              
              if (data.error) {
                throw new Error(data.status || 'Error desconocido');
              }
            } catch (parseError) {
              console.error('Error parsing JSON:', parseError);
            }
          }
        }
      }

    } catch (error) {
      console.error("Error al llamar a la API:", error);
      const errorMessage = { text: "Lo siento, no pude conectarme con mis sistemas. Por favor, intenta de nuevo más tarde.", sender: 'bot' };
      setMessages(prevMessages => [...prevMessages, errorMessage]);
      setProcessingStatus('');
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !isLoading) {
      handleSendMessage();
    }
  };

  return (
    <div className="chat-window">
      <div className="messages-area">
        {messages.map((msg, index) => (
          <MessageBox key={index} message={msg.text} sender={msg.sender} />
        ))}
        {isLoading && (
          <div className="processing-status">
            <div className="status-indicator">
              <div className="loading-spinner"></div>
              <span>{processingStatus || 'Procesando...'}</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="input-area">
        <input
          type="text"
          className="input-field"
          placeholder="Nº Cliente / Medidor (ej. MED00001)"
          value={identifier}
          onChange={(e) => setIdentifier(e.target.value)}
          disabled={isLoading}
        />
        <input
          type="text"
          className="input-field"
          placeholder="Escribe tu pregunta aquí..."
          value={userInput}
          onChange={(e) => setUserInput(e.target.value)}
          disabled={isLoading}
          onKeyPress={handleKeyPress}
        />
        <button className="send-button" onClick={handleSendMessage} disabled={isLoading}>
          {isLoading ? 'Enviando...' : 'Enviar'}
        </button>
      </div>
    </div>
  );
};

export default ChatWindow;