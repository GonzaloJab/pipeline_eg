import { useState, useEffect } from 'react';
import DatabaseCard from '../components/DatabaseCard';
import api from '../services/api';

export default function Database() {
  const [dbVersions, setDbVersions] = useState([]);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [refreshStatus, setRefreshStatus] = useState(null);
  const [selectedTrainingDb, setSelectedTrainingDb] = useState(null);
  const [selectedTestingDb, setSelectedTestingDb] = useState(null);

  useEffect(() => {
    fetchDbVersions();
    // Load saved selections from localStorage
    const savedTrainingDb = localStorage.getItem('selectedTrainingDb');
    const savedTestingDb = localStorage.getItem('selectedTestingDb');
    if (savedTrainingDb) setSelectedTrainingDb(JSON.parse(savedTrainingDb));
    if (savedTestingDb) setSelectedTestingDb(JSON.parse(savedTestingDb));
  }, []);

  const fetchDbVersions = async () => {
    try {
      console.log('Fetching database versions...');
      const response = await api.getDatabaseVersions();
      console.log('Database versions response:', response);
      setDbVersions(response.data);
      setError(null);
    } catch (error) {
      console.error('Error fetching database versions:', error);
      setError('Failed to fetch database versions. Please check if the backend server is running.');
    }
  };

  const handleRefreshDatabase = async () => {
    try {
      setIsRefreshing(true);
      setError(null);
      const response = await api.refreshDatabase();
      const result = response.data;
      setRefreshStatus(result);
      
      // If the database was updated, refresh the versions list
      if (result.status === 'updated') {
        await fetchDbVersions();
      }
    } catch (error) {
      console.error('Error refreshing database:', error);
      setError(error.message || 'Failed to refresh database. Please try again.');
      setRefreshStatus(null);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleDatabaseSelection = (version, type) => {
    const selection = version ? {
      path: version.path,
      version: version.filename,
      selected_at: new Date().toISOString()
    } : null;

    if (type === 'training') {
      setSelectedTrainingDb(selection);
      if (selection) {
        localStorage.setItem('selectedTrainingDb', JSON.stringify(selection));
        console.log('Saved training database selection:', selection);
      } else {
        localStorage.removeItem('selectedTrainingDb');
      }
    } else {
      setSelectedTestingDb(selection);
      if (selection) {
        localStorage.setItem('selectedTestingDb', JSON.stringify(selection));
      } else {
        localStorage.removeItem('selectedTestingDb');
      }
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-3xl font-bold">Database Management</h1>
        <div className="flex gap-4">
          <button
            onClick={handleRefreshDatabase}
            disabled={isRefreshing}
            className={`inline-flex items-center px-4 py-2 border rounded-md shadow-sm text-sm font-medium
              ${isRefreshing 
                ? 'bg-gray-100 text-gray-500 cursor-not-allowed' 
                : 'bg-white text-gray-700 hover:bg-gray-50 border-gray-300'
              }
              focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500`}
          >
            {isRefreshing ? (
              <>
                <svg className="animate-spin h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
                </svg>
                Checking for changes...
              </>
            ) : (
              'Refresh Database'
            )}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
          <strong className="font-bold">Error!</strong>
          <span className="block sm:inline"> {error}</span>
        </div>
      )}

      {refreshStatus && (
        <div className={`mb-6 p-4 rounded-lg border ${
          refreshStatus.status === 'updated'
            ? 'bg-green-50 border-green-200 text-green-800'
            : 'bg-blue-50 border-blue-200 text-blue-800'
        }`}>
          <h3 className="font-medium mb-2">
            {refreshStatus.message}
          </h3>
          {refreshStatus.details && (
            <div className="mt-2 text-sm">
              <p>Checked {refreshStatus.details.total_directories} directories</p>
              {refreshStatus.details.modified_directories?.length > 0 && (
                <>
                  <p className="mt-1 font-medium">Modified directories:</p>
                  <ul className="list-disc list-inside mt-1">
                    {refreshStatus.details.modified_directories.map((dir, index) => (
                      <li key={index} className="truncate">{dir}</li>
                    ))}
                  </ul>
                </>
              )}
            </div>
          )}
          <p className="text-xs mt-2 text-gray-600">
            Next automatic check scheduled for 3:00 AM
          </p>
        </div>
      )}

      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-lg font-medium text-gray-900">Database Version History</h2>
            <div className="flex gap-4">
              <div className="text-sm">
                <p className="font-medium text-gray-700">Training DB:</p>
                <p className="text-gray-500 truncate max-w-xs">
                  {selectedTrainingDb?.version || 'None selected'}
                </p>
              </div>
              <div className="text-sm">
                <p className="font-medium text-gray-700">Testing DB:</p>
                <p className="text-gray-500 truncate max-w-xs">
                  {selectedTestingDb?.version || 'None selected'}
                </p>
              </div>
            </div>
          </div>
          <div className="space-y-4">
            {dbVersions.map((version, index) => (
              <DatabaseCard
                key={version.filename}
                version={version}
                index={index}
                selectedTrainingDb={selectedTrainingDb}
                selectedTestingDb={selectedTestingDb}
                onDatabaseSelection={handleDatabaseSelection}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
} 