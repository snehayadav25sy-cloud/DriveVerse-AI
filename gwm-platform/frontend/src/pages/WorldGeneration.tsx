import { useState } from 'react';
import { useWorldGeneration } from '../services/world';

export default function WorldGeneration() {
  const [location, setLocation] = useState('MG Road, Bengaluru');
  const [country, setCountry] = useState('india');
  const [scenario, setScenario] = useState('monsoon_evening');
  const [worldSeed, setWorldSeed] = useState(12345);
  const { generatePlan, generating, worldData } = useWorldGeneration();

  const handleGenerate = () => {
    generatePlan({
      resolved_scenario: {
        country,
        weather: scenario,
        traffic: 'heavy',
        time_of_day: 'sunset',
        road_type: 'urban',
      },
      map_artifact: {
        location_query: location,
        resolution: {
          resolved_latitude: 12.9755,
          resolved_longitude: 77.6068,
          resolved_country: 'India',
          resolved_city: 'Bengaluru',
        },
        carla_map_name: 'Town01',
      },
      country_profile: {
        id: country,
        rules: { drive_side: 'left' },
        vehicle_mix: { sedan: 0.4, motorcycle: 0.3, bus: 0.2, auto_rickshaw: 0.1 },
      },
      seeds: {
        world: worldSeed,
        traffic: worldSeed + 1,
        pedestrian: worldSeed + 2,
        weather: worldSeed + 3,
        asset: worldSeed + 4,
        scenario: worldSeed + 5,
      },
    });
  };

  const stats = worldData?.plan ? {
    buildings: worldData.plan.buildings?.length || 0,
    vegetation: worldData.plan.vegetation?.length || 0,
    street_furniture: worldData.plan.street_furniture?.length || 0,
    signs: worldData.plan.signs?.length || 0,
    traffic_lights: worldData.plan.traffic_lights?.length || 0,
    vehicles: worldData.plan.vehicles?.length || 0,
    pedestrians: worldData.plan.pedestrians?.length || 0,
    events: worldData.plan.events?.length || 0,
  } : null;

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-3xl font-bold mb-6">World Generation</h1>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Configuration</h2>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Location</label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full border rounded px-3 py-2"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Country</label>
            <select
              value={country}
              onChange={(e) => setCountry(e.target.value)}
              className="w-full border rounded px-3 py-2"
            >
              <option value="india">India</option>
              <option value="usa">USA</option>
              <option value="germany">Germany</option>
              <option value="japan">Japan</option>
              <option value="dubai">Dubai</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Scenario</label>
            <select
              value={scenario}
              onChange={(e) => setScenario(e.target.value)}
              className="w-full border rounded px-3 py-2"
            >
              <option value="monsoon_evening">Monsoon Evening</option>
              <option value="sunny_noon">Sunny Noon</option>
              <option value="foggy_morning">Foggy Morning</option>
              <option value="night_rain">Night Rain</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">World Seed</label>
            <input
              type="number"
              value={worldSeed}
              onChange={(e) => setWorldSeed(Number(e.target.value))}
              className="w-full border rounded px-3 py-2"
            />
          </div>
        </div>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="mt-4 bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
        >
          {generating ? 'Generating...' : 'Generate World Plan'}
        </button>
      </div>

      {stats && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">World Plan</h2>
          <div className="grid grid-cols-4 gap-4">
            <Stat label="Buildings" value={stats.buildings} />
            <Stat label="Vegetation" value={stats.vegetation} />
            <Stat label="Street Furniture" value={stats.street_furniture} />
            <Stat label="Signs" value={stats.signs} />
            <Stat label="Traffic Lights" value={stats.traffic_lights} />
            <Stat label="Vehicles" value={stats.vehicles} />
            <Stat label="Pedestrians" value={stats.pedestrians} />
            <Stat label="Events" value={stats.events} />
          </div>

          <div className="mt-6">
            <h3 className="font-semibold mb-2">Provenance</h3>
            <pre className="bg-gray-100 p-3 rounded text-sm overflow-auto">
              {JSON.stringify(worldData?.provenance, null, 2)}
            </pre>
          </div>

          {worldData?.plan?.asset_resolution_stats && (
            <div className="mt-4">
              <h3 className="font-semibold mb-2">Asset Resolution</h3>
              <div className="flex gap-4">
                <span>Exact: {worldData.plan.asset_resolution_stats.exact}</span>
                <span>Fallback: {worldData.plan.asset_resolution_stats.fallback}</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="bg-gray-50 rounded p-3 text-center">
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-sm text-gray-600">{label}</div>
    </div>
  );
}
