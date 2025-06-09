// components/TrainingForm.js
import React, { useState, useEffect } from 'react';
import Button from "./ui/Button";
import { AVAILABLE_MODELS } from '../config/models';

export default function TrainingForm({ formData, handleChange, handleSubmit }) {
  const [csvFiles, setCsvFiles] = useState([]);
  const [error, setError] = useState(null);
  const [dbVersions, setDbVersions] = useState([]);
  const [existingNames, setExistingNames] = useState(new Set());
  const [nameError, setNameError] = useState('');
  
  const DATASET_TYPES = [
    'DnD',
    'PvsM',
    'Punct',
    'Multiple'
  ];

  useEffect(() => {
    async function fetchData() {
      try {
        const baseUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/trains$/, '') || 'http://localhost:8000';
        console.log('Fetching from base URL:', baseUrl); // Debug log
        
        // Fetch database versions
        const dbRes = await fetch(`${baseUrl}/database/versions`, {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
          mode: 'cors',
        });

        if (!dbRes.ok) {
          throw new Error(`HTTP error! status: ${dbRes.status} - ${await dbRes.text()}`);
        }
        const versions = await dbRes.json();
        console.log('Received versions:', versions); // Debug log
        setDbVersions(versions);
        
        // Fetch existing task names
        const namesRes = await fetch(`${baseUrl}/trains/names`, {
          method: 'GET',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          },
          mode: 'cors',
        });

        if (namesRes.ok) {
          const data = await namesRes.json();
          console.log('Received task names:', data); // Debug log
          setExistingNames(new Set(data.names));
        }
        
        // If no database is selected and we have versions, select the current one
        if (!formData.selectedDatabase && versions.length > 0) {
          const currentDb = versions.find(v => v.is_current) || versions[0];
          handleChange("selectedDatabase")({ target: { value: currentDb.path } });
        }

        setError(null);
      } catch (error) {
        console.error('Error fetching data:', error);
        setError(`Failed to fetch data: ${error.message}`);
      }
    }
    fetchData();
  }, []);

  const handleNameChange = (e) => {
    const newName = e.target.value;
    if (existingNames.has(newName)) {
      setNameError('This name already exists. Please choose a different name.');
    } else {
      setNameError('');
    }
    handleChange("name")(e);
  };

  const onSubmit = async (e) => {
    e.preventDefault();
    if (nameError) {
      return;
    }
    try {
      await handleSubmit(e);
      // If submission is successful, add the name to existing names
      setExistingNames(prev => new Set([...prev, formData.name]));
    } catch (error) {
      console.error('Error submitting form:', error);
    }
  };

  return (
    <form
      onSubmit={onSubmit}
      className="max-w-screen-lg mx-auto p-6 bg-white shadow-md rounded-md"
    >
      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
          <strong className="font-bold">Error!</strong>
          <span className="block sm:inline"> {error}</span>
        </div>
      )}
      {/* General Section */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
        {/* Task Name */}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Nombre tarea
          </label>
          <input
            type="text"
            placeholder="Task Name"
            required
            value={formData.name}
            onChange={handleNameChange}
            className={`w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
              nameError ? 'border-red-500' : ''
            }`}
          />
          {nameError && (
            <p className="text-red-500 text-sm mt-1">{nameError}</p>
          )}
        </div>
        {/* Modelo */}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Modelo
          </label>
          <select
            value={formData.model}
            onChange={handleChange("model")}
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">-- Select a model --</option>
            {AVAILABLE_MODELS.map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
          </select>
        </div>
        {/* Pesos */}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Pesos
          </label>
          <input
            type="text"
            placeholder="Weights"
            value={formData.weights}
            onChange={handleChange("weights")}
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Database and Dataset Type Selection */}
      <h2 className="text-2xl font-semibold text-gray-800 mb-4">
        Database & Dataset Selection
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
        {/* Database Selection */}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Select Database Version
          </label>
          <select
            value={formData.selectedDatabase || ''}
            onChange={handleChange("selectedDatabase")}
            required
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">-- Select a database --</option>
            {dbVersions.map((db) => (
              <option key={db.path} value={db.path}>
                {db.filename} {db.is_current ? '(Current)' : ''} - {new Date(db.created_at).toLocaleString()}
              </option>
            ))}
          </select>
        </div>
        {/* Dataset Type Selection */}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Select Dataset Type
          </label>
          <select
            value={formData.datasetType || ''}
            onChange={handleChange("datasetType")}
            required
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">-- Select a dataset type --</option>
            {DATASET_TYPES.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* File Paths Section */}
      <h2 className="text-2xl font-semibold text-gray-800 mb-4">
        Rutas de archivos
      </h2>
      <div className="grid grid-cols-1 sm:grid-cols-1 gap-4 mb-6">
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Imágenes:
          </label>
          <input
            type="text"
            placeholder="Data In"
            required
            value={formData.dataIn}
            onChange={handleChange("dataIn")}
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Guardar en:
          </label>
          <input
            type="text"
            placeholder="Output Directory"
            required
            value={formData.outputDirectory}
            onChange={handleChange("outputDirectory")}
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Hiperparámetros Section */}
      <h2 className="text-2xl font-semibold text-gray-800 mb-4">
        Hiperparámetros
      </h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-6">
        {/* Batch Size */}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Batch Size
          </label>
          <input
            type="number"
            required
            value={formData.batchSize}
            onChange={handleChange("batchSize")}
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        {/* Epochs */}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Epochs
          </label>
          <input
            type="number"
            required
            value={formData.epochs}
            onChange={handleChange("epochs")}
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        {/* Learning Rate */}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Learning Rate
          </label>
          <input
            type="number"
            step="0.0001"
            required
            value={formData.lr}
            onChange={handleChange("lr")}
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        {/* Exp LR Decrease Factor */}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Exp-LR Dec.Factor
          </label>
          <input
            type="number"
            step="0.01"
            required
            value={formData.expLRDecreaseFactor}
            onChange={handleChange("expLRDecreaseFactor")}
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        {/* Step Size */}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Step Size
          </label>
          <input
            type="number"
            required
            value={formData.stepSize}
            onChange={handleChange("stepSize")}
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        {/* Gamma */}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Gamma
          </label>
          <input
            type="number"
            step="0.01"
            required
            value={formData.gamma}
            onChange={handleChange("gamma")}
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Optimizer Settings Section */}
      <h2 className="text-2xl font-semibold text-gray-800 mb-4">
        Optimizer Settings
      </h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-6">
        {/* Solver */}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Solver
          </label>
          <select
            value={formData.solver}
            onChange={handleChange("solver")}
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="sgd">sgd</option>
            <option value="adam">adam</option>
          </select>
        </div>
        {/* Momentum */}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Momentum
          </label>
          <input
            type="number"
            step="0.01"
            required
            value={formData.momentum}
            onChange={handleChange("momentum")}
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        {/* Weight Decay */}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Weight Decay
          </label>
          <input
            type="number"
            step="0.0001"
            required
            value={formData.weightDecay}
            onChange={handleChange("weightDecay")}
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      {/* Other Settings Section */}
      <h2 className="text-2xl font-semibold text-gray-800 mb-4">
        Other Settings
      </h2>
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-4 mb-6">
        {/* Num Workers */}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Num Workers
          </label>
          <input
            type="number"
            required
            value={formData.numWorkers}
            onChange={handleChange("numWorkers")}
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        {/* Prefetch Factor */}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Prefetch Factor
          </label>
          <input
            type="number"
            required
            value={formData.prefetchFactor}
            onChange={handleChange("prefetchFactor")}
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div className="mt-6">
        <Button
          variant="default"
          type="submit"
          className="w-full bg-red-500 text-white py-2 rounded-md hover:bg-red-600"
        >
          Create Task
        </Button>
      </div>
    </form>
  );
}
