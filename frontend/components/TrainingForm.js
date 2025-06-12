// components/TrainingForm.js
import React, { useState, useEffect } from 'react';
import { AVAILABLE_MODELS_OPTIONS } from './formData/models';
import { AVAILABLE_WEIGHTS } from './formData/weights';
import { GPU_MEMORY_OPTIONS } from './formData/gpu';
import api from '../services/api';

export default function TrainingForm({ onSuccess }) {
  const [formData, setFormData] = useState({
    name: '',
    taskType: 'training',
    model: AVAILABLE_MODELS_OPTIONS[0] || '',
    weights: 'DEFAULT',
    datasetType: 'PvsM',
    selectedDatabase: '',
    outputDirectory: '/media/isend/ssd_storage/1_EYES_TRAIN/0_remote_runs/train_tasks',
    batchSize: 8,
    epochs: 10,
    lr: 0.001,
    expLRDecreaseFactor: 0.1,
    stepSize: 30,
    gamma: 0.1,
    solver: 'sgd',
    momentum: 0.9,
    weightDecay: 0.0001,
    numWorkers: 4,
    prefetchFactor: 2,
    gpu: '12GB',
    unfreeze_index: 0,
  });

  const [dbVersions, setDbVersions] = useState([]);
  const [selectedDb, setSelectedDb] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchSelectedDatabase = async () => {
    try {
      setError(null);
      const response = await api.getSelectedDatabase();
      if (response.data) {
        setSelectedDb(response.data);
        // Only update form data if we have a selected database
        if (response.data.path) {
          setFormData(prev => ({
            ...prev,
            selectedDatabase: response.data.path
          }));
        }
      }
    } catch (error) {
      console.error('Error fetching selected database:', error);
      setError('Failed to load selected database');
    }
  };

  const fetchDbVersions = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await api.getDatabaseVersions();
      if (response?.data) {
        setDbVersions(response.data);
      }
    } catch (error) {
      console.error('Error fetching database versions:', error);
      setError('Failed to load database versions');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchDbVersions();
    fetchSelectedDatabase();
  }, []);

  const handleDatabaseSelect = async (version) => {
    try {
      await api.setSelectedDatabase(version);
      setSelectedDb(version);
      setFormData(prev => ({
        ...prev,
        selectedDatabase: version.path
      }));
    } catch (error) {
      console.error('Error setting selected database:', error);
      setError('Failed to set selected database');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    try {
      const taskData = {
        ...formData,
        weights: formData.weights || 'DEFAULT'
      };
      await api.createTask(taskData);
      setIsLoading(false);
      if (onSuccess) onSuccess();
    } catch (err) {
      console.error('Error creating task:', err);
      setError(err.response?.data?.detail || 'Failed to create training task.');
      setIsLoading(false);
    }
  };

  const handleChange = (field) => (e) => {
    const value = e.target.type === 'number' ? parseFloat(e.target.value) : e.target.value;
    setFormData({ ...formData, [field]: value });
  };

  return (
    <div className="bg-white shadow rounded-lg">
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}
      <form onSubmit={handleSubmit} className="px-4 py-5 sm:p-6">
        <div className="space-y-4">
          {/* First row: 4 columns */}
          <div className="grid grid-cols-4 gap-4">
            {/* Task Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Task Name
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={handleChange("name")}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                required
              />
            </div>

            {/* Model Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Model
              </label>
              <select
                value={formData.model}
                onChange={handleChange("model")}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              >
                {AVAILABLE_MODELS_OPTIONS.map(model => (
                  <option key={model} value={model}>
                    {model}
                  </option>
                ))}
              </select>
            </div>

            {/* Weights */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                Weights
              </label>
              <select
                value={formData.weights}
                onChange={handleChange("weights")}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              >
                {AVAILABLE_WEIGHTS.map(weight => (
                  <option key={weight.value} value={weight.value}>
                    {weight.label}
                  </option>
                ))}
              </select>
            </div>

            {/* GPU Memory */}
            <div>
              <label className="block text-sm font-medium text-gray-700">
                GPU Memory
              </label>
              <select
                value={formData.gpu}
                onChange={handleChange("gpu")}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              >
                {GPU_MEMORY_OPTIONS.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Selected Database Display */}
          <div className="bg-gray-50 p-4 rounded-md">
            <label className="block text-sm font-medium text-gray-700">
              Selected Database
            </label>
            {selectedDb ? (
              <div className="text-gray-900">
                <p className="font-medium">{selectedDb.version}</p>
                <p className="text-sm text-gray-500 mt-1">{selectedDb.path}</p>
              </div>
            ) : (
              <div className="text-yellow-600 bg-yellow-50 p-2 rounded">
                No database selected. Please select one in the Database tab.
              </div>
            )}
          </div>

          {/* Dataset Type */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Dataset Type
            </label>
            <select
              value={formData.datasetType}
              onChange={handleChange("datasetType")}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
              required
            >
              <option value="">Select Dataset Type</option>
              <option value="DnD">DnD</option>
              <option value="PvsM">PvsM</option>
              <option value="Punct">Punct</option>
              <option value="Multiple">Multiple</option>
            </select>
          </div>

          {/* Training Parameters */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold">Training Parameters</h3>
            
            {/* First row of parameters */}
            <div className="grid grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Batch Size
                </label>
                <input
                  type="number"
                  value={formData.batchSize}
                  onChange={handleChange("batchSize")}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Epochs
                </label>
                <input
                  type="number"
                  value={formData.epochs}
                  onChange={handleChange("epochs")}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Learning Rate
                </label>
                <input
                  type="number"
                  value={formData.lr}
                  onChange={handleChange("lr")}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  step="0.0001"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  LR Decrease Factor
                </label>
                <input
                  type="number"
                  value={formData.expLRDecreaseFactor}
                  onChange={handleChange("expLRDecreaseFactor")}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  step="0.1"
                  required
                />
              </div>
            </div>

            {/* Second row of parameters */}
            <div className="grid grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Step Size
                </label>
                <input
                  type="number"
                  value={formData.stepSize}
                  onChange={handleChange("stepSize")}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Gamma
                </label>
                <input
                  type="number"
                  value={formData.gamma}
                  onChange={handleChange("gamma")}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  step="0.1"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Solver
                </label>
                <select
                  value={formData.solver}
                  onChange={handleChange("solver")}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                >
                  <option value="sgd">SGD</option>
                  <option value="adam">Adam</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Momentum
                </label>
                <input
                  type="number"
                  value={formData.momentum}
                  onChange={handleChange("momentum")}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  step="0.1"
                  required
                />
              </div>
            </div>

            {/* Third row of parameters */}
            <div className="grid grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Weight Decay
                </label>
                <input
                  type="number"
                  value={formData.weightDecay}
                  onChange={handleChange("weightDecay")}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  step="0.0001"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Num Workers
                </label>
                <input
                  type="number"
                  value={formData.numWorkers}
                  onChange={handleChange("numWorkers")}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Prefetch Factor
                </label>
                <input
                  type="number"
                  value={formData.prefetchFactor}
                  onChange={handleChange("prefetchFactor")}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700">
                  Unfreeze Index
                </label>
                <input
                  type="number"
                  value={formData.unfreeze_index}
                  onChange={handleChange("unfreeze_index")}
                  className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
                  required
                />
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className={`w-full py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white 
              ${isLoading ? 'bg-blue-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'} 
              focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500`}
          >
            {isLoading ? 'Creating...' : 'Create Training Task'}
          </button>
        </div>
      </form>
    </div>
  );
}
