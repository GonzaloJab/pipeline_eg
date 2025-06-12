import React from 'react';

export default function DatabaseCard({ 
  version, 
  index, 
  selectedTrainingDb, 
  selectedTestingDb, 
  onDatabaseSelection 
}) {
  const handleUnselect = (type) => {
    onDatabaseSelection(null, type);
  };

  return (
    <div
      className={`p-4 rounded-lg border ${
        index === 0 ? 'bg-white border-gray-200' : 'bg-white border-gray-200'
      }`}
    >
      <div className="flex justify-between items-start">
        <div>
          <h3 className="text-sm font-medium text-gray-900">{version.filename}</h3>
          <p className="text-sm text-gray-500 mt-1">
            Created: {new Date(version.created_at).toLocaleString()}
          </p>
          <p className="text-sm text-gray-500">Path: {version.path}</p>
        </div>
        <div className="flex gap-2">
          {selectedTrainingDb?.version === version.filename ? (
            <button
              onClick={() => handleUnselect('training')}
              className="px-3 py-1 text-xs font-medium rounded-full bg-blue-100 text-blue-800 border border-blue-300 hover:bg-blue-200"
            >
              Unselect Training
            </button>
          ) : (
            <button
              onClick={() => onDatabaseSelection(version, 'training')}
              className="px-3 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800 border border-gray-200 hover:bg-gray-200"
            >
              Use for Training
            </button>
          )}
          
          {selectedTestingDb?.version === version.filename ? (
            <button
              onClick={() => handleUnselect('testing')}
              className="px-3 py-1 text-xs font-medium rounded-full bg-purple-100 text-purple-800 border border-purple-300 hover:bg-purple-200"
            >
              Unselect Testing
            </button>
          ) : (
            <button
              onClick={() => onDatabaseSelection(version, 'testing')}
              className="px-3 py-1 text-xs font-medium rounded-full bg-gray-100 text-gray-800 border border-gray-200 hover:bg-gray-200"
            >
              Use for Testing
            </button>
          )}
        </div>
      </div>
    </div>
  );
} 