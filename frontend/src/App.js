import './App.css';
import ChatWindow from './components/ChatWindow';
// Importa tu imagen aquí
import logo from './assets/logo.png'; // Ajusta el nombre según tu archivo

function App() {
  const handleHelp = () => {
    alert('💧 ¿Necesitas ayuda?\n\n1. Ingresa tu número de medidor (ej: MED00001)\n2. Haz tu pregunta sobre servicios de agua\n3. Usa los botones de sugerencias para consultas rápidas');
  };

  const handleContact = () => {
    alert('📞 Contacta con nosotros:\n\n• Teléfono: 1-800-AGUA-123\n• Email: soporte@aquallm.com\n• Horario: Lun-Vie 8:00-18:00');
  };

  const handleImageError = (e) => {
    // Si la imagen no carga, mostrar emoji como fallback
    e.target.style.display = 'none';
    e.target.nextSibling.style.display = 'block';
  };

  return (
    <div className="App">
      <header className="App-header">
        <div className="nav-left">
          <img 
            src={logo} 
            alt="AquaLLM Logo" 
            className="nav-logo-img"
            onError={handleImageError}
          />
          <div className="nav-logo" style={{display: 'none'}}>💧</div>
          <h1 className="nav-title">AquaLLM - Asistente Virtual</h1>
        </div>
        
        <div className="nav-right">
          <div className="status-indicator">
            <div className="status-dot"></div>
            <span>En línea</span>
          </div>
          
          <button className="nav-button" onClick={handleHelp}>
            ❓ Ayuda
          </button>
          
          <button className="nav-button" onClick={handleContact}>
            📞 Contacto
          </button>
        </div>
      </header>
      
      <main>
        <ChatWindow />
      </main>
    </div>
  );
}

export default App;