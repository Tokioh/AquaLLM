import { useState, useEffect, useRef } from 'react';
import MessageBox from './MessageBox';
import './ChatWindow.css';

const ChatWindow = () => {
  const [messages, setMessages] = useState([]);
  const [userInput, setUserInput] = useState('');
  const [identifier, setIdentifier] = useState('');
  const [isLoading, setIsLoading] = useState(false);

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
    setUserInput('');
    setIsLoading(true);

    try {
      // Se corrige la URL para apuntar directamente al backend en localhost:8000
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: userInput,
          identifier: identifier,
        }),
      });

      if (!response.ok) {
        throw new Error(`Error del servidor: ${response.status}`);
      }

      const data = await response.json();
      const botResponse = { text: data.answer, sender: 'bot' };
      setMessages(prevMessages => [...prevMessages, botResponse]);

    } catch (error) {
      console.error("Error al llamar a la API:", error);
      const errorMessage = { text: "Lo siento, no pude conectarme con el sistemas. Por favor, intenta de nuevo más tarde.", sender: 'bot' };
      setMessages(prevMessages => [...prevMessages, errorMessage]);
    } finally {
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
        {isLoading && <MessageBox message="Escribiendo..." sender="bot" />}
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