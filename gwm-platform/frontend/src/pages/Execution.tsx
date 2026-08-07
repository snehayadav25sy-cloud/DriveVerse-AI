import { useState } from 'react';
import { useExecution } from '../services/execution';

export default function Execution() {
  const [sessionId, setSessionId] = useState('');
  const [worldPlanId, setWorldPlanId] = useState('');
  const { startExecution, starting, stopExecution, stopping, sessionData } = useExecution();

  const handleStart = () => {
    startExecution({
      world_plan_id: worldPlanId,
      seeds: {
        master_seed: 42,
        traffic_seed: 43,
        spawn_seed: 44,
        event_seed: 45,
        weather_seed: 46,
        sensor_seed: 47,
      },
    });
    if (sessionData?.session_id) {
      setSessionId(sessionData.session_id);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">Execution</h1>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Simulation Control</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">World Plan ID</label>
            <input
              type="text"
              value={worldPlanId}
              onChange={(e) => setWorldPlanId(e.target.value)}
              className="w-full border rounded px-3 py-2"
              placeholder="world_plan_id"
            />
          </div>
        </div>
        <div className="mt-4 flex gap-4">
          <button
            onClick={handleStart}
            disabled={starting || !worldPlanId}
            className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700 disabled:bg-gray-400"
          >
            {starting ? 'Starting...' : 'Start'}
          </button>
          <button
            onClick={() => sessionId && stopExecution(sessionId)}
            disabled={stopping || !sessionId}
            className="bg-red-600 text-white px-6 py-2 rounded hover:bg-red-700 disabled:bg-gray-400"
          >
            {stopping ? 'Stopping...' : 'Stop'}
          </button>
        </div>
      </div>

      {sessionData && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Session</h2>
          <div className="grid grid-cols-2 gap-4">
            <Stat label="Session ID" value={sessionData.session_id} />
            <Stat label="Status" value={sessionData.status} />
            <Stat label="Frame" value={sessionData.current_frame} />
            <Stat label="Time" value={`${sessionData.current_simulation_time_s.toFixed(1)}s`} />
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: any }) {
  return (
    <div className="bg-gray-50 rounded p-3">
      <div className="text-sm text-gray-600">{label}</div>
      <div className="text-lg font-bold">{value}</div>
    </div>
  );
}
