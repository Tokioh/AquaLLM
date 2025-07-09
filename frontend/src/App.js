import './App.css';
import ChatWindow from './components/ChatWindow';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>AquaLLM - Asistente Virtual</h1>
      </header>
      <main>
        <ChatWindow />
      </main>
    </div>
  );
}

export default App;