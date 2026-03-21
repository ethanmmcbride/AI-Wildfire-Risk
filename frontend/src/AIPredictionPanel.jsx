import React, { useState, useEffect } from 'react';

const AIPredictionPanel = ({ fireData }) => {
  const [predictions, setPredictions] = useState(null);
  const [aiError, setAiError] = useState(false);

  useEffect(() => {
    const fetchPredictions = async () => {
      try {
        // Example API call to your AI endpoint
        const response = await fetch('/api/predictions', {
            headers: { 'X-API-Key': 'dev-secret-key-123' } // Remember your new key!
        });
        
        if (!response.ok) throw new Error("AI subsystem degraded");
        
        const data = await response.json();
        setPredictions(data);
      } catch (error) {
        console.error("AI Prediction failure:", error);
        setAiError(true);
      }
    };

    if (fireData) fetchPredictions();
  }, [fireData]);

  if (aiError) {
    return (
      <div className="bg-yellow-900 border-l-4 border-yellow-500 text-yellow-100 p-4 rounded-md">
        <p className="font-bold">⚠️ Predictive Models Offline</p>
        <p className="text-sm">Real-time data is currently available, but AI risk forecasting is temporarily degraded.</p>
      </div>
    );
  }

  // Render normal AI prediction UI here
  return (
    <div>
      {/* Your standard AI visualizations */}
    </div>
  );
};

export default AIPredictionPanel;