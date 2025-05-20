// components/TrainingForm.js
import React, { useState, useEffect } from 'react';
import Button from "@/components/ui/Button";

export default function TrainingForm({ formData, handleChange, handleSubmit }) {
  const [csvFiles, setCsvFiles] = useState([]);

  useEffect(() => {
    async function fetchCsvFiles() {
      try {
        // Derive the base URL from NEXT_PUBLIC_API_URL (assumes it ends with "/trains" and removes it)
        const baseUrl = process.env.NEXT_PUBLIC_API_URL.replace(/\/trains$/, '');
        const res = await fetch(`${baseUrl}/csv-files`);
        const files = await res.json();
        setCsvFiles(Array.isArray(files) ? files : files.files || []);
        console.log("CSV:", files);
      } catch (error) {
        console.error('Error fetching CSV files:', error);
      }
    }
    fetchCsvFiles();
  }, []);

  return (
    <form
      onSubmit={handleSubmit}
      className="max-w-screen-lg mx-auto p-6 bg-white shadow-md rounded-md"
    >
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
            onChange={handleChange("name")}
            className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
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
            <option value="DnD">DnD</option>
            <option value="PvsM">PvsM</option>
            <option value="MULTI">MULTI</option>
            <option value="PUNCT">PUNCT</option>
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

      {/* CSV Dataset Selection */}
      <div className="space-y-1 mb-6">
        <label className="block text-sm font-medium text-gray-700">
          Training dataset
        </label>
        <select
          value={formData.selectedCsv || ""}
          onChange={handleChange("selectedCsv")}
          className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">-- Selecciona un archivo CSV --</option>
          {csvFiles.map((file) => (
            <option key={file} value={file}>
              {file}
            </option>
          ))}
        </select>
      </div>
        {/* CSV Dataset Selection */}
        <div className="space-y-1 mb-6">
        <label className="block text-sm font-medium text-gray-700">
          Validation dataset
        </label>
        <select
          value={formData.selectedCsv || ""}
          onChange={handleChange("selectedCsv")}
          className="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">-- Selecciona un archivo CSV --</option>
          {csvFiles.map((file) => (
            <option key={file} value={file}>
              {file}
            </option>
          ))}
        </select>
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
        {/* Unfreeze Index */}
        <div className="space-y-1">
          <label className="block text-sm font-medium text-gray-700">
            Unfreeze Index
          </label>
          <input
            type="number"
            required
            value={formData.unfreezeIndex}
            onChange={handleChange("unfreezeIndex")}
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
