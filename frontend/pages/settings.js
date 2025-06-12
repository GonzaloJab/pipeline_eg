import { useState, useEffect } from 'react';

export default function Settings() {
  const [settings, setSettings] = useState({
    apiUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    tensorboardUrl: process.env.NEXT_PUBLIC_ML_FLOW_URL || 'http://localhost:6006',
  });

  const handleChange = (field) => (e) => {
    setSettings({ ...settings, [field]: e.target.value });
  };

  const handleSave = () => {
    // In a real application, you would save these settings to a backend or local storage
    console.log('Saving settings:', settings);
  };

  return (
    <div className="max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold mb-8">Settings</h1>

      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h2 className="text-lg font-medium text-gray-900 mb-4">API Configuration</h2>
          
          <div className="space-y-6">
            <div>
              <label htmlFor="apiUrl" className="block text-sm font-medium text-gray-700">
                API URL
              </label>
              <input
                type="text"
                id="apiUrl"
                value={settings.apiUrl}
                onChange={handleChange('apiUrl')}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
              <p className="mt-2 text-sm text-gray-500">
                The base URL for the backend API
              </p>
            </div>

            <div>
              <label htmlFor="tensorboardUrl" className="block text-sm font-medium text-gray-700">
                Tensorboard URL
              </label>
              <input
                type="text"
                id="tensorboardUrl"
                value={settings.tensorboardUrl}
                onChange={handleChange('tensorboardUrl')}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              />
              <p className="mt-2 text-sm text-gray-500">
                The URL for accessing Tensorboard visualizations
              </p>
            </div>

            <div className="pt-4">
              <button
                onClick={handleSave}
                className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                Save Settings
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}