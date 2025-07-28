import React, { useState } from 'react';
import './QuickSuggestions.css';

const QuickSuggestions = ({ onQuickQuery, identifier, isLoading }) => {
  const [activeTab, setActiveTab] = useState('finanzas');

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
    { id: 'finanzas', label: '💰 Finanzas', icon: '💰' },
    { id: 'consumo', label: '🚰 Consumo', icon: '🚰' },
    { id: 'servicio', label: '🔧 Servicio', icon: '🔧' },
    { id: 'pagos', label: '💳 Pagos', icon: '💳' }
  ];

  const handleSuggestionClick = (suggestion) => {
    if (!identifier) {
      alert('Por favor, introduce tu número de cliente o medidor primero.');
      return;
    }
    onQuickQuery(suggestion.type, suggestion.text);
  };

  return (
    <div className="quick-suggestions">
      <div className="suggestions-header">
        <h3>💡 Preguntas Frecuentes</h3>
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
  );
};

export default QuickSuggestions;
