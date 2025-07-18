import React, { useState, useEffect } from "react";
import "./App.css";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const WS_URL = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://');

function App() {
  const [alerts, setAlerts] = useState([]);
  const [zones, setZones] = useState([]);
  const [alertTypes, setAlertTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [selectedZone, setSelectedZone] = useState("");
  const [selectedType, setSelectedType] = useState("");
  const [ws, setWs] = useState(null);
  const [isConnected, setIsConnected] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    alert_type: "",
    zone: "",
    reporter_name: ""
  });

  // Load initial data
  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const [zonesRes, typesRes, alertsRes] = await Promise.all([
          fetch(`${API}/zones`),
          fetch(`${API}/alert-types`),
          fetch(`${API}/alerts`)
        ]);

        const zonesData = await zonesRes.json();
        const typesData = await typesRes.json();
        const alertsData = await alertsRes.json();

        setZones(zonesData.zones);
        setAlertTypes(typesData.alert_types);
        setAlerts(alertsData);
        setLoading(false);
      } catch (error) {
        console.error("Erreur lors du chargement des données:", error);
        setLoading(false);
      }
    };

    loadInitialData();
  }, []);

  // WebSocket connection
  useEffect(() => {
    const connectWebSocket = () => {
      const websocket = new WebSocket(`${WS_URL}/ws`);
      
      websocket.onopen = () => {
        console.log("Connexion WebSocket établie");
        setIsConnected(true);
      };

      websocket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === "new_alert") {
            setAlerts(prev => [data.alert, ...prev]);
            // Show browser notification
            if (Notification.permission === "granted") {
              new Notification(`🚨 Nouvelle alerte: ${data.alert.title}`, {
                body: `${data.alert.zone} - ${data.alert.description}`,
                icon: "/favicon.ico"
              });
            }
          } else if (data.type === "alert_update") {
            setAlerts(prev => prev.map(alert => 
              alert.id === data.alert.id ? data.alert : alert
            ));
          }
        } catch (error) {
          console.log("Message WebSocket:", event.data);
        }
      };

      websocket.onclose = () => {
        console.log("Connexion WebSocket fermée");
        setIsConnected(false);
        // Reconnect after 3 seconds
        setTimeout(connectWebSocket, 3000);
      };

      websocket.onerror = (error) => {
        console.error("Erreur WebSocket:", error);
        setIsConnected(false);
      };

      setWs(websocket);
    };

    connectWebSocket();

    // Request notification permission
    if (Notification.permission !== "granted") {
      Notification.requestPermission();
    }

    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await fetch(`${API}/alerts`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        setFormData({
          title: "",
          description: "",
          alert_type: "",
          zone: "",
          reporter_name: ""
        });
        setShowCreateForm(false);
      }
    } catch (error) {
      console.error("Erreur lors de la création de l'alerte:", error);
    }
  };

  // Filter alerts
  const filteredAlerts = alerts.filter(alert => {
    return (
      (selectedZone === "" || alert.zone === selectedZone) &&
      (selectedType === "" || alert.alert_type === selectedType)
    );
  });

  // Get alert type info
  const getAlertTypeInfo = (typeId) => {
    return alertTypes.find(type => type.id === typeId) || { label: typeId, icon: "📢" };
  };

  // Format date
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Chargement des alertes...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">🚨 Alertes CI</h1>
              <span className="ml-4 text-sm text-gray-600">
                Côte d'Ivoire - Alertes Communautaires
              </span>
              <div className="ml-4 flex items-center">
                <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="ml-2 text-sm text-gray-600">
                  {isConnected ? 'Connecté' : 'Déconnecté'}
                </span>
              </div>
            </div>
            <button
              onClick={() => setShowCreateForm(!showCreateForm)}
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition duration-200"
            >
              📢 Créer une alerte
            </button>
          </div>
        </div>
      </div>

      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 items-center">
            <div>
              <h2 className="text-4xl font-bold mb-4">
                Ensemble pour une Côte d'Ivoire plus sûre
              </h2>
              <p className="text-xl text-blue-100 mb-6">
                Partagez et recevez des alertes en temps réel sur les vols, accidents et catastrophes naturelles dans votre zone.
              </p>
              <div className="flex flex-wrap gap-4 text-sm">
                <div className="bg-blue-700 px-3 py-1 rounded-full">🚨 {alerts.filter(a => a.alert_type === 'vol').length} Vols signalés</div>
                <div className="bg-blue-700 px-3 py-1 rounded-full">🚑 {alerts.filter(a => a.alert_type === 'accident').length} Accidents</div>
                <div className="bg-blue-700 px-3 py-1 rounded-full">⚠️ {alerts.filter(a => a.alert_type === 'catastrophe').length} Catastrophes</div>
              </div>
            </div>
            <div className="hidden lg:block">
              <img 
                src="https://images.unsplash.com/photo-1610873221478-4e2bd7218bca?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NDQ2MzR8MHwxfHNlYXJjaHwzfHxlbWVyZ2VuY3klMjBhbGVydHxlbnwwfHx8Ymx1ZXwxNzUyODAxNzU1fDA&ixlib=rb-4.1.0&q=85"
                alt="Alertes d'urgence"
                className="rounded-lg shadow-xl"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Create Alert Form */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Créer une nouvelle alerte</h3>
              <button
                onClick={() => setShowCreateForm(false)}
                className="text-gray-500 hover:text-gray-700"
              >
                ✕
              </button>
            </div>
            
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Titre de l'alerte
                </label>
                <input
                  type="text"
                  required
                  value={formData.title}
                  onChange={(e) => setFormData({...formData, title: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Ex: Vol de téléphone au marché"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Type d'alerte
                </label>
                <select
                  required
                  value={formData.alert_type}
                  onChange={(e) => setFormData({...formData, alert_type: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Sélectionnez un type</option>
                  {alertTypes.map(type => (
                    <option key={type.id} value={type.id}>
                      {type.icon} {type.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Zone
                </label>
                <select
                  required
                  value={formData.zone}
                  onChange={(e) => setFormData({...formData, zone: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Sélectionnez une zone</option>
                  {zones.map(zone => (
                    <option key={zone} value={zone}>{zone}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  required
                  value={formData.description}
                  onChange={(e) => setFormData({...formData, description: e.target.value})}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Décrivez l'incident en détail..."
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Votre nom (optionnel)
                </label>
                <input
                  type="text"
                  value={formData.reporter_name}
                  onChange={(e) => setFormData({...formData, reporter_name: e.target.value})}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Anonyme"
                />
              </div>

              <div className="flex space-x-3">
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="flex-1 px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 transition duration-200"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition duration-200"
                >
                  Publier l'alerte
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Zone:</label>
              <select
                value={selectedZone}
                onChange={(e) => setSelectedZone(e.target.value)}
                className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Toutes les zones</option>
                {zones.map(zone => (
                  <option key={zone} value={zone}>{zone}</option>
                ))}
              </select>
            </div>
            
            <div className="flex items-center space-x-2">
              <label className="text-sm font-medium text-gray-700">Type:</label>
              <select
                value={selectedType}
                onChange={(e) => setSelectedType(e.target.value)}
                className="px-3 py-1 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">Tous les types</option>
                {alertTypes.map(type => (
                  <option key={type.id} value={type.id}>
                    {type.icon} {type.label}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="text-sm text-gray-600">
              {filteredAlerts.length} alerte{filteredAlerts.length !== 1 ? 's' : ''} trouvée{filteredAlerts.length !== 1 ? 's' : ''}
            </div>
          </div>
        </div>

        {/* Alerts List */}
        <div className="space-y-4">
          {filteredAlerts.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-gray-400 text-4xl mb-4">🔍</div>
              <p className="text-gray-600">Aucune alerte trouvée pour les critères sélectionnés.</p>
            </div>
          ) : (
            filteredAlerts.map(alert => {
              const typeInfo = getAlertTypeInfo(alert.alert_type);
              return (
                <div key={alert.id} className="bg-white rounded-lg shadow-sm border-l-4 border-blue-600 p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <span className="text-2xl">{typeInfo.icon}</span>
                        <h3 className="text-lg font-semibold text-gray-900">{alert.title}</h3>
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full font-medium">
                          {typeInfo.label}
                        </span>
                      </div>
                      
                      <p className="text-gray-700 mb-3">{alert.description}</p>
                      
                      <div className="flex flex-wrap gap-4 text-sm text-gray-600">
                        <div className="flex items-center space-x-1">
                          <span>📍</span>
                          <span>{alert.zone}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <span>⏰</span>
                          <span>{formatDate(alert.timestamp)}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <span>👤</span>
                          <span>{alert.reporter_name || 'Anonyme'}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        alert.status === 'active' 
                          ? 'bg-red-100 text-red-800' 
                          : 'bg-green-100 text-green-800'
                      }`}>
                        {alert.status === 'active' ? 'Actif' : 'Résolu'}
                      </span>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}

export default App;