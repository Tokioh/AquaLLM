import './MessageBox.css';

const MessageBox = ({ message, sender }) => {
  const messageClass = sender === 'user' ? 'user-message' : 'bot-message';

  return (
    <div className={`message-box-container ${messageClass}`}>
      <div className="message-box">
        <p>{message}</p>
      </div>
    </div>
  );
};

export default MessageBox;