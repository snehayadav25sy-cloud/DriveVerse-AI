import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

export default function Generate() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [projects, setProjects] = useState<any[]>([]);
  
  const [projectId, setProjectId] = useState('');
  const [scenario, setScenario] = useState('Urban Cruising');
  const [weather, setWeather] = useState('ClearNoon');
  const [roadType, setRoadType] = useState('City Street');
  const [frames, setFrames] = useState(200);

  useEffect(() => {
    async function fetchProjects() {
      try {
        const res = await fetch('http://127.0.0.1:8000/projects', { headers: { Authorization: `Bearer ${token}` } });
        const data = await res.json();
        setProjects(data);
        if (data.length > 0) setProjectId(data[0].id);
      } catch (e) {
        console.error(e);
      }
    }
    if (token) fetchProjects();
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectId) return alert("Please create a project first.");
    try {
      await fetch('http://127.0.0.1:8000/jobs', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ project_id: projectId, scenario, weather, road_type: roadType, frames }),
      });
      navigate('/');
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Generate Dataset</h1>
      
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Target Project</label>
          <select value={projectId} onChange={e => setProjectId(e.target.value)} required className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 bg-white">
            <option value="" disabled>Select a project</option>
            {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Scenario</label>
            <select value={scenario} onChange={e => setScenario(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 bg-white">
              <option>Urban Cruising</option>
              <option>Highway Merge</option>
              <option>Intersection Negotiation</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Weather</label>
            <select value={weather} onChange={e => setWeather(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 bg-white">
              <option>ClearNoon</option>
              <option>HeavyRainSunset</option>
              <option>FoggyNight</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Road Type</label>
            <select value={roadType} onChange={e => setRoadType(e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 bg-white">
              <option>City Street</option>
              <option>Highway</option>
              <option>Rural Road</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Number of Frames</label>
            <input type="number" value={frames} onChange={e => setFrames(parseInt(e.target.value))} min={10} max={1000} className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500" />
          </div>
        </div>

        <div className="pt-4 border-t border-gray-100 flex justify-end">
          <button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-md font-medium shadow-sm w-full md:w-auto">
            Submit Generation Request
          </button>
        </div>
      </form>
    </div>
  );
}
