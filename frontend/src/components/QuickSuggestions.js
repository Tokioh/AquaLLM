import React, { useState, useRef, useEffect } from 'react';
import './QuickSuggestions.css';

const QuickSuggestions = ({ onQuickQuery, identifier, isLoading }) => {
  const [activeTab, setActiveTab] = useState('finanzas');
  const [isExpanded, setIsExpanded] = useState(false);
  const suggestionRef = useRef(null);

  // Efecto para cerrar el menú al hacer clic fuera
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (suggestionRef.current && !suggestionRef.current.contains(event.target)) {
        setIsExpanded(false);
      }
    };

    // Solo agregar el listener si el menú está expandido
    if (isExpanded) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    // Cleanup: remover el listener cuando el componente se desmonte o cambie isExpanded
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [isExpanded]);

  const suggestions = {
    finanzas: [
      { id: 'saldo_actual', text: '💰 ¿Cuál es mi saldo actual?', type: 'saldo_actual' },
      { id: 'proxima_factura', text: '📅 ¿Cuándo vence mi próxima factura?', type: 'proxima_factura' },
      { id: 'promedio_facturacion', text: '📊 ¿Cuál es mi promedio de facturación?', type: 'promedio_facturacion' },
      { id: 'facturas_vencidas', text: '⚠️ ¿Tengo facturas vencidas?', type: 'facturas_vencidas' }
    ],
    consumo: [
      { id: 'consumo_actual', text: '🚰 ¿Cuál es mi consumo actual?', type: 'consumo_actual' },
      { id: 'promedio_consumo', text: '📈 ¿Cuál es mi promedio de consumo?', type: 'promedio_consumo' },
      { id: 'comparar_mes_anterior', text: '⚖️ Comparar con el mes anterior', type: 'comparar_mes_anterior' },
      { id: 'consumo_normal', text: '❓ ¿Mi consumo es normal?', type: 'consumo_normal' }
    ],
    servicio: [
      { id: 'informacion_medidor', text: '🔧 Información de mi medidor', type: 'informacion_medidor' },
      { id: 'estado_solicitudes', text: '📋 Estado de mis solicitudes', type: 'estado_solicitudes' },
      { id: 'reportar_fuga', text: '💧 ¿Cómo reportar una fuga?', type: 'reportar_fuga' },
      { id: 'cambiar_medidor', text: '🔄 ¿Cómo cambiar mi medidor?', type: 'cambiar_medidor' }
    ],
    pagos: [
      { id: 'como_pagar', text: '💳 ¿Cómo puedo pagar mi factura?', type: 'como_pagar' },
      { id: 'donde_pagar', text: '📍 ¿Dónde puedo pagar?', type: 'donde_pagar' },
      { id: 'pago_online', text: '💻 ¿Puedo pagar en línea?', type: 'pago_online' },
      { id: 'descuentos', text: '🎁 ¿Hay descuentos disponibles?', type: 'descuentos' }
    ]
  };

  const tabs = [
    { id: 'finanzas', label: 'Finanzas', icon: '💰' },
    { id: 'consumo', label: 'Consumo', icon: '🚰' },
    { id: 'servicio', label: 'Servicio', icon: '🔧' },
    { id: 'pagos', label: 'Pagos', icon: '💳' }
  ];

  const handleSuggestionClick = (suggestion) => {
    if (!identifier) {
      alert('Por favor, introduce tu número de cliente o medidor primero.');
      return;
    }
    onQuickQuery(suggestion.type, suggestion.text);
  };

  return (
    <div ref={suggestionRef} className={`quick-suggestions ${isExpanded ? 'expanded' : 'collapsed'}`}>
      {/* Botón de toggle compacto */}
      <div className="suggestions-toggle" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="toggle-content">
          <span className="toggle-icon">💡</span>
          <span className="toggle-text">
            {isExpanded ? 'Ocultar Sugerencias' : 'Preguntas Frecuentes'}
          </span>
          <span className={`toggle-arrow ${isExpanded ? 'up' : 'down'}`}>
            {isExpanded ? '▲' : '▼'}
          </span>
        </div>
      </div>

      {/* Panel expandible */}
      <div className={`suggestions-panel ${isExpanded ? 'show' : 'hide'}`}>
        <div className="suggestions-header">
          <p>Haz clic en cualquier pregunta para obtener una respuesta rápida</p>
        </div>
        
        <div className="tabs-container">
          {tabs.map(tab => (
            <button
              key={tab.id}
              className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => setActiveTab(tab.id)}
              disabled={isLoading}
            >
              <span className="tab-icon">{tab.icon}</span>
              <span className="tab-label">{tab.label}</span>
            </button>
          ))}
        </div>

        <div className="suggestions-grid">
          {suggestions[activeTab].map(suggestion => (
            <button
              key={suggestion.id}
              className="suggestion-button"
              onClick={() => handleSuggestionClick(suggestion)}
              disabled={isLoading || !identifier}
            >
              {suggestion.text}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default QuickSuggestions;
